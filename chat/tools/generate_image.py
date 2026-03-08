"""Chat tool handler for FLUX.1 image generation."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from generators import GeneratorType, create_generator
from generators.config import GeneratorSettings


def handle_generate_image(
    prompt: str,
    model: str = "schnell",
    width: int = 1024,
    height: int = 1024,
    steps: Optional[int] = None,
    seed: Optional[int] = None,
    output_path: Optional[str] = None,
) -> dict:
    """Generate an image from a text prompt using FLUX.1."""
    type_map = {
        "dev": GeneratorType.FLUX_DEV,
        "schnell": GeneratorType.FLUX_SCHNELL,
    }
    gen_type = type_map.get(model)
    if gen_type is None:
        return {"error": f"Unknown model '{model}'. Use 'dev' or 'schnell'."}

    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(Path(f"~/Desktop/flux_{timestamp}.png").expanduser())

    settings = GeneratorSettings()
    generator = create_generator(gen_type, settings)

    result = generator.generate(
        prompt=prompt,
        output_path=output_path,
        width=width,
        height=height,
        steps=steps,
        seed=seed,
    )

    return result.model_dump(mode="json")
