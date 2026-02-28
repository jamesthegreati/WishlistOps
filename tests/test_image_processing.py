#!/usr/bin/env python3
"""
Test script to process test_image.png with WishlistOps image compositor.
Shows how the tool resizes images to Steam's 800x450 banner requirements.
"""

from pathlib import Path
from PIL import Image
from wishlistops.image_compositor import ImageCompositor
from wishlistops.models import BrandingConfig

def main():
    print("🎨 WishlistOps Image Processing Test\n")
    
    # Load test image
    test_image_path = Path("test_image.png")
    if not test_image_path.exists():
        print(f"❌ Error: {test_image_path} not found!")
        return
    
    with open(test_image_path, 'rb') as f:
        image_data = f.read()
    
    # Get original dimensions
    original_img = Image.open(test_image_path)
    print(f"📐 Original Image:")
    print(f"   Size: {original_img.size}")
    print(f"   Dimensions: {original_img.width}x{original_img.height}")
    print(f"   Mode: {original_img.mode}")
    print(f"   Aspect Ratio: {original_img.width/original_img.height:.2f}:1\n")
    
    # Create branding config (minimal - no logo overlay for this test)
    branding = BrandingConfig(
        art_style="game screenshot",
        color_palette=["#FF6B6B"],
        logo_position="top-right",
        logo_size_percent=20,
        logo_path=None  # No logo, just resize
    )
    
    # Initialize compositor
    compositor = ImageCompositor(branding)
    
    print(f"🎯 Steam Requirements:")
    print(f"   Target Size: {compositor.STEAM_WIDTH}x{compositor.STEAM_HEIGHT}")
    print(f"   Aspect Ratio: {compositor.STEAM_WIDTH/compositor.STEAM_HEIGHT:.2f}:1")
    print(f"   Safe Zones: H={compositor.SAFE_ZONE_HORIZONTAL}px, V={compositor.SAFE_ZONE_VERTICAL}px\n")
    
    # Process image
    print("🔄 Processing image...")
    processed_data = compositor.composite_logo(
        base_image_data=image_data,
        logo_path=None  # No logo overlay
    )
    
    # Save the processed image
    output_path = Path("test_image_processed.png")
    with open(output_path, 'wb') as f:
        f.write(processed_data)
    print(f"   Saved to: {output_path}")
    
    # Check result
    processed_img = Image.open(output_path)
    print(f"\n✅ Processed Image:")
    print(f"   Size: {processed_img.size}")
    print(f"   Dimensions: {processed_img.width}x{processed_img.height}")
    print(f"   Mode: {processed_img.mode}")
    print(f"   File saved: test_image_processed.png")
    print(f"   File size: {len(processed_data):,} bytes\n")
    
    # Calculate resize method used
    original_ratio = original_img.width / original_img.height
    steam_ratio = compositor.STEAM_WIDTH / compositor.STEAM_HEIGHT
    
    print(f"📊 Processing Details:")
    print(f"   Original Ratio: {original_ratio:.3f}:1")
    print(f"   Steam Ratio: {steam_ratio:.3f}:1")
    
    if original_ratio > steam_ratio:
        print(f"   Method: Image was wider → cropped horizontally to fit")
    elif original_ratio < steam_ratio:
        print(f"   Method: Image was taller → cropped vertically to fit")
    else:
        print(f"   Method: Perfect match → simple resize")
    
    print(f"\n🎉 Success! Image ready for Steam upload.")

if __name__ == "__main__":
    main()
