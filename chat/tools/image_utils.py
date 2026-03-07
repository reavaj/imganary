import base64
from pathlib import Path

from PIL import Image

MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
    ".tiff": "image/tiff",
    ".tif": "image/tiff",
}


def guess_media_type(path: str) -> str:
    ext = Path(path).suffix.lower()
    return MEDIA_TYPES.get(ext, "image/png")


def encode_image_base64(path: str) -> str:
    return base64.b64encode(Path(path).read_bytes()).decode()


def get_image_info(image_path: str) -> dict:
    p = Path(image_path)
    if not p.exists():
        return {"error": f"File not found: {image_path}"}
    with Image.open(p) as img:
        return {
            "width": img.width,
            "height": img.height,
            "format": img.format,
            "mode": img.mode,
            "file_size_mb": round(p.stat().st_size / (1024 * 1024), 2),
        }
