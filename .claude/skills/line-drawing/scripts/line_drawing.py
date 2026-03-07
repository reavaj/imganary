#!/usr/bin/env python3
"""
GIMP 3.x Python-Fu script: Line Drawing
Converts a photo into a clean line drawing using the photocopy GEGL filter.

Config variables at the top are injected by Claude before writing to a temp file.
"""

# === CONFIG (injected by Claude) ===
INPUT_PATH = "__INPUT_PATH__"
OUTPUT_PATH = "__OUTPUT_PATH__"
MASK_RADIUS = __MASK_RADIUS__      # float, controls line thickness (smaller = thinner)
SHARPNESS = __SHARPNESS__          # float 0.0-1.0, edge sharpness
BLACK = __BLACK__                  # float 0.0-1.0, black fill amount
WHITE = __WHITE__                  # float 0.0-1.0, white fill amount

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

    # Apply photocopy filter
    f = Gimp.DrawableFilter.new(drawable, "gegl:photocopy", "photocopy")
    config = f.get_config()
    config.set_property("mask-radius", float(MASK_RADIUS))
    config.set_property("sharpness", float(SHARPNESS))
    config.set_property("black", float(BLACK))
    config.set_property("white", float(WHITE))
    drawable.append_filter(f)
    drawable.merge_filter(f)
    print(f"Photocopy: mask-radius={MASK_RADIUS}, sharpness={SHARPNESS}, black={BLACK}, white={WHITE}")

    image.flatten()
    Gimp.file_save(Gimp.RunMode.NONINTERACTIVE, image, Gio.File.new_for_path(OUTPUT_PATH))
    print(f"Output saved to: {OUTPUT_PATH}")
    image.delete()

run()
