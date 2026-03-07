---
name: pixelize
description: >-
  Apply a pixelation/mosaic effect to images via GIMP GEGL filter batch
  automation. Reduces the image to large colored blocks. Trigger on:
  "pixelate", "pixelize", "pixel art", "mosaic", "blocky",
  "8-bit look", "retro pixels", "censor".
user-invocable: true
compatibility: |
  Requires GIMP 3.x with Python-Fu support enabled.
---

# Pixelize

Reduce an image to large colored blocks for a pixelated/mosaic look.

## Instructions

### Step 1: Check GIMP is installed

```bash
gimp --version
```

### Step 2: Get the image path

Ask the user for the image path if not already provided.

### Step 3: Determine block size

| Pixel Size | Effect |
|-----------|--------|
| **4** | Subtle texture |
| **8** | Light pixelation |
| **16** | Classic pixel look |
| **32** | Strong mosaic |
| **64** | Very blocky, abstract |

Default to **16** if the user doesn't specify.

For censoring/redacting a region, use a larger size (32-64).

### Step 4: Prepare the script

1. Read the bundled script template at `scripts/pixelize.py` (relative to this SKILL.md)
2. Replace the config placeholders:
   - `__INPUT_PATH__` → absolute path to the input image
   - `__OUTPUT_PATH__` → output path (default: append `_pixelized` before extension)
   - `__PIXEL_SIZE__` → integer, 2-100
3. Write the modified script to `/tmp/imganary_pixelize.py`

### Step 5: Run GIMP batch

**macOS:**
```bash
LSBackgroundOnly=1 /Applications/GIMP.app/Contents/MacOS/gimp-console \
  -n -i --no-data --quit \
  --gimprc="$HOME/Library/Application Support/GIMP/3.0/batch-gimprc" \
  --batch-interpreter=python-fu-eval \
  -b "exec(open('/tmp/imganary_pixelize.py').read())" 2>&1
```

**Linux:**
```bash
gimp -n -i --no-data --batch-interpreter=python-fu-eval \
  -b "exec(open('/tmp/imganary_pixelize.py').read())" \
  -b '(gimp-quit 0)' 2>&1
```

### Step 6: Present the result

Tell the user the output file path and block size used.
