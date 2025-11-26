"""
Template-based banner generator for WishlistOps.

Generates professional Steam banners using templates, without requiring AI APIs.
This serves as a reliable fallback when AI services are unavailable or for users
who want predictable, fast results.

Usage:
    generator = TemplateBannerGenerator()
    banner_bytes = generator.generate(
        title="Version 1.0.0 Update",
        game_name="My Awesome Game",
        logo_path=Path("logo.png"),
        style="gradient"
    )
"""

import logging
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple, List
from datetime import datetime
from enum import Enum

from PIL import Image, ImageDraw, ImageFont, ImageFilter

logger = logging.getLogger(__name__)


class BannerStyle(str, Enum):
    """Available banner template styles."""
    GRADIENT = "gradient"           # Solid gradient background
    PATTERN = "pattern"             # Geometric pattern background
    MINIMAL = "minimal"             # Clean, minimal design
    BOLD = "bold"                   # Bold colors, strong contrast
    DARK = "dark"                   # Dark theme
    LIGHT = "light"                 # Light theme


class TemplateBannerGenerator:
    """
    Generate Steam banners using predefined templates.
    
    Features:
    - Multiple style presets
    - Customizable color schemes
    - Logo compositing
    - Text overlay with proper typography
    - Steam-compliant dimensions (800x450)
    
    This is a fallback option that works without AI APIs.
    """
    
    # Steam banner specifications
    WIDTH = 800
    HEIGHT = 450
    
    # Typography settings
    TITLE_FONT_SIZE = 48
    SUBTITLE_FONT_SIZE = 24
    
    # Safe margins
    MARGIN = 40
    
    # Default color palettes for each style
    STYLE_COLORS = {
        BannerStyle.GRADIENT: {
            "primary": (41, 128, 185),      # Blue
            "secondary": (52, 73, 94),       # Dark blue
            "text": (255, 255, 255),
            "accent": (46, 204, 113),        # Green
        },
        BannerStyle.PATTERN: {
            "primary": (155, 89, 182),       # Purple
            "secondary": (142, 68, 173),     # Darker purple
            "text": (255, 255, 255),
            "accent": (241, 196, 15),        # Yellow
        },
        BannerStyle.MINIMAL: {
            "primary": (245, 245, 245),      # Light gray
            "secondary": (230, 230, 230),    # Slightly darker
            "text": (44, 62, 80),            # Dark text
            "accent": (231, 76, 60),         # Red accent
        },
        BannerStyle.BOLD: {
            "primary": (231, 76, 60),        # Red
            "secondary": (192, 57, 43),      # Darker red
            "text": (255, 255, 255),
            "accent": (241, 196, 15),        # Yellow
        },
        BannerStyle.DARK: {
            "primary": (33, 33, 33),         # Near black
            "secondary": (66, 66, 66),       # Dark gray
            "text": (255, 255, 255),
            "accent": (0, 188, 212),         # Cyan
        },
        BannerStyle.LIGHT: {
            "primary": (255, 255, 255),      # White
            "secondary": (240, 240, 240),    # Light gray
            "text": (33, 33, 33),            # Dark text
            "accent": (76, 175, 80),         # Green
        },
    }
    
    def __init__(self, custom_colors: Optional[dict] = None):
        """
        Initialize template banner generator.
        
        Args:
            custom_colors: Override default colors (primary, secondary, text, accent)
        """
        self.custom_colors = custom_colors or {}
        logger.info("Template banner generator initialized")
    
    def generate(
        self,
        title: str,
        game_name: Optional[str] = None,
        logo_path: Optional[Path] = None,
        style: BannerStyle = BannerStyle.GRADIENT,
        version_tag: Optional[str] = None,
        custom_colors: Optional[dict] = None,
    ) -> bytes:
        """
        Generate a banner image from template.
        
        Args:
            title: Main title text (e.g., "New Update!")
            game_name: Optional game name subtitle
            logo_path: Path to game logo PNG
            style: Visual style preset
            version_tag: Optional version tag (e.g., "v1.0.0")
            custom_colors: Override colors for this generation
            
        Returns:
            PNG image bytes ready for Steam
        """
        logger.info(f"Generating template banner: style={style.value}, title='{title[:30]}...'")
        
        # Get colors
        colors = self._get_colors(style, custom_colors)
        
        # Create base image
        image = self._create_background(style, colors)
        
        # Add decorative elements
        image = self._add_decorations(image, style, colors)
        
        # Add logo if provided
        if logo_path and logo_path.exists():
            image = self._add_logo(image, logo_path)
        
        # Add text
        image = self._add_text(image, title, game_name, version_tag, colors)
        
        # Add subtle vignette for polish
        image = self._add_vignette(image)
        
        # Convert to bytes
        buffer = BytesIO()
        image.save(buffer, format='PNG', optimize=True)
        buffer.seek(0)
        
        logger.info("Template banner generated successfully")
        return buffer.read()
    
    def _get_colors(self, style: BannerStyle, custom_colors: Optional[dict]) -> dict:
        """Get color palette for style, with custom overrides."""
        colors = self.STYLE_COLORS.get(style, self.STYLE_COLORS[BannerStyle.GRADIENT]).copy()
        
        # Apply instance custom colors
        colors.update(self.custom_colors)
        
        # Apply per-call custom colors
        if custom_colors:
            colors.update(custom_colors)
        
        return colors
    
    def _create_background(self, style: BannerStyle, colors: dict) -> Image.Image:
        """Create the base background for the banner."""
        image = Image.new('RGBA', (self.WIDTH, self.HEIGHT))
        draw = ImageDraw.Draw(image)
        
        primary = colors['primary']
        secondary = colors['secondary']
        
        if style == BannerStyle.GRADIENT:
            # Diagonal gradient
            for y in range(self.HEIGHT):
                # Calculate gradient color
                ratio = y / self.HEIGHT
                r = int(primary[0] * (1 - ratio) + secondary[0] * ratio)
                g = int(primary[1] * (1 - ratio) + secondary[1] * ratio)
                b = int(primary[2] * (1 - ratio) + secondary[2] * ratio)
                draw.line([(0, y), (self.WIDTH, y)], fill=(r, g, b, 255))
        
        elif style == BannerStyle.PATTERN:
            # Base color
            draw.rectangle([0, 0, self.WIDTH, self.HEIGHT], fill=(*primary, 255))
            # Add geometric pattern
            self._draw_hexagon_pattern(draw, secondary)
        
        elif style in (BannerStyle.MINIMAL, BannerStyle.LIGHT):
            # Solid with subtle gradient
            for y in range(self.HEIGHT):
                ratio = y / self.HEIGHT * 0.1  # Very subtle
                r = int(primary[0] * (1 - ratio) + secondary[0] * ratio)
                g = int(primary[1] * (1 - ratio) + secondary[1] * ratio)
                b = int(primary[2] * (1 - ratio) + secondary[2] * ratio)
                draw.line([(0, y), (self.WIDTH, y)], fill=(r, g, b, 255))
        
        elif style == BannerStyle.BOLD:
            # Bold diagonal split
            draw.polygon(
                [(0, 0), (self.WIDTH, 0), (self.WIDTH, self.HEIGHT * 0.7), (0, self.HEIGHT)],
                fill=(*primary, 255)
            )
            draw.polygon(
                [(0, self.HEIGHT), (self.WIDTH, self.HEIGHT * 0.7), (self.WIDTH, self.HEIGHT)],
                fill=(*secondary, 255)
            )
        
        elif style == BannerStyle.DARK:
            # Dark gradient with subtle noise effect
            for y in range(self.HEIGHT):
                ratio = y / self.HEIGHT
                r = int(primary[0] * (1 - ratio) + secondary[0] * ratio)
                g = int(primary[1] * (1 - ratio) + secondary[1] * ratio)
                b = int(primary[2] * (1 - ratio) + secondary[2] * ratio)
                draw.line([(0, y), (self.WIDTH, y)], fill=(r, g, b, 255))
        
        return image
    
    def _draw_hexagon_pattern(self, draw: ImageDraw.Draw, color: Tuple[int, int, int]):
        """Draw hexagon pattern overlay."""
        hex_size = 60
        opacity = 30  # Subtle
        fill = (*color, opacity)
        
        for row in range(-1, self.HEIGHT // hex_size + 2):
            for col in range(-1, self.WIDTH // hex_size + 2):
                offset_x = (row % 2) * (hex_size // 2)
                x = col * hex_size + offset_x
                y = row * hex_size * 0.866  # Hex height ratio
                
                # Only draw every other hex for pattern
                if (row + col) % 3 == 0:
                    self._draw_hexagon(draw, x, y, hex_size // 2, fill)
    
    def _draw_hexagon(self, draw: ImageDraw.Draw, cx: float, cy: float, radius: int, fill):
        """Draw a single hexagon."""
        import math
        points = []
        for i in range(6):
            angle = math.pi / 3 * i - math.pi / 6
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            points.append((x, y))
        draw.polygon(points, fill=fill)
    
    def _add_decorations(self, image: Image.Image, style: BannerStyle, colors: dict) -> Image.Image:
        """Add decorative elements based on style."""
        draw = ImageDraw.Draw(image)
        accent = colors['accent']
        
        if style == BannerStyle.GRADIENT:
            # Accent line at bottom
            draw.rectangle(
                [0, self.HEIGHT - 8, self.WIDTH, self.HEIGHT],
                fill=(*accent, 255)
            )
        
        elif style == BannerStyle.BOLD:
            # Accent corner triangle
            draw.polygon(
                [(0, 0), (150, 0), (0, 150)],
                fill=(*accent, 255)
            )
        
        elif style == BannerStyle.DARK:
            # Glowing accent line
            for i in range(5):
                alpha = 50 - i * 10
                draw.line(
                    [(0, self.HEIGHT - 20 - i), (self.WIDTH, self.HEIGHT - 20 - i)],
                    fill=(*accent, alpha),
                    width=2
                )
        
        return image
    
    def _add_logo(self, image: Image.Image, logo_path: Path) -> Image.Image:
        """Add game logo to banner."""
        try:
            logo = Image.open(logo_path)
            if logo.mode != 'RGBA':
                logo = logo.convert('RGBA')
            
            # Calculate logo size (25% of width max)
            max_logo_width = int(self.WIDTH * 0.25)
            max_logo_height = int(self.HEIGHT * 0.4)
            
            # Resize maintaining aspect ratio
            logo_ratio = logo.width / logo.height
            if logo.width > max_logo_width:
                new_width = max_logo_width
                new_height = int(new_width / logo_ratio)
            else:
                new_width = logo.width
                new_height = logo.height
            
            if new_height > max_logo_height:
                new_height = max_logo_height
                new_width = int(new_height * logo_ratio)
            
            logo = logo.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Position in top-right corner with margin
            x = self.WIDTH - new_width - self.MARGIN
            y = self.MARGIN
            
            # Create shadow
            shadow = Image.new('RGBA', logo.size, (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow)
            shadow_draw.rectangle([0, 0, logo.width, logo.height], fill=(0, 0, 0, 60))
            shadow = shadow.filter(ImageFilter.GaussianBlur(10))
            
            # Paste shadow then logo
            image.paste(shadow, (x + 4, y + 4), shadow)
            image.paste(logo, (x, y), logo)
            
            logger.debug(f"Added logo at ({x}, {y}), size {logo.size}")
            
        except Exception as e:
            logger.warning(f"Failed to add logo: {e}")
        
        return image
    
    def _add_text(
        self,
        image: Image.Image,
        title: str,
        game_name: Optional[str],
        version_tag: Optional[str],
        colors: dict
    ) -> Image.Image:
        """Add text overlays to banner."""
        draw = ImageDraw.Draw(image)
        text_color = (*colors['text'], 255)
        accent_color = (*colors['accent'], 255)
        
        # Load fonts (with fallbacks)
        title_font = self._get_font(self.TITLE_FONT_SIZE, bold=True)
        subtitle_font = self._get_font(self.SUBTITLE_FONT_SIZE)
        tag_font = self._get_font(18)
        
        # Calculate text positions (left-aligned with margin)
        current_y = self.HEIGHT - self.MARGIN
        
        # Version tag (if provided) - at bottom
        if version_tag:
            current_y -= 30
            self._draw_text_with_shadow(draw, (self.MARGIN, current_y), version_tag, tag_font, accent_color)
        
        # Title - above version tag
        current_y -= self.TITLE_FONT_SIZE + 10
        # Truncate title if too long
        title_display = title[:50] + "..." if len(title) > 50 else title
        self._draw_text_with_shadow(draw, (self.MARGIN, current_y), title_display, title_font, text_color)
        
        # Game name - above title
        if game_name:
            current_y -= self.SUBTITLE_FONT_SIZE + 10
            self._draw_text_with_shadow(draw, (self.MARGIN, current_y), game_name, subtitle_font, text_color)
        
        return image
    
    def _draw_text_with_shadow(
        self,
        draw: ImageDraw.Draw,
        position: Tuple[int, int],
        text: str,
        font,
        color: Tuple[int, int, int, int]
    ):
        """Draw text with drop shadow for visibility."""
        x, y = position
        shadow_offset = 2
        shadow_color = (0, 0, 0, 100)
        
        # Draw shadow
        draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=shadow_color)
        
        # Draw main text
        draw.text((x, y), text, font=font, fill=color)
    
    def _get_font(self, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        """Get font with fallback to default."""
        # List of fonts to try (in order of preference)
        font_names = [
            "arial.ttf",
            "Arial.ttf",
            "DejaVuSans.ttf",
            "liberation-sans/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
        
        if bold:
            font_names = [
                "arialbd.ttf",
                "Arial Bold.ttf",
                "DejaVuSans-Bold.ttf",
            ] + font_names
        
        for font_name in font_names:
            try:
                return ImageFont.truetype(font_name, size)
            except (IOError, OSError):
                continue
        
        # Fallback to default
        logger.debug("Using default font (no TrueType fonts found)")
        return ImageFont.load_default()
    
    def _add_vignette(self, image: Image.Image) -> Image.Image:
        """Add subtle vignette effect for polish."""
        # Create radial gradient mask
        mask = Image.new('L', (self.WIDTH, self.HEIGHT), 255)
        draw = ImageDraw.Draw(mask)
        
        # Draw concentric circles with decreasing opacity
        cx, cy = self.WIDTH // 2, self.HEIGHT // 2
        max_radius = int((self.WIDTH ** 2 + self.HEIGHT ** 2) ** 0.5 / 2)
        
        for i in range(0, max_radius, 2):
            opacity = 255 - int((i / max_radius) * 40)  # Subtle darkening
            if opacity > 0:
                draw.ellipse(
                    [cx - i, cy - i, cx + i, cy + i],
                    outline=opacity,
                    width=2
                )
        
        # Apply blur to mask
        mask = mask.filter(ImageFilter.GaussianBlur(50))
        
        # Create darkening layer
        dark = Image.new('RGBA', (self.WIDTH, self.HEIGHT), (0, 0, 0, 30))
        
        # Composite with inverted mask (dark edges)
        inverted_mask = Image.eval(mask, lambda x: 255 - x)
        image = Image.composite(
            Image.alpha_composite(image, dark),
            image,
            inverted_mask
        )
        
        return image
    
    def list_styles(self) -> List[str]:
        """List available style names."""
        return [style.value for style in BannerStyle]
    
    def preview_colors(self, style: BannerStyle) -> dict:
        """Get color palette for a style."""
        return self.STYLE_COLORS.get(style, {})


# Convenience function for quick generation
def generate_template_banner(
    title: str,
    game_name: Optional[str] = None,
    logo_path: Optional[Path] = None,
    style: str = "gradient"
) -> bytes:
    """
    Quick template banner generation.
    
    Args:
        title: Banner title
        game_name: Optional game name
        logo_path: Optional logo path
        style: Style name ("gradient", "pattern", "minimal", "bold", "dark", "light")
        
    Returns:
        PNG bytes
    """
    generator = TemplateBannerGenerator()
    return generator.generate(
        title=title,
        game_name=game_name,
        logo_path=logo_path,
        style=BannerStyle(style)
    )
