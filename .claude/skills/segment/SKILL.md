---
name: segment
description: >-
  Segment foreground subjects from images using SAM2 (Segment Anything Model 2).
  Outputs transparent PNG. Trigger on: "segment", "remove background",
  "extract subject", "cut out", "foreground extraction", "isolate subject",
  "transparent background", "background removal".
user-invocable: true
compatibility: |
  Requires PyTorch, transformers, PIL. Uses MPS on Apple Silicon with PYTORCH_ENABLE_MPS_FALLBACK=1.
---

# Segment (SAM2 Foreground Extraction)

Extract a foreground subject from an image and save it as a transparent PNG.

## Instructions

### Step 1: Get the image path

Ask the user for the image path if not already provided.

### Step 2: Determine parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| **output** | `<name>_segmented.png` | Output path for the transparent PNG |

### Step 3: Run segment.py

```bash
cd /Users/reavaj/Documents/vscode_projects/imganary
source .venv/bin/activate && python segment.py <image_path> [--output <output_path>]
```

### Step 4: Evaluate the result

Check the console output for the foreground percentage. Good segmentations typically cover 10-50% of the image. If the result is poor (too small, wrong object), use the advanced techniques below.

### Step 5: Advanced — Manual point prompts (if automatic fails)

The automatic grid works for centered subjects. For difficult cases (curly hair, off-center subjects, multiple overlapping objects), write a custom Python script with targeted foreground AND background point prompts.

**Critical SAM2 API details:**

```python
import torch
from PIL import Image
from transformers import Sam2Model, Sam2Processor

# Load model
model = Sam2Model.from_pretrained("facebook/sam2-hiera-tiny").to("mps")
processor = Sam2Processor.from_pretrained("facebook/sam2-hiera-tiny")

image = Image.open(path).convert("RGB")
w, h = image.size

# MUST use 4 levels of nesting: [image][object][point][coords]
# input_labels: 1 = foreground, 0 = background
inputs = processor(
    images=image,
    input_points=[[[[x1, y1], [x2, y2], [x3, y3]]]],
    input_labels=[[[1, 1, 0]]],  # first two are fg, third is bg
    return_tensors="pt",
).to("mps")

with torch.no_grad():
    outputs = model(**inputs)

# post_process_masks takes ONLY 2 args (no reshaped_input_sizes)
masks = processor.post_process_masks(
    outputs.pred_masks.cpu(),
    inputs["original_sizes"].cpu(),
)

# masks[0] shape: (objects, 3_predictions, H, W)
# outputs.iou_scores shape: (batch, objects, 3)
```

**Point prompt strategy for portraits:**
- Place fg points (label=1) on: forehead, chin, each shoulder, chest center, hair edges
- Place bg points (label=0) on: corners, edges, areas clearly NOT the subject
- More points = better discrimination, especially for hair boundaries
- SAM2 treats hair/face/body as separate objects — comprehensive fg points help merge them

**Mask selection:**
- SAM2 returns 3 mask predictions per point set, ranked by IoU score
- Filter by area (1-90% of image) and confidence (>0.7)
- For portraits, the correct mask is usually the largest one covering 20-50% of the image
- Merge overlapping masks (>50% overlap) that belong to the same subject

### Step 6: Present the result

Tell the user:
- Output file path
- Foreground coverage percentage
- Suggest next steps: `composite.py` to place on a background, or `imagine.py --image <composite> --strength 0.3` to harmonize

## Common workflow

```bash
# 1. Segment
./segment.py ~/Desktop/subject.jpg

# 2. Composite onto background
./composite.py ~/Desktop/subject_segmented.png ~/Desktop/background.jpg

# 3. Harmonize with img2img
./imagine.py "the scene" --image ~/Desktop/composite.png --strength 0.3 --hd
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Only grabbed hair, not face | Add explicit fg points on forehead, chin, cheeks |
| Got background in the mask | Add bg points (label=0) on corners and obvious background areas |
| Subject split into pieces | Add more fg points across all body parts to unify |
| Curly hair edges rough | SAM2 struggles with fine hair; accept some loss or manually refine |
| Model download slow | First run downloads ~150MB; cached at `~/.cache/huggingface/` |
| MPS errors | Ensure `PYTORCH_ENABLE_MPS_FALLBACK=1` is set |
