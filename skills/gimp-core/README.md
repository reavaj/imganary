# GIMP Core Skills

Claude Code skills for GIMP 3.x batch image processing. Each skill generates a Python-Fu script, injects user parameters, and runs it through GIMP in headless batch mode.

## Available Skills

### Color
- **brightness-contrast** — Adjust brightness and contrast (-1.0 to 1.0)
- **color-balance** — Shift color balance in shadows, midtones, and highlights
- **color-harmonize** — Recolor using harmonious palettes (tetradic, complementary, analogous, split-complementary)
- **desaturate** — Convert to grayscale with multiple desaturation modes
- **duotone** — Two-tone effect mapping shadows and highlights to chosen colors
- **posterize** — Reduce colors to a limited number of levels (2-256)

### Effects
- **cartoon** — Cartoon/comic effect via `gegl:cartoon`
- **vignette** — Darkened edges via `gegl:vignette`
- **pixelize** — Pixelation/mosaic via `gegl:pixelize`
- **line-drawing** — Clean line art via `gegl:photocopy`

### Text
- **text-overlay** — Add text layers with configurable size, color, and position

## Architecture

All skills follow the template pattern:
1. Read Python-Fu template from the skill directory
2. Replace `__PLACEHOLDER__` tokens with user parameters
3. Write configured script to `/tmp/`
4. Execute via `gimp-console` batch mode with `--quit`

See `docs/gimp-batch-mode.md` for macOS-specific batch mode setup.
