"""ComfyUI generator — delegates image generation to a local ComfyUI server via HTTP."""

import json
import random
import time
from pathlib import Path
from typing import Optional

from .comfyui_client import ComfyUIClient
from .config import GeneratorSettings
from .exceptions import ImageGenerationError, InvalidPromptError
from .interfaces import GenerationResult, GeneratorType, ImageGenerator

from models.logging import get_logger

WORKFLOWS_DIR = Path(__file__).parent.parent / "workflows"


def _load_workflow(name: str, replacements: dict) -> dict:
    """Load a workflow JSON template and replace placeholder values."""
    path = WORKFLOWS_DIR / f"{name}.json"
    raw = path.read_text()

    for key, value in replacements.items():
        placeholder = f'"__{key}__"'
        # For string values, wrap in quotes; for numeric values, use raw
        if isinstance(value, (int, float)):
            raw = raw.replace(placeholder, str(value))
        else:
            raw = raw.replace(placeholder, json.dumps(value))

    return json.loads(raw)


class ComfyUIGenerator(ImageGenerator):
    def __init__(self, generator_type: GeneratorType, settings: GeneratorSettings):
        self._type = generator_type
        self._settings = settings
        self._client = ComfyUIClient(
            base_url=settings.comfyui_url,
            timeout=settings.comfyui_timeout,
        )
        self._logger = get_logger("imganary.comfyui", settings.log_level)

    @property
    def generator_type(self) -> GeneratorType:
        return self._type

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

        output_path = Path(output_path).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        steps = steps or 25
        seed = seed if seed is not None else random.randint(0, 2**32 - 1)

        # Check server is reachable
        if not self._client.ping():
            return GenerationResult(
                generator_type=self._type,
                prompt=prompt,
                output_path=str(output_path),
                width=width,
                height=height,
                steps=steps,
                seed=seed,
                processing_time_ms=0,
                error=f"ComfyUI server not reachable at {self._settings.comfyui_url}",
            )

        # Choose workflow: IP-Adapter style transfer vs plain txt2img
        use_ipadapter = image_path is not None
        style_strength = image_strength if image_strength is not None else 0.7

        start = time.monotonic()
        try:
            replacements = {
                "MODEL_NAME": self._settings.comfyui_model_name,
                "CLIP_NAME1": self._settings.comfyui_clip_name1,
                "CLIP_NAME2": self._settings.comfyui_clip_name2,
                "VAE_NAME": self._settings.comfyui_vae_name,
                "PROMPT": prompt,
                "SEED": seed,
                "WIDTH": width,
                "HEIGHT": height,
                "STEPS": steps,
            }

            if use_ipadapter:
                # Upload style reference image to ComfyUI
                server_filename = self._client.upload_image(image_path)
                replacements["STYLE_IMAGE"] = server_filename
                replacements["STYLE_STRENGTH"] = style_strength
                replacements["IPADAPTER_NAME"] = self._settings.comfyui_ipadapter_name
                workflow = _load_workflow("flux_ipadapter", replacements)
                self._logger.info(
                    f"Submitting IP-Adapter workflow (style_strength={style_strength})"
                )
            else:
                workflow = _load_workflow("flux_txt2img", replacements)
                self._logger.info("Submitting txt2img workflow")

            prompt_id = self._client.queue_prompt(workflow)
            self._logger.info(f"Queued prompt {prompt_id}")

            result = self._client.wait_for_result(prompt_id)

            # Download the first output image
            images = self._client.find_output_images(result)
            if not images:
                raise ImageGenerationError("No output images in ComfyUI result")

            img_info = images[0]
            self._client.download_image(
                filename=img_info["filename"],
                output_path=output_path,
                subfolder=img_info.get("subfolder", ""),
                image_type=img_info.get("type", "output"),
            )

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
        self._logger.info(f"Generated {width}x{height} image in {elapsed_ms:.0f}ms")

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
