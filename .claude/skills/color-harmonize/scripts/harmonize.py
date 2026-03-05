#!/usr/bin/env python3
"""
GIMP 3.x Python-Fu script: Color Harmonize
Remaps image hues to a harmonious palette while preserving luminance and saturation.

Config variables at the top are injected by Claude before writing to a temp file.
Run via: /Applications/GIMP.app/Contents/MacOS/gimp-console -n -i --no-data \
           --gimprc="$HOME/Library/Application Support/GIMP/3.0/batch-gimprc" \
           --batch-interpreter=python-fu-eval \
           -b 'exec(open("/tmp/imganary_harmonize.py").read())'
"""

# === CONFIG (injected by Claude) ===
INPUT_PATH = "__INPUT_PATH__"
OUTPUT_PATH = "__OUTPUT_PATH__"
HARMONY_SCHEME = "__HARMONY_SCHEME__"  # complementary|analogous|split-complementary|tetradic

# === IMPORTS ===
import gi
gi.require_version("Gimp", "3.0")
gi.require_version("Gegl", "0.4")
from gi.repository import Gimp, Gegl, GLib, Gio
import colorsys
import math
import random
import sys

# === COLOR HARMONY MATH ===

def build_palette(dominant_hue, scheme):
    """
    Build a harmonious palette from a dominant hue (0-360 degrees).
    Returns a list of hue values (0-360).
    """
    h = dominant_hue % 360
    schemes = {
        "complementary": [h, (h + 180) % 360],
        "analogous": [(h - 30) % 360, h, (h + 30) % 360, (h + 60) % 360],
        "split-complementary": [h, (h + 150) % 360, (h + 210) % 360],
        "tetradic": [h, (h + 90) % 360, (h + 180) % 360, (h + 270) % 360],
    }
    if scheme not in schemes:
        print(f"Unknown scheme '{scheme}', falling back to complementary")
        scheme = "complementary"
    return schemes[scheme]


# GIMP hue ranges and their center hues (degrees)
HUE_RANGES = [
    (Gimp.HueRange.RED,     0),    # Red: ~330-30
    (Gimp.HueRange.YELLOW,  60),   # Yellow: ~30-90
    (Gimp.HueRange.GREEN,   120),  # Green: ~90-150
    (Gimp.HueRange.CYAN,    180),  # Cyan: ~150-210
    (Gimp.HueRange.BLUE,    240),  # Blue: ~210-270
    (Gimp.HueRange.MAGENTA, 300),  # Magenta: ~270-330
]


def hue_distance(h1, h2):
    """Shortest angular distance between two hues (0-360)."""
    d = abs(h1 - h2) % 360
    return min(d, 360 - d)


def signed_hue_offset(source, target):
    """Signed shortest rotation from source to target hue (-180 to +180)."""
    d = (target - source) % 360
    if d > 180:
        d -= 360
    return d


def find_nearest_palette_hue(range_center, palette):
    """Find the palette hue closest to a given range center."""
    return min(palette, key=lambda p: hue_distance(range_center, p))


# === DOMINANT HUE DETECTION ===

def detect_dominant_hue(drawable, num_samples=1000):
    """
    Randomly sample pixels from a drawable, build a hue histogram, return the dominant hue.
    Returns hue in degrees (0-360).
    """
    width = drawable.get_width()
    height = drawable.get_height()

    histogram = [0] * 36  # 36 bins of 10 degrees each

    for _ in range(num_samples):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        # get_pixel returns a Gegl.Color directly in GIMP 3.x
        color = drawable.get_pixel(x, y)
        rgba = color.get_rgba()
        h, s, v = colorsys.rgb_to_hsv(rgba.red, rgba.green, rgba.blue)
        # Only count pixels with enough saturation and brightness
        if s > 0.1 and v > 0.1:
            bin_idx = int(h * 36) % 36
            histogram[bin_idx] += 1

    # Find the peak bin
    if max(histogram) == 0:
        return 0  # Fallback: grayscale image
    peak_bin = histogram.index(max(histogram))
    dominant_hue = peak_bin * 10 + 5  # Center of the bin
    return dominant_hue


# === MAIN ===

def run():
    # Load the image
    file = Gio.File.new_for_path(INPUT_PATH)
    image = Gimp.file_load(Gimp.RunMode.NONINTERACTIVE, file)
    if image is None:
        print(f"ERROR: Failed to load image: {INPUT_PATH}")
        Gimp.quit(1)
        return

    # GIMP 3.x: get_layers() instead of get_active_drawable()
    drawable = image.get_layers()[0]

    # Detect dominant hue
    dominant_hue = detect_dominant_hue(drawable)
    print(f"Dominant hue: {dominant_hue:.0f} degrees")

    # Build palette
    palette = build_palette(dominant_hue, HARMONY_SCHEME)
    print(f"Harmony scheme: {HARMONY_SCHEME}")
    print(f"Palette hues: {[f'{h:.0f}' for h in palette]}")

    # Remap each GIMP hue range to the nearest palette color
    # GIMP 3.x: hue_saturation is a method on drawable
    for hue_range, center in HUE_RANGES:
        nearest = find_nearest_palette_hue(center, palette)
        offset = signed_hue_offset(center, nearest)
        if abs(offset) > 0.5:  # Only apply if there's a meaningful shift
            drawable.hue_saturation(
                hue_range,
                offset,   # hue offset
                0.0,      # lightness offset
                0.0,      # saturation offset
                0.0,      # overlap
            )
            print(f"  {hue_range.value_nick}: shifted {offset:+.0f} degrees -> {nearest:.0f}")

    # Flatten and export
    image.flatten()

    out_file = Gio.File.new_for_path(OUTPUT_PATH)
    Gimp.file_save(Gimp.RunMode.NONINTERACTIVE, image, out_file)

    print(f"Output saved to: {OUTPUT_PATH}")

    # Clean up
    image.delete()
    Gimp.quit()

run()
