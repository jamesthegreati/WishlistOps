"""
Tests for image compositor functionality.

Tests logo compositing, positioning, effects, and Steam compliance.
"""

import pytest
from pathlib import Path
from PIL import Image
from io import BytesIO

from wishlistops.image_compositor import ImageCompositor, CompositorError, composite_logo_simple
from wishlistops.models import BrandingConfig, LogoPosition


@pytest.fixture
def test_base_image():
    """Create test base image."""
    img = Image.new('RGB', (1024, 576), color='blue')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()


@pytest.fixture
def test_logo(tmp_path):
    """Create test logo."""
    logo_path = tmp_path / "logo.png"
    img = Image.new('RGBA', (200, 200), color=(255, 0, 0, 255))
    img.save(logo_path)
    return logo_path


@pytest.fixture
def branding_config(test_logo):
    """Create test branding config."""
    return BrandingConfig(
        art_style="test style for unit testing",
        logo_position=LogoPosition.TOP_RIGHT,
        logo_size_percent=25,
        logo_path=str(test_logo)
    )


def test_compositor_initialization(branding_config):
    """Test compositor can be initialized."""
    compositor = ImageCompositor(branding_config)
    assert compositor.config == branding_config


def test_composite_logo_success(test_base_image, test_logo, branding_config):
    """Test logo compositing works."""
    compositor = ImageCompositor(branding_config)
    
    result = compositor.composite_logo(
        base_image_data=test_base_image,
        logo_path=test_logo
    )
    
    assert isinstance(result, bytes)
    assert len(result) > 0
    
    # Verify result is valid image
    img = Image.open(BytesIO(result))
    assert img.size == (800, 450)  # Steam specs


def test_resize_to_steam_specs(test_base_image, branding_config):
    """Test image is resized to Steam specifications."""
    compositor = ImageCompositor(branding_config)
    
    result = compositor.composite_logo(test_base_image)
    img = Image.open(BytesIO(result))
    
    assert img.size == (ImageCompositor.STEAM_WIDTH, ImageCompositor.STEAM_HEIGHT)


def test_logo_positions(test_base_image, test_logo, branding_config):
    """Test all logo positions work."""
    positions = [
        LogoPosition.TOP_LEFT,
        LogoPosition.TOP_RIGHT,
        LogoPosition.CENTER,
        LogoPosition.BOTTOM_LEFT,
        LogoPosition.BOTTOM_RIGHT
    ]
    
    for position in positions:
        branding_config.logo_position = position
        compositor = ImageCompositor(branding_config)
        
        result = compositor.composite_logo(
            base_image_data=test_base_image,
            logo_path=test_logo
        )
        
        assert len(result) > 0


def test_missing_logo_handled(test_base_image, branding_config):
    """Test missing logo is handled gracefully."""
    branding_config.logo_path = "nonexistent.png"
    compositor = ImageCompositor(branding_config)
    
    # Should return base image without logo
    result = compositor.composite_logo(test_base_image)
    assert len(result) > 0


def test_add_text_overlay(test_base_image, branding_config):
    """Test text overlay works."""
    compositor = ImageCompositor(branding_config)
    
    result = compositor.add_text_overlay(
        test_base_image,
        text="v1.0.0",
        position="bottom"
    )
    
    assert len(result) > 0
    img = Image.open(BytesIO(result))
    assert img.size == (800, 450)


def test_file_size_optimization(test_base_image, test_logo, branding_config):
    """Test output file size is reasonable."""
    compositor = ImageCompositor(branding_config)
    
    result = compositor.composite_logo(
        base_image_data=test_base_image,
        logo_path=test_logo
    )
    
    # Should be under 2MB (Steam limit)
    assert len(result) < 2 * 1024 * 1024
    # Should be reasonably compressed (not huge)
    assert len(result) < 500 * 1024  # Less than 500KB for test image


def test_different_logo_sizes(test_base_image, test_logo, branding_config):
    """Test different logo sizes work correctly."""
    sizes = [10, 25, 40, 50]
    
    for size in sizes:
        branding_config.logo_size_percent = size
        compositor = ImageCompositor(branding_config)
        
        result = compositor.composite_logo(
            base_image_data=test_base_image,
            logo_path=test_logo
        )
        
        assert len(result) > 0
        img = Image.open(BytesIO(result))
        assert img.size == (800, 450)


def test_output_path_saving(test_base_image, test_logo, branding_config, tmp_path):
    """Test saving to output path works."""
    compositor = ImageCompositor(branding_config)
    output_path = tmp_path / "output" / "result.png"
    
    result = compositor.composite_logo(
        base_image_data=test_base_image,
        logo_path=test_logo,
        output_path=output_path
    )
    
    # Check file was created
    assert output_path.exists()
    
    # Check file content matches returned bytes
    with open(output_path, 'rb') as f:
        saved_bytes = f.read()
    assert saved_bytes == result


def test_resize_to_steam_specs_method(branding_config):
    """Test _resize_to_steam_specs method directly."""
    compositor = ImageCompositor(branding_config)
    
    # Test image that needs resizing
    img = Image.new('RGB', (1920, 1080), color='red')
    resized = compositor._resize_to_steam_specs(img)
    
    assert resized.size == (800, 450)
    
    # Test image that's already correct size
    img_correct = Image.new('RGB', (800, 450), color='green')
    resized_correct = compositor._resize_to_steam_specs(img_correct)
    
    assert resized_correct.size == (800, 450)


def test_load_and_prepare_logo(test_logo, branding_config):
    """Test _load_and_prepare_logo method."""
    compositor = ImageCompositor(branding_config)
    
    logo = compositor._load_and_prepare_logo(test_logo)
    
    # Should be RGBA
    assert logo.mode == 'RGBA'
    
    # Should be resized according to config
    expected_width = int(800 * 25 / 100)  # 25% of 800
    assert logo.size[0] == expected_width


def test_load_and_prepare_logo_invalid_path(branding_config):
    """Test _load_and_prepare_logo with invalid path raises error."""
    compositor = ImageCompositor(branding_config)
    
    with pytest.raises(CompositorError):
        compositor._load_and_prepare_logo(Path("nonexistent_logo.png"))


def test_calculate_logo_position(branding_config):
    """Test _calculate_logo_position for all positions."""
    compositor = ImageCompositor(branding_config)
    banner_size = (800, 450)
    logo_size = (100, 100)
    
    test_cases = [
        (LogoPosition.TOP_LEFT, (40, 40)),
        (LogoPosition.TOP_RIGHT, (660, 40)),  # 800 - 100 - 40
        (LogoPosition.CENTER, (350, 175)),     # (800-100)//2, (450-100)//2
        (LogoPosition.BOTTOM_LEFT, (40, 310)),  # 450 - 100 - 40
        (LogoPosition.BOTTOM_RIGHT, (660, 310))
    ]
    
    for position, expected_coords in test_cases:
        compositor.config.logo_position = position
        result = compositor._calculate_logo_position(banner_size, logo_size)
        assert result == expected_coords, f"Position {position} failed"


def test_create_drop_shadow(branding_config):
    """Test _create_drop_shadow creates valid shadow."""
    compositor = ImageCompositor(branding_config)
    
    # Create test logo
    logo = Image.new('RGBA', (100, 100), color=(255, 0, 0, 255))
    
    shadow = compositor._create_drop_shadow(logo)
    
    # Should be same size as logo
    assert shadow.size == logo.size
    
    # Should be RGBA
    assert shadow.mode == 'RGBA'


def test_image_to_bytes(branding_config):
    """Test _image_to_bytes converts correctly."""
    compositor = ImageCompositor(branding_config)
    
    img = Image.new('RGB', (800, 450), color='blue')
    result_bytes = compositor._image_to_bytes(img)
    
    # Should be valid PNG
    assert isinstance(result_bytes, bytes)
    assert len(result_bytes) > 0
    
    # Should be readable as image
    reloaded = Image.open(BytesIO(result_bytes))
    assert reloaded.size == (800, 450)


def test_add_text_overlay_positions(test_base_image, branding_config):
    """Test text overlay at different positions."""
    compositor = ImageCompositor(branding_config)
    
    positions = ["top", "bottom", "center"]
    
    for position in positions:
        result = compositor.add_text_overlay(
            test_base_image,
            text=f"Test {position}",
            position=position
        )
        
        assert len(result) > 0
        img = Image.open(BytesIO(result))
        assert img.size == (800, 450)


def test_composite_logo_simple_convenience_function(test_base_image, test_logo):
    """Test convenience function works."""
    result = composite_logo_simple(
        test_base_image,
        test_logo,
        logo_size_percent=30
    )
    
    assert isinstance(result, bytes)
    assert len(result) > 0
    
    img = Image.open(BytesIO(result))
    assert img.size == (800, 450)


def test_logo_with_transparency(test_base_image, tmp_path, branding_config):
    """Test logo with actual transparency is composited correctly."""
    # Create logo with partial transparency
    logo_path = tmp_path / "transparent_logo.png"
    logo = Image.new('RGBA', (200, 200), (0, 0, 0, 0))
    
    # Draw a circle with transparency
    from PIL import ImageDraw
    draw = ImageDraw.Draw(logo)
    draw.ellipse([50, 50, 150, 150], fill=(255, 0, 0, 200))
    logo.save(logo_path)
    
    compositor = ImageCompositor(branding_config)
    result = compositor.composite_logo(
        base_image_data=test_base_image,
        logo_path=logo_path
    )
    
    assert len(result) > 0
    img = Image.open(BytesIO(result))
    assert img.size == (800, 450)


def test_various_input_image_formats(test_logo, branding_config, tmp_path):
    """Test compositing works with different input formats."""
    compositor = ImageCompositor(branding_config)
    
    # Test JPEG input
    jpg_img = Image.new('RGB', (1024, 576), color='green')
    jpg_buffer = BytesIO()
    jpg_img.save(jpg_buffer, format='JPEG')
    
    result = compositor.composite_logo(
        base_image_data=jpg_buffer.getvalue(),
        logo_path=test_logo
    )
    
    assert len(result) > 0
    img = Image.open(BytesIO(result))
    assert img.size == (800, 450)


def test_safe_zones_respected(branding_config):
    """Test that safe zones are properly applied."""
    compositor = ImageCompositor(branding_config)
    
    # Logo at edges should respect safe zones
    banner_size = (800, 450)
    logo_size = (100, 100)
    
    # Top-left should be at (40, 40) not (0, 0)
    compositor.config.logo_position = LogoPosition.TOP_LEFT
    x, y = compositor._calculate_logo_position(banner_size, logo_size)
    
    assert x >= ImageCompositor.SAFE_ZONE_HORIZONTAL
    assert y >= ImageCompositor.SAFE_ZONE_VERTICAL
    
    # Bottom-right should respect safe zones
    compositor.config.logo_position = LogoPosition.BOTTOM_RIGHT
    x, y = compositor._calculate_logo_position(banner_size, logo_size)
    
    assert x <= banner_size[0] - logo_size[0] - ImageCompositor.SAFE_ZONE_HORIZONTAL
    assert y <= banner_size[1] - logo_size[1] - ImageCompositor.SAFE_ZONE_VERTICAL
