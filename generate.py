#!/usr/bin/env python3
"""Generate an image from a text prompt using FLUX.1."""

import logging
import os
import random
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

# Pre-create logger at WARNING before generators package initializes with handlers
logging.getLogger("imganary.flux").setLevel(logging.WARNING)

from generators import GeneratorType, create_generator
from generators.config import GeneratorSettings


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: ./generate.py <prompt> "
            "[--model dev|schnell] [--steps N] [--seed N] "
            "[--width N] [--height N] [--output path.png]"
        )
        sys.exit(1)

    prompt = sys.argv[1]

    # Parse optional flags
    def _flag(name: str, default=None):
        if name in sys.argv:
            idx = sys.argv.index(name)
            if idx + 1 < len(sys.argv):
                return sys.argv[idx + 1]
        return default

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

    # Resolve seed early so it can be included in the filename
    if seed is None:
        seed = random.randint(0, 2**32 - 1)
    else:
        seed = int(seed)

    # Default output path
    if not output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = str(Path(f"~/Desktop/flux_{timestamp}_s{seed}.png").expanduser())

    settings = GeneratorSettings()
    generator = create_generator(gen_type, settings)

    print(f"Model:  FLUX.1-{model}")
    print(f"Prompt: {prompt}")
    print()

    result = generator.generate(
        prompt=prompt,
        output_path=output,
        width=int(width),
        height=int(height),
        steps=int(steps) if steps else None,
        seed=seed,
    )

    if result.error:
        print(f"Error: {result.error}")
        sys.exit(1)

    print(f"Generated {result.width}x{result.height} in {result.processing_time_ms:.0f}ms")
    print(f"Seed:     {result.seed}")
    print(f"Saved to: {result.output_path}")


if __name__ == "__main__":
    main()
