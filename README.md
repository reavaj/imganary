# Imganary — AI-Driven Image Generation & GIMP Automation

A framework that combines FLUX.1 image generation, a curated visual style library, and GIMP batch automation for AI-driven creative workflows. Claude Code skills handle everything from prompt expansion to post-processing effects.

## What It Does

1. **Generate** — Create images from text prompts using FLUX.1 (Schnell for speed, Dev for quality)
2. **Imagine** — Describe a vibe and let Gemini expand it into a production-ready FLUX prompt, drawing from a 124-style visual library
3. **Analyze** — Run local vision models (LLaVA, YOLO, CLIP) to understand image content
4. **Edit** — Apply GIMP effects via Claude Code skills (color grading, filters, text overlay, and more)

## Quick Start

```bash
# Set up Python environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Copy env template and add your API keys
cp .env.example .env

# Generate an image from a direct prompt
./generate.py "a rabbit in a field of wildflowers" --model schnell

# Generate from a vibe (auto-expanded via Gemini + style library)
./imagine.py "dystopian corridor"

# Higher quality with FLUX.1-dev (25 inference steps)
./imagine.py "cyberpunk alleyway" --model dev

# HD output (1024x1024)
./imagine.py "ethereal forest" --model dev --hd

# Analyze an image
./analyze.py ~/Desktop/photo.jpg --model llava
```

## Models

| Model | Type | Steps | Speed | Quality | Use Case |
|-------|------|-------|-------|---------|----------|
| FLUX.1-schnell | Generation | 4 | ~10s | Good | Rapid iteration, concept exploration |
| FLUX.1-dev | Generation | 25 | ~45-90s | High | Final renders, production quality |
| LLaVA | Vision | — | ~5s* | — | Scene description, visual Q&A |
| YOLO | Vision | — | <1s | — | Object detection, bounding boxes |
| CLIP | Vision | — | <1s | — | Image-text similarity, classification |

*First load ~160s, subsequent runs ~5s

## Prompt Handling

The `imagine.py` pipeline has three modes:

- **Vibe mode** (default): Short prompts (1-2 sentences) are classified against the style library, then expanded by Gemini into FLUX-optimized language
- **Detailed mode** (auto): Prompts with 3+ sentences are used verbatim — no Gemini rewrite, no risk of overriding deliberate creative choices
- **Raw mode** (`--raw`): Bypasses all expansion, sends the prompt directly to FLUX

```bash
# Vibe — gets expanded
./imagine.py "melancholic rain"

# Detailed — used verbatim (3+ sentences detected)
./imagine.py "A lone figure stands beneath a flickering fluorescent light in an abandoned hospital corridor. The walls are stained with water damage and peeling green paint. Shot on 35mm film with heavy grain and desaturated color."

# Raw — no processing at all
./imagine.py "rabbit sitting in grass" --raw
```

## Style Library

124 style definitions across 16 categories, used by the prompt expansion pipeline:

| Category | Count | Examples |
|----------|-------|---------|
| **Styles** | | |
| photography/ | 4 | film-noir, editorial-fashion, street-documentary |
| illustration/ | 5 | anime-cel, ukiyo-e, vintage-poster |
| fine-art/ | 3 | oil-painting, watercolor, pop-art |
| design/ | 4 | psychedelic, steampunk, swiss-modernist |
| digital/ | 4 | cyberpunk, dystopian, vaporwave |
| architecture/ | 3 | brutalist, art-deco, metabolist |
| **Adjectives** | | |
| lighting/ | 12 | chiaroscuro, volumetric, candlelit, fluorescent |
| color/ | 12 | saturated, neon, jewel-toned, oxidized |
| texture/ | 12 | grainy, impasto, corroded, translucent |
| mood/ | 14 | ethereal, ominous, whimsical, hallucinatory |
| composition/ | 10 | symmetrical, panoramic, fragmented, towering |
| rendering/ | 12 | painterly, cel-shaded, solarized, cross-hatched |
| form/ | 8 | angular, organic, monolithic, skeletal |
| scale/ | 8 | intricate, hyper-detailed, vast, ornate |
| optical/ | 6 | anamorphic, shallow-focus, telephoto |
| time-motion/ | 6 | frozen, blurred, ephemeral, decayed |

Each style file contains Visual DNA (what it does, key characteristics, reference points, pairings) and FLUX keywords for prompt injection.

## GIMP Skills

Claude Code skills for batch image processing via GIMP 3.x:

- **Color**: brightness-contrast, color-balance, color-harmonize, desaturate, duotone, posterize
- **Effects**: cartoon, vignette, pixelize
- **Text**: text-overlay
- **Conversion**: line-drawing

## Repository Structure

```
imganary/
├── generate.py          # Direct FLUX prompt → image
├── imagine.py           # Vibe → expand → generate pipeline
├── analyze.py           # Vision model analysis (LLaVA/YOLO/CLIP)
├── imganary.py          # Chat agent interface
├── generators/          # FLUX generator (ABC, factory, config)
├── models/              # Vision model wrappers
├── prompts/
│   ├── expand.md        # Gemini system prompt for vibe expansion
│   ├── style_researcher.py  # Auto-research pipeline for new styles
│   └── styles/          # 124 style definitions (16 categories)
├── chat/                # Chat agent tools and scaffolding
├── .claude/skills/      # GIMP automation skill definitions
└── docs/                # Setup guides, GIMP batch mode notes
```

## Environment

- Python 3.12 (Apple Silicon native)
- GIMP 3.0.8 (Homebrew cask)
- mflux for FLUX.1 generation (MLX, Apple Silicon optimized)
- Ollama for LLaVA
- Google Gemini API for prompt expansion

## License

MIT
