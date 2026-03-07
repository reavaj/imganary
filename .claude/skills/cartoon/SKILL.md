---
name: cartoon
description: >-
  Apply a cartoon/comic effect to images via GIMP GEGL filter batch automation.
  Traces edges with dark lines and flattens shading for a hand-drawn look.
  Trigger on: "cartoon", "comic effect", "comic book", "cartoon effect",
  "make it look like a cartoon", "hand-drawn look", "cel shading".
user-invocable: true
compatibility: |
  Requires GIMP 3.x with Python-Fu support enabled.
---

# Cartoon Effect

Apply a cartoon/comic look: dark edge lines with flattened shading.

## Instructions

### Step 1: Check GIMP is installed

```bash
gimp --version
```

### Step 2: Get the image path

Ask the user for the image path if not already provided.

### Step 3: Determine parameters

| Parameter | Range | Default | Description |
|-----------|-------|---------|-------------|
| **mask-radius** | 1.0–50.0 | 7.0 | Edge detection radius. Higher = thicker/more edges |
| **pct-black** | 0.0–1.0 | 0.2 | Amount of black for edges. Higher = darker/more contrast |

Presets:

| Preset | mask-radius | pct-black | Look |
|--------|-------------|-----------|------|
| **Subtle** | 4.0 | 0.1 | Light edge emphasis |
| **Classic** | 7.0 | 0.2 | Standard cartoon look |
| **Bold** | 12.0 | 0.3 | Heavy comic style |
| **Ink** | 20.0 | 0.5 | Strong ink outlines |

Default to **Classic** if the user doesn't specify.

### Step 4: Prepare the script

1. Read the bundled script template at `scripts/cartoon.py` (relative to this SKILL.md)
2. Replace the config placeholders:
   - `__INPUT_PATH__` → absolute path to the input image
   - `__OUTPUT_PATH__` → output path (default: append `_cartoon` before extension)
   - `__MASK_RADIUS__` → float, 1.0-50.0
   - `__PCT_BLACK__` → float, 0.0-1.0
3. Write the modified script to `/tmp/imganary_cartoon.py`

### Step 5: Run GIMP batch

**macOS:**
```bash
LSBackgroundOnly=1 /Applications/GIMP.app/Contents/MacOS/gimp-console \
  -n -i --no-data --quit \
  --gimprc="$HOME/Library/Application Support/GIMP/3.0/batch-gimprc" \
  --batch-interpreter=python-fu-eval \
  -b "exec(open('/tmp/imganary_cartoon.py').read())" 2>&1
```

**Linux:**
```bash
gimp -n -i --no-data --batch-interpreter=python-fu-eval \
  -b "exec(open('/tmp/imganary_cartoon.py').read())" \
  -b '(gimp-quit 0)' 2>&1
```

### Step 6: Present the result

Tell the user the output file path and the settings used. Suggest adjusting mask-radius or pct-black if they want more or less effect.

## GIMP 3.x API Notes

This skill uses the GEGL filter system (new in GIMP 3.x):
```python
f = Gimp.DrawableFilter.new(drawable, "gegl:cartoon", "cartoon")
config = f.get_config()
config.set_property("mask-radius", 7.0)
config.set_property("pct-black", 0.2)
drawable.append_filter(f)
drawable.merge_filter(f)
```
