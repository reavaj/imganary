from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field


class AnalyzerType(str, Enum):
    LLAVA = "llava"
    YOLO = "yolo"
    CLIP = "clip"


class BoundingBox(BaseModel):
    """Pixel coordinates for a detected object."""

    x_min: float
    y_min: float
    x_max: float
    y_max: float


class DetectedObject(BaseModel):
    """A single object detected by YOLO."""

    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    bounding_box: BoundingBox


class SceneDescription(BaseModel):
    """Free-text scene description from LLaVA."""

    description: str
    model_name: str


class SemanticMatch(BaseModel):
    """A candidate label with its similarity score from CLIP."""

    label: str
    score: float = Field(ge=0.0, le=1.0)


class AnalysisResult(BaseModel):
    """Unified result envelope returned by all analyzers."""

    analyzer_type: AnalyzerType
    image_path: str
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    scene_description: Optional[SceneDescription] = None
    detected_objects: Optional[List[DetectedObject]] = None
    semantic_matches: Optional[List[SemanticMatch]] = None
    processing_time_ms: Optional[float] = None
    error: Optional[str] = None


class ImageAnalyzer(ABC):
    """Abstract interface for all vision model wrappers."""

    @property
    @abstractmethod
    def analyzer_type(self) -> AnalyzerType:
        """Return which type of analyzer this is."""
        ...

    @abstractmethod
    def analyze(self, image_path: str | Path) -> AnalysisResult:
        """Analyze an image and return structured results."""
        ...
