import sys
from pathlib import Path

# Add project root to path so models package is importable
_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from models import AnalyzerType, ModelSettings, create_analyzer


def handle_analyze_image(image_path: str, model: str) -> dict:
    settings = ModelSettings()
    analyzer_type = AnalyzerType(model)
    analyzer = create_analyzer(analyzer_type, settings)
    result = analyzer.analyze(image_path)
    return result.model_dump(mode="json")
