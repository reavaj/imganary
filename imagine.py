#!/usr/bin/env python3
"""Generate an image from a vibe prompt — expands via Gemini, then renders via FLUX."""

import logging
import os
import sys
import warnings
from datetime import datetime
from pathlib import Path

# Suppress noisy library warnings before any imports
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_DISABLE_EXPERIMENTAL_WARNING"] = "1"
os.environ["DO_NOT_TRACK"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings("ignore")
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("imganary.flux").setLevel(logging.WARNING)

from google import genai

from generators import GeneratorType, create_generator
from generators.config import GeneratorSettings
from prompts.style_researcher import classify_vibe, research_and_create_style

PROMPTS_DIR = Path(__file__).parent / "prompts"
EXPAND_PROMPT_PATH = PROMPTS_DIR / "expand.md"
STYLES_DIR = PROMPTS_DIR / "styles"


def style_index() -> str:
    """Return a compact list of style names for classification."""
    return ", ".join(
        f"{md.parent.name}/{md.stem}" for md in sorted(STYLES_DIR.rglob("*.md"))
    )


def load_styles(names: list[str]) -> str:
    """Load specific style definitions by 'category/name' keys."""
    # Build lookup: "category/stem" → path
    lookup = {
        f"{md.parent.name}/{md.stem}": md
        for md in STYLES_DIR.rglob("*.md")
    }
    sections = []
    for name in names:
        path = lookup.get(name)
        if path:
            sections.append(f"[{name}]\n{path.read_text().strip()}")
    return "\n\n---\n\n".join(sections)


def classify_and_resolve(vibe: str, settings: GeneratorSettings) -> list[str]:
    """Classify the vibe, auto-research if needed, return matched style names."""
    api_key = settings.ai_api_key or os.environ.get("AI_API_KEY", "")
    if not api_key:
        return []

    try:
        classification = classify_vibe(vibe, style_index(), settings)
    except Exception:
        return []

    matched = classification.get("matched_styles", [])

    if not classification.get("match", True):
        concept = classification.get("concept", "unknown")
        print(f"New style detected: {concept}")
        try:
            new_path = research_and_create_style(vibe, classification, settings)
            if new_path:
                # Add the newly created style to the matched list
                matched.append(f"{classification['category']}/{new_path.stem}")
            print()
        except Exception as e:
            print(f"Warning: Style research failed ({e}), continuing with existing styles.")

    return matched


def expand_prompt(vibe: str, settings: GeneratorSettings) -> str:
    """Expand a short vibe prompt into FLUX-optimized language via Gemini."""
    api_key = settings.ai_api_key or os.environ.get("AI_API_KEY", "")
    if not api_key:
        print("Warning: No AI API key found — skipping expansion.")
        print("Set IMGANARY_AI_API_KEY in .env or AI_API_KEY env var.")
        return vibe

    # Classify vibe → get relevant styles (auto-research if needed)
    matched_styles = classify_and_resolve(vibe, settings)

    system_prompt = EXPAND_PROMPT_PATH.read_text()
    if matched_styles:
        style_content = load_styles(matched_styles)
        system_prompt += (
            "\n\n---\n\n"
            "# Matched Style References\n\n"
            "Use these style definitions as your primary visual framework. "
            "Draw on their Visual DNA, textures, lighting, and FLUX keywords "
            "to build your expanded prompt. Blend them if appropriate.\n\n"
            f"{style_content}"
        )

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=vibe,
        config=genai.types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=300,
        ),
    )
    return response.text.strip()


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: ./imagine.py <vibe> "
            "[--model dev|schnell] [--steps N] [--seed N] "
            "[--width N] [--height N] [--output path.png] [--raw] [--hd]"
        )
        sys.exit(1)

    vibe = sys.argv[1]

    # Parse optional flags
    def _flag(name: str, default=None):
        if name in sys.argv:
            idx = sys.argv.index(name)
            if idx + 1 < len(sys.argv):
                return sys.argv[idx + 1]
        return default

    raw = "--raw" in sys.argv
    hd = "--hd" in sys.argv
    model = _flag("--model", "schnell")
    steps = _flag("--steps")
    seed = _flag("--seed")
    default_size = "1024" if hd else "512"
    width = _flag("--width", default_size)
    height = _flag("--height", default_size)
    output = _flag("--output")

    # Resolve generator type
    type_map = {"dev": GeneratorType.FLUX_DEV, "schnell": GeneratorType.FLUX_SCHNELL}
    gen_type = type_map.get(model)
    if gen_type is None:
        print(f"Error: Unknown model '{model}'. Use 'dev' or 'schnell'.")
        sys.exit(1)

    settings = GeneratorSettings()

    # Expand or pass through
    if raw:
        prompt = vibe
        print(f"Prompt: {prompt}")
    else:
        print(f"Vibe:   {vibe}")
        print("Expanding...")
        prompt = expand_prompt(vibe, settings)
        print(f"Prompt: {prompt}")

    print()

    # Default output path
    if not output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = str(Path(f"~/Desktop/flux_{timestamp}.png").expanduser())

    print(f"Model:  FLUX.1-{model}")
    print(f"Output: {output}")
    print()

    generator = create_generator(gen_type, settings)
    result = generator.generate(
        prompt=prompt,
        output_path=output,
        width=int(width),
        height=int(height),
        steps=int(steps) if steps else None,
        seed=int(seed) if seed else None,
    )

    if result.error:
        print(f"Error: {result.error}")
        sys.exit(1)

    print(f"Generated {result.width}x{result.height} in {result.processing_time_ms:.0f}ms")
    if result.seed is not None:
        print(f"Seed:   {result.seed}")
    print(f"Saved to: {result.output_path}")


if __name__ == "__main__":
    main()
