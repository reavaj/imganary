---
name: posterize
description: >-
  Reduce image colors to a limited number of levels via GIMP Python-Fu batch
  automation. Creates a flat, graphic poster-like effect. Trigger on:
  "posterize", "poster effect", "reduce colors", "flat colors",
  "graphic look", "pop art colors".
user-invocable: true
compatibility: |
  Requires GIMP 3.x with Python-Fu support enabled.
---

# Posterize

Reduce an image to a limited number of color levels per channel.

## Instructions

### Step 1: Check GIMP is installed

```bash
gimp --version
```

### Step 2: Get the image path

Ask the user for the image path if not already provided.

### Step 3: Determine number of levels

| Levels | Effect |
|--------|--------|
| **2** | Extreme — almost silhouette |
| **3** | Strong poster effect |
| **4** | Classic pop art look |
| **6** | Moderate reduction |
| **8** | Subtle, still noticeable |

Default to **4** if the user says "posterize" without specifics.

### Step 4: Prepare the script

1. Read the bundled script template at `scripts/posterize.py` (relative to this SKILL.md)
2. Replace the config placeholders:
   - `__INPUT_PATH__` → absolute path to the input image
   - `__OUTPUT_PATH__` → output path (default: append `_posterized` before extension)
   - `__LEVELS__` → integer, 2-256
3. Write the modified script to `/tmp/imganary_posterize.py`

### Step 5: Run GIMP batch

**macOS:**
```bash
LSBackgroundOnly=1 /Applications/GIMP.app/Contents/MacOS/gimp-console \
  -n -i --no-data --quit \
  --gimprc="$HOME/Library/Application Support/GIMP/3.0/batch-gimprc" \
  --batch-interpreter=python-fu-eval \
  -b "exec(open('/tmp/imganary_posterize.py').read())" 2>&1
```

**Linux:**
```bash
gimp -n -i --no-data --batch-interpreter=python-fu-eval \
  -b "exec(open('/tmp/imganary_posterize.py').read())" \
  -b '(gimp-quit 0)' 2>&1
```

### Step 6: Present the result

Tell the user the output file path and how many levels were used.
