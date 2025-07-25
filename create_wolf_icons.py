#!/usr/bin/env python3
"""
Script to create wolf logo PWA icons from the base64 image provided by the user
"""

import base64
from PIL import Image, ImageDraw
import io
import os

# The wolf logo as seen in the user's message - black circle with white wolf
def create_wolf_icon(size):
    """Create a wolf icon with the specified size"""
    # Create a new image with black background (circular)
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw black circle background
    draw.ellipse([0, 0, size, size], fill=(0, 0, 0, 255))
    
    # Create a simple wolf silhouette using geometric shapes
    # This is a simplified version of the wolf logo from the user's image
    center_x, center_y = size // 2, size // 2
    
    # Scale factor based on icon size
    scale = size / 192.0
    
    # Wolf head outline (simplified)
    # Main head shape
    head_size = int(60 * scale)
    head_y = center_y - int(10 * scale)
    draw.ellipse([center_x - head_size//2, head_y - head_size//2, 
                  center_x + head_size//2, head_y + head_size//2], 
                 fill=(255, 255, 255, 255))
    
    # Ears
    ear_size = int(20 * scale)
    ear_offset_x = int(35 * scale)
    ear_offset_y = int(35 * scale)
    
    # Left ear
    draw.polygon([(center_x - ear_offset_x, head_y - ear_offset_y),
                  (center_x - ear_offset_x + ear_size, head_y - ear_offset_y - int(15 * scale)),
                  (center_x - ear_offset_x + int(10 * scale), head_y - ear_offset_y + int(10 * scale))], 
                 fill=(255, 255, 255, 255))
    
    # Right ear
    draw.polygon([(center_x + ear_offset_x, head_y - ear_offset_y),
                  (center_x + ear_offset_x - ear_size, head_y - ear_offset_y - int(15 * scale)),
                  (center_x + ear_offset_x - int(10 * scale), head_y - ear_offset_y + int(10 * scale))], 
                 fill=(255, 255, 255, 255))
    
    # Snout/muzzle
    muzzle_width = int(25 * scale)
    muzzle_height = int(15 * scale)
    muzzle_y = head_y + int(20 * scale)
    draw.ellipse([center_x - muzzle_width//2, muzzle_y - muzzle_height//2,
                  center_x + muzzle_width//2, muzzle_y + muzzle_height//2],
                 fill=(255, 255, 255, 255))
    
    # Eyes (black dots)
    eye_size = int(4 * scale)
    eye_offset_x = int(15 * scale)
    eye_offset_y = int(10 * scale)
    draw.ellipse([center_x - eye_offset_x - eye_size//2, head_y - eye_offset_y - eye_size//2,
                  center_x - eye_offset_x + eye_size//2, head_y - eye_offset_y + eye_size//2],
                 fill=(0, 0, 0, 255))
    draw.ellipse([center_x + eye_offset_x - eye_size//2, head_y - eye_offset_y - eye_size//2,
                  center_x + eye_offset_x + eye_size//2, head_y - eye_offset_y + eye_size//2],
                 fill=(0, 0, 0, 255))
    
    # Body/torso (simplified geometric shape)
    body_width = int(40 * scale)
    body_height = int(50 * scale)
    body_y = center_y + int(30 * scale)
    draw.ellipse([center_x - body_width//2, body_y - body_height//2,
                  center_x + body_width//2, body_y + body_height//2],
                 fill=(255, 255, 255, 255))
    
    return img

def main():
    """Create wolf icons for PWA"""
    output_dir = "/app/frontend/public"
    
    # Create icons for different sizes
    sizes = [192, 512]
    
    for size in sizes:
        print(f"Creating {size}x{size} wolf icon...")
        icon = create_wolf_icon(size)
        
        # Save as PNG
        icon_path = os.path.join(output_dir, f"icon-{size}.png")
        icon.save(icon_path, "PNG", optimize=True)
        print(f"Saved: {icon_path}")
    
    print("Wolf icons created successfully!")

if __name__ == "__main__":
    main()