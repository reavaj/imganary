from typing import Dict, Optional

from .clip_analyzer import ClipAnalyzer
from .config import ModelSettings
from .interfaces import AnalyzerType, ImageAnalyzer
from .llava_analyzer import LlavaAnalyzer
from .yolo_analyzer import YoloAnalyzer

_REGISTRY: Dict[AnalyzerType, type] = {
    AnalyzerType.LLAVA: LlavaAnalyzer,
    AnalyzerType.YOLO: YoloAnalyzer,
    AnalyzerType.CLIP: ClipAnalyzer,
}


def create_analyzer(
    analyzer_type: AnalyzerType,
    settings: Optional[ModelSettings] = None,
) -> ImageAnalyzer:
    """Create a configured analyzer instance."""
    if settings is None:
        settings = ModelSettings()

    cls = _REGISTRY.get(analyzer_type)
    if cls is None:
        raise ValueError(f"Unknown analyzer type: {analyzer_type}")
    return cls(settings)


def create_all_analyzers(
    settings: Optional[ModelSettings] = None,
) -> Dict[AnalyzerType, ImageAnalyzer]:
    """Create one instance of every registered analyzer."""
    if settings is None:
        settings = ModelSettings()
    return {t: cls(settings) for t, cls in _REGISTRY.items()}
