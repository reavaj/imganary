---
name: brightness-contrast
description: >-
  Adjust image brightness and contrast via GIMP Python-Fu batch automation.
  Trigger on: "brighten", "darken", "increase contrast", "decrease contrast",
  "brightness", "contrast", "make brighter", "make darker", "more contrast",
  "less contrast", "exposure adjustment".
user-invocable: true
compatibility: |
  Requires GIMP 3.x with Python-Fu support enabled.
---

# Brightness/Contrast

Adjust the brightness and contrast of an image.

## Instructions

### Step 1: Check GIMP is installed

```bash
gimp --version
```

### Step 2: Get the image path

Ask the user for the image path if not already provided.

### Step 3: Determine brightness and contrast values

Both values range from **-1.0 to 1.0** (0.0 = no change).

Common adjustments:
| Intent | Brightness | Contrast |
|--------|-----------|----------|
| Slightly brighter | 0.15 | 0.0 |
| Much brighter | 0.4 | 0.0 |
| Slightly darker | -0.15 | 0.0 |
| More contrast | 0.0 | 0.25 |
| Pop (bright + punchy) | 0.08 | 0.24 |
| Faded/matte look | 0.0 | -0.2 |

Default to **brightness=0.0, contrast=0.25** if the user says "more contrast" without specifics.

### Step 4: Prepare the script

1. Read the bundled script template at `scripts/brightness_contrast.py` (relative to this SKILL.md)
2. Replace the config placeholders:
   - `__INPUT_PATH__` → absolute path to the input image
   - `__OUTPUT_PATH__` → output path (default: append `_adjusted` before extension)
   - `__BRIGHTNESS__` → float, -1.0 to 1.0
   - `__CONTRAST__` → float, -1.0 to 1.0
3. Write the modified script to `/tmp/imganary_brightness_contrast.py`

### Step 5: Run GIMP batch

**macOS:**
```bash
LSBackgroundOnly=1 /Applications/GIMP.app/Contents/MacOS/gimp-console \
  -n -i --no-data --quit \
  --gimprc="$HOME/Library/Application Support/GIMP/3.0/batch-gimprc" \
  --batch-interpreter=python-fu-eval \
  -b "exec(open('/tmp/imganary_brightness_contrast.py').read())" 2>&1
```

**Linux:**
```bash
gimp -n -i --no-data --batch-interpreter=python-fu-eval \
  -b "exec(open('/tmp/imganary_brightness_contrast.py').read())" \
  -b '(gimp-quit 0)' 2>&1
```

### Step 6: Present the result

Tell the user the output file path and the values applied.
