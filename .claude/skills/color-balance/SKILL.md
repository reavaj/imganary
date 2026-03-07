---
name: color-balance
description: >-
  Shift color balance in shadows, midtones, and highlights via GIMP Python-Fu
  batch automation. Trigger on: "warm up", "cool down", "color balance",
  "warmer shadows", "cooler highlights", "add warmth", "color shift",
  "golden hour", "blue shadows".
user-invocable: true
compatibility: |
  Requires GIMP 3.x with Python-Fu support enabled.
---

# Color Balance

Shift colors in shadows, midtones, and highlights independently.

## Instructions

### Step 1: Check GIMP is installed

```bash
gimp --version
```

### Step 2: Get the image path

Ask the user for the image path if not already provided.

### Step 3: Determine color balance values

Three axes per tonal range, each from **-100 to 100** (0 = no change):
- **Cyan ↔ Red**
- **Magenta ↔ Green**
- **Yellow ↔ Blue**

Common presets:

| Preset | Shadows (CR,MG,YB) | Midtones (CR,MG,YB) | Highlights (CR,MG,YB) |
|--------|--------------------|--------------------|----------------------|
| **Warm** | 10, 0, -15 | 15, 0, -10 | 5, 0, -5 |
| **Cool** | -10, 0, 15 | -10, 0, 10 | -5, 0, 10 |
| **Golden hour** | 15, -5, -20 | 20, 0, -15 | 10, 5, -5 |
| **Blue shadows** | -15, 0, 20 | 0, 0, 0 | 10, 0, -10 |
| **Teal & orange** | -20, 5, 15 | 15, -5, -10 | 20, 0, -15 |

Default to **Warm** if the user just says "warm it up".

### Step 4: Prepare the script

1. Read the bundled script template at `scripts/color_balance.py` (relative to this SKILL.md)
2. Replace all config placeholders:
   - `__INPUT_PATH__`, `__OUTPUT_PATH__`
   - `__SHADOW_CYAN_RED__`, `__SHADOW_MAGENTA_GREEN__`, `__SHADOW_YELLOW_BLUE__`
   - `__MID_CYAN_RED__`, `__MID_MAGENTA_GREEN__`, `__MID_YELLOW_BLUE__`
   - `__HIGH_CYAN_RED__`, `__HIGH_MAGENTA_GREEN__`, `__HIGH_YELLOW_BLUE__`
3. Write the modified script to `/tmp/imganary_color_balance.py`

### Step 5: Run GIMP batch

**macOS:**
```bash
LSBackgroundOnly=1 /Applications/GIMP.app/Contents/MacOS/gimp-console \
  -n -i --no-data --quit \
  --gimprc="$HOME/Library/Application Support/GIMP/3.0/batch-gimprc" \
  --batch-interpreter=python-fu-eval \
  -b "exec(open('/tmp/imganary_color_balance.py').read())" 2>&1
```

**Linux:**
```bash
gimp -n -i --no-data --batch-interpreter=python-fu-eval \
  -b "exec(open('/tmp/imganary_color_balance.py').read())" \
  -b '(gimp-quit 0)' 2>&1
```

### Step 6: Present the result

Tell the user the output file path and which tonal ranges were shifted.
