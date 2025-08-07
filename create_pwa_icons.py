#!/usr/bin/env python3
"""
PWA Icon Generator for Alphalete Club
Creates separate "any" and "maskable" icons with proper specifications
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_alphalete_icon(size, icon_type="any"):
    """
    Create Alphalete Club icon with proper PWA specifications
    
    Args:
        size (int): Icon size in pixels
        icon_type (str): "any" or "maskable"
    """
    
    # Create canvas
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    if icon_type == "maskable":
        # Maskable icons need 20% padding on all sides (safe zone)
        safe_zone = int(size * 0.2)
        content_size = size - (safe_zone * 2)
        offset = safe_zone
        
        # Add a subtle background for maskable version
        draw.ellipse([
            safe_zone // 2, safe_zone // 2, 
            size - safe_zone // 2, size - safe_zone // 2
        ], fill=(17, 24, 39, 255))  # Dark background matching theme
        
    else:
        # "Any" icons can use full canvas
        content_size = size
        offset = 0
    
    # Main circle background
    circle_padding = int(content_size * 0.05)
    circle_size = content_size - (circle_padding * 2)
    circle_x = offset + circle_padding
    circle_y = offset + circle_padding
    
    # Gradient-like effect with multiple circles
    draw.ellipse([
        circle_x, circle_y, 
        circle_x + circle_size, circle_y + circle_size
    ], fill=(220, 38, 38, 255))  # Primary red
    
    # Inner circle for depth
    inner_padding = int(circle_size * 0.1)
    draw.ellipse([
        circle_x + inner_padding, circle_y + inner_padding,
        circle_x + circle_size - inner_padding, circle_y + circle_size - inner_padding
    ], fill=(239, 68, 68, 255))  # Lighter red
    
    # Dumbbell icon in center
    center_x = circle_x + circle_size // 2
    center_y = circle_y + circle_size // 2
    dumbbell_size = int(circle_size * 0.4)
    
    # Dumbbell weights (circles)
    weight_radius = int(dumbbell_size * 0.15)
    bar_width = int(dumbbell_size * 0.08)
    bar_length = int(dumbbell_size * 0.6)
    
    # Left weight
    draw.ellipse([
        center_x - bar_length//2 - weight_radius, center_y - weight_radius,
        center_x - bar_length//2 + weight_radius, center_y + weight_radius
    ], fill=(255, 255, 255, 255))
    
    # Right weight  
    draw.ellipse([
        center_x + bar_length//2 - weight_radius, center_y - weight_radius,
        center_x + bar_length//2 + weight_radius, center_y + weight_radius
    ], fill=(255, 255, 255, 255))
    
    # Connecting bar
    draw.rectangle([
        center_x - bar_length//2, center_y - bar_width//2,
        center_x + bar_length//2, center_y + bar_width//2
    ], fill=(255, 255, 255, 255))
    
    # Add "A" letter in center for branding
    if size >= 192:
        try:
            # Try to load a font, fallback to default if not available
            font_size = int(dumbbell_size * 0.3)
            font = ImageFont.load_default()
            
            # Draw "A" for Alphalete
            text = "A"
            
            # Get text size for centering
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            text_x = center_x - text_width // 2
            text_y = center_y + int(dumbbell_size * 0.15) - text_height // 2
            
            draw.text((text_x, text_y), text, fill=(17, 24, 39, 255), font=font)
            
        except Exception as e:
            print(f"Note: Could not add text overlay: {e}")
    
    return img

def main():
    """Generate all required PWA icons"""
    print("🎨 Creating PWA icons for Alphalete Club...")
    
    # Icon specifications for PWA
    icon_specs = [
        (192, "any"),
        (192, "maskable"), 
        (512, "any"),
        (512, "maskable"),
        # Additional useful sizes
        (72, "any"),
        (96, "any"), 
        (128, "any"),
        (144, "any"),
        (152, "any"),
        (384, "any"),
    ]
    
    output_dir = "/app/frontend/public"
    
    for size, icon_type in icon_specs:
        print(f"📱 Creating {size}x{size} {icon_type} icon...")
        
        try:
            icon = create_alphalete_icon(size, icon_type)
            
            # Save with descriptive filename
            if icon_type == "maskable":
                filename = f"icon-{size}x{size}-maskable.png"
            else:
                filename = f"icon-{size}x{size}.png"
                
            filepath = os.path.join(output_dir, filename)
            icon.save(filepath, "PNG", optimize=True)
            
            print(f"✅ Saved: {filename}")
            
        except Exception as e:
            print(f"❌ Error creating {size}x{size} {icon_type} icon: {e}")
    
    # Also create legacy named files for backward compatibility
    print("\n🔄 Creating legacy named files...")
    
    try:
        # Create icon-192.png (any purpose)
        icon_192_any = create_alphalete_icon(192, "any")
        icon_192_any.save("/app/frontend/public/icon-192.png", "PNG", optimize=True)
        print("✅ Updated: icon-192.png")
        
        # Create icon-512.png (any purpose) 
        icon_512_any = create_alphalete_icon(512, "any")
        icon_512_any.save("/app/frontend/public/icon-512.png", "PNG", optimize=True)
        print("✅ Updated: icon-512.png")
        
    except Exception as e:
        print(f"❌ Error creating legacy icons: {e}")
    
    print("\n🎉 PWA icon generation complete!")
    print("📋 Files created:")
    print("   • icon-192x192.png (any)")
    print("   • icon-192x192-maskable.png (maskable)") 
    print("   • icon-512x512.png (any)")
    print("   • icon-512x512-maskable.png (maskable)")
    print("   • Additional sizes for various devices")
    print("   • Legacy icon-192.png and icon-512.png updated")

if __name__ == "__main__":
    main()