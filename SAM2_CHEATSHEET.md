# SAM2 Cheat Sheet

## Quick Start

```bash
# Basic segmentation (automatic point grid)
./segment.py ~/Desktop/photo.jpg

# Custom output path
./segment.py ~/Desktop/photo.jpg --output ~/Desktop/result.png
```

Output: transparent PNG with background removed.

## Full Workflow (Segment + Composite + Harmonize)

```bash
# 1. Extract subject
./segment.py ~/Desktop/subject.jpg

# 2. Place on new background
./composite.py ~/Desktop/subject_segmented.png ~/Desktop/background.jpg

# 3. Harmonize edges with img2img
./imagine.py "the scene" --image ~/Desktop/composite.png --strength 0.3 --hd
```

## How It Works

SAM2 (Segment Anything Model 2) uses point prompts to identify objects. `segment.py` probes a 5x5 center-weighted grid of points, collects all valid masks, scores them by size and confidence, then merges overlapping masks into one foreground extraction.

- Model: `facebook/sam2-hiera-tiny` (~150MB, auto-downloaded)
- Device: MPS (Apple Silicon) with CPU fallback
- Requires: `PYTORCH_ENABLE_MPS_FALLBACK=1` (set automatically by segment.py)

## Python API

```python
from segment import segment_foreground

# Returns path to saved RGBA PNG
output = segment_foreground("~/Desktop/photo.jpg")
output = segment_foreground("~/Desktop/photo.jpg", output_path="~/Desktop/out.png")
```

## SAM2 API Reference (HuggingFace Transformers)

### Loading

```python
from transformers import Sam2Model, Sam2Processor

model = Sam2Model.from_pretrained("facebook/sam2-hiera-tiny").to("mps")
processor = Sam2Processor.from_pretrained("facebook/sam2-hiera-tiny")
```

### Input Format

```python
# CRITICAL: input_points needs 4 levels of nesting
# [image_batch][object][point][x, y]
inputs = processor(
    images=image,                                    # PIL Image (RGB)
    input_points=[[[[x1, y1], [x2, y2]]]],          # 4 levels!
    input_labels=[[[1, 1]]],                         # 1=foreground, 0=background
    return_tensors="pt",
).to("mps")
```

| Nesting Level | Meaning | Example |
|---------------|---------|---------|
| Level 1 | Image batch | `[...]` — one image |
| Level 2 | Object | `[[...]]` — one object to segment |
| Level 3 | Points | `[[[x,y], [x,y]]]` — multiple point prompts |
| Level 4 | Coordinates | `[[[[100, 200]]]]` — x, y pixel coords |

### Inference

```python
with torch.no_grad():
    outputs = model(**inputs)
```

### Post-Processing

```python
# ONLY 2 args — no reshaped_input_sizes parameter
masks = processor.post_process_masks(
    outputs.pred_masks.cpu(),        # raw 256x256 predictions
    inputs["original_sizes"].cpu(),  # upscale to original resolution
)

# masks[0] shape: (num_objects, 3_predictions, H, W)
# outputs.iou_scores shape: (batch, num_objects, 3)
```

Each point set returns **3 mask predictions** ranked by IoU confidence score.

### Applying a Mask

```python
import numpy as np

mask = masks[0].squeeze(0)[best_idx].cpu().numpy()  # boolean (H, W)
img_array = np.array(image.convert("RGBA"))
img_array[~mask] = [0, 0, 0, 0]  # transparent background
result = Image.fromarray(img_array, "RGBA")
result.save("output.png")
```

## Point Prompt Strategy

### Automatic (what segment.py does)

- 5x5 grid in the center 30-70% of the image (25 points + center)
- Filters masks: 1-90% area, >0.7 confidence
- Scores: prefers 5-50% area sweet spot
- Merges overlapping masks (>50% overlap)

### Manual (for difficult subjects)

```python
# Portrait example: fg points on body, bg points on background
fg_points = [
    [w*0.5, h*0.15],   # top of head
    [w*0.5, h*0.3],    # forehead
    [w*0.5, h*0.5],    # nose/center face
    [w*0.5, h*0.7],    # chin/neck
    [w*0.5, h*0.85],   # chest
    [w*0.35, h*0.4],   # left cheek
    [w*0.65, h*0.4],   # right cheek
    [w*0.3, h*0.7],    # left shoulder
    [w*0.7, h*0.7],    # right shoulder
]
bg_points = [
    [w*0.05, h*0.05],  # top-left corner
    [w*0.95, h*0.05],  # top-right corner
    [w*0.05, h*0.95],  # bottom-left corner
    [w*0.95, h*0.95],  # bottom-right corner
    [w*0.1, h*0.5],    # left edge
    [w*0.9, h*0.5],    # right edge
]

all_points = fg_points + bg_points
labels = [1]*len(fg_points) + [0]*len(bg_points)

inputs = processor(
    images=image,
    input_points=[[[p for p in all_points]]],
    input_labels=[[labels]],
    return_tensors="pt",
).to("mps")
```

### Tips

| Scenario | Strategy |
|----------|----------|
| Centered portrait | Automatic grid usually works |
| Off-center subject | Manual fg points on the subject |
| Curly/fine hair | Add fg points on hair edges + bg points just outside hair |
| Multiple people | Focus fg points on ONE person; bg points on others |
| Subject vs similar background | More bg points near the boundary |
| Only got partial subject | Add fg points on the missed body parts |

## Mask Selection Guide

| Foreground % | Likely Content |
|--------------|----------------|
| 1-5% | Single small object or face-only crop |
| 5-20% | Head and shoulders, or a small animal |
| 20-50% | Full upper body, full animal, typical portrait |
| 50-80% | Close-up, full body filling frame |
| >80% | Probably grabbed background instead |

## Composite Options

After segmenting, use `composite.py` to place the subject:

```bash
# Basic (centered, bottom-aligned)
./composite.py foreground.png background.jpg

# Scaled down, custom position
./composite.py foreground.png background.jpg --scale 0.5 --x 300 --y 800

# Custom output
./composite.py foreground.png background.jpg --output ~/Desktop/final.png
```

| Flag | Default | Description |
|------|---------|-------------|
| `--scale N` | 1.0 | Resize foreground (0.5 = half size) |
| `--x N` | centered | Horizontal center position |
| `--y N` | bottom-aligned | Vertical bottom position |
| `--output path` | `~/Desktop/composite.png` | Output path |

## Gotchas

| Issue | Details |
|-------|---------|
| `input_points` nesting | Must be 4 levels deep: `[[[[x, y]]]]`. 3 levels = crash |
| `post_process_masks` args | Only 2 args (pred_masks, original_sizes). No `reshaped_input_sizes` |
| MPS fallback required | Some SAM2 ops not implemented on MPS; needs CPU fallback |
| Hair segmentation | SAM2 often treats hair as a separate object from face/body |
| First run slow | Downloads model weights (~150MB) on first use |
| Memory | Model uses ~2GB VRAM; unload before running FLUX |
