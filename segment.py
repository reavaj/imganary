#!/usr/bin/env python3
"""Segment the foreground subject from an image using SAM2.

Usage:
    ./segment.py <image_path> [--output path.png]

Outputs a PNG with transparency — the background is removed, foreground preserved.

Workflow:
    ./segment.py ~/Desktop/subject.jpg
    ./composite.py ~/Desktop/subject_segmented.png ~/Desktop/background.jpg
    ./imagine.py "the scene" --image ~/Desktop/composite.png --strength 0.3 --hd
"""

import os
import sys
import warnings
from pathlib import Path

# Suppress noisy library warnings
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_DISABLE_EXPERIMENTAL_WARNING"] = "1"
os.environ["DO_NOT_TRACK"] = "1"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
warnings.filterwarnings("ignore")


def segment_foreground(
    image_path: str,
    output_path: str | None = None,
) -> str:
    """Segment the most prominent foreground object from an image.

    Uses SAM2 (Segment Anything Model 2) with point prompts to find
    and extract the largest foreground subject.

    Args:
        image_path: Path to the input image.
        output_path: Where to save the result. Defaults to <name>_segmented.png.

    Returns:
        Path to the saved RGBA PNG with transparent background.
    """
    import numpy as np
    import torch
    from PIL import Image
    from transformers import Sam2Model, Sam2Processor

    image_path = str(Path(image_path).expanduser())
    if not Path(image_path).is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")

    if output_path is None:
        p = Path(image_path)
        output_path = str(p.parent / f"{p.stem}_segmented.png")
    else:
        output_path = str(Path(output_path).expanduser())

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Loading SAM2 model on {device} (first run downloads weights)...")
    model = Sam2Model.from_pretrained("facebook/sam2-hiera-tiny").to(device)
    processor = Sam2Processor.from_pretrained("facebook/sam2-hiera-tiny")

    print(f"Segmenting: {image_path}")
    image = Image.open(image_path).convert("RGB")
    w, h = image.size
    total_pixels = h * w

    # Sample a center-weighted grid of point prompts — foreground subjects
    # are typically near the center of the frame.
    grid_points = []
    for gy in range(3, 8):  # 5 rows in the middle band
        for gx in range(3, 8):  # 5 columns in the middle band
            grid_points.append([w * gx / 10, h * gy / 10])
    grid_points.append([w / 2, h / 2])  # dead center

    all_masks = []
    all_scores = []

    print(f"Probing {len(grid_points)} points for foreground objects...")
    for point in grid_points:
        # Sam2Processor expects 4 levels: [image][object][point][coords]
        inputs = processor(
            images=image,
            input_points=[[[[point[0], point[1]]]]],
            return_tensors="pt",
        ).to(device)

        with torch.no_grad():
            outputs = model(**inputs)

        # post_process_masks upscales 256x256 predictions to original size
        masks = processor.post_process_masks(
            outputs.pred_masks.cpu(),
            inputs["original_sizes"].cpu(),
        )

        # masks[0] shape: (objects, 3_predictions, H, W)
        mask_tensor = masks[0].squeeze(0)  # (3, H, W)
        scores = outputs.iou_scores.squeeze(0)  # (1, 3)

        for i in range(mask_tensor.shape[0]):
            mask = mask_tensor[i].cpu().numpy()
            score = scores[0, i].item()
            area = mask.sum()
            # Filter: must cover at least 1% but less than 90% of the image
            if 0.01 * total_pixels < area < 0.90 * total_pixels and score > 0.7:
                all_masks.append(mask)
                all_scores.append(score)

    if not all_masks:
        print("Warning: No clear foreground object found. Trying center point with relaxed threshold...")
        inputs = processor(
            images=image,
            input_points=[[[[w / 2, h / 2]]]],
            return_tensors="pt",
        ).to(device)
        with torch.no_grad():
            outputs = model(**inputs)
        masks = processor.post_process_masks(
            outputs.pred_masks.cpu(),
            inputs["original_sizes"].cpu(),
        )
        mask_tensor = masks[0].squeeze(0)
        scores = outputs.iou_scores.squeeze(0)
        best_idx = scores[0].argmax().item()
        best_mask = mask_tensor[best_idx].cpu().numpy()
        all_masks = [best_mask]
        all_scores = [scores[0, best_idx].item()]

    # Score masks: prefer large, high-confidence masks in the 5-50% area sweet spot
    scored = []
    for mask, score in zip(all_masks, all_scores):
        area_frac = mask.sum() / total_pixels
        size_bonus = 1.0 if 0.05 < area_frac < 0.50 else 0.7
        scored.append((score * size_bonus, mask))

    scored.sort(key=lambda x: x[0], reverse=True)
    best_mask = scored[0][1]

    # Merge overlapping masks that likely belong to the same object
    for _, mask in scored[1:]:
        overlap = (best_mask & mask).sum() / max(mask.sum(), 1)
        if overlap > 0.5:
            best_mask = best_mask | mask

    # Apply mask to create RGBA image with transparent background
    img_array = np.array(image.convert("RGBA"))
    img_array[~best_mask] = [0, 0, 0, 0]
    result = Image.fromarray(img_array, "RGBA")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    result.save(output_path)

    fg_pct = best_mask.sum() / total_pixels * 100
    print(f"Foreground extracted ({fg_pct:.1f}% of image)")
    print(f"Saved to: {output_path}")
    return output_path


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: ./segment.py <image_path> [--output path.png]\n\n"
            "Segment the foreground subject and remove the background.\n"
            "Output is a PNG with transparency.\n\n"
            "Workflow:\n"
            "  ./segment.py ~/Desktop/subject.jpg\n"
            "  ./composite.py ~/Desktop/subject_segmented.png ~/Desktop/background.jpg\n"
            "  ./imagine.py \"the scene\" --image ~/Desktop/composite.png --strength 0.3 --hd"
        )
        sys.exit(1)

    image_path = sys.argv[1]

    output = None
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            output = sys.argv[idx + 1]

    try:
        segment_foreground(image_path, output)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
