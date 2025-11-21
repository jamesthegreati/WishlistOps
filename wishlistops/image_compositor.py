"""
Image compositor for logo overlay on AI-generated banners.

Composites game logos onto AI-generated banner images with proper
positioning, sizing, and effects for Steam requirements.

Architecture: See 04_WishlistOps_System_Architecture_Diagrams.md Section 3
"""

import logging
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops
from PIL.Image import Resampling

from .models import BrandingConfig


logger = logging.getLogger(__name__)


class CompositorError(Exception):
    """Base exception for compositor errors."""
    pass


class ImageCompositor:
    """
    Composite game logos onto AI-generated banners.
    
    Handles:
    - Resizing to Steam specifications
    - Logo positioning with safe zones
    - Drop shadow effects
    - Alpha blending
    - File optimization
    
    Attributes:
        config: Branding configuration
    """
    
    # Steam banner specifications
    STEAM_WIDTH = 800
    STEAM_HEIGHT = 450
    
    # Safe zones (pixels from edge)
    SAFE_ZONE_HORIZONTAL = 40
    SAFE_ZONE_VERTICAL = 40
    
    def __init__(self, config: BrandingConfig) -> None:
        """
        Initialize image compositor.
        
        Args:
            config: Branding configuration with logo settings
        """
        self.config = config
        logger.info("Image compositor initialized", extra={
            "logo_position": config.logo_position,
            "logo_size_percent": config.logo_size_percent
        })
    
    def composite_logo(
        self,
        base_image_data: bytes,
        logo_path: Optional[Path] = None,
        output_path: Optional[Path] = None
    ) -> bytes:
        """
        Composite logo onto base image.
        
        Args:
            base_image_data: Base banner image bytes (from AI)
            logo_path: Path to logo PNG (uses config default if None)
            output_path: Path to save result (optional)
            
        Returns:
            Final composited image as PNG bytes
            
        Raises:
            CompositorError: If compositing fails
        """
        try:
            # Load base image
            base_image = Image.open(BytesIO(base_image_data))
            logger.info("Loaded base image", extra={
                "size": base_image.size,
                "mode": base_image.mode
            })
            
            # Resize to Steam specifications
            base_image = self._resize_to_steam_specs(base_image)
            if base_image.mode != 'RGBA':
                base_image = base_image.convert('RGBA')
            
            # Get logo path
            logo_path = logo_path or (Path(self.config.logo_path) if self.config.logo_path else None)
            
            # If no logo, return base image
            if not logo_path or not logo_path.exists():
                logger.warning(f"Logo not found: {logo_path}, skipping overlay")
                return self._image_to_bytes(base_image)
            
            # Load and process logo
            logo = self._load_and_prepare_logo(logo_path)
            
            # Calculate position
            position = self._calculate_logo_position(base_image.size, logo.size)
            
            # Create shadow layer
            shadow = self._create_drop_shadow(logo)
            
            # Composite shadow first
            base_image.paste(shadow, position, shadow)
            
            # Composite logo
            base_image.paste(logo, position, logo)
            
            logger.info("Logo composited successfully", extra={
                "logo_size": logo.size,
                "position": position
            })
            
            # Convert to bytes
            result_bytes = self._image_to_bytes(base_image)
            
            # Save if output path provided
            if output_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'wb') as f:
                    f.write(result_bytes)
                logger.info(f"Saved composited image: {output_path}")
            
            return result_bytes
            
        except Exception as e:
            raise CompositorError(f"Failed to composite logo: {e}") from e
    
    def _resize_to_steam_specs(self, image: Image.Image) -> Image.Image:
        """
        Resize image to exact Steam specifications.
        
        Args:
            image: Input image
            
        Returns:
            Resized image (800x450)
        """
        target_size = (self.STEAM_WIDTH, self.STEAM_HEIGHT)
        
        if image.size == target_size:
            return image
        
        logger.debug(f"Resizing from {image.size} to {target_size}")
        
        # Use high-quality Lanczos resampling
        return image.resize(target_size, Resampling.LANCZOS)
    
    def _load_and_prepare_logo(self, logo_path: Path) -> Image.Image:
        """
        Load logo and prepare for compositing.
        
        Args:
            logo_path: Path to logo file
            
        Returns:
            Prepared logo image with alpha channel
            
        Raises:
            CompositorError: If logo cannot be loaded
        """
        try:
            logo = Image.open(logo_path)
            
            # Ensure RGBA mode (with alpha channel)
            if logo.mode != 'RGBA':
                logger.debug(f"Converting logo from {logo.mode} to RGBA")
                logo = logo.convert('RGBA')
            
            # Calculate target logo size
            target_width = int(self.STEAM_WIDTH * self.config.logo_size_percent / 100)
            
            # Maintain aspect ratio
            aspect_ratio = logo.height / logo.width
            target_height = int(target_width * aspect_ratio)
            target_size = (target_width, target_height)
            
            # Resize logo
            if logo.size != target_size:
                logger.debug(f"Resizing logo from {logo.size} to {target_size}")
                logo = logo.resize(target_size, Resampling.LANCZOS)
            
            # Apply configured opacity to logo alpha channel
            if self.config.logo_opacity < 1.0:
                alpha = logo.split()[3]
                adjusted_alpha = alpha.point(
                    lambda value: int(value * self.config.logo_opacity)
                )
                logo.putalpha(adjusted_alpha)
            
            return logo
            
        except Exception as e:
            raise CompositorError(f"Failed to load logo from {logo_path}: {e}") from e
    
    def _calculate_logo_position(
        self,
        banner_size: Tuple[int, int],
        logo_size: Tuple[int, int]
    ) -> Tuple[int, int]:
        """
        Calculate logo position based on configuration.
        
        Args:
            banner_size: Size of banner (width, height)
            logo_size: Size of logo (width, height)
            
        Returns:
            Position tuple (x, y) for top-left corner of logo
        """
        banner_width, banner_height = banner_size
        logo_width, logo_height = logo_size
        
        position_str = self.config.logo_position.value
        
        # Calculate positions with safe zones
        if position_str == "top-left":
            x = self.SAFE_ZONE_HORIZONTAL
            y = self.SAFE_ZONE_VERTICAL
        
        elif position_str == "top-right":
            x = banner_width - logo_width - self.SAFE_ZONE_HORIZONTAL
            y = self.SAFE_ZONE_VERTICAL
        
        elif position_str == "center":
            x = (banner_width - logo_width) // 2
            y = (banner_height - logo_height) // 2
        
        elif position_str == "bottom-left":
            x = self.SAFE_ZONE_HORIZONTAL
            y = banner_height - logo_height - self.SAFE_ZONE_VERTICAL
        
        elif position_str == "bottom-right":
            x = banner_width - logo_width - self.SAFE_ZONE_HORIZONTAL
            y = banner_height - logo_height - self.SAFE_ZONE_VERTICAL
        
        else:
            # Default to top-right
            x = banner_width - logo_width - self.SAFE_ZONE_HORIZONTAL
            y = self.SAFE_ZONE_VERTICAL
        
        logger.debug(f"Logo position: {position_str} -> ({x}, {y})")
        
        return (x, y)
    
    def _create_drop_shadow(
        self,
        logo: Image.Image,
        offset: Tuple[int, int] = (4, 4),
        blur_radius: int = 8,
        color: Tuple[int, int, int, int] = (0, 0, 0, 180)
    ) -> Image.Image:
        """
        Create drop shadow for logo visibility.
        
        Args:
            logo: Logo image
            offset: Shadow offset (x, y)
            blur_radius: Blur amount
            color: Shadow color (R, G, B, A)
            
        Returns:
            Shadow layer as RGBA image
        """
        # Create shadow layer (same size as logo)
        shadow = Image.new('RGBA', logo.size, (0, 0, 0, 0))
        offset_x, offset_y = offset
        
        # Extract alpha channel from logo
        if logo.mode == 'RGBA':
            alpha = logo.split()[3]
        else:
            alpha = Image.new('L', logo.size, 255)
        
        # Create shadow mask from alpha and apply blur
        shadow_alpha = Image.new('L', logo.size, 0)
        shadow_alpha.paste(color[3], (0, 0), alpha)
        shadow_alpha = shadow_alpha.filter(ImageFilter.GaussianBlur(blur_radius))
        
        # Offset shadow to create depth, clearing wrapped regions
        shadow_alpha = ImageChops.offset(shadow_alpha, offset_x, offset_y)
        if offset_x > 0:
            shadow_alpha.paste(0, (0, 0, offset_x, shadow_alpha.height))
        elif offset_x < 0:
            shadow_alpha.paste(0, (shadow_alpha.width + offset_x, 0, shadow_alpha.width, shadow_alpha.height))
        if offset_y > 0:
            shadow_alpha.paste(0, (0, 0, shadow_alpha.width, offset_y))
        elif offset_y < 0:
            shadow_alpha.paste(0, (0, shadow_alpha.height + offset_y, shadow_alpha.width, shadow_alpha.height))
        
        # Create colored shadow
        shadow = Image.merge('RGBA', (
            Image.new('L', logo.size, color[0]),
            Image.new('L', logo.size, color[1]),
            Image.new('L', logo.size, color[2]),
            shadow_alpha
        ))
        
        return shadow
    
    def _image_to_bytes(self, image: Image.Image) -> bytes:
        """
        Convert PIL Image to PNG bytes.
        
        Args:
            image: PIL Image
            
        Returns:
            PNG bytes
        """
        buffer = BytesIO()
        
        # Optimize for file size
        image.save(
            buffer,
            format='PNG',
            optimize=True,
            compress_level=6  # Balance between size and speed
        )
        
        buffer.seek(0)
        return buffer.read()
    
    def add_text_overlay(
        self,
        image_data: bytes,
        text: str,
        position: str = "bottom",
        font_size: int = 24
    ) -> bytes:
        """
        Add text overlay to image (for version numbers, etc.).
        
        Args:
            image_data: Input image bytes
            text: Text to add
            position: Position ("top", "bottom", "center")
            font_size: Font size in pixels
            
        Returns:
            Image with text overlay as bytes
        """
        image = Image.open(BytesIO(image_data))
        image = self._resize_to_steam_specs(image)
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        draw = ImageDraw.Draw(image)
        
        # Try to load a nice font, fall back to default
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        # Calculate text size and position
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        if position == "bottom":
            x = (image.width - text_width) // 2
            y = image.height - text_height - 20
        elif position == "top":
            x = (image.width - text_width) // 2
            y = 20
        else:  # center
            x = (image.width - text_width) // 2
            y = (image.height - text_height) // 2
        
        # Draw text with outline for visibility
        outline_range = 2
        for adj_x in range(-outline_range, outline_range + 1):
            for adj_y in range(-outline_range, outline_range + 1):
                draw.text((x + adj_x, y + adj_y), text, font=font, fill=(0, 0, 0, 255))
        
        # Draw main text
        draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
        
        return self._image_to_bytes(image)


# Convenience function
def composite_logo_simple(
    base_image_bytes: bytes,
    logo_path: Path,
    logo_size_percent: int = 25
) -> bytes:
    """
    Quick logo compositing (convenience function).
    
    Args:
        base_image_bytes: Base image
        logo_path: Path to logo
        logo_size_percent: Logo size as % of width
        
    Returns:
        Composited image bytes
    """
    from .models import BrandingConfig, LogoPosition
    
    config = BrandingConfig(
        art_style="default brand pack",
        logo_size_percent=logo_size_percent,
        logo_position=LogoPosition.TOP_RIGHT,
        logo_path=str(logo_path)
    )
    
    compositor = ImageCompositor(config)
    return compositor.composite_logo(base_image_bytes)
