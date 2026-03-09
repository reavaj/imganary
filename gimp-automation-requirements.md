# Imganary — Project Requirements

## Overview

AI-driven image generation and GIMP automation framework. Three core pipelines:

1. **Generate** — Text prompt → FLUX.1 image (Schnell for speed, Dev for quality)
2. **Analyze** — Image → structured scene understanding (LLaVA, YOLO, CLIP)
3. **Edit** — Image → GIMP batch automation via Claude Code skills

## Generation Pipeline

### FLUX.1 Models

| Model | Steps | Speed | Quality | Use Case |
|-------|-------|-------|---------|----------|
| Schnell | 4 | ~10s | Good | Rapid iteration, concept exploration |
| Dev | 25 | ~45-90s | High | Final renders, production quality |

- Runtime: mflux (MLX, Apple Silicon native)
- Quantization: 8-bit
- Output: PNG to `~/Desktop/` by default
- Models cached at `~/.cache/huggingface/hub/`

### Prompt Handling

Three modes via `imagine.py`:

- **Vibe mode** (default): 1-2 sentence prompts are classified against the style library, then expanded by Gemini into FLUX-optimized language
- **Detailed mode** (auto): 3+ sentence prompts are used verbatim — no Gemini rewrite
- **Raw mode** (`--raw`): Bypasses all expansion

### Style Library

124 style definitions across 16 categories under `prompts/styles/`:

**Style categories** (6): photography, illustration, fine-art, design, digital, architecture
**Adjective categories** (10): lighting, color, texture, mood, composition, rendering, form, scale, optical, time-motion

Each style file contains:
- Visual DNA (what it does, key characteristics, reference points, pairings)
- FLUX keywords for prompt injection

Auto-research pipeline (`style_researcher.py`): when a vibe doesn't match existing styles, the system searches for references, optionally analyzes them with LLaVA, and creates a new style definition via Gemini.

## Analysis Pipeline

Three local vision models, all implementing `ImageAnalyzer` ABC:

- **LLaVA** — Scene description via Ollama REST API
- **YOLO** — Object detection (ultralytics)
- **CLIP** — Semantic image-text similarity (transformers)

CLI: `./analyze.py <image> [--model llava|yolo|clip]`

## Editing Pipeline

Claude Code skills automate GIMP 3.x in headless batch mode:

### Skills (11)

**Color**: brightness-contrast, color-balance, color-harmonize, desaturate, duotone, posterize
**Effects**: cartoon, vignette, pixelize, line-drawing
**Text**: text-overlay

### Architecture

- Template pattern: read Python-Fu script → inject `__PLACEHOLDER__` config → write to `/tmp/` → run GIMP batch
- macOS batch mode: `gimp-console` + filtered plugin directory + `--quit` flag
- See `docs/gimp-batch-mode.md` for full macOS setup

## Environment

- Python 3.12 (Apple Silicon ARM native)
- GIMP 3.0.8 (Homebrew cask)
- mflux ≥0.9.0 (MLX, Apple Silicon optimized)
- Ollama (LLaVA)
- Google Gemini API (prompt expansion)
- pydantic-settings for all configuration
