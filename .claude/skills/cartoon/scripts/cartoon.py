#!/usr/bin/env python3
"""
GIMP 3.x Python-Fu script: Cartoon Effect
Applies a cartoon/comic look using GEGL's cartoon filter.
Traces edges with dark lines and flattens shading.

Config variables at the top are injected by Claude before writing to a temp file.
"""

# === CONFIG (injected by Claude) ===
INPUT_PATH = "__INPUT_PATH__"
OUTPUT_PATH = "__OUTPUT_PATH__"
MASK_RADIUS = __MASK_RADIUS__    # 1.0-50.0 (default 7.0) — edge detection radius
PCT_BLACK = __PCT_BLACK__        # 0.0-1.0 (default 0.2) — amount of black for edges

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

    # Create and configure the cartoon filter
    f = Gimp.DrawableFilter.new(drawable, "gegl:cartoon", "cartoon")
    config = f.get_config()
    config.set_property("mask-radius", float(MASK_RADIUS))
    config.set_property("pct-black", float(PCT_BLACK))

    # Apply
    drawable.append_filter(f)
    drawable.merge_filter(f)
    print(f"Cartoon effect: mask-radius={MASK_RADIUS}, pct-black={PCT_BLACK}")

    image.flatten()
    Gimp.file_save(Gimp.RunMode.NONINTERACTIVE, image, Gio.File.new_for_path(OUTPUT_PATH))
    print(f"Output saved to: {OUTPUT_PATH}")
    image.delete()

run()
