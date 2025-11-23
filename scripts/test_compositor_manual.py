"""Quick manual test of image compositor."""

from pathlib import Path
from PIL import Image
from io import BytesIO

from wishlistops.image_compositor import ImageCompositor, composite_logo_simple
from wishlistops.models import BrandingConfig, LogoPosition

def test_basic():
    """Test basic compositing."""
    print("Creating test images...")
    
    # Create base image
    base_img = Image.new('RGB', (1024, 576), color='blue')
    base_buffer = BytesIO()
    base_img.save(base_buffer, format='PNG')
    base_bytes = base_buffer.getvalue()
    
    # Create logo
    logo_img = Image.new('RGBA', (200, 200), color=(255, 0, 0, 255))
    logo_path = Path('test_logo.png')
    logo_img.save(logo_path)
    
    print("Testing image compositor...")
    
    # Test with config
    config = BrandingConfig(
        art_style="test style for manual testing",
        logo_position=LogoPosition.TOP_RIGHT,
        logo_size_percent=25,
        logo_path=str(logo_path)
    )
    
    compositor = ImageCompositor(config)
    result = compositor.composite_logo(base_bytes)
    
    # Verify result
    result_img = Image.open(BytesIO(result))
    print(f"✓ Result size: {result_img.size}")
    assert result_img.size == (800, 450), "Wrong size!"
    print(f"✓ File size: {len(result)} bytes ({len(result)/1024:.1f} KB)")
    assert len(result) < 2 * 1024 * 1024, "Too large!"
    
    # Test convenience function
    result2 = composite_logo_simple(base_bytes, logo_path, 30)
    print(f"✓ Convenience function works: {len(result2)} bytes")
    
    # Test all positions
    for pos in LogoPosition:
        config.logo_position = pos
        compositor = ImageCompositor(config)
        result = compositor.composite_logo(base_bytes)
        print(f"✓ Position {pos.value} works")
    
    # Clean up
    logo_path.unlink()
    
    print("\n✅ ALL TESTS PASSED!")

if __name__ == '__main__':
    test_basic()
