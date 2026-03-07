#!/usr/bin/env python3
"""
GIMP 3.x Python-Fu script: Text Overlay
Adds text to an image with configurable position, size, and color.

Config variables at the top are injected by Claude before writing to a temp file.
"""

# === CONFIG (injected by Claude) ===
INPUT_PATH = "__INPUT_PATH__"
OUTPUT_PATH = "__OUTPUT_PATH__"
TEXT = "__TEXT__"
FONT_SIZE = __FONT_SIZE__        # pixels
COLOR_HTML = "__COLOR_HTML__"    # hex color e.g. "#ffffff"
POSITION = "__POSITION__"        # center|top|bottom|top-left|top-right|bottom-left|bottom-right
MARGIN = __MARGIN__              # pixels from edge

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

    print(f"Loaded: {image.get_width()}x{image.get_height()}")

    # Create text layer using context font (works reliably in batch mode)
    font = Gimp.context_get_font()
    text_layer = Gimp.TextLayer.new(image, TEXT, font, FONT_SIZE, Gimp.Unit.pixel())

    if text_layer is None:
        print("ERROR: Failed to create text layer")
        image.delete()
        return

    # Set text color
    color = Gegl.Color.new(COLOR_HTML)
    text_layer.set_color(color)

    # Insert the text layer
    image.insert_layer(text_layer, None, -1)

    # Position the text
    img_w = image.get_width()
    img_h = image.get_height()
    txt_w = text_layer.get_width()
    txt_h = text_layer.get_height()

    positions = {
        "center": ((img_w - txt_w) // 2, (img_h - txt_h) // 2),
        "top": ((img_w - txt_w) // 2, MARGIN),
        "bottom": ((img_w - txt_w) // 2, img_h - txt_h - MARGIN),
        "top-left": (MARGIN, MARGIN),
        "top-right": (img_w - txt_w - MARGIN, MARGIN),
        "bottom-left": (MARGIN, img_h - txt_h - MARGIN),
        "bottom-right": (img_w - txt_w - MARGIN, img_h - txt_h - MARGIN),
    }

    x, y = positions.get(POSITION, positions["center"])
    text_layer.set_offsets(x, y)
    print(f"Text '{TEXT}' at ({x}, {y}), size={FONT_SIZE}px, color={COLOR_HTML}")

    # Flatten and save
    image.flatten()
    Gimp.file_save(Gimp.RunMode.NONINTERACTIVE, image, Gio.File.new_for_path(OUTPUT_PATH))
    print(f"Output saved to: {OUTPUT_PATH}")
    image.delete()

run()
