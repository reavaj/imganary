---
name: text-overlay
description: >-
  Add text to images via GIMP Python-Fu batch automation. Creates a text layer
  with configurable text, size, color, and position. Trigger on: "add text",
  "text overlay", "watermark", "caption", "title text", "add label",
  "write text on image".
user-invocable: true
compatibility: |
  Requires GIMP 3.x with Python-Fu support enabled.
---

# Text Overlay

Add text to an image with configurable position, size, and color.

## Instructions

### Step 1: Check GIMP is installed

```bash
gimp --version
```

### Step 2: Get the image path

Ask the user for the image path if not already provided.

### Step 3: Determine text parameters

Ask the user for:
- **Text content**: The text to display
- **Font size**: In pixels. Defaults based on image size: ~5% of image height is a good starting point
- **Color**: HTML hex color. Default white `#ffffff` for dark images, black `#000000` for light
- **Position**: Where to place the text

| Position | Description |
|----------|------------|
| **center** | Centered in image |
| **top** | Centered horizontally, near top |
| **bottom** | Centered horizontally, near bottom |
| **top-left** | Top-left corner |
| **top-right** | Top-right corner |
| **bottom-left** | Bottom-left corner |
| **bottom-right** | Bottom-right corner |

- **Margin**: Pixels from edge (default: 40)

Default to **bottom-center, white, 5% of image height** if not specified.

### Step 4: Prepare the script

1. Read the bundled script template at `scripts/text_overlay.py` (relative to this SKILL.md)
2. Replace the config placeholders:
   - `__INPUT_PATH__` → absolute path to the input image
   - `__OUTPUT_PATH__` → output path (default: append `_text` before extension)
   - `__TEXT__` → the text string (escape any quotes)
   - `__FONT_SIZE__` → integer, pixels
   - `__COLOR_HTML__` → hex color string e.g. `#ffffff`
   - `__POSITION__` → one of: center, top, bottom, top-left, top-right, bottom-left, bottom-right
   - `__MARGIN__` → integer, pixels from edge
3. Write the modified script to `/tmp/imganary_text_overlay.py`

**Note**: The script uses `Gimp.context_get_font()` for the default font. GIMP's font-by-name lookup does not work in batch mode — the context font is reliable.

### Step 5: Run GIMP batch

**macOS:**
```bash
LSBackgroundOnly=1 /Applications/GIMP.app/Contents/MacOS/gimp-console \
  -n -i --no-data --quit \
  --gimprc="$HOME/Library/Application Support/GIMP/3.0/batch-gimprc" \
  --batch-interpreter=python-fu-eval \
  -b "exec(open('/tmp/imganary_text_overlay.py').read())" 2>&1
```

**Linux:**
```bash
gimp -n -i --no-data --batch-interpreter=python-fu-eval \
  -b "exec(open('/tmp/imganary_text_overlay.py').read())" \
  -b '(gimp-quit 0)' 2>&1
```

### Step 6: Present the result

Tell the user the output file path, the text that was added, and its position.
