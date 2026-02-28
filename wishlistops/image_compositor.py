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
import tempfile
import os

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
        Resize image to exact Steam specifications with AI upscaling.
        
        Args:
            image: Input image
            
        Returns:
            Resized image (800x450) with enhanced quality
        """
        target_size = (self.STEAM_WIDTH, self.STEAM_HEIGHT)
        
        if image.size == target_size:
            return image
        
        logger.debug(f"Resizing from {image.size} to {target_size}")
        
        # First, smart crop to correct aspect ratio
        cropped = self._smart_crop(image, *target_size)
        
        # Determine if we're upscaling or downscaling
        needs_upscale = cropped.width < target_size[0] or cropped.height < target_size[1]
        
        if needs_upscale:
            logger.info(f"Upscaling detected ({cropped.size} -> {target_size}), using AI enhancement")
            try:
                # Try AI upscaling for better quality
                upscaled = self._ai_upscale(cropped, target_size)
                if upscaled is not None:
                    return upscaled
            except Exception as e:
                logger.warning(f"AI upscaling failed, using standard resize: {e}")
        
        # Fallback to high-quality LANCZOS resize
        return cropped.resize(target_size, Resampling.LANCZOS)
    
    def _ai_upscale(self, image: Image.Image, target_size: Tuple[int, int]) -> Optional[Image.Image]:
        """
        AI-powered upscaling using Real-ESRGAN (state-of-the-art super-resolution).
        Falls back to enhanced OpenCV methods if Real-ESRGAN unavailable.
        
        Args:
            image: Input image to upscale
            target_size: Target dimensions
            
        Returns:
            Upscaled image with maximum quality
        """
        # Try Real-ESRGAN first (best quality)
        result = self._realesrgan_upscale(image, target_size)
        if result is not None:
            return result
        
        # Fallback to enhanced OpenCV (good quality)
        return self._opencv_enhanced_upscale(image, target_size)
    
    def _realesrgan_upscale(self, image: Image.Image, target_size: Tuple[int, int]) -> Optional[Image.Image]:
        """
        Use Real-ESRGAN for photo-realistic super-resolution.
        This is the industry-standard method for high-quality upscaling.
        """
        try:
            from realesrgan import RealESRGANer
            from basicsr.archs.rrdbnet_arch import RRDBNet
            import torch
            import cv2
            import numpy as np
            
            # Calculate scale needed
            scale_x = target_size[0] / image.width
            scale_y = target_size[1] / image.height
            scale = max(scale_x, scale_y)
            
            # Choose appropriate model based on scale
            if scale <= 2:
                model_name = 'RealESRGAN_x2plus'
                model_scale = 2
            elif scale <= 4:
                model_name = 'RealESRGAN_x4plus'
                model_scale = 4
            else:
                # For very large scales, upscale in stages
                model_name = 'RealESRGAN_x4plus'
                model_scale = 4
            
            # Initialize model
            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=model_scale)
            
            # Determine device
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            
            # Create upsampler
            upsampler = RealESRGANer(
                scale=model_scale,
                model_path=f'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/{model_name}.pth',
                model=model,
                tile=400,  # Tile size for memory efficiency
                tile_pad=10,
                pre_pad=0,
                half=True if device.type == 'cuda' else False,
                device=device
            )
            
            # Convert PIL to cv2 format
            img_array = np.array(image)
            if len(img_array.shape) == 2:
                img_cv = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)
                is_gray = True
            elif img_array.shape[2] == 4:  # RGBA
                alpha = img_array[:, :, 3]
                img_cv = cv2.cvtColor(img_array[:, :, :3], cv2.COLOR_RGB2BGR)
                is_alpha = True
            else:  # RGB
                img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                is_alpha = False
                is_gray = False
            
            # Upscale with Real-ESRGAN
            output, _ = upsampler.enhance(img_cv, outscale=scale)
            
            # Resize to exact target if needed
            if (output.shape[1], output.shape[0]) != target_size:
                output = cv2.resize(output, target_size, interpolation=cv2.INTER_LANCZOS4)
            
            logger.info(f"✨ Real-ESRGAN upscaling: {image.width}x{image.height} → {target_size[0]}x{target_size[1]} ({scale:.1f}x)")
            
            # Convert back to PIL
            output_rgb = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)
            
            if 'is_alpha' in locals() and is_alpha:
                # Resize and merge alpha
                alpha_resized = cv2.resize(alpha, target_size, interpolation=cv2.INTER_LANCZOS4)
                output_rgba = np.dstack((output_rgb, alpha_resized))
                return Image.fromarray(output_rgba, 'RGBA')
            elif 'is_gray' in locals() and is_gray:
                gray = cv2.cvtColor(output, cv2.COLOR_BGR2GRAY)
                return Image.fromarray(gray, 'L')
            else:
                return Image.fromarray(output_rgb, 'RGB')
        
        except ImportError:
            logger.debug("Real-ESRGAN not available, falling back to OpenCV")
            return None
        except Exception as e:
            logger.warning(f"Real-ESRGAN failed ({e}), falling back to OpenCV")
            return None
    
    def _opencv_enhanced_upscale(self, image: Image.Image, target_size: Tuple[int, int]) -> Optional[Image.Image]:
        """
        Enhanced OpenCV upscaling with multiple quality improvements.
        Used as fallback when Real-ESRGAN is not available.
        """
        try:
            import cv2
            import numpy as np
            
            # Convert PIL to OpenCV
            img_array = np.array(image)
            if len(img_array.shape) == 2:
                img_cv = img_array
                alpha = None
            elif img_array.shape[2] == 4:  # RGBA
                alpha = img_array[:, :, 3]
                img_cv = cv2.cvtColor(img_array[:, :, :3], cv2.COLOR_RGB2BGR)
            else:  # RGB
                img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                alpha = None
            
            # Use LANCZOS4 for high-quality upscaling
            result = cv2.resize(img_cv, target_size, interpolation=cv2.INTER_LANCZOS4)
            
            # Apply unsharp mask for better clarity
            gaussian = cv2.GaussianBlur(result, (0, 0), 2.0)
            result = cv2.addWeighted(result, 1.5, gaussian, -0.5, 0)
            
            # Apply bilateral filter to reduce noise while keeping edges sharp
            result = cv2.bilateralFilter(result, 5, 50, 50)
            
            # Subtle contrast enhancement
            lab = cv2.cvtColor(result, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            result = cv2.merge([l, a, b])
            result = cv2.cvtColor(result, cv2.COLOR_LAB2BGR)
            
            logger.info(f"Enhanced OpenCV upscaling: LANCZOS4 + unsharp mask + bilateral filter")
            
            # Convert back to PIL
            if alpha is not None:
                alpha_resized = cv2.resize(alpha, target_size, interpolation=cv2.INTER_LANCZOS4)
                result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
                result_rgba = np.dstack((result_rgb, alpha_resized))
                return Image.fromarray(result_rgba, 'RGBA')
            else:
                result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
                return Image.fromarray(result_rgb, 'RGB')
                
        except ImportError:
            logger.debug("OpenCV not available for enhanced upscaling")
            return None
        except Exception as e:
            logger.warning(f"Enhanced upscaling error: {e}")
            return None

    def _smart_crop(self, image: Image.Image, target_width: int, target_height: int) -> Image.Image:
        """Content-aware crop using edge detection to preserve important details."""
        target_ratio = target_width / target_height
        current_ratio = image.width / image.height

        if abs(current_ratio - target_ratio) < 1e-3:
            return image

        try:
            import cv2
            import numpy as np
            
            # Convert PIL to OpenCV format
            img_array = np.array(image)
            if len(img_array.shape) == 2:  # Grayscale
                img_cv = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)
            elif img_array.shape[2] == 4:  # RGBA
                img_cv = cv2.cvtColor(img_array[:, :, :3], cv2.COLOR_RGB2BGR)
            else:  # RGB
                img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale for edge detection
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            
            # Use Canny edge detection to find important features
            edges = cv2.Canny(gray, 50, 150)
            
            # Apply Gaussian blur to create heat map
            heatmap = cv2.GaussianBlur(edges, (21, 21), 0)
            
            # Find regions with most edges (important content)
            if current_ratio > target_ratio:
                # Image is wider - find best vertical strip
                new_width = int(image.height * target_ratio)
                
                # Sum edges column-wise to find content-rich regions
                col_sums = np.sum(heatmap, axis=0)
                
                # Use sliding window to find best region
                best_score = 0
                best_offset = (image.width - new_width) // 2  # Default center
                
                for offset in range(0, max(1, image.width - new_width + 1), max(1, new_width // 20)):
                    score = np.sum(col_sums[offset:offset + new_width])
                    if score > best_score:
                        best_score = score
                        best_offset = offset
                
                box = (best_offset, 0, best_offset + new_width, image.height)
                logger.debug(f"Smart horizontal crop: offset={best_offset} (score={best_score:.0f})")
            else:
                # Image is taller - find best horizontal strip
                new_height = int(image.width / target_ratio)
                
                # Sum edges row-wise to find content-rich regions
                row_sums = np.sum(heatmap, axis=1)
                
                # Use sliding window to find best region
                best_score = 0
                best_offset = (image.height - new_height) // 2  # Default center
                
                for offset in range(0, max(1, image.height - new_height + 1), max(1, new_height // 20)):
                    score = np.sum(row_sums[offset:offset + new_height])
                    if score > best_score:
                        best_score = score
                        best_offset = offset
                
                box = (0, best_offset, image.width, best_offset + new_height)
                logger.debug(f"Smart vertical crop: offset={best_offset} (score={best_score:.0f})")
                
        except (ImportError, Exception) as e:
            logger.warning(f"Content-aware crop failed, using center crop: {e}")
            # Fallback to center crop
            if current_ratio > target_ratio:
                new_width = int(image.height * target_ratio)
                offset = (image.width - new_width) // 2
                box = (offset, 0, offset + new_width, image.height)
            else:
                new_height = int(image.width / target_ratio)
                offset = (image.height - new_height) // 2
                box = (0, offset, image.width, offset + new_height)

        logger.debug(f"Crop box: {box}")
        return image.crop(box)
    
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
