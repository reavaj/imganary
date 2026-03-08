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

EXPAND_PROMPT_PATH = Path(__file__).parent / "prompts" / "expand.md"


def expand_prompt(vibe: str, settings: GeneratorSettings) -> str:
    """Expand a short vibe prompt into FLUX-optimized language via Gemini."""
    api_key = settings.ai_api_key or os.environ.get("AI_API_KEY", "")
    if not api_key:
        print("Warning: No AI API key found — skipping expansion.")
        print("Set IMGANARY_AI_API_KEY in .env or AI_API_KEY env var.")
        return vibe

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=vibe,
        config=genai.types.GenerateContentConfig(
            system_instruction=EXPAND_PROMPT_PATH.read_text(),
            max_output_tokens=300,
        ),
    )
    return response.text.strip()


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: ./imagine.py <vibe> "
            "[--model dev|schnell] [--steps N] [--seed N] "
            "[--width N] [--height N] [--output path.png] [--raw]"
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
    model = _flag("--model", "schnell")
    steps = _flag("--steps")
    seed = _flag("--seed")
    width = _flag("--width", "1024")
    height = _flag("--height", "1024")
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
    print(f"Saved to: {result.output_path}")


if __name__ == "__main__":
    main()
