#!/usr/bin/env python3
"""
Generate a motor/gear icon for the application.
"""

import math
from PIL import Image, ImageDraw


def create_motor_icon(size=256):
    """Create a motor/gear icon with industrial yellow-black theme."""
    # Create image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    center = size // 2

    # Colors (industrial theme)
    yellow = (255, 193, 7, 255)      # #ffc107
    dark = (26, 26, 26, 255)         # #1a1a1a
    gray = (45, 45, 45, 255)         # #2d2d2d

    # Draw outer gear
    outer_radius = int(size * 0.45)
    inner_radius = int(size * 0.32)
    teeth = 12
    tooth_height = int(size * 0.08)

    # Draw gear body (dark circle)
    draw.ellipse(
        [center - outer_radius, center - outer_radius,
         center + outer_radius, center + outer_radius],
        fill=dark, outline=yellow, width=3
    )

    # Draw gear teeth
    for i in range(teeth):
        angle = i * (360 / teeth)
        rad = math.radians(angle)

        # Tooth outer points
        x1 = center + int((outer_radius + tooth_height) * math.cos(rad - 0.15))
        y1 = center + int((outer_radius + tooth_height) * math.sin(rad - 0.15))
        x2 = center + int((outer_radius + tooth_height) * math.cos(rad + 0.15))
        y2 = center + int((outer_radius + tooth_height) * math.sin(rad + 0.15))

        # Tooth base points
        x3 = center + int(outer_radius * math.cos(rad - 0.2))
        y3 = center + int(outer_radius * math.sin(rad - 0.2))
        x4 = center + int(outer_radius * math.cos(rad + 0.2))
        y4 = center + int(outer_radius * math.sin(rad + 0.2))

        # Draw tooth
        draw.polygon([x3, y3, x1, y1, x2, y2, x4, y4], fill=yellow)

    # Draw inner circle (motor shaft area)
    shaft_radius = int(size * 0.15)
    draw.ellipse(
        [center - shaft_radius, center - shaft_radius,
         center + shaft_radius, center + shaft_radius],
        fill=gray, outline=yellow, width=3
    )

    # Draw center dot (shaft)
    dot_radius = int(size * 0.05)
    draw.ellipse(
        [center - dot_radius, center - dot_radius,
         center + dot_radius, center + dot_radius],
        fill=yellow
    )

    # Draw rotation arrow indicator
    arrow_radius = int(size * 0.25)
    arrow_width = int(size * 0.03)

    # Arc points
    start_angle = 45
    end_angle = 315

    # Draw arc using lines
    for angle in range(start_angle, end_angle, 5):
        rad1 = math.radians(angle)
        rad2 = math.radians(angle + 5)
        x1 = center + int(arrow_radius * math.cos(rad1))
        y1 = center + int(arrow_radius * math.sin(rad1))
        x2 = center + int(arrow_radius * math.cos(rad2))
        y2 = center + int(arrow_radius * math.sin(rad2))
        draw.line([(x1, y1), (x2, y2)], fill=yellow, width=arrow_width)

    # Draw arrowhead
    arrow_angle = math.radians(end_angle)
    ax = center + int(arrow_radius * math.cos(arrow_angle))
    ay = center + int(arrow_radius * math.sin(arrow_angle))

    arrow_size = int(size * 0.08)
    draw.polygon([
        (ax, ay),
        (ax - arrow_size, ay - arrow_size // 2),
        (ax - arrow_size // 2, ay + arrow_size // 2)
    ], fill=yellow)

    return img


def main():
    """Generate icons in multiple sizes."""
    import os

    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Generate PNG icons
    sizes = [16, 32, 48, 64, 128, 256]

    for size in sizes:
        icon = create_motor_icon(size)
        icon.save(os.path.join(script_dir, f'motor_{size}.png'))
        print(f"Generated motor_{size}.png")

    # Generate main icon
    icon_256 = create_motor_icon(256)
    icon_256.save(os.path.join(script_dir, 'motor_icon.png'))
    print("Generated motor_icon.png")

    # Generate ICO file (Windows)
    icon_sizes = []
    for size in [16, 32, 48, 64, 128, 256]:
        icon_sizes.append(create_motor_icon(size))

    # Save as ICO with all sizes embedded
    icon_256 = create_motor_icon(256)
    icon_256.save(
        os.path.join(script_dir, 'motor_icon.ico'),
        format='ICO',
        append_images=[create_motor_icon(s) for s in [128, 64, 48, 32, 16]],
        sizes=[(s, s) for s in [256, 128, 64, 48, 32, 16]]
    )
    print("Generated motor_icon.ico")


if __name__ == '__main__':
    main()
