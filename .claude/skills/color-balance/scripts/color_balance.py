#!/usr/bin/env python3
"""
GIMP 3.x Python-Fu script: Color Balance
Shifts color balance in shadows, midtones, and highlights independently.

Config variables at the top are injected by Claude before writing to a temp file.
"""

# === CONFIG (injected by Claude) ===
INPUT_PATH = "__INPUT_PATH__"
OUTPUT_PATH = "__OUTPUT_PATH__"
# Each value ranges from -100 to 100
# Shadows
SHADOW_CYAN_RED = __SHADOW_CYAN_RED__
SHADOW_MAGENTA_GREEN = __SHADOW_MAGENTA_GREEN__
SHADOW_YELLOW_BLUE = __SHADOW_YELLOW_BLUE__
# Midtones
MID_CYAN_RED = __MID_CYAN_RED__
MID_MAGENTA_GREEN = __MID_MAGENTA_GREEN__
MID_YELLOW_BLUE = __MID_YELLOW_BLUE__
# Highlights
HIGH_CYAN_RED = __HIGH_CYAN_RED__
HIGH_MAGENTA_GREEN = __HIGH_MAGENTA_GREEN__
HIGH_YELLOW_BLUE = __HIGH_YELLOW_BLUE__

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

    # Apply color balance to each tonal range
    for range_type, cr, mg, yb, label in [
        (Gimp.TransferMode.SHADOWS, SHADOW_CYAN_RED, SHADOW_MAGENTA_GREEN, SHADOW_YELLOW_BLUE, "Shadows"),
        (Gimp.TransferMode.MIDTONES, MID_CYAN_RED, MID_MAGENTA_GREEN, MID_YELLOW_BLUE, "Midtones"),
        (Gimp.TransferMode.HIGHLIGHTS, HIGH_CYAN_RED, HIGH_MAGENTA_GREEN, HIGH_YELLOW_BLUE, "Highlights"),
    ]:
        if cr != 0 or mg != 0 or yb != 0:
            drawable.color_balance(range_type, True, cr, mg, yb)
            print(f"  {label}: cyan-red={cr:+d}, magenta-green={mg:+d}, yellow-blue={yb:+d}")

    image.flatten()
    Gimp.file_save(Gimp.RunMode.NONINTERACTIVE, image, Gio.File.new_for_path(OUTPUT_PATH))
    print(f"Output saved to: {OUTPUT_PATH}")
    image.delete()

run()
