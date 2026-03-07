#!/usr/bin/env python3
"""
GIMP 3.x Python-Fu script: Vignette
Adds a vignette (darkened edges) effect using GEGL's vignette filter.

Config variables at the top are injected by Claude before writing to a temp file.
"""

# === CONFIG (injected by Claude) ===
INPUT_PATH = "__INPUT_PATH__"
OUTPUT_PATH = "__OUTPUT_PATH__"
SOFTNESS = __SOFTNESS__      # 0.0-1.0 (default 0.8) — edge softness
RADIUS = __RADIUS__          # 0.5-3.0 (default 1.2) — vignette size (larger = less effect)

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

    f = Gimp.DrawableFilter.new(drawable, "gegl:vignette", "vignette")
    config = f.get_config()
    config.set_property("softness", float(SOFTNESS))
    config.set_property("radius", float(RADIUS))

    drawable.append_filter(f)
    drawable.merge_filter(f)
    print(f"Vignette: softness={SOFTNESS}, radius={RADIUS}")

    image.flatten()
    Gimp.file_save(Gimp.RunMode.NONINTERACTIVE, image, Gio.File.new_for_path(OUTPUT_PATH))
    print(f"Output saved to: {OUTPUT_PATH}")
    image.delete()

run()
