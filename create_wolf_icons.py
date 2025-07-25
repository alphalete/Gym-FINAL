#!/usr/bin/env python3
"""
Script to create cross logo PWA icons - black circle with white cross
"""

import base64
from PIL import Image, ImageDraw
import io
import os

def create_cross_icon(size):
    """Create a cross icon with the specified size"""
    # Create a new image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw black circle background
    draw.ellipse([0, 0, size, size], fill=(0, 0, 0, 255))
    
    # Create a white cross in the center
    center_x, center_y = size // 2, size // 2
    
    # Scale factor based on icon size
    scale = size / 192.0
    
    # Cross dimensions
    cross_width = int(20 * scale)  # Width of cross lines
    cross_length = int(60 * scale)  # Length of cross lines
    
    # Horizontal bar of cross
    draw.rectangle([
        center_x - cross_length//2, 
        center_y - cross_width//2,
        center_x + cross_length//2, 
        center_y + cross_width//2
    ], fill=(255, 255, 255, 255))
    
    # Vertical bar of cross
    draw.rectangle([
        center_x - cross_width//2, 
        center_y - cross_length//2,
        center_x + cross_width//2, 
        center_y + cross_length//2
    ], fill=(255, 255, 255, 255))
    
    return img

def main():
    """Create cross icons for PWA"""
    output_dir = "/app/frontend/public"
    
    # Create icons for different sizes
    sizes = [192, 512]
    
    for size in sizes:
        print(f"Creating {size}x{size} cross icon...")
        icon = create_cross_icon(size)
        
        # Save as PNG
        icon_path = os.path.join(output_dir, f"icon-{size}.png")
        icon.save(icon_path, "PNG", optimize=True)
        print(f"Saved: {icon_path}")
    
    print("Cross icons created successfully!")

if __name__ == "__main__":
    main()