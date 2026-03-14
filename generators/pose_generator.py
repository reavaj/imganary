"""Pose-guided image generation using FLUX.1-dev + ControlNet-Union-Pro via diffusers.

Uses Shakker-Labs/FLUX.1-dev-ControlNet-Union-Pro with control_mode=4 (pose).
"""

import random
import time
from pathlib import Path
from typing import Optional

import torch
from PIL import Image

from .config import GeneratorSettings
from .exceptions import ImageGenerationError, InvalidPromptError
from .interfaces import GenerationResult, GeneratorType, ImageGenerator

from models.logging import get_logger

# Union Pro control modes
POSE_MODE = 4


class PoseGenerator(ImageGenerator):
    """Generates images guided by a pose skeleton using FluxControlNetPipeline."""

    CONTROLNET_REPO = "Shakker-Labs/FLUX.1-dev-ControlNet-Union-Pro"
    BASE_MODEL_REPO = "black-forest-labs/FLUX.1-dev"

    def __init__(self, generator_type: GeneratorType, settings: GeneratorSettings):
        self._type = generator_type
        self._settings = settings
        self._pipe = None
        self._logger = get_logger("imganary.pose", settings.log_level)

    @property
    def generator_type(self) -> GeneratorType:
        return self._type

    def _load_pipeline(self):
        if self._pipe is not None:
            return

        from diffusers import FluxControlNetModel, FluxControlNetPipeline

        self._logger.info(
            "Loading ControlNet-Union-Pro (first run downloads ~12GB base + ~3GB ControlNet)..."
        )
        print("Loading ControlNet-Union-Pro model (first run downloads weights)...")

        controlnet = FluxControlNetModel.from_pretrained(
            self.CONTROLNET_REPO,
            torch_dtype=torch.bfloat16,
        )

        self._pipe = FluxControlNetPipeline.from_pretrained(
            self.BASE_MODEL_REPO,
            controlnet=controlnet,
            torch_dtype=torch.bfloat16,
        )

        self._pipe.to("mps")
        print("Pose ControlNet pipeline ready.")

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
        if not prompt or not prompt.strip():
            raise InvalidPromptError("Prompt cannot be empty")

        # controlnet_image_path is the pose skeleton image
        if controlnet_image_path is None:
            raise ImageGenerationError(
                "Pose generator requires a pose skeleton image via controlnet_image_path. "
                "Use pose.py to extract a skeleton first."
            )

        output_path = Path(output_path).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        steps = steps or 28
        guidance = guidance if guidance is not None else self._settings.flux_guidance
        seed = seed if seed is not None else self._settings.flux_default_seed
        if seed is None:
            seed = random.randint(0, 2**32 - 1)
        controlnet_strength = controlnet_strength if controlnet_strength is not None else 0.9

        self._load_pipeline()

        # Load and prepare pose skeleton image
        pose_path = Path(controlnet_image_path).expanduser()
        if not pose_path.is_file():
            raise ImageGenerationError(f"Pose image not found: {pose_path}")
        pose_image = Image.open(str(pose_path)).convert("RGB")

        start = time.monotonic()
        try:
            generator = torch.Generator("mps").manual_seed(seed)

            result_images = self._pipe(
                prompt=prompt,
                control_image=pose_image,
                control_mode=POSE_MODE,
                controlnet_conditioning_scale=controlnet_strength,
                control_guidance_end=0.65,
                num_inference_steps=steps,
                guidance_scale=guidance,
                height=height,
                width=width,
                generator=generator,
            ).images

            result_images[0].save(str(output_path))

        except Exception as exc:
            elapsed_ms = (time.monotonic() - start) * 1000
            self._logger.error(f"Pose generation failed: {exc}")
            return GenerationResult(
                generator_type=self._type,
                prompt=prompt,
                output_path=str(output_path),
                width=width,
                height=height,
                steps=steps,
                seed=seed,
                processing_time_ms=elapsed_ms,
                error=str(exc),
            )

        elapsed_ms = (time.monotonic() - start) * 1000
        self._logger.info(f"Generated {width}x{height} pose-guided image in {elapsed_ms:.0f}ms")

        return GenerationResult(
            generator_type=self._type,
            prompt=prompt,
            output_path=str(output_path),
            width=width,
            height=height,
            steps=steps,
            seed=seed,
            processing_time_ms=elapsed_ms,
        )
