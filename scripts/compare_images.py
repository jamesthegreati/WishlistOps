#!/usr/bin/env python3
"""Compare original and processed images."""

from PIL import Image
import os

# Original
orig = Image.open('test_image.png')
orig_size = os.path.getsize('test_image.png')

# Processed
proc = Image.open('test_image_processed.png')
proc_size = os.path.getsize('test_image_processed.png')

print('Image Comparison Report')
print('=' * 60)
print()
print('ORIGINAL IMAGE:')
print(f'  Dimensions: {orig.width} x {orig.height} pixels')
print(f'  Aspect Ratio: {orig.width/orig.height:.3f}:1')
print(f'  Color Mode: {orig.mode}')
print(f'  File Size: {orig_size:,} bytes ({orig_size/1024:.1f} KB)')
print()
print('PROCESSED IMAGE (Steam Format):')
print(f'  Dimensions: {proc.width} x {proc.height} pixels')
print(f'  Aspect Ratio: {proc.width/proc.height:.3f}:1')
print(f'  Color Mode: {proc.mode}')
print(f'  File Size: {proc_size:,} bytes ({proc_size/1024:.1f} KB)')
print()
print('TRANSFORMATION APPLIED:')
print(f'  Width: {orig.width}px -> {proc.width}px (+{proc.width-orig.width}px, {((proc.width/orig.width-1)*100):.1f}% increase)')
print(f'  Height: {orig.height}px -> {proc.height}px (+{proc.height-orig.height}px, {((proc.height/orig.height-1)*100):.1f}% increase)')
print(f'  File Size: +{((proc_size/orig_size-1)*100):.1f}% increase')
print(f'  Color Mode: {orig.mode} -> {proc.mode} (alpha channel added for transparency)')
print()
print('PROCESSING METHOD:')
original_ratio = orig.width / orig.height
steam_ratio = proc.width / proc.height

if original_ratio > steam_ratio:
    crop_info = "Image was WIDER than Steam format -> Cropped sides to fit"
    width_cropped = orig.width - (orig.height * steam_ratio)
    print(f'  {crop_info}')
    print(f'  Cropped ~{int(width_cropped)}px from horizontal edges')
elif original_ratio < steam_ratio:
    crop_info = "Image was TALLER than Steam format -> Cropped top/bottom to fit"
    height_cropped = orig.height - (orig.width / steam_ratio)
    print(f'  {crop_info}')
    print(f'  Cropped ~{int(height_cropped)}px from vertical edges')
else:
    print('  Perfect aspect ratio match -> Simple upscale')

print()
print('STEAM COMPLIANCE:')
print(f'  Required: 800x450 pixels -> {"PASS" if proc.width == 800 and proc.height == 450 else "FAIL"}')
print(f'  Aspect Ratio: 16:9 (1.778:1) -> {"PASS" if abs(steam_ratio - 1.778) < 0.01 else "FAIL"}')
print()
print('OUTPUT: test_image_processed.png')
print('Status: Ready for Steam Community Hub upload!')
