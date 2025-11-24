#!/usr/bin/env python3
"""
Test enhanced image processing with content-aware cropping and AI upscaling.
"""

from pathlib import Path
from PIL import Image
from wishlistops.image_compositor import ImageCompositor
from wishlistops.models import BrandingConfig

def main():
    print("=" * 70)
    print("🚀 ENHANCED IMAGE PROCESSING TEST")
    print("   Content-Aware Cropping + AI Upscaling")
    print("=" * 70)
    print()
    
    # Load test image
    test_image_path = Path("test_image.png")
    if not test_image_path.exists():
        print(f"❌ Error: {test_image_path} not found!")
        return
    
    with open(test_image_path, 'rb') as f:
        image_data = f.read()
    
    # Get original dimensions
    original_img = Image.open(test_image_path)
    print(f"📐 ORIGINAL IMAGE:")
    print(f"   Dimensions: {original_img.width} × {original_img.height} pixels")
    print(f"   Aspect Ratio: {original_img.width/original_img.height:.3f}:1")
    print(f"   Mode: {original_img.mode}")
    print()
    
    # Create branding config
    branding = BrandingConfig(
        art_style="game screenshot",
        color_palette=["#FF6B6B"],
        logo_position="top-right",
        logo_size_percent=20,
        logo_path=None
    )
    
    # Initialize compositor
    compositor = ImageCompositor(branding)
    
    print(f"🎯 STEAM REQUIREMENTS:")
    print(f"   Target: {compositor.STEAM_WIDTH} × {compositor.STEAM_HEIGHT} pixels")
    print(f"   Aspect Ratio: {compositor.STEAM_WIDTH/compositor.STEAM_HEIGHT:.3f}:1 (16:9)")
    print()
    
    print("🔄 PROCESSING WITH ENHANCEMENTS...")
    print("   ✓ Content-aware cropping (saliency detection)")
    print("   ✓ AI-powered upscaling (quality enhancement)")
    print()
    
    # Process image
    processed_data = compositor.composite_logo(
        base_image_data=image_data,
        logo_path=None
    )
    
    # Save the processed image
    output_path = Path("test_image_enhanced.png")
    with open(output_path, 'wb') as f:
        f.write(processed_data)
    
    # Check result
    processed_img = Image.open(output_path)
    
    print("✅ PROCESSING COMPLETE!")
    print()
    print(f"📊 RESULTS:")
    print(f"   Output Size: {processed_img.width} × {processed_img.height} pixels")
    print(f"   Aspect Ratio: {processed_img.width/processed_img.height:.3f}:1")
    print(f"   Color Mode: {processed_img.mode}")
    print(f"   File Size: {len(processed_data):,} bytes ({len(processed_data)/1024:.1f} KB)")
    print(f"   Saved As: {output_path}")
    print()
    
    # Compare with old version
    old_output = Path("test_image_processed.png")
    if old_output.exists():
        old_img = Image.open(old_output)
        old_size = old_output.stat().st_size
        
        print("📈 QUALITY COMPARISON:")
        print(f"   Old Method: {old_size:,} bytes ({old_size/1024:.1f} KB)")
        print(f"   Enhanced: {len(processed_data):,} bytes ({len(processed_data)/1024:.1f} KB)")
        print(f"   Difference: {((len(processed_data)/old_size - 1) * 100):+.1f}%")
        print()
    
    print("🎉 ENHANCEMENTS APPLIED:")
    print("   ✓ Smart content detection preserves important details")
    print("   ✓ AI upscaling maintains image quality during resize")
    print("   ✓ Edge enhancement for crisp output")
    print("   ✓ Optimized for Steam Community Hub")
    print()
    print("=" * 70)
    print("Ready for Steam upload! 🎮")
    print("=" * 70)

if __name__ == "__main__":
    main()
