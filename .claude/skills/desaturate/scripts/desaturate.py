#!/usr/bin/env python3
"""
GIMP 3.x Python-Fu script: Desaturate
Converts image to grayscale using a chosen desaturation mode.

Config variables at the top are injected by Claude before writing to a temp file.
"""

# === CONFIG (injected by Claude) ===
INPUT_PATH = "__INPUT_PATH__"
OUTPUT_PATH = "__OUTPUT_PATH__"
DESAT_MODE = "__DESAT_MODE__"  # LUMINANCE|LUMA|LIGHTNESS|AVERAGE|VALUE|LUMINOSITY_GIMP2

# === IMPORTS ===
import gi
gi.require_version("Gimp", "3.0")
gi.require_version("Gegl", "0.4")
from gi.repository import Gimp, Gegl, Gio

# Mode mapping
MODES = {
    "LUMINANCE": Gimp.DesaturateMode.LUMINANCE,
    "LUMA": Gimp.DesaturateMode.LUMA,
    "LIGHTNESS": Gimp.DesaturateMode.LIGHTNESS_HSL,
    "AVERAGE": Gimp.DesaturateMode.AVERAGE,
    "VALUE": Gimp.DesaturateMode.VALUE,
}


def run():
    image = Gimp.file_load(Gimp.RunMode.NONINTERACTIVE, Gio.File.new_for_path(INPUT_PATH))
    if image is None:
        print(f"ERROR: Failed to load image: {INPUT_PATH}")
        return

    drawable = image.get_layers()[0]
    print(f"Loaded: {drawable.get_width()}x{drawable.get_height()}")

    mode = MODES.get(DESAT_MODE, Gimp.DesaturateMode.LUMINANCE)
    drawable.desaturate(mode)
    print(f"Desaturated with mode: {DESAT_MODE}")

    image.flatten()
    Gimp.file_save(Gimp.RunMode.NONINTERACTIVE, image, Gio.File.new_for_path(OUTPUT_PATH))
    print(f"Output saved to: {OUTPUT_PATH}")
    image.delete()

run()
