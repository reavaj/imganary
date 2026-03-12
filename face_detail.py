"""Face detail enhancement via YOLO detection + FLUX.1 Fill inpainting."""

import tempfile
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFilter


# HuggingFace face detection model (auto-downloaded on first use)
FACE_MODEL_REPO = "arnabdhar/YOLOv8-Face-Detection"
FACE_MODEL_FILE = "model.pt"
FACE_CONFIDENCE = 0.4

_face_model = None


def _get_face_model():
    """Load face YOLO model, downloading from HuggingFace if needed."""
    global _face_model
    if _face_model is not None:
        return _face_model

    from huggingface_hub import hf_hub_download
    from ultralytics import YOLO

    model_path = hf_hub_download(repo_id=FACE_MODEL_REPO, filename=FACE_MODEL_FILE)
    _face_model = YOLO(model_path)
    return _face_model


def detect_faces(image_path: str | Path) -> list[dict]:
    """Detect faces using YOLO face model. Returns list of {x_min, y_min, x_max, y_max, conf}."""
    model = _get_face_model()
    results = model(str(image_path), conf=FACE_CONFIDENCE, verbose=False)

    faces = []
    for result in results:
        boxes = result.boxes
        for i in range(len(boxes)):
            coords = boxes.xyxy[i].tolist()
            faces.append({
                "x_min": coords[0],
                "y_min": coords[1],
                "x_max": coords[2],
                "y_max": coords[3],
                "conf": float(boxes.conf[i]),
            })
    return faces


def _expand_box(box: dict, img_width: int, img_height: int, factor: float = 1.5) -> tuple:
    """Expand a face bounding box by factor, clamped to image bounds.
    Returns (x_min, y_min, x_max, y_max) as ints.
    """
    cx = (box["x_min"] + box["x_max"]) / 2
    cy = (box["y_min"] + box["y_max"]) / 2
    w = (box["x_max"] - box["x_min"]) * factor
    h = (box["y_max"] - box["y_min"]) * factor

    x_min = max(0, int(cx - w / 2))
    y_min = max(0, int(cy - h / 2))
    x_max = min(img_width, int(cx + w / 2))
    y_max = min(img_height, int(cy + h / 2))
    return x_min, y_min, x_max, y_max


def _create_face_mask(img_size: tuple, region: tuple) -> Image.Image:
    """Create a white-on-black mask for the face region (white = inpaint area).
    Feathers the edges for smooth blending.
    """
    mask = Image.new("L", img_size, 0)
    draw = ImageDraw.Draw(mask)
    x_min, y_min, x_max, y_max = region
    # Inset slightly so feathering doesn't leak outside the region
    draw.rectangle([x_min + 2, y_min + 2, x_max - 2, y_max - 2], fill=255)
    # Feather edges
    mask = mask.filter(ImageFilter.GaussianBlur(radius=8))
    return mask


def enhance_faces(
    image_path: str | Path,
    generator,
    prompt: str,
    seed: int,
    guidance: Optional[float] = None,
    steps: Optional[int] = None,
) -> int:
    """Detect faces in the image and re-generate each at higher detail via Fill inpainting.

    Args:
        image_path: Path to the generated image.
        generator: A FluxGenerator instance (will be loaded in "fill" mode).
        prompt: The original generation prompt (reused for inpainting context).
        seed: Seed for reproducibility.
        guidance: CFG guidance scale.
        steps: Inference steps for inpainting (defaults to generator default).

    Returns:
        Number of faces enhanced.
    """
    image_path = Path(image_path)
    faces = detect_faces(image_path)
    if not faces:
        return 0

    img = Image.open(image_path).convert("RGB")
    img_w, img_h = img.size

    for face in faces:
        region = _expand_box(face, img_w, img_h, factor=1.5)
        x_min, y_min, x_max, y_max = region

        # Create mask: white = area to regenerate
        mask = _create_face_mask((img_w, img_h), region)

        # Save image and mask to temp files for Fill model
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_img:
            img.save(tmp_img.name)
            tmp_img_path = tmp_img.name
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_mask:
            mask.save(tmp_mask.name)
            tmp_mask_path = tmp_mask.name
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_out:
            tmp_out_path = tmp_out.name

        try:
            # Load Fill model and inpaint
            generator._load_model("fill")

            gen_kwargs = dict(
                seed=seed,
                prompt=f"detailed face, sharp features, natural skin texture. {prompt}",
                num_inference_steps=steps or generator._default_steps(),
                height=img_h,
                width=img_w,
                image_path=tmp_img_path,
                masked_image_path=tmp_mask_path,
            )
            if guidance is not None:
                gen_kwargs["guidance"] = guidance

            result_image = generator._model.generate_image(**gen_kwargs)
            result_image.save(path=tmp_out_path)

            # Composite: blend inpainted face back using the feathered mask
            inpainted = Image.open(tmp_out_path).convert("RGB")
            img = Image.composite(inpainted, img, mask)
        finally:
            Path(tmp_img_path).unlink(missing_ok=True)
            Path(tmp_mask_path).unlink(missing_ok=True)
            Path(tmp_out_path).unlink(missing_ok=True)

    # Save final composited result back
    img.save(str(image_path))
    return len(faces)
