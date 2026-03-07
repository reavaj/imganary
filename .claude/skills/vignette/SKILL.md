---
name: vignette
description: >-
  Add a vignette (darkened edges) effect to images via GIMP GEGL filter batch
  automation. Trigger on: "vignette", "darken edges", "dark corners",
  "vignetting", "add vignette", "photo vignette".
user-invocable: true
compatibility: |
  Requires GIMP 3.x with Python-Fu support enabled.
---

# Vignette

Darken the edges of an image for a classic vignette effect.

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
| **softness** | 0.0–1.0 | 0.8 | Edge transition softness |
| **radius** | 0.5–3.0 | 1.2 | Vignette size. Lower = more darkening |

Presets:

| Preset | softness | radius | Look |
|--------|----------|--------|------|
| **Subtle** | 0.9 | 1.5 | Barely noticeable |
| **Classic** | 0.8 | 1.2 | Standard photo vignette |
| **Strong** | 0.6 | 0.9 | Heavy darkening |
| **Spotlight** | 0.4 | 0.7 | Dramatic center focus |

Default to **Classic** if the user doesn't specify.

### Step 4: Prepare the script

1. Read the bundled script template at `scripts/vignette.py` (relative to this SKILL.md)
2. Replace the config placeholders:
   - `__INPUT_PATH__` → absolute path to the input image
   - `__OUTPUT_PATH__` → output path (default: append `_vignette` before extension)
   - `__SOFTNESS__` → float, 0.0-1.0
   - `__RADIUS__` → float, 0.5-3.0
3. Write the modified script to `/tmp/imganary_vignette.py`

### Step 5: Run GIMP batch

**macOS:**
```bash
LSBackgroundOnly=1 /Applications/GIMP.app/Contents/MacOS/gimp-console \
  -n -i --no-data --quit \
  --gimprc="$HOME/Library/Application Support/GIMP/3.0/batch-gimprc" \
  --batch-interpreter=python-fu-eval \
  -b "exec(open('/tmp/imganary_vignette.py').read())" 2>&1
```

**Linux:**
```bash
gimp -n -i --no-data --batch-interpreter=python-fu-eval \
  -b "exec(open('/tmp/imganary_vignette.py').read())" \
  -b '(gimp-quit 0)' 2>&1
```

### Step 6: Present the result

Tell the user the output file path and settings used.
