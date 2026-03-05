---
name: color-harmonize
description: >-
  Recolor images using harmonious color palettes via GIMP Python-Fu batch
  automation. Analyzes dominant hue, constructs a 4-color palette using color
  theory (tetradic, complementary, split-complementary, or analogous), and
  remaps the image hue channel while preserving luminance and saturation.
  Trigger on: "recolor this image", "apply color harmony", "harmonize colors",
  "tetradic palette", "complementary colors", "analogous palette",
  "split-complementary", "make colors more balanced", or any request combining
  color theory with an image path.
user-invocable: true
compatibility: |
  Requires GIMP 3.x with Python-Fu support enabled.
  macOS: brew install --cask gimp (or download from gimp.org)
---

# Color Harmonize

Recolor an image using a harmonious color palette derived from its dominant hue.

## Overview

This skill:
1. Analyzes an image's dominant hue via pixel sampling
2. Constructs a harmonious palette using the user's chosen color theory scheme
3. Remaps the image's hue channel in GIMP using Python-Fu batch mode
4. Outputs a new recolored PNG file

## Instructions

### Step 1: Check GIMP is installed

Run this command to verify GIMP is available:

```bash
gimp --version
```

If GIMP is not installed, tell the user:
- **macOS**: `brew install --cask gimp` or download from https://www.gimp.org/downloads/
- **Linux**: `sudo apt install gimp` or `sudo dnf install gimp`
- GIMP 3.x is required (Python 3 support)

### Step 2: Get the image path

Ask the user for the image path if not already provided. The image must be a format GIMP can open (PNG, JPEG, TIFF, BMP, etc.). GIMP `.xcf` files also work.

### Step 3: Determine the harmony scheme

If the user hasn't specified a scheme, ask them to choose one:

| Scheme | Description | Palette |
|--------|-------------|---------|
| **complementary** | Opposite colors on the wheel | H, H+180° |
| **analogous** | Adjacent colors, warm/cool feel | H-30°, H, H+30°, H+60° |
| **split-complementary** | Softer contrast than complementary | H, H+150°, H+210° |
| **tetradic** | Four evenly spaced colors, vibrant | H, H+90°, H+180°, H+270° |

Default to **complementary** if the user says "just pick one" or doesn't have a preference.

### Step 4: Prepare the script

1. Read the bundled script template at `scripts/harmonize.py` (relative to this SKILL.md)
2. Replace the config placeholders:
   - `__INPUT_PATH__` → absolute path to the input image
   - `__OUTPUT_PATH__` → output path (default: append `_harmonized` before the extension, e.g. `photo.jpg` → `photo_harmonized.png`)
   - `__HARMONY_SCHEME__` → the chosen scheme name (lowercase, e.g. `complementary`)
3. Write the modified script to `/tmp/imganary_harmonize.py`

### Step 5: Run GIMP batch

**macOS** — Use `gimp-console` with `--no-data` and the batch gimprc to avoid plugin initialization hangs:

```bash
timeout 120 /Applications/GIMP.app/Contents/MacOS/gimp-console -n -i --no-data \
  --gimprc="$HOME/Library/Application Support/GIMP/3.0/batch-gimprc" \
  --batch-interpreter=python-fu-eval \
  -b "exec(open('/tmp/imganary_harmonize.py').read())" 2>&1
```

**Linux** — Standard GIMP batch mode works:

```bash
gimp -n -i --batch-interpreter=python-fu-eval \
  -b "exec(open('/tmp/imganary_harmonize.py').read())" \
  -b '(gimp-quit 0)' 2>&1
```

The script will print progress to stdout:
- `Dominant hue: 35 degrees`
- `Harmony scheme: complementary`
- `Palette hues: ['35', '215']`
- Per-range hue shifts applied
- `Output saved to: /path/to/output.png`

**macOS Setup Note**: The batch gimprc and filtered plugin directory must exist. If missing, create them:
1. Create `~/Library/Application Support/GIMP/3.0/batch-plug-ins/` with symlinks to all system plugins EXCEPT `file-rawtherapee` (which hangs during init on macOS)
2. Create `~/Library/Application Support/GIMP/3.0/batch-gimprc` containing: `(plug-in-path "${gimp_dir}/plug-ins:${gimp_dir}/batch-plug-ins")`

### Step 6: Present the result

Tell the user:
- The output file path
- The dominant hue that was detected
- The palette that was applied
- Suggest they open the file to compare with the original

If the command fails, check:
- Is the image path correct and accessible?
- Is GIMP 3.x installed (not 2.x)?
- Does the output directory exist and is it writable?

## GIMP Batch Mode Reference

**macOS — gimp-console (recommended):**
```bash
/Applications/GIMP.app/Contents/MacOS/gimp-console -n -i --no-data \
  --gimprc="$HOME/Library/Application Support/GIMP/3.0/batch-gimprc" \
  --batch-interpreter=python-fu-eval \
  -b "exec(open('/path/to/script.py').read())"
```
The script should call `Gimp.quit(0)` at the end to exit cleanly.

**Linux — standard gimp:**
```bash
gimp -n -i --batch-interpreter=python-fu-eval \
  -b "exec(open('/path/to/script.py').read())" \
  -b '(gimp-quit 0)'
```

Flags:
- `-n` — Start a new GIMP instance
- `-i` — No user interface (headless)
- `--no-data` — Skip loading brushes, gradients, patterns (faster startup)
- `--gimprc=...` — Use custom config (macOS: excludes problematic plugins)
- `--batch-interpreter=python-fu-eval` — Use Python-Fu instead of Script-Fu
- `-b '...'` — Batch command to execute

GIMP 3.x API notes:
- Python 3 only. Use `exec(open(...).read())` not `execfile()`
- `image.get_layers()[0]` instead of `image.get_active_drawable()`
- `drawable.hue_saturation(range, hue, light, sat, overlap)` — method on drawable
- `drawable.get_pixel(x, y)` returns `Gegl.Color`; use `.get_rgba()` for components
- `Gimp.file_save(RunMode.NONINTERACTIVE, image, gio_file)` — 3 args

## Output

A recolored PNG image saved alongside the original with `_harmonized` suffix. The image preserves the original's luminance and saturation relationships while shifting all hues to align with the chosen harmonic palette.
