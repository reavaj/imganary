# Image Analysis Skills

Local vision model wrappers for understanding image content before generating edits.

## Models

- **LLaVA** — General-purpose scene description via Ollama REST API (~5s per image, first load ~160s)
- **YOLO** — Object detection with bounding boxes and confidence scores (<1s)
- **CLIP** — Semantic image-text similarity and zero-shot classification (<1s)

## Usage

```bash
./analyze.py ~/Desktop/photo.jpg --model llava
./analyze.py ~/Desktop/photo.jpg --model yolo
./analyze.py ~/Desktop/photo.jpg --model clip
```

All analyzers implement the `ImageAnalyzer` ABC and return structured `AnalysisResult` objects. See `models/README.md` for the Python API.
