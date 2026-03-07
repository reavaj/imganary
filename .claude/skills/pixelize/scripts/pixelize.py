#!/usr/bin/env python3
"""
GIMP 3.x Python-Fu script: Pixelize
Applies a pixelation/mosaic effect using GEGL's pixelize filter.

Config variables at the top are injected by Claude before writing to a temp file.
"""

# === CONFIG (injected by Claude) ===
INPUT_PATH = "__INPUT_PATH__"
OUTPUT_PATH = "__OUTPUT_PATH__"
PIXEL_SIZE = __PIXEL_SIZE__    # 2-100 (default 16) — block size in pixels

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

    f = Gimp.DrawableFilter.new(drawable, "gegl:pixelize", "pixelize")
    config = f.get_config()
    config.set_property("size-x", int(PIXEL_SIZE))
    config.set_property("size-y", int(PIXEL_SIZE))

    drawable.append_filter(f)
    drawable.merge_filter(f)
    print(f"Pixelized: block size={PIXEL_SIZE}x{PIXEL_SIZE}")

    image.flatten()
    Gimp.file_save(Gimp.RunMode.NONINTERACTIVE, image, Gio.File.new_for_path(OUTPUT_PATH))
    print(f"Output saved to: {OUTPUT_PATH}")
    image.delete()

run()
