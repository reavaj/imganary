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
        self._model_mode = None  # "txt2img", "controlnet", or "fill"
        self._logger = get_logger("imganary.flux", settings.log_level)

    @property
    def generator_type(self) -> GeneratorType:
        return self._type

    def _model_name(self) -> str:
        return "schnell" if self._type == GeneratorType.FLUX_SCHNELL else "dev"

    def _default_steps(self) -> int:
        return 4 if self._type == GeneratorType.FLUX_SCHNELL else 25

    def _lora_kwargs(self) -> dict:
        """Common LoRA kwargs for model constructors."""
        kwargs = {}
        if self._settings.flux_lora_paths:
            kwargs["lora_paths"] = self._settings.flux_lora_paths
            kwargs["lora_scales"] = (
                self._settings.flux_lora_scales
                or [1.0] * len(self._settings.flux_lora_paths)
            )
        return kwargs

    def _load_model(self, mode: str = "txt2img"):
        """Load the appropriate model variant. Reloads if mode changes."""
        if self._model is not None and self._model_mode == mode:
            return
        from mflux.models.common.config.model_config import ModelConfig

        is_dev = self._type == GeneratorType.FLUX_DEV
        kwargs = {}
        if self._settings.flux_quantization:
            kwargs["quantize"] = self._settings.flux_quantization
        kwargs.update(self._lora_kwargs())

        if mode == "controlnet":
            from mflux.models.flux.variants.controlnet.flux_controlnet import Flux1Controlnet
            model_config = (
                ModelConfig.dev_controlnet_canny() if is_dev
                else ModelConfig.schnell_controlnet_canny()
            )
            self._logger.info(
                f"Loading FLUX.1-{self._model_name()} ControlNet "
                f"(first run downloads ~3.6GB of ControlNet weights)..."
            )
            kwargs["model_config"] = model_config
            self._model = Flux1Controlnet(**kwargs)

        else:  # txt2img
            from mflux.models.flux.variants.txt2img.flux import Flux1
            model_config = ModelConfig.dev() if is_dev else ModelConfig.schnell()
            self._logger.info(
                f"Loading FLUX.1-{self._model_name()} "
                f"(first run downloads ~12GB from HuggingFace)..."
            )
            kwargs["model_config"] = model_config
            self._model = Flux1(**kwargs)

        self._model_mode = mode

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
        base_image_path: Optional[str | Path] = None,
        base_image_strength: Optional[float] = None,
    ) -> GenerationResult:
        if not prompt or not prompt.strip():
            raise InvalidPromptError("Prompt cannot be empty")

        output_path = Path(output_path).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        steps = steps or self._default_steps()
        guidance = guidance if guidance is not None else self._settings.flux_guidance
        seed = seed if seed is not None else self._settings.flux_default_seed
        if seed is None:
            seed = random.randint(0, 2**32 - 1)

        # Choose model variant based on inputs
        if controlnet_image_path:
            mode = "controlnet"
        else:
            mode = "txt2img"
        self._load_model(mode)

        start = time.monotonic()
        try:
            gen_kwargs = dict(
                seed=seed,
                prompt=prompt,
                num_inference_steps=steps,
                height=height,
                width=width,
                guidance=guidance,
            )
            if controlnet_image_path is not None:
                gen_kwargs["controlnet_image_path"] = str(
                    Path(controlnet_image_path).expanduser()
                )
                gen_kwargs["controlnet_strength"] = controlnet_strength or 0.5
            elif image_path is not None:
                gen_kwargs["image_path"] = str(Path(image_path).expanduser())
                gen_kwargs["image_strength"] = image_strength or 0.5
            image = self._model.generate_image(**gen_kwargs)
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
