from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class GeneratorType(str, Enum):
    FLUX_DEV = "flux-dev"
    FLUX_SCHNELL = "flux-schnell"
    COMFYUI = "comfyui"


class GenerationResult(BaseModel):
    """Result envelope returned by all generators."""

    generator_type: GeneratorType
    prompt: str
    output_path: str
    width: int
    height: int
    steps: int
    seed: Optional[int] = None
    processing_time_ms: Optional[float] = None
    error: Optional[str] = None
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class ImageGenerator(ABC):
    """Abstract interface for all image generation wrappers."""

    @property
    @abstractmethod
    def generator_type(self) -> GeneratorType:
        """Return which type of generator this is."""
        ...

    @abstractmethod
    def generate(
        self,
        prompt: str,
        output_path: str | Path,
        width: int = 1024,
        height: int = 1024,
        steps: Optional[int] = None,
        seed: Optional[int] = None,
        image_path: Optional[str | Path] = None,
        image_strength: Optional[float] = None,
        guidance: Optional[float] = None,
        controlnet_image_path: Optional[str | Path] = None,
        controlnet_strength: Optional[float] = None,
    ) -> GenerationResult:
        """Generate an image from a text prompt, optionally using a reference image."""
        ...
