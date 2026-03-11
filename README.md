# Imganary — AI-Driven Image Generation & GIMP Automation

A framework that combines FLUX.1 image generation, a curated visual style library, and GIMP batch automation for AI-driven creative workflows. Claude Code skills handle everything from prompt expansion to post-processing effects.

## What It Does

1. **Generate** — Direct FLUX prompt-to-image (`generate.py`). No expansion, no styles, no grading — bare-metal manual control for when you know exactly what you want.
2. **Imagine** — Describe a vibe and let Gemini expand it into a production-ready FLUX prompt (`imagine.py`). Classifies against a 124-style visual library, supports LoRA loading, CFG guidance, and optional GIMP post-grading.
3. **Analyze** — Run local vision models (LLaVA, YOLO, CLIP) to understand image content.
4. **Edit** — Apply GIMP effects via Claude Code skills (color grading, filters, text overlay).

## Quick Start

```bash
# Set up Python environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Copy env template and add your API keys
cp .env.example .env
```

## Generation

### generate.py — Direct Prompt

Sends your prompt straight to FLUX with no processing. Use this when you want full control over the exact prompt text.

```bash
# Basic generation (schnell, fast)
./generate.py "a rabbit in a field of wildflowers" --model schnell

# Higher quality with dev model
./generate.py "a rabbit in a field of wildflowers" --model dev --steps 30

# Custom seed for reproducibility
./generate.py "a rabbit in a field of wildflowers" --seed 42 --output ~/Desktop/rabbit.png
```

### imagine.py — Vibe-to-Image Pipeline

The full creative pipeline: classifies your vibe against the style library, expands it via Gemini into FLUX-optimized language, generates the image, and optionally applies GIMP post-grading.

```bash
# Vibe mode — short prompt gets expanded via Gemini + style library
./imagine.py "melancholic rain"

# HD output (1024x1024)
./imagine.py "ethereal forest" --model dev --hd

# Portrait aspect ratio (768x1152) for full-body shots
./imagine.py "street fashion" --model dev --portrait

# LoRA weights (HuggingFace repo ID, auto-downloaded and cached)
./imagine.py "tired nurse" --model dev --lora XLabs-AI/flux-RealismLora

# Lower CFG guidance for less saturated output (dev only, default 3.5)
./imagine.py "person at a cafe" --model dev --guidance 2.5

# Post-processing with GIMP grading presets
./imagine.py "golden hour portrait" --model dev --grade natural
./imagine.py "street scene" --model dev --grade film

# Shorthand for --grade natural
./imagine.py "beach sunset" --model dev --natural

# Image-to-image with reference
./imagine.py "oil painting version" --image ~/Desktop/photo.jpg --strength 0.6

# Detailed prompts (3+ sentences) are used verbatim — no Gemini rewrite
./imagine.py "A lone figure stands beneath a flickering fluorescent light..."

# Raw mode — no expansion at all
./imagine.py "rabbit sitting in grass" --raw
```

### generate.py vs imagine.py

| | `generate.py` | `imagine.py` |
|---|---|---|
| **Purpose** | Manual control | Creative pipeline |
| **Prompt** | Used verbatim | Expanded via Gemini + style library |
| **Styles** | None | Auto-classified from 124-style library |
| **LoRA** | No | `--lora` flag |
| **Guidance** | No | `--guidance` flag (dev only) |
| **Grading** | No | `--grade` / `--natural` flags |
| **Best for** | Testing exact prompts, debugging | Creative exploration, production images |

## Models

| Model | Type | Steps | Speed | Quality | Use Case |
|-------|------|-------|-------|---------|----------|
| FLUX.1-schnell | Generation | 4 | ~10s | Good | Rapid iteration, concept exploration |
| FLUX.1-dev | Generation | 25 | ~45-90s | High | Final renders, production quality |
| LLaVA | Vision | — | ~5s* | — | Scene description, visual Q&A |
| YOLO | Vision | — | <1s | — | Object detection, bounding boxes |
| CLIP | Vision | — | <1s | — | Image-text similarity, classification |

*First load ~160s, subsequent runs ~5s

## LoRA Support

LoRA weights bias FLUX output in specific directions without modifying the base model.

### Browse & Download (CivitAI)

Search CivitAI's library of FLUX-compatible LoRAs, view details, and download directly:

```bash
# Search for realism LoRAs
./loras.py search realism

# Browse top FLUX.1 Dev LoRAs
./loras.py search "" --limit 20

# Search across all base models
./loras.py search "film grain" --all

# View model details (shows versions, trigger words, download counts)
./loras.py info 631986

# Download a specific version to loras/
./loras.py download 706528

# List all locally available LoRAs (local + HuggingFace cached)
./loras.py list
```

Downloaded LoRAs are saved to `loras/` with a JSON metadata sidecar containing trigger words and source info.

### Using LoRAs

```bash
# HuggingFace repo ID (auto-downloaded and cached)
./imagine.py "street portrait" --model dev --lora XLabs-AI/flux-RealismLora

# Local file from CivitAI download
./imagine.py "street portrait" --model dev --lora loras/xlabs-flux-realism-lora.safetensors

# Anime cel style
./imagine.py "warrior in forest" --model dev --lora alvdansen/flux-koda

# Multiple LoRAs (comma-separated)
./imagine.py "scene" --model dev --lora XLabs-AI/flux-RealismLora,alvdansen/flux-koda
```

HuggingFace LoRAs are cached at `~/Library/Caches/mflux/loras/`. CivitAI downloads go to `loras/`.

## Grading Pipeline

Optional GIMP-based post-processing that reduces AI oversaturation and adds film-like qualities. Only runs when explicitly requested via `--grade` or `--natural`.

| Preset | What it does |
|--------|-------------|
| `minimal` | Targeted desaturation of reds/yellows (fixes AI skin tones) |
| `natural` | + lift blacks (film fade) + warm color temperature shift |
| `film` | + film grain + vignette + edge softening |

```bash
./imagine.py "portrait" --model dev --grade minimal
./imagine.py "portrait" --model dev --grade natural
./imagine.py "portrait" --model dev --grade film
```

## Style Library

140 style definitions across 16 categories, used by the prompt expansion pipeline:

| Category | Count | Examples |
|----------|-------|---------|
| **Styles** | | |
| photography/ | 16 | film-noir, editorial-fashion, food, rain-wet, golden-hour, portrait, macro, interior-design, infrared, signage-typography, abandoned-decay, underwater, period-1950s, period-1970s |
| illustration/ | 5 | anime-cel, ukiyo-e, vintage-poster |
| fine-art/ | 3 | oil-painting, watercolor, pop-art |
| design/ | 4 | psychedelic, steampunk, swiss-modernist |
| digital/ | 4 | cyberpunk, dystopian, vaporwave |
| architecture/ | 3 | brutalist, art-deco, metabolist |
| **Adjectives** | | |
| lighting/ | 12 | chiaroscuro, volumetric, candlelit, fluorescent |
| color/ | 12 | saturated, neon, jewel-toned, oxidized |
| texture/ | 15 | grainy, impasto, corroded, translucent, glass-transparency, fabric-textile, metal-patina |
| mood/ | 14 | ethereal, ominous, whimsical, hallucinatory |
| composition/ | 10 | symmetrical, panoramic, fragmented, towering |
| rendering/ | 12 | painterly, cel-shaded, solarized, cross-hatched |
| form/ | 8 | angular, organic, monolithic, skeletal |
| scale/ | 8 | intricate, hyper-detailed, vast, ornate |
| optical/ | 7 | anamorphic, shallow-focus, telephoto, tilt-shift |
| time-motion/ | 6 | frozen, blurred, ephemeral, decayed |

Each style file contains Visual DNA (key characteristics, reference points, pairings) and FLUX keywords for prompt injection. When a vibe doesn't match existing styles, the system auto-researches and creates a new style definition.

## GIMP Skills

Claude Code skills for batch image processing via GIMP 3.x:

- **Color**: brightness-contrast, color-balance, color-harmonize, desaturate, duotone, posterize
- **Effects**: vignette
- **Text**: text-overlay

## Repository Structure

```
imganary/
├── generate.py          # Direct FLUX prompt → image (manual control)
├── imagine.py           # Vibe → expand → generate → grade pipeline
├── analyze.py           # Vision model analysis (LLaVA/YOLO/CLIP)
├── grade.py             # GIMP grading pipeline (minimal/natural/film presets)
├── loras.py             # CivitAI LoRA browser, search, and downloader
├── loras/               # Downloaded LoRA weights + metadata (gitignored)
├── generators/          # FLUX generator (ABC, factory, config, LoRA support)
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
- mflux for FLUX.1 generation (MLX, Apple Silicon optimized)
- Google Gemini API for prompt expansion
- Ollama for LLaVA (optional — only needed for `analyze.py`)
- GIMP 3.0+ (optional — only needed for `--grade`/`--natural` and Claude Code skills)

### Installing GIMP (optional)

GIMP is only required for the grading pipeline and GIMP skills. Generation and analysis work without it.

```bash
# macOS (Homebrew)
brew install --cask gimp

# Linux
sudo apt install gimp   # Debian/Ubuntu
sudo dnf install gimp   # Fedora
```

See [docs/gimp-batch-mode.md](docs/gimp-batch-mode.md) for macOS headless batch mode setup.

## License

MIT
