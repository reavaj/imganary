#!/usr/bin/env python3
"""
GIMP 3.x Python-Fu script: Duotone
Converts image to a two-color duotone using desaturation + per-channel curves.

Config variables at the top are injected by Claude before writing to a temp file.
"""

# === CONFIG (injected by Claude) ===
INPUT_PATH = "__INPUT_PATH__"
OUTPUT_PATH = "__OUTPUT_PATH__"
SHADOW_R = __SHADOW_R__
SHADOW_G = __SHADOW_G__
SHADOW_B = __SHADOW_B__
HIGHLIGHT_R = __HIGHLIGHT_R__
HIGHLIGHT_G = __HIGHLIGHT_G__
HIGHLIGHT_B = __HIGHLIGHT_B__

# === IMPORTS ===
import gi
gi.require_version("Gimp", "3.0")
gi.require_version("Gegl", "0.4")
from gi.repository import Gimp, Gegl, Gio


def run():
    image = Gimp.file_load(Gimp.RunMode.NONINTERACTIVE, Gio.File.new_for_path(INPUT_PATH))
    if image is None:
        print(f"ERROR: Failed to load image: {INPUT_PATH}")
        return

    drawable = image.get_layers()[0]
    print(f"Loaded: {drawable.get_width()}x{drawable.get_height()}")

    # Desaturate to luminance grayscale
    drawable.desaturate(Gimp.DesaturateMode.LUMINANCE)
    print("Desaturated")

    # Map shadow and highlight colors via per-channel curves
    for channel, shadow_val, highlight_val in [
        (Gimp.HistogramChannel.RED, SHADOW_R, HIGHLIGHT_R),
        (Gimp.HistogramChannel.GREEN, SHADOW_G, HIGHLIGHT_G),
        (Gimp.HistogramChannel.BLUE, SHADOW_B, HIGHLIGHT_B),
    ]:
        s = shadow_val / 255.0
        h = highlight_val / 255.0
        drawable.curves_spline(channel, [0.0, s, 1.0, h])

    print(f"Duotone: shadows=({SHADOW_R},{SHADOW_G},{SHADOW_B}) highlights=({HIGHLIGHT_R},{HIGHLIGHT_G},{HIGHLIGHT_B})")

    image.flatten()
    Gimp.file_save(Gimp.RunMode.NONINTERACTIVE, image, Gio.File.new_for_path(OUTPUT_PATH))
    print(f"Output saved to: {OUTPUT_PATH}")
    image.delete()

run()
