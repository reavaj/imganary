---
name: desaturate
description: >-
  Convert images to grayscale via GIMP Python-Fu batch automation with multiple
  desaturation modes. Trigger on: "grayscale", "black and white", "desaturate",
  "remove color", "b&w", "monochrome".
user-invocable: true
compatibility: |
  Requires GIMP 3.x with Python-Fu support enabled.
---

# Desaturate

Convert an image to grayscale using different desaturation algorithms.

## Instructions

### Step 1: Check GIMP is installed

```bash
gimp --version
```

### Step 2: Get the image path

Ask the user for the image path if not already provided.

### Step 3: Determine desaturation mode

| Mode | Description | Best for |
|------|------------|---------|
| **LUMINANCE** | Perceptual luminance (ITU-R 709) | General purpose, most natural |
| **LUMA** | Linear luminance | Technical accuracy |
| **LIGHTNESS** | HSL lightness | Brighter result |
| **AVERAGE** | (R+G+B)/3 | Simple, even |
| **VALUE** | max(R,G,B) | Brightest possible |

Default to **LUMINANCE** if the user doesn't specify.

### Step 4: Prepare the script

1. Read the bundled script template at `scripts/desaturate.py` (relative to this SKILL.md)
2. Replace the config placeholders:
   - `__INPUT_PATH__` → absolute path to the input image
   - `__OUTPUT_PATH__` → output path (default: append `_bw` before extension)
   - `__DESAT_MODE__` → one of: LUMINANCE, LUMA, LIGHTNESS, AVERAGE, VALUE
3. Write the modified script to `/tmp/imganary_desaturate.py`

### Step 5: Run GIMP batch

**macOS:**
```bash
LSBackgroundOnly=1 /Applications/GIMP.app/Contents/MacOS/gimp-console \
  -n -i --no-data --quit \
  --gimprc="$HOME/Library/Application Support/GIMP/3.0/batch-gimprc" \
  --batch-interpreter=python-fu-eval \
  -b "exec(open('/tmp/imganary_desaturate.py').read())" 2>&1
```

**Linux:**
```bash
gimp -n -i --no-data --batch-interpreter=python-fu-eval \
  -b "exec(open('/tmp/imganary_desaturate.py').read())" \
  -b '(gimp-quit 0)' 2>&1
```

### Step 6: Present the result

Tell the user the output file path and which desaturation mode was used.
