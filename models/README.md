# Local Vision Models

This directory is reserved for local vision/recognition model configurations and utilities. Large model weight files (`.bin`, `.pt`, `.onnx`, `.safetensors`) are gitignored.

## Supported Models

### LLaVA (via Ollama)

General-purpose vision-language model. Used for scene description and understanding image content before generating GIMP edits.

```bash
ollama pull llava
ollama run llava "Describe this image" --images ./path/to/image.jpg
```

### YOLO

Object detection model. Useful for identifying and locating specific objects in images.

### CLIP

Semantic image understanding. Enables natural-language queries about image content.

## Workflow

```
image path → local model → scene description → Claude generates GIMP script → script saved to library
```
