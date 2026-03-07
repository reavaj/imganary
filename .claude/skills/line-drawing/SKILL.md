---
name: line-drawing
description: >-
  Convert a photo into a clean line drawing using GIMP's photocopy GEGL filter.
  Trigger on: "line drawing", "line art", "lineart", "sketch", "pen drawing",
  "ink drawing", "outline", "convert to lines", "trace outline".
user-invocable: true
compatibility: |
  Requires GIMP 3.x with Python-Fu support enabled.
---

# Line Drawing

Convert a photo into a clean line drawing using the photocopy GEGL filter.

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
| MASK_RADIUS | 1.0 - 50.0 | 5.0 | Line thickness (smaller = thinner lines) |
| SHARPNESS | 0.0 - 1.0 | 0.8 | Edge sharpness |
| BLACK | 0.0 - 1.0 | 0.1 | Black fill amount (lower = less fill) |
| WHITE | 0.0 - 1.0 | 0.1 | White fill amount (lower = less fill) |

Presets:

| Intent | MASK_RADIUS | SHARPNESS | BLACK | WHITE |
|--------|-------------|-----------|-------|-------|
| Clean thin lines (default) | 5.0 | 0.8 | 0.1 | 0.1 |
| Bold lines | 10.0 | 0.9 | 0.2 | 0.15 |
| Delicate / fine detail | 3.0 | 0.7 | 0.05 | 0.05 |
| Heavy ink | 15.0 | 1.0 | 0.3 | 0.2 |

Default to **mask_radius=5.0, sharpness=0.8, black=0.1, white=0.1** if unspecified.

### Step 4: Prepare the script

1. Read the bundled script template at `scripts/line_drawing.py` (relative to this SKILL.md)
2. Replace the config placeholders:
   - `__INPUT_PATH__` → absolute path to the input image
   - `__OUTPUT_PATH__` → output path (default: append `_lineart` before extension)
   - `__MASK_RADIUS__` → float
   - `__SHARPNESS__` → float
   - `__BLACK__` → float
   - `__WHITE__` → float
3. Write the modified script to `/tmp/imganary_line_drawing.py`

### Step 5: Run GIMP batch

**macOS:**
```bash
LSBackgroundOnly=1 /Applications/GIMP.app/Contents/MacOS/gimp-console \
  -n -i --no-data --quit \
  --gimprc="$HOME/Library/Application Support/GIMP/3.0/batch-gimprc" \
  --batch-interpreter=python-fu-eval \
  -b "exec(open('/tmp/imganary_line_drawing.py').read())" 2>&1
```

**Linux:**
```bash
gimp -n -i --no-data --batch-interpreter=python-fu-eval \
  -b "exec(open('/tmp/imganary_line_drawing.py').read())" \
  -b '(gimp-quit 0)' 2>&1
```

### Step 6: Present the result

Tell the user the output file path and the values applied.
