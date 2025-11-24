"""
Advanced Real-ESRGAN upscaling test.
Demonstrates state-of-the-art super-resolution quality.
"""

from PIL import Image
import time
import os

print("=" * 80)
print("🚀 REAL-ESRGAN UPSCALING TEST - State-of-the-Art Super-Resolution")
print("=" * 80)

# Test if Real-ESRGAN is available
print("\n📦 Checking Dependencies...")
try:
    import torch
    print(f"   ✓ PyTorch {torch.__version__}")
    print(f"   ✓ CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"   ✓ GPU: {torch.cuda.get_device_name(0)}")
except:
    print("   ⚠️  PyTorch not available")

try:
    from realesrgan import RealESRGANer
    from basicsr.archs.rrdbnet_arch import RRDBNet
    print("   ✓ Real-ESRGAN installed")
    realesrgan_available = True
except:
    print("   ⚠️  Real-ESRGAN not available")
    realesrgan_available = False

try:
    import cv2
    import numpy as np
    print(f"   ✓ OpenCV {cv2.__version__}")
except:
    print("   ⚠️  OpenCV not available")

# Load test image
print("\n📸 Loading Test Image...")
test_image = "test_image.png"
if os.path.exists(test_image):
    img = Image.open(test_image)
    print(f"   Input: {img.width}×{img.height} pixels")
    print(f"   Mode: {img.mode}")
    print(f"   Format: {img.format}")
else:
    print(f"   ❌ Test image not found: {test_image}")
    exit(1)

target_size = (800, 450)
print(f"   Target: {target_size[0]}×{target_size[1]} pixels (Steam banner)")

# Method 1: Real-ESRGAN (Best Quality)
if realesrgan_available:
    print("\n🌟 METHOD 1: Real-ESRGAN (State-of-the-Art)")
    print("-" * 80)
    
    try:
        import torch
        import cv2
        import numpy as np
        from realesrgan import RealESRGANer
        from basicsr.archs.rrdbnet_arch import RRDBNet
        
        # Calculate scale
        scale_x = target_size[0] / img.width
        scale_y = target_size[1] / img.height
        scale = max(scale_x, scale_y)
        
        print(f"   Scale Factor: {scale:.2f}x")
        
        # Choose model
        if scale <= 2:
            model_name = 'RealESRGAN_x2plus'
            model_scale = 2
        else:
            model_name = 'RealESRGAN_x4plus'
            model_scale = 4
        
        print(f"   Model: {model_name}")
        print(f"   Processing...")
        
        start_time = time.time()
        
        # Initialize model
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=model_scale)
        
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"   Device: {device}")
        
        # Create upsampler
        upsampler = RealESRGANer(
            scale=model_scale,
            model_path=f'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/{model_name}.pth',
            model=model,
            tile=400,
            tile_pad=10,
            pre_pad=0,
            half=True if device.type == 'cuda' else False,
            device=device
        )
        
        # Convert to cv2
        img_array = np.array(img)
        if img.mode == 'RGBA':
            alpha = img_array[:, :, 3]
            img_cv = cv2.cvtColor(img_array[:, :, :3], cv2.COLOR_RGB2BGR)
        else:
            img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            alpha = None
        
        # Enhance
        output, _ = upsampler.enhance(img_cv, outscale=scale)
        
        # Resize to exact target
        if (output.shape[1], output.shape[0]) != target_size:
            output = cv2.resize(output, target_size, interpolation=cv2.INTER_LANCZOS4)
        
        elapsed = time.time() - start_time
        
        # Convert back
        output_rgb = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)
        if alpha is not None:
            alpha_resized = cv2.resize(alpha, target_size, interpolation=cv2.INTER_LANCZOS4)
            output_rgba = np.dstack((output_rgb, alpha_resized))
            result_realesrgan = Image.fromarray(output_rgba, 'RGBA')
        else:
            result_realesrgan = Image.fromarray(output_rgb, 'RGB')
        
        # Save
        output_path = "test_image_realesrgan.png"
        result_realesrgan.save(output_path, quality=95)
        file_size = os.path.getsize(output_path) // 1024
        
        print(f"   ✅ Complete in {elapsed:.2f}s")
        print(f"   📁 Saved: {output_path}")
        print(f"   📊 Size: {file_size} KB")
        print(f"   🎨 Quality: Photo-realistic (ESRGAN architecture)")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        realesrgan_available = False

# Method 2: Enhanced OpenCV (Fallback)
print("\n⚡ METHOD 2: Enhanced OpenCV (Fast Fallback)")
print("-" * 80)

try:
    import cv2
    import numpy as np
    
    print(f"   Processing...")
    start_time = time.time()
    
    # Convert to cv2
    img_array = np.array(img)
    if img.mode == 'RGBA':
        alpha = img_array[:, :, 3]
        img_cv = cv2.cvtColor(img_array[:, :, :3], cv2.COLOR_RGB2BGR)
    else:
        img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        alpha = None
    
    # High-quality resize
    result = cv2.resize(img_cv, target_size, interpolation=cv2.INTER_LANCZOS4)
    
    # Unsharp mask
    gaussian = cv2.GaussianBlur(result, (0, 0), 2.0)
    result = cv2.addWeighted(result, 1.5, gaussian, -0.5, 0)
    
    # Bilateral filter
    result = cv2.bilateralFilter(result, 5, 50, 50)
    
    # CLAHE
    lab = cv2.cvtColor(result, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    result = cv2.merge([l, a, b])
    result = cv2.cvtColor(result, cv2.COLOR_LAB2BGR)
    
    elapsed = time.time() - start_time
    
    # Convert back
    result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
    if alpha is not None:
        alpha_resized = cv2.resize(alpha, target_size, interpolation=cv2.INTER_LANCZOS4)
        result_rgba = np.dstack((result_rgb, alpha_resized))
        result_opencv = Image.fromarray(result_rgba, 'RGBA')
    else:
        result_opencv = Image.fromarray(result_rgb, 'RGB')
    
    # Save
    output_path = "test_image_opencv.png"
    result_opencv.save(output_path, quality=95)
    file_size = os.path.getsize(output_path) // 1024
    
    print(f"   ✅ Complete in {elapsed:.2f}s")
    print(f"   📁 Saved: {output_path}")
    print(f"   📊 Size: {file_size} KB")
    print(f"   🎨 Quality: Very good (multi-stage enhancement)")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

# Summary
print("\n" + "=" * 80)
print("📊 QUALITY COMPARISON SUMMARY")
print("=" * 80)

if realesrgan_available and os.path.exists("test_image_realesrgan.png"):
    realesrgan_size = os.path.getsize("test_image_realesrgan.png") // 1024
    opencv_size = os.path.getsize("test_image_opencv.png") // 1024
    
    print(f"\n{'Method':<25} {'File Size':<15} {'Quality':<20} {'Speed'}")
    print("-" * 80)
    print(f"{'Real-ESRGAN':<25} {realesrgan_size:>6} KB       {'★★★★★ Excellent':<20} {'Slower'}")
    print(f"{'Enhanced OpenCV':<25} {opencv_size:>6} KB       {'★★★★☆ Very Good':<20} {'Fast'}")
    
    diff_percent = ((realesrgan_size - opencv_size) / opencv_size) * 100
    print(f"\n💾 Detail Preservation: Real-ESRGAN has {diff_percent:+.1f}% more image data")
    print(f"🎯 Recommendation: Real-ESRGAN for best quality, OpenCV for speed")
else:
    print("\n✅ Enhanced OpenCV upscaling available")
    print("📦 Install Real-ESRGAN for best quality:")
    print("   pip install realesrgan basicsr torch torchvision")

print("\n🎉 Testing Complete!")
print("=" * 80)
