import random
import time
from pathlib import Path
from typing import Optional

from .config import GeneratorSettings
from .exceptions import ImageGenerationError, InvalidPromptError
from .interfaces import GenerationResult, GeneratorType, ImageGenerator

from models.logging import get_logger


class FluxGenerator(ImageGenerator):
    def __init__(self, generator_type: GeneratorType, settings: GeneratorSettings):
        self._type = generator_type
        self._settings = settings
        self._model = None
        self._logger = get_logger("imganary.flux", settings.log_level)

    @property
    def generator_type(self) -> GeneratorType:
        return self._type

    def _model_name(self) -> str:
        return "schnell" if self._type == GeneratorType.FLUX_SCHNELL else "dev"

    def _default_steps(self) -> int:
        return 4 if self._type == GeneratorType.FLUX_SCHNELL else 25

    def _load_model(self):
        if self._model is not None:
            return
        from mflux.models.flux.variants.txt2img.flux import Flux1

        self._logger.info(
            f"Loading FLUX.1-{self._model_name()} "
            f"(first run downloads ~12GB from HuggingFace)..."
        )
        kwargs = {"model_name": self._model_name()}
        if self._settings.flux_quantization:
            kwargs["quantize"] = self._settings.flux_quantization
        self._model = Flux1.from_name(**kwargs)

    def generate(
        self,
        prompt: str,
        output_path: str | Path,
        width: int = 1024,
        height: int = 1024,
        steps: Optional[int] = None,
        seed: Optional[int] = None,
    ) -> GenerationResult:
        if not prompt or not prompt.strip():
            raise InvalidPromptError("Prompt cannot be empty")

        output_path = Path(output_path).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        steps = steps or self._default_steps()
        seed = seed if seed is not None else self._settings.flux_default_seed
        if seed is None:
            seed = random.randint(0, 2**32 - 1)

        self._load_model()

        start = time.monotonic()
        try:
            image = self._model.generate_image(
                seed=seed,
                prompt=prompt,
                num_inference_steps=steps,
                height=height,
                width=width,
            )
            image.save(path=str(output_path))
        except Exception as exc:
            elapsed_ms = (time.monotonic() - start) * 1000
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
        self._logger.info(
            f"Generated {width}x{height} image in {elapsed_ms:.0f}ms"
        )

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
