#!/usr/bin/env python3
"""Trace a raster image into smooth vector-style line art.

Usage:
    ./trace.py <image_path> [options]

Examples:
    # Full pipeline: photo → edge detect → smooth trace
    ./trace.py ~/Desktop/photo.jpg

    # Already line art — skip edge detection, just smooth it
    ./trace.py ~/Desktop/lines.png --no-edges

    # Tweak parameters
    ./trace.py ~/Desktop/photo.jpg --blur 5 --threshold 180 --canny-low 30 --canny-high 100

Pipeline:
    1. (optional) Canny edge detection → black-on-white line art
    2. Gaussian blur to soften jagged pixels
    3. Re-threshold to crisp B&W
    4. Potrace → smooth bezier SVG
    5. Inkscape → PNG at original resolution
"""

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def trace_image(
    image_path: str,
    output_path: str | None = None,
    skip_edges: bool = False,
    blur_radius: float = 3.0,
    threshold: int = 200,
    canny_low: int = 20,
    canny_high: int = 80,
    dilate: int = 2,
    turd_size: int = 25,
    keep_svg: bool = False,
) -> str:
    """Trace a raster image into smooth vector-style line art.

    Args:
        image_path: Path to the input image.
        output_path: Where to save the result. Defaults to <name>_traced.png.
        skip_edges: If True, skip edge detection (input is already line art).
        blur_radius: Gaussian blur radius before tracing (higher = smoother).
        threshold: Brightness threshold for B&W conversion (0-255).
        canny_low: Canny edge detection low threshold.
        canny_high: Canny edge detection high threshold.
        dilate: Dilation iterations to thicken edge lines (0 = none).
        turd_size: Potrace turd suppression — removes speckles smaller than this.
        keep_svg: If True, also save the intermediate SVG.

    Returns:
        Path to the saved PNG.
    """
    import cv2
    import numpy as np
    from PIL import Image, ImageFilter

    image_path = str(Path(image_path).expanduser())
    if not Path(image_path).is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")

    p = Path(image_path)
    if output_path is None:
        output_path = str(p.parent / f"{p.stem}_traced.png")
    else:
        output_path = str(Path(output_path).expanduser())

    svg_path = str(Path(output_path).with_suffix(".svg"))

    # Load image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
    h, w = img.shape[:2]
    print(f"Input: {w}x{h}")

    if skip_edges:
        # Input is already line art — convert to grayscale
        print("Skipping edge detection (--no-edges)")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        # Invert if lines are dark on light (potrace traces black regions)
        # Check if image is mostly white (line art on white bg)
        if np.mean(gray) > 128:
            bw = gray  # already light bg, dark lines — will threshold below
        else:
            bw = 255 - gray
    else:
        # Edge detection pipeline
        print("Extracting edges (Canny)...")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Double bilateral filter to smooth while preserving edges
        smooth = cv2.bilateralFilter(gray, 9, 75, 75)
        smooth = cv2.bilateralFilter(smooth, 9, 75, 75)
        # Canny edge detection
        edges = cv2.Canny(smooth, canny_low, canny_high)
        # Dilate to thicken lines
        if dilate > 0:
            kernel = np.ones((3, 3), np.uint8)
            edges = cv2.dilate(edges, kernel, iterations=dilate)
        # Invert: black lines on white background
        bw = 255 - edges

    # Convert to PIL for blur + threshold + potrace input
    pil_img = Image.fromarray(bw).convert("L")

    # Gaussian blur to soften jagged edges
    if blur_radius > 0:
        print(f"Softening edges (blur radius={blur_radius})...")
        pil_img = pil_img.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    # Threshold to crisp black and white
    pil_bw = pil_img.point(lambda p: 0 if p < threshold else 255, "1")

    # Save as PBM for potrace
    with tempfile.NamedTemporaryFile(suffix=".pbm", delete=False) as f:
        pbm_path = f.name
    pil_bw.save(pbm_path)

    # Potrace: bitmap → smooth SVG
    print("Tracing to smooth vectors (potrace)...")
    potrace = "/usr/local/bin/potrace"
    if not Path(potrace).is_file():
        potrace = "potrace"  # try PATH

    result = subprocess.run(
        [potrace, "-s", "-t", str(turd_size), "-a", "4.19", "-O", "2.0",
         "-o", svg_path, pbm_path],
        capture_output=True, text=True,
    )
    os.unlink(pbm_path)
    if result.returncode != 0:
        raise RuntimeError(f"potrace failed: {result.stderr}")

    # Inkscape: SVG → PNG at original resolution
    print(f"Rendering to PNG ({w}x{h})...")
    inkscape = "/opt/homebrew/bin/inkscape"
    if not Path(inkscape).is_file():
        inkscape = "inkscape"  # try PATH

    result = subprocess.run(
        [inkscape, svg_path, "--export-type=png",
         f"--export-filename={output_path}",
         f"--export-width={w}", f"--export-height={h}"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"inkscape failed: {result.stderr}")

    if not keep_svg:
        os.unlink(svg_path)

    print(f"Saved: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Trace a raster image into smooth vector-style line art.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  ./trace.py ~/Desktop/photo.jpg\n"
            "  ./trace.py ~/Desktop/lines.png --no-edges\n"
            "  ./trace.py ~/Desktop/photo.jpg --blur 5 --threshold 180\n"
            "  ./trace.py ~/Desktop/photo.jpg --keep-svg"
        ),
    )
    parser.add_argument("image", help="Path to the input image")
    parser.add_argument("--output", "-o", help="Output path (default: <name>_traced.png)")
    parser.add_argument("--no-edges", action="store_true",
                        help="Skip edge detection (input is already line art)")
    parser.add_argument("--blur", type=float, default=3.0,
                        help="Gaussian blur radius before tracing (default: 3.0)")
    parser.add_argument("--threshold", type=int, default=200,
                        help="B&W threshold 0-255 (default: 200)")
    parser.add_argument("--canny-low", type=int, default=20,
                        help="Canny low threshold (default: 20)")
    parser.add_argument("--canny-high", type=int, default=80,
                        help="Canny high threshold (default: 80)")
    parser.add_argument("--dilate", type=int, default=2,
                        help="Line dilation iterations (default: 2, 0=none)")
    parser.add_argument("--turd", type=int, default=25,
                        help="Speckle removal size in pixels (default: 25)")
    parser.add_argument("--keep-svg", action="store_true",
                        help="Keep the intermediate SVG file")

    args = parser.parse_args()

    try:
        trace_image(
            image_path=args.image,
            output_path=args.output,
            skip_edges=args.no_edges,
            blur_radius=args.blur,
            threshold=args.threshold,
            canny_low=args.canny_low,
            canny_high=args.canny_high,
            dilate=args.dilate,
            turd_size=args.turd,
            keep_svg=args.keep_svg,
        )
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
