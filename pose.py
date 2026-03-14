#!/usr/bin/env python3
"""Extract a pose skeleton from an image using OpenPose.

Usage:
    ./pose.py <image_path> [--output path.png] [--width N] [--height N]

The output pose skeleton can be fed directly to imagine.py via --pose-image:
    ./pose.py ~/Desktop/dancer.jpg
    ./imagine.py "dancer in neon light" --pose-image ~/Desktop/dancer_pose.png --hd

For portrait shots, match the target dimensions:
    ./pose.py ~/Desktop/dancer.jpg --width 768 --height 1152
    ./imagine.py "dancer in neon light" --pose-image ~/Desktop/dancer_pose.png --portrait
"""

import os
import sys
import warnings
from pathlib import Path

# Suppress noisy library warnings
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_DISABLE_EXPERIMENTAL_WARNING"] = "1"
os.environ["DO_NOT_TRACK"] = "1"
warnings.filterwarnings("ignore")


def extract_pose(
    image_path: str,
    output_path: str | None = None,
    width: int = 1024,
    height: int = 1024,
) -> str:
    """Extract pose skeleton from an image using OpenPose.

    Args:
        image_path: Path to the input image containing a person.
        output_path: Where to save the pose skeleton. Defaults to <name>_pose.png.
        width: Width of the output skeleton image.
        height: Height of the output skeleton image.

    Returns:
        Path to the saved pose skeleton image.
    """
    import numpy as np
    from controlnet_aux import OpenposeDetector
    from PIL import Image

    image_path = str(Path(image_path).expanduser())
    if not Path(image_path).is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")

    if output_path is None:
        p = Path(image_path)
        output_path = str(p.parent / f"{p.stem}_pose.png")
    else:
        output_path = str(Path(output_path).expanduser())

    print("Loading OpenPose detector (first run downloads model weights)...")
    detector = OpenposeDetector.from_pretrained("lllyasviel/ControlNet")

    print(f"Detecting pose in: {image_path}")
    input_image = Image.open(image_path).convert("RGB")

    # Detect at the larger dimension for accuracy, then resize to target
    detect_resolution = max(width, height)
    pose_image = detector(
        input_image,
        detect_resolution=detect_resolution,
        image_resolution=detect_resolution,
    )

    # Resize to exact target dimensions
    if pose_image.size != (width, height):
        pose_image = pose_image.resize((width, height), Image.Resampling.LANCZOS)

    # Check if any pose was actually detected (non-black pixels)
    arr = np.array(pose_image)
    if arr.max() == 0:
        print("Warning: No human pose detected — image may not contain a person.")
        print("OpenPose only detects human body poses.")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    pose_image.save(output_path)
    print(f"Pose skeleton saved to: {output_path} ({width}x{height})")
    return output_path


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: ./pose.py <image_path> [--output path.png] "
            "[--width N] [--height N]\n\n"
            "Extract a pose skeleton, then use it with imagine.py:\n"
            "  ./pose.py ~/Desktop/dancer.jpg\n"
            "  ./imagine.py \"dancer in neon light\" --pose-image ~/Desktop/dancer_pose.png --hd\n\n"
            "For portrait shots, match dimensions:\n"
            "  ./pose.py ~/Desktop/dancer.jpg --width 768 --height 1152\n"
            "  ./imagine.py \"dancer\" --pose-image ~/Desktop/dancer_pose.png --portrait"
        )
        sys.exit(1)

    image_path = sys.argv[1]

    def _flag(name: str, default=None):
        if name in sys.argv:
            idx = sys.argv.index(name)
            if idx + 1 < len(sys.argv):
                return sys.argv[idx + 1]
        return default

    output = _flag("--output")
    width = int(_flag("--width", "1024") or "1024")
    height = int(_flag("--height", "1024") or "1024")

    try:
        extract_pose(image_path, output, width, height)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
