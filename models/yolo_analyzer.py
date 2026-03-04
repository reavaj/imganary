import time
from pathlib import Path

from .config import ModelSettings
from .exceptions import InvalidImageError
from .interfaces import (
    AnalysisResult,
    AnalyzerType,
    BoundingBox,
    DetectedObject,
    ImageAnalyzer,
)
from .logging import get_logger


class YoloAnalyzer(ImageAnalyzer):
    def __init__(self, settings: ModelSettings):
        self._settings = settings
        self._logger = get_logger("imganary.yolo", settings.log_level)
        self._model = None

    def _load_model(self):
        if self._model is None:
            from ultralytics import YOLO

            self._model = YOLO(self._settings.yolo_model_path)
            self._logger.info(
                "YOLO model loaded",
                extra={"props": {"model_path": self._settings.yolo_model_path}},
            )

    @property
    def analyzer_type(self) -> AnalyzerType:
        return AnalyzerType.YOLO

    def analyze(self, image_path: str | Path) -> AnalysisResult:
        image_path = Path(image_path)
        if not image_path.is_file():
            raise InvalidImageError(f"File not found: {image_path}")

        self._load_model()

        start = time.monotonic()
        results = self._model(
            str(image_path),
            conf=self._settings.yolo_confidence_threshold,
            verbose=False,
        )
        elapsed_ms = (time.monotonic() - start) * 1000

        detected = []
        for result in results:
            boxes = result.boxes
            for i in range(len(boxes)):
                coords = boxes.xyxy[i].tolist()
                detected.append(
                    DetectedObject(
                        label=result.names[int(boxes.cls[i])],
                        confidence=float(boxes.conf[i]),
                        bounding_box=BoundingBox(
                            x_min=coords[0],
                            y_min=coords[1],
                            x_max=coords[2],
                            y_max=coords[3],
                        ),
                    )
                )

        return AnalysisResult(
            analyzer_type=AnalyzerType.YOLO,
            image_path=str(image_path),
            detected_objects=detected,
            processing_time_ms=elapsed_ms,
        )
