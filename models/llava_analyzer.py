import base64
import time
from pathlib import Path

import httpx

from .config import ModelSettings
from .exceptions import (
    AnalysisTimeoutError,
    InvalidImageError,
    ModelNotAvailableError,
)
from .interfaces import (
    AnalysisResult,
    AnalyzerType,
    ImageAnalyzer,
    SceneDescription,
)
from .logging import get_logger


class LlavaAnalyzer(ImageAnalyzer):
    def __init__(self, settings: ModelSettings):
        self._settings = settings
        self._client = httpx.Client(
            base_url=settings.ollama_base_url,
            timeout=settings.llava_timeout_seconds,
        )
        self._logger = get_logger("imganary.llava", settings.log_level)

    @property
    def analyzer_type(self) -> AnalyzerType:
        return AnalyzerType.LLAVA

    def analyze(self, image_path: str | Path) -> AnalysisResult:
        image_path = Path(image_path)
        if not image_path.is_file():
            raise InvalidImageError(f"File not found: {image_path}")

        image_b64 = base64.b64encode(image_path.read_bytes()).decode("utf-8")

        start = time.monotonic()
        try:
            response = self._client.post(
                "/api/generate",
                json={
                    "model": self._settings.llava_model_name,
                    "prompt": (
                        "Describe this image in detail. "
                        "Include objects, colors, composition, and mood."
                    ),
                    "images": [image_b64],
                    "stream": False,
                },
            )
            response.raise_for_status()
        except httpx.ConnectError as exc:
            raise ModelNotAvailableError(
                f"Cannot connect to Ollama at {self._settings.ollama_base_url}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise AnalysisTimeoutError("LLaVA inference timed out") from exc

        elapsed_ms = (time.monotonic() - start) * 1000
        data = response.json()

        if data.get("error"):
            return AnalysisResult(
                analyzer_type=AnalyzerType.LLAVA,
                image_path=str(image_path),
                error=data["error"],
                processing_time_ms=elapsed_ms,
            )

        return AnalysisResult(
            analyzer_type=AnalyzerType.LLAVA,
            image_path=str(image_path),
            scene_description=SceneDescription(
                description=data.get("response", ""),
                model_name=self._settings.llava_model_name,
            ),
            processing_time_ms=elapsed_ms,
        )
