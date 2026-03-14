#!/usr/bin/env python3
"""Composite a segmented foreground subject onto a background image.

Usage:
    ./composite.py <foreground.png> <background.jpg> [--output path.png]
        [--x N] [--y N] [--scale N]

The foreground must be a PNG with transparency (from segment.py).
The result is sized to match the background image.

Workflow:
    ./segment.py ~/Desktop/subject.jpg
    ./composite.py ~/Desktop/subject_segmented.png ~/Desktop/background.jpg
    ./imagine.py "the scene" --image ~/Desktop/composite.png --strength 0.3 --hd
"""

import sys
from pathlib import Path


def composite(
    foreground_path: str,
    background_path: str,
    output_path: str | None = None,
    x: int | None = None,
    y: int | None = None,
    scale: float = 1.0,
) -> str:
    """Paste a transparent foreground onto a background image.

    Args:
        foreground_path: Path to the RGBA PNG (from segment.py).
        background_path: Path to the background image.
        output_path: Where to save. Defaults to ~/Desktop/composite.png.
        x: Horizontal position of foreground center. Defaults to center.
        y: Vertical position of foreground bottom. Defaults to bottom.
        scale: Scale factor for the foreground (1.0 = original size).

    Returns:
        Path to the saved composite image.
    """
    from PIL import Image

    fg_path = str(Path(foreground_path).expanduser())
    bg_path = str(Path(background_path).expanduser())

    if not Path(fg_path).is_file():
        raise FileNotFoundError(f"Foreground not found: {fg_path}")
    if not Path(bg_path).is_file():
        raise FileNotFoundError(f"Background not found: {bg_path}")

    if output_path is None:
        output_path = str(Path("~/Desktop/composite.png").expanduser())
    else:
        output_path = str(Path(output_path).expanduser())

    bg = Image.open(bg_path).convert("RGBA")
    fg = Image.open(fg_path).convert("RGBA")
    bg_w, bg_h = bg.size

    # Crop foreground to its bounding box (trim transparent edges)
    bbox = fg.getbbox()
    if bbox is None:
        raise ValueError("Foreground image is fully transparent — nothing to composite.")
    fg = fg.crop(bbox)

    # Scale foreground
    if scale != 1.0:
        new_w = int(fg.width * scale)
        new_h = int(fg.height * scale)
        fg = fg.resize((new_w, new_h), Image.Resampling.LANCZOS)

    fg_w, fg_h = fg.size

    # Default position: centered horizontally, bottom-aligned
    if x is None:
        x = (bg_w - fg_w) // 2
    else:
        x = x - fg_w // 2  # x is center position
    if y is None:
        y = bg_h - fg_h
    else:
        y = y - fg_h  # y is bottom position

    # Composite using alpha channel
    result = bg.copy()
    result.paste(fg, (x, y), fg)

    # Save as RGB (flatten alpha onto white or keep the background)
    result_rgb = Image.new("RGB", bg.size, (0, 0, 0))
    result_rgb.paste(result, mask=result.split()[3])
    # Actually, just flatten properly — paste background then foreground
    result_flat = Image.new("RGB", bg.size)
    bg_rgb = Image.open(bg_path).convert("RGB")
    result_flat.paste(bg_rgb, (0, 0))
    result_flat.paste(fg, (x, y), fg)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    result_flat.save(output_path)

    print(f"Foreground: {fg_w}x{fg_h} (scale {scale}x)")
    print(f"Background: {bg_w}x{bg_h}")
    print(f"Position:   ({x}, {y})")
    print(f"Saved to:   {output_path}")
    return output_path


def main():
    if len(sys.argv) < 3:
        print(
            "Usage: ./composite.py <foreground.png> <background.jpg> [options]\n\n"
            "Options:\n"
            "  --output path.png   Output path (default: ~/Desktop/composite.png)\n"
            "  --x N               Horizontal center position (default: centered)\n"
            "  --y N               Vertical bottom position (default: bottom-aligned)\n"
            "  --scale N           Scale foreground (default: 1.0)\n\n"
            "Workflow:\n"
            "  ./segment.py ~/Desktop/subject.jpg\n"
            "  ./composite.py ~/Desktop/subject_segmented.png ~/Desktop/background.jpg\n"
            "  ./imagine.py \"the scene\" --image ~/Desktop/composite.png --strength 0.3 --hd"
        )
        sys.exit(1)

    foreground = sys.argv[1]
    background = sys.argv[2]

    def _flag(name: str, default=None):
        if name in sys.argv:
            idx = sys.argv.index(name)
            if idx + 1 < len(sys.argv):
                return sys.argv[idx + 1]
        return default

    output = _flag("--output")
    x = _flag("--x")
    y = _flag("--y")
    scale = float(_flag("--scale", "1.0") or "1.0")

    try:
        composite(
            foreground,
            background,
            output_path=output,
            x=int(x) if x else None,
            y=int(y) if y else None,
            scale=scale,
        )
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
