from typing import Dict, Optional

from .config import GeneratorSettings
from .flux_generator import FluxGenerator
from .interfaces import GeneratorType, ImageGenerator

_REGISTRY: Dict[GeneratorType, type] = {
    GeneratorType.FLUX_DEV: FluxGenerator,
    GeneratorType.FLUX_SCHNELL: FluxGenerator,
}


def create_generator(
    generator_type: GeneratorType,
    settings: Optional[GeneratorSettings] = None,
) -> ImageGenerator:
    """Create a configured generator instance."""
    if settings is None:
        settings = GeneratorSettings()

    cls = _REGISTRY.get(generator_type)
    if cls is None:
        raise ValueError(f"Unknown generator type: {generator_type}")
    return cls(generator_type, settings)
