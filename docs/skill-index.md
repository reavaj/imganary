# Skill Index

Claude Code skills for GIMP batch automation. Each skill reads an image, generates a Python-Fu script with injected parameters, and runs it through GIMP in headless batch mode.

## Available Skills

| Skill | Category | Description |
|-------|----------|-------------|
| brightness-contrast | Color | Adjust image brightness and contrast (-1.0 to 1.0) |
| color-balance | Color | Shift color balance in shadows, midtones, and highlights |
| color-harmonize | Color | Recolor using harmonious palettes (tetradic, complementary, analogous, split-complementary) |
| desaturate | Color | Convert to grayscale with multiple desaturation modes |
| duotone | Color | Two-tone color effect mapping shadows and highlights to chosen colors |
| posterize | Color | Reduce colors to a limited number of levels (2-256) |
| cartoon | Effects | Cartoon/comic effect via GEGL filter (edge tracing + flat shading) |
| vignette | Effects | Darkened edges effect via GEGL filter |
| pixelize | Effects | Pixelation/mosaic effect via GEGL filter |
| line-drawing | Effects | Convert photo to clean line drawing via GEGL photocopy filter |
| text-overlay | Text | Add text layers with configurable size, color, and position |

## Skill Architecture

All skills follow the same pattern:

1. Read a Python-Fu template script from the skill directory
2. Inject user-specified parameters via `__PLACEHOLDER__` substitution
3. Write the configured script to `/tmp/`
4. Execute via GIMP batch mode (`gimp-console` with `--quit`)

See [gimp-batch-mode.md](gimp-batch-mode.md) for the macOS batch mode setup these skills depend on.

## Adding New Skills

1. Create a skill directory under `.claude/skills/`
2. Add a `SKILL.md` with trigger phrases and the skill prompt
3. Include a Python-Fu template script with `__PLACEHOLDER__` tokens for configurable parameters
4. Follow the GIMP 3.x API conventions documented in [gimp-batch-mode.md](gimp-batch-mode.md)
