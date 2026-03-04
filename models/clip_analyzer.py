import time
from pathlib import Path
from typing import List, Optional

from .config import ModelSettings
from .exceptions import InvalidImageError
from .interfaces import (
    AnalysisResult,
    AnalyzerType,
    ImageAnalyzer,
    SemanticMatch,
)
from .logging import get_logger


class ClipAnalyzer(ImageAnalyzer):
    def __init__(self, settings: ModelSettings):
        self._settings = settings
        self._logger = get_logger("imganary.clip", settings.log_level)
        self._model = None
        self._processor = None

    def _load_model(self):
        if self._model is None:
            from transformers import CLIPModel, CLIPProcessor

            model_name = self._settings.clip_model_name
            self._processor = CLIPProcessor.from_pretrained(model_name)
            self._model = CLIPModel.from_pretrained(model_name)
            self._logger.info(
                "CLIP model loaded",
                extra={"props": {"model_name": model_name}},
            )

    @property
    def analyzer_type(self) -> AnalyzerType:
        return AnalyzerType.CLIP

    def analyze(
        self,
        image_path: str | Path,
        candidate_labels: Optional[List[str]] = None,
    ) -> AnalysisResult:
        image_path = Path(image_path)
        if not image_path.is_file():
            raise InvalidImageError(f"File not found: {image_path}")

        self._load_model()

        from PIL import Image
        import torch

        labels = candidate_labels or self._settings.clip_candidate_labels
        image = Image.open(image_path).convert("RGB")

        start = time.monotonic()
        inputs = self._processor(
            text=labels,
            images=image,
            return_tensors="pt",
            padding=True,
        )
        with torch.no_grad():
            outputs = self._model(**inputs)

        logits = outputs.logits_per_image[0]
        probs = logits.softmax(dim=0).tolist()
        elapsed_ms = (time.monotonic() - start) * 1000

        matches = sorted(
            [
                SemanticMatch(label=lbl, score=score)
                for lbl, score in zip(labels, probs)
            ],
            key=lambda m: m.score,
            reverse=True,
        )

        return AnalysisResult(
            analyzer_type=AnalyzerType.CLIP,
            image_path=str(image_path),
            semantic_matches=matches,
            processing_time_ms=elapsed_ms,
        )
