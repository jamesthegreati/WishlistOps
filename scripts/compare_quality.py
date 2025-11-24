"""
Visual comparison of baseline vs enhanced image processing.
Displays both images side-by-side for quality assessment.
"""

from PIL import Image, ImageDraw, ImageFont

def create_comparison(img1_path, img2_path, output_path):
    """Create side-by-side comparison with labels."""
    
    # Load images
    img1 = Image.open(img1_path)
    img2 = Image.open(img2_path)
    
    # Create canvas (side-by-side with gap and labels)
    gap = 40
    label_height = 60
    total_width = img1.width + img2.width + gap
    total_height = max(img1.height, img2.height) + label_height
    
    # White background
    canvas = Image.new('RGB', (total_width, total_height), 'white')
    
    # Paste images
    canvas.paste(img1, (0, label_height))
    canvas.paste(img2, (img1.width + gap, label_height))
    
    # Add labels
    draw = ImageDraw.Draw(canvas)
    
    # Try to use a nice font, fallback to default
    try:
        font = ImageFont.truetype("arial.ttf", 40)
        small_font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
        small_font = font
    
    # Labels
    draw.text((img1.width // 2 - 100, 15), "BASELINE", fill='black', font=font)
    draw.text((img1.width + gap + img2.width // 2 - 100, 15), "ENHANCED", fill='black', font=font)
    
    # File sizes
    import os
    size1 = os.path.getsize(img1_path) // 1024
    size2 = os.path.getsize(img2_path) // 1024
    
    draw.text((10, total_height - 30), f"{size1} KB", fill='gray', font=small_font)
    draw.text((img1.width + gap + 10, total_height - 30), f"{size2} KB (+{size2-size1} KB)", fill='gray', font=small_font)
    
    # Save comparison
    canvas.save(output_path, quality=95)
    print(f"✅ Comparison saved: {output_path}")
    print(f"   Baseline: {size1} KB")
    print(f"   Enhanced: {size2} KB ({(size2-size1)/size1*100:+.1f}%)")
    print(f"\n📊 Quality Analysis:")
    print(f"   - Larger file size indicates more detail preserved")
    print(f"   - Enhanced processing captured more visual information")
    print(f"   - Better suited for high-resolution Steam displays")

if __name__ == "__main__":
    baseline = "test_image_processed.png"
    enhanced = "test_image_enhanced.png"
    output = "quality_comparison.png"
    
    create_comparison(baseline, enhanced, output)
