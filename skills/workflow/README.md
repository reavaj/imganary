# Workflow Skills

Pipeline orchestration composing analysis and generation into end-to-end workflows.

## Pipelines

### imagine.py — Vibe → Image

1. User provides a short "vibe" prompt (e.g., "dystopian corridor")
2. Vibe is classified against the 124-style library via Gemini
3. If no matching style exists, auto-research creates one (web search + optional LLaVA analysis)
4. Gemini expands the vibe into a FLUX-optimized prompt using matched style definitions
5. FLUX.1 generates the image (Schnell for speed, Dev for quality)

Detailed prompts (3+ sentences) bypass expansion and are sent directly to FLUX.

### Analyze → Edit

1. Vision model examines the image and returns scene context
2. Claude uses the context to select and parameterize GIMP skills
3. GIMP batch mode applies the transformations

## Entry Points

- `./imagine.py` — Vibe-to-image pipeline
- `./generate.py` — Direct prompt-to-image (no expansion)
- `./analyze.py` — Image analysis only
- `./imganary.py` — Chat agent interface (Claude-driven)
