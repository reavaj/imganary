---
name: duotone
description: >-
  Apply a duotone color effect to images via GIMP Python-Fu batch automation.
  Desaturates the image and maps shadows and highlights to two chosen colors
  using per-channel curves. Trigger on: "duotone", "two-tone", "duo tone",
  "tint shadows and highlights", or any request combining two colors with
  toning/grading.
user-invocable: true
compatibility: |
  Requires GIMP 3.x with Python-Fu support enabled.
  macOS: brew install --cask gimp (or download from gimp.org)
---

# Duotone

Apply a two-color duotone effect: shadows take one color, highlights take another.

## Instructions

### Step 1: Check GIMP is installed

```bash
gimp --version
```

### Step 2: Get the image path

Ask the user for the image path if not already provided.

### Step 3: Determine the duotone colors

Ask the user for shadow and highlight colors. Common presets:

| Preset | Shadows (R,G,B) | Highlights (R,G,B) |
|--------|-----------------|-------------------|
| **Navy & Cream** | 20, 30, 80 | 240, 210, 160 |
| **Midnight & Gold** | 15, 15, 40 | 255, 200, 50 |
| **Forest & Amber** | 10, 40, 20 | 230, 180, 60 |
| **Burgundy & Peach** | 60, 10, 20 | 255, 200, 170 |
| **Slate & Ice** | 40, 50, 60 | 200, 220, 240 |
| **Sepia** | 40, 25, 10 | 230, 190, 140 |

The user can also specify custom RGB values or color names (convert to approximate RGB).

Default to **Navy & Cream** if the user says "just pick one".

### Step 4: Prepare the script

1. Read the bundled script template at `scripts/duotone.py` (relative to this SKILL.md)
2. Replace the config placeholders:
   - `__INPUT_PATH__` → absolute path to the input image
   - `__OUTPUT_PATH__` → output path (default: append `_duotone` before extension)
   - `__SHADOW_R__`, `__SHADOW_G__`, `__SHADOW_B__` → shadow color RGB (0-255)
   - `__HIGHLIGHT_R__`, `__HIGHLIGHT_G__`, `__HIGHLIGHT_B__` → highlight color RGB (0-255)
3. Write the modified script to `/tmp/imganary_duotone.py`

### Step 5: Run GIMP batch

**macOS:**
```bash
LSBackgroundOnly=1 /Applications/GIMP.app/Contents/MacOS/gimp-console \
  -n -i --no-data --quit \
  --gimprc="$HOME/Library/Application Support/GIMP/3.0/batch-gimprc" \
  --batch-interpreter=python-fu-eval \
  -b "exec(open('/tmp/imganary_duotone.py').read())" 2>&1
```

**Linux:**
```bash
gimp -n -i --no-data --batch-interpreter=python-fu-eval \
  -b "exec(open('/tmp/imganary_duotone.py').read())" \
  -b '(gimp-quit 0)' 2>&1
```

### Step 6: Present the result

Tell the user the output file path, the shadow and highlight colors used, and suggest they open the file to compare.
