# Vision Models

Python package providing unified wrappers for local vision models. All analyzers implement the `ImageAnalyzer` ABC and return structured `AnalysisResult` objects.

## Supported Models

### LLaVA (via Ollama)

General-purpose vision-language model. Returns free-text scene descriptions via Ollama REST API (httpx, `stream: False`). First load takes ~160s, subsequent runs ~5s.

```bash
ollama pull llava
```

### YOLO (Ultralytics YOLOv8)

Object detection. Returns detected objects with bounding boxes and confidence scores. The `yolov8n.pt` model (~6MB) auto-downloads on first use.

### CLIP (OpenAI)

Semantic image understanding. Zero-shot classification against candidate labels. Model weights (~600MB) download on first use.

## CLI Usage

```bash
# Analyze with a specific model
./analyze.py ~/Desktop/photo.jpg --model llava
./analyze.py ~/Desktop/photo.jpg --model yolo
./analyze.py ~/Desktop/photo.jpg --model clip
```

## Python API

```python
from models import create_analyzer, AnalyzerType

# LLaVA — scene description
analyzer = create_analyzer(AnalyzerType.LLAVA)
result = analyzer.analyze("photo.jpg")
print(result.scene_description.description)

# YOLO — object detection
yolo = create_analyzer(AnalyzerType.YOLO)
result = yolo.analyze("photo.jpg")
for obj in result.detected_objects:
    print(f"{obj.label}: {obj.confidence:.2f}")

# CLIP — semantic matching
clip = create_analyzer(AnalyzerType.CLIP)
result = clip.analyze("photo.jpg")
for match in result.semantic_matches:
    print(f"{match.label}: {match.score:.2f}")

# All analyzers at once
from models import create_all_analyzers
analyzers = create_all_analyzers()
for name, analyzer in analyzers.items():
    print(analyzer.analyze("photo.jpg"))
```

## Configuration

All settings are loaded from environment variables (prefix `IMGANARY_`) or a `.env` file. See `generators/config.py` and `models/config.py`.

## Module Structure

- `interfaces.py` — `ImageAnalyzer` ABC, `AnalysisResult`, and all Pydantic result models
- `config.py` — `ModelSettings` (pydantic-settings)
- `llava_analyzer.py` — LLaVA wrapper (httpx → Ollama API)
- `yolo_analyzer.py` — YOLO wrapper (ultralytics)
- `clip_analyzer.py` — CLIP wrapper (transformers + torch)
- `factory.py` — `create_analyzer()` and `create_all_analyzers()` factory functions
- `exceptions.py` — Custom exception hierarchy
- `logging.py` — JSON structured logger
