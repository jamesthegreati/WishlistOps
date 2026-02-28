"""
Advanced Image Processing for WishlistOps.

Processes USER-PROVIDED screenshots and game images for Steam announcements.
This module does NOT generate images with AI - it only enhances and formats
images provided by the user.

Features:
- Smart content-aware cropping with saliency detection
- High-quality upscaling (optional ML enhancement available)
- Multiple quality presets
- Steam-optimized output

Dependencies: Only Pillow required (lightweight ~10MB)
Optional: Install wishlistops[image-enhancement] for AI upscaling (~3GB)
"""

import logging
from dataclasses import dataclass
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple, List, Union

from PIL import Image, ImageFilter, ImageDraw, ImageEnhance, ImageOps
from PIL.Image import Resampling

logger = logging.getLogger(__name__)


class QualityPreset(str, Enum):
    """Quality presets for different use cases."""
    FAST = "fast"           # Quick processing, good quality
    BALANCED = "balanced"   # Default - best quality/speed ratio
    QUALITY = "quality"     # Maximum quality, slower
    STEAM = "steam"         # Optimized for Steam (800x450)


class CropMode(str, Enum):
    """Cropping strategies."""
    CENTER = "center"           # Simple center crop
    SMART = "smart"             # Content-aware smart crop
    TOP = "top"                 # Favor top of image (landscapes)
    BOTTOM = "bottom"           # Favor bottom (UI screenshots)
    RULE_OF_THIRDS = "thirds"   # Position along rule of thirds


@dataclass
class ProcessingResult:
    """Result of image processing."""
    image_bytes: bytes
    original_size: Tuple[int, int]
    final_size: Tuple[int, int]
    crop_applied: bool
    crop_region: Optional[Tuple[int, int, int, int]]
    upscale_factor: float
    quality_score: float  # 0-100
    warnings: List[str]


class ImageProcessor:
    """
    Advanced image processor for Steam banners.
    
    Provides high-quality cropping and upscaling with minimal dependencies.
    Primary dependency is Pillow; numpy is optional for advanced features.
    """
    
    # Steam banner specifications
    STEAM_WIDTH = 800
    STEAM_HEIGHT = 450
    STEAM_ASPECT = STEAM_WIDTH / STEAM_HEIGHT  # ~1.778
    
    # Quality thresholds
    MIN_INPUT_WIDTH = 400
    MIN_INPUT_HEIGHT = 225
    OPTIMAL_INPUT_WIDTH = 1600
    OPTIMAL_INPUT_HEIGHT = 900
    
    def __init__(
        self,
        preset: QualityPreset = QualityPreset.BALANCED,
        crop_mode: CropMode = CropMode.SMART
    ):
        """
        Initialize image processor.
        
        Args:
            preset: Quality preset (fast/balanced/quality/steam)
            crop_mode: Cropping strategy
        """
        self.preset = preset
        self.crop_mode = crop_mode
        self._has_numpy = self._check_numpy()
        
        logger.info(f"ImageProcessor initialized: preset={preset.value}, crop_mode={crop_mode.value}")
    
    def _check_numpy(self) -> bool:
        """Check if numpy is available for advanced processing."""
        try:
            import numpy
            return True
        except ImportError:
            logger.debug("NumPy not available - using PIL-only processing")
            return False
    
    def process_for_steam(
        self,
        image_input: Union[bytes, Path, Image.Image],
        output_path: Optional[Path] = None
    ) -> ProcessingResult:
        """
        Process image for Steam banner (800x450).
        
        This is the main entry point for processing screenshots into
        Steam-ready announcement banners.
        
        Args:
            image_input: Image bytes, file path, or PIL Image
            output_path: Optional path to save output
            
        Returns:
            ProcessingResult with processed image and metadata
        """
        warnings: List[str] = []
        
        # Load image
        image, original_size = self._load_image(image_input)
        
        # Validate input
        input_warnings = self._validate_input(image)
        warnings.extend(input_warnings)
        
        # Calculate target aspect ratio crop
        target_size = (self.STEAM_WIDTH, self.STEAM_HEIGHT)
        
        # Step 1: Smart crop to correct aspect ratio
        cropped, crop_region = self._smart_crop(
            image,
            target_aspect=self.STEAM_ASPECT,
            mode=self.crop_mode
        )
        crop_applied = crop_region is not None
        
        # Step 2: Resize to final dimensions
        needs_upscale = cropped.width < target_size[0] or cropped.height < target_size[1]
        
        if needs_upscale:
            # Upscale with quality enhancement
            final = self._high_quality_upscale(cropped, target_size)
            upscale_factor = target_size[0] / cropped.width
        else:
            # Downscale with quality preservation
            final = self._high_quality_downscale(cropped, target_size)
            upscale_factor = target_size[0] / cropped.width
        
        # Step 3: Final enhancement based on preset
        if self.preset in (QualityPreset.QUALITY, QualityPreset.BALANCED):
            final = self._enhance_final(final)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(
            original_size, final.size, upscale_factor
        )
        
        # Convert to bytes
        image_bytes = self._image_to_bytes(final)
        
        # Save if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(image_bytes)
            logger.info(f"Saved processed image: {output_path}")
        
        return ProcessingResult(
            image_bytes=image_bytes,
            original_size=original_size,
            final_size=final.size,
            crop_applied=crop_applied,
            crop_region=crop_region,
            upscale_factor=upscale_factor,
            quality_score=quality_score,
            warnings=warnings
        )
    
    def _load_image(
        self,
        image_input: Union[bytes, Path, Image.Image]
    ) -> Tuple[Image.Image, Tuple[int, int]]:
        """Load image from various input types."""
        if isinstance(image_input, Image.Image):
            image = image_input
        elif isinstance(image_input, bytes):
            image = Image.open(BytesIO(image_input))
        elif isinstance(image_input, Path):
            image = Image.open(image_input)
        else:
            raise ValueError(f"Unsupported image input type: {type(image_input)}")
        
        original_size = image.size
        
        # Ensure RGBA mode for consistent processing
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        logger.debug(f"Loaded image: {original_size}, mode={image.mode}")
        return image, original_size
    
    def _validate_input(self, image: Image.Image) -> List[str]:
        """Validate input image and return warnings."""
        warnings = []
        
        if image.width < self.MIN_INPUT_WIDTH or image.height < self.MIN_INPUT_HEIGHT:
            warnings.append(
                f"Input image ({image.width}x{image.height}) is very small. "
                f"Minimum recommended: {self.MIN_INPUT_WIDTH}x{self.MIN_INPUT_HEIGHT}. "
                "Quality may be reduced."
            )
        elif image.width < self.OPTIMAL_INPUT_WIDTH or image.height < self.OPTIMAL_INPUT_HEIGHT:
            warnings.append(
                f"Input image ({image.width}x{image.height}) is below optimal size. "
                f"Recommended: {self.OPTIMAL_INPUT_WIDTH}x{self.OPTIMAL_INPUT_HEIGHT} for best results."
            )
        
        return warnings
    
    def _smart_crop(
        self,
        image: Image.Image,
        target_aspect: float,
        mode: CropMode
    ) -> Tuple[Image.Image, Optional[Tuple[int, int, int, int]]]:
        """
        Smart content-aware crop to target aspect ratio.
        
        Uses multiple techniques:
        1. Edge detection to find content-rich regions
        2. Brightness analysis to avoid cropping important areas
        3. Rule of thirds positioning
        """
        current_aspect = image.width / image.height
        
        # If already correct aspect ratio, no crop needed
        if abs(current_aspect - target_aspect) < 0.01:
            return image, None
        
        if mode == CropMode.CENTER:
            return self._center_crop(image, target_aspect)
        elif mode == CropMode.TOP:
            return self._position_crop(image, target_aspect, position="top")
        elif mode == CropMode.BOTTOM:
            return self._position_crop(image, target_aspect, position="bottom")
        elif mode == CropMode.RULE_OF_THIRDS:
            return self._thirds_crop(image, target_aspect)
        else:  # SMART
            return self._saliency_crop(image, target_aspect)
    
    def _center_crop(
        self,
        image: Image.Image,
        target_aspect: float
    ) -> Tuple[Image.Image, Tuple[int, int, int, int]]:
        """Simple center crop to target aspect ratio."""
        current_aspect = image.width / image.height
        
        if current_aspect > target_aspect:
            # Image is wider - crop width
            new_width = int(image.height * target_aspect)
            offset = (image.width - new_width) // 2
            box = (offset, 0, offset + new_width, image.height)
        else:
            # Image is taller - crop height
            new_height = int(image.width / target_aspect)
            offset = (image.height - new_height) // 2
            box = (0, offset, image.width, offset + new_height)
        
        return image.crop(box), box
    
    def _position_crop(
        self,
        image: Image.Image,
        target_aspect: float,
        position: str = "top"
    ) -> Tuple[Image.Image, Tuple[int, int, int, int]]:
        """Crop favoring top or bottom of image."""
        current_aspect = image.width / image.height
        
        if current_aspect > target_aspect:
            # Image is wider - crop width (center horizontally)
            new_width = int(image.height * target_aspect)
            offset = (image.width - new_width) // 2
            box = (offset, 0, offset + new_width, image.height)
        else:
            # Image is taller - crop height
            new_height = int(image.width / target_aspect)
            if position == "top":
                offset = 0
            else:  # bottom
                offset = image.height - new_height
            box = (0, offset, image.width, offset + new_height)
        
        return image.crop(box), box
    
    def _thirds_crop(
        self,
        image: Image.Image,
        target_aspect: float
    ) -> Tuple[Image.Image, Tuple[int, int, int, int]]:
        """Crop along rule of thirds lines."""
        current_aspect = image.width / image.height
        
        if current_aspect > target_aspect:
            new_width = int(image.height * target_aspect)
            # Position at 1/3 or 2/3 point
            max_offset = image.width - new_width
            offset = max_offset // 3  # Favor left third
            box = (offset, 0, offset + new_width, image.height)
        else:
            new_height = int(image.width / target_aspect)
            max_offset = image.height - new_height
            offset = max_offset // 3  # Favor upper third
            box = (0, offset, image.width, offset + new_height)
        
        return image.crop(box), box
    
    def _saliency_crop(
        self,
        image: Image.Image,
        target_aspect: float
    ) -> Tuple[Image.Image, Tuple[int, int, int, int]]:
        """
        Content-aware crop using saliency detection.
        
        Finds the most "interesting" region of the image using:
        - Edge detection (content boundaries)
        - Contrast analysis (areas with detail)
        - Brightness variance (avoid flat regions)
        """
        current_aspect = image.width / image.height
        
        # Generate saliency map
        saliency = self._compute_saliency_map(image)
        
        if current_aspect > target_aspect:
            # Image is wider - find best horizontal position
            new_width = int(image.height * target_aspect)
            best_offset = self._find_best_crop_position(
                saliency, "horizontal", new_width
            )
            box = (best_offset, 0, best_offset + new_width, image.height)
        else:
            # Image is taller - find best vertical position
            new_height = int(image.width / target_aspect)
            best_offset = self._find_best_crop_position(
                saliency, "vertical", new_height
            )
            box = (0, best_offset, image.width, best_offset + new_height)
        
        logger.debug(f"Saliency crop: box={box}")
        return image.crop(box), box
    
    def _compute_saliency_map(self, image: Image.Image) -> Image.Image:
        """
        Compute simple saliency map using PIL only.
        
        Combines:
        - Edge detection (find content boundaries)
        - Brightness variance (find areas with detail)
        """
        # Convert to grayscale for analysis
        gray = image.convert('L')
        
        # Edge detection using emboss filter
        edges = gray.filter(ImageFilter.FIND_EDGES)
        
        # Enhance edges
        edges = edges.filter(ImageFilter.GaussianBlur(radius=3))
        
        # Increase contrast for better saliency
        enhancer = ImageEnhance.Contrast(edges)
        saliency = enhancer.enhance(2.0)
        
        return saliency
    
    def _find_best_crop_position(
        self,
        saliency: Image.Image,
        direction: str,
        crop_size: int
    ) -> int:
        """Find best crop position based on saliency map."""
        # Convert to brightness values
        if self._has_numpy:
            return self._find_best_position_numpy(saliency, direction, crop_size)
        else:
            return self._find_best_position_pil(saliency, direction, crop_size)
    
    def _find_best_position_pil(
        self,
        saliency: Image.Image,
        direction: str,
        crop_size: int
    ) -> int:
        """Find best position using PIL-only (no numpy)."""
        width, height = saliency.size
        
        if direction == "horizontal":
            # Sum brightness along columns
            total_dimension = width
            step = max(1, crop_size // 20)  # Check every 5%
            
            best_score = 0
            best_offset = (total_dimension - crop_size) // 2  # Default center
            
            for offset in range(0, max(1, total_dimension - crop_size + 1), step):
                # Crop region and calculate brightness sum
                region = saliency.crop((offset, 0, offset + crop_size, height))
                # Get sum of all pixels (approximate brightness)
                score = sum(region.getdata())
                
                if score > best_score:
                    best_score = score
                    best_offset = offset
        else:
            # Sum brightness along rows
            total_dimension = height
            step = max(1, crop_size // 20)
            
            best_score = 0
            best_offset = (total_dimension - crop_size) // 2
            
            for offset in range(0, max(1, total_dimension - crop_size + 1), step):
                region = saliency.crop((0, offset, width, offset + crop_size))
                score = sum(region.getdata())
                
                if score > best_score:
                    best_score = score
                    best_offset = offset
        
        return best_offset
    
    def _find_best_position_numpy(
        self,
        saliency: Image.Image,
        direction: str,
        crop_size: int
    ) -> int:
        """Find best position using numpy for better performance."""
        import numpy as np
        
        arr = np.array(saliency)
        
        if direction == "horizontal":
            # Sum along columns
            col_sums = np.sum(arr, axis=0)
            total = len(col_sums)
            
            # Sliding window to find best region
            best_score = 0
            best_offset = (total - crop_size) // 2
            
            for offset in range(0, max(1, total - crop_size + 1), max(1, crop_size // 20)):
                score = np.sum(col_sums[offset:offset + crop_size])
                if score > best_score:
                    best_score = score
                    best_offset = offset
        else:
            # Sum along rows
            row_sums = np.sum(arr, axis=1)
            total = len(row_sums)
            
            best_score = 0
            best_offset = (total - crop_size) // 2
            
            for offset in range(0, max(1, total - crop_size + 1), max(1, crop_size // 20)):
                score = np.sum(row_sums[offset:offset + crop_size])
                if score > best_score:
                    best_score = score
                    best_offset = offset
        
        return best_offset
    
    def _high_quality_upscale(
        self,
        image: Image.Image,
        target_size: Tuple[int, int]
    ) -> Image.Image:
        """
        High-quality upscaling using Pillow only.
        
        Multi-step process:
        1. Initial LANCZOS upscale
        2. Unsharp mask for clarity
        3. Subtle contrast enhancement
        """
        logger.debug(f"Upscaling {image.size} -> {target_size}")
        
        # Step 1: LANCZOS upscale (best PIL resampling)
        upscaled = image.resize(target_size, Resampling.LANCZOS)
        
        # Step 2: Unsharp mask for clarity
        if self.preset != QualityPreset.FAST:
            upscaled = self._apply_unsharp_mask(upscaled, amount=1.2, radius=1.0, threshold=3)
        
        # Step 3: Subtle enhancement for quality preset
        if self.preset == QualityPreset.QUALITY:
            upscaled = self._subtle_enhance(upscaled)
        
        return upscaled
    
    def _high_quality_downscale(
        self,
        image: Image.Image,
        target_size: Tuple[int, int]
    ) -> Image.Image:
        """
        High-quality downscaling with anti-aliasing.
        
        For large images being reduced to Steam size.
        """
        logger.debug(f"Downscaling {image.size} -> {target_size}")
        
        # For large reductions, use progressive downscaling
        current = image
        current_size = image.size
        
        # Step down in 2x increments for better quality
        while current_size[0] > target_size[0] * 2:
            new_size = (current_size[0] // 2, current_size[1] // 2)
            current = current.resize(new_size, Resampling.LANCZOS)
            current_size = new_size
        
        # Final resize to exact target
        return current.resize(target_size, Resampling.LANCZOS)
    
    def _apply_unsharp_mask(
        self,
        image: Image.Image,
        amount: float = 1.5,
        radius: float = 1.0,
        threshold: int = 3
    ) -> Image.Image:
        """
        Apply unsharp mask for enhanced clarity.
        
        PIL's UnsharpMask filter with customizable parameters.
        """
        try:
            # PIL's UnsharpMask takes (radius, percent, threshold)
            # percent = amount * 100
            percent = int(amount * 100)
            sharpened = image.filter(
                ImageFilter.UnsharpMask(radius=radius, percent=percent, threshold=threshold)
            )
            return sharpened
        except Exception as e:
            logger.warning(f"Unsharp mask failed: {e}")
            return image
    
    def _subtle_enhance(self, image: Image.Image) -> Image.Image:
        """Apply subtle enhancements for quality preset."""
        # Subtle contrast boost
        contrast = ImageEnhance.Contrast(image)
        enhanced = contrast.enhance(1.05)
        
        # Subtle color boost
        color = ImageEnhance.Color(enhanced)
        enhanced = color.enhance(1.05)
        
        return enhanced
    
    def _enhance_final(self, image: Image.Image) -> Image.Image:
        """Final enhancement pass for balanced/quality presets."""
        # Very subtle sharpening for final output
        if self.preset == QualityPreset.QUALITY:
            image = self._apply_unsharp_mask(image, amount=0.5, radius=0.5, threshold=2)
        
        return image
    
    def _calculate_quality_score(
        self,
        original_size: Tuple[int, int],
        final_size: Tuple[int, int],
        upscale_factor: float
    ) -> float:
        """
        Calculate quality score (0-100) based on processing.
        
        Higher scores indicate better expected output quality.
        """
        score = 100.0
        
        # Penalize heavy upscaling
        if upscale_factor > 1.0:
            # Each 2x upscale reduces score
            penalty = min(40, (upscale_factor - 1.0) * 20)
            score -= penalty
        
        # Bonus for large source images
        if original_size[0] >= self.OPTIMAL_INPUT_WIDTH:
            score = min(100, score + 10)
        elif original_size[0] < self.MIN_INPUT_WIDTH:
            score -= 20
        
        return max(0, min(100, score))
    
    def _image_to_bytes(self, image: Image.Image) -> bytes:
        """Convert PIL Image to optimized PNG bytes."""
        # Ensure RGB for output (remove alpha if present)
        if image.mode == 'RGBA':
            # Create white background and composite
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        buffer = BytesIO()
        
        # Optimize based on preset
        if self.preset == QualityPreset.FAST:
            image.save(buffer, format='PNG', optimize=False)
        else:
            image.save(buffer, format='PNG', optimize=True)
        
        buffer.seek(0)
        return buffer.read()
    
    def preview_crop(
        self,
        image_input: Union[bytes, Path, Image.Image],
        show_grid: bool = True
    ) -> bytes:
        """
        Generate preview image showing crop region.
        
        Useful for dashboard preview before final processing.
        
        Args:
            image_input: Source image
            show_grid: Whether to show rule of thirds grid
            
        Returns:
            Preview PNG bytes with crop region highlighted
        """
        image, _ = self._load_image(image_input)
        
        # Calculate crop region
        _, crop_region = self._smart_crop(
            image,
            target_aspect=self.STEAM_ASPECT,
            mode=self.crop_mode
        )
        
        # Create preview image
        preview = image.copy()
        draw = ImageDraw.Draw(preview, 'RGBA')
        
        if crop_region:
            # Darken areas outside crop
            full_rect = (0, 0, image.width, image.height)
            
            # Draw semi-transparent overlay on cropped-out areas
            overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rectangle(full_rect, fill=(0, 0, 0, 120))
            
            # Clear the crop region
            overlay_draw.rectangle(crop_region, fill=(0, 0, 0, 0))
            
            preview = Image.alpha_composite(preview, overlay)
            draw = ImageDraw.Draw(preview)
            
            # Draw crop border
            x1, y1, x2, y2 = crop_region
            draw.rectangle([x1, y1, x2, y2], outline=(87, 242, 135, 255), width=3)
        
        if show_grid and crop_region:
            # Draw rule of thirds grid inside crop region
            x1, y1, x2, y2 = crop_region
            w = x2 - x1
            h = y2 - y1
            
            # Vertical lines
            draw.line([(x1 + w//3, y1), (x1 + w//3, y2)], fill=(255, 255, 255, 100), width=1)
            draw.line([(x1 + 2*w//3, y1), (x1 + 2*w//3, y2)], fill=(255, 255, 255, 100), width=1)
            
            # Horizontal lines
            draw.line([(x1, y1 + h//3), (x2, y1 + h//3)], fill=(255, 255, 255, 100), width=1)
            draw.line([(x1, y1 + 2*h//3), (x2, y1 + 2*h//3)], fill=(255, 255, 255, 100), width=1)
        
        return self._image_to_bytes(preview)


# Convenience functions
def process_screenshot(
    image_path: Path,
    output_path: Optional[Path] = None,
    preset: str = "balanced"
) -> ProcessingResult:
    """
    Quick screenshot processing for Steam.
    
    Args:
        image_path: Path to source image
        output_path: Optional path to save result
        preset: Quality preset (fast/balanced/quality)
        
    Returns:
        ProcessingResult with processed image
    """
    processor = ImageProcessor(preset=QualityPreset(preset))
    return processor.process_for_steam(image_path, output_path)


def get_crop_preview(image_path: Path) -> bytes:
    """Get preview of how image will be cropped."""
    processor = ImageProcessor()
    return processor.preview_crop(image_path)
