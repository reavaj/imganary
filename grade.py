"""GIMP-based photo grading pipeline — multi-stage film emulation for photorealism."""

import os
import subprocess
import tempfile
from pathlib import Path

# Preset configurations: (targeted_desat, global_desat, lift_blacks, warm_shift, grain, vignette, edge_soften)
PRESETS = {
    "minimal": {
        "targeted_desat": True,
        "global_desat": 10.0,
        "lift_blacks": 0.0,
        "warm_shift": 0,
        "grain": 0.0,
        "vignette": False,
        "edge_soften": 0.0,
    },
    "natural": {
        "targeted_desat": True,
        "global_desat": 15.0,
        "lift_blacks": 0.06,
        "warm_shift": 300,
        "grain": 0.0,
        "vignette": False,
        "edge_soften": 0.0,
    },
    "film": {
        "targeted_desat": True,
        "global_desat": 15.0,
        "lift_blacks": 0.06,
        "warm_shift": 300,
        "grain": 4.0,
        "vignette": True,
        "edge_soften": 0.4,
    },
}

# GIMP script template — multi-stage grading pipeline
# Uses string concatenation for print statements to avoid f-string / .format() conflicts
_GRADE_SCRIPT = """\
import gi
gi.require_version("Gimp", "3.0")
gi.require_version("Gegl", "0.4")
from gi.repository import Gimp, Gegl, GLib, Gio

INPUT_PATH = "{input_path}"
OUTPUT_PATH = "{output_path}"

# Grading parameters
TARGETED_DESAT = {targeted_desat}
GLOBAL_DESAT = {global_desat}
LIFT_BLACKS = {lift_blacks}
WARM_SHIFT = {warm_shift}
GRAIN = {grain}
VIGNETTE = {vignette}
EDGE_SOFTEN = {edge_soften}

file = Gio.File.new_for_path(INPUT_PATH)
image = Gimp.file_load(Gimp.RunMode.NONINTERACTIVE, file)
if image is None:
    print("ERROR: Failed to load image: " + INPUT_PATH)
else:
    drawable = image.get_layers()[0]

    # Stage 1: Targeted desaturation — pull reds/oranges/yellows down selectively
    # This kills AI-oversaturated skin tones without muting the whole image
    if TARGETED_DESAT:
        drawable.hue_saturation(Gimp.HueRange.RED, 0.0, 0.0, -20.0, 0.0)
        drawable.hue_saturation(Gimp.HueRange.YELLOW, 0.0, 0.0, -15.0, 0.0)
        print("Stage 1: targeted desat (red -20, yellow -15)")

    # Stage 2: Global desaturation — gentle overall muting
    if GLOBAL_DESAT > 0:
        drawable.hue_saturation(Gimp.HueRange.ALL, 0.0, 0.0, -GLOBAL_DESAT, 0.0)
        print("Stage 2: global desat -" + str(GLOBAL_DESAT))

    # Stage 3: Lift blacks — film fade effect (no pure blacks)
    if LIFT_BLACKS > 0:
        f = Gimp.DrawableFilter.new(drawable, "gegl:levels", "lift-blacks")
        config = f.get_config()
        config.set_property("out-low", LIFT_BLACKS)
        drawable.append_filter(f)
        drawable.merge_filter(f)
        print("Stage 3: lift blacks " + str(LIFT_BLACKS))

    # Stage 4: Warm color temperature shift — real cameras drift slightly warm
    if WARM_SHIFT > 0:
        f = Gimp.DrawableFilter.new(drawable, "gegl:color-temperature", "warm-shift")
        config = f.get_config()
        config.set_property("original-temperature", 6500.0)
        config.set_property("intended-temperature", 6500.0 + WARM_SHIFT)
        drawable.append_filter(f)
        drawable.merge_filter(f)
        print("Stage 4: warm shift +" + str(WARM_SHIFT) + "K")

    # Stage 5: Film grain — luminance noise mimicking film stock
    if GRAIN > 0:
        f = Gimp.DrawableFilter.new(drawable, "gegl:noise-hsv", "film-grain")
        config = f.get_config()
        config.set_property("holdness", 2)
        config.set_property("hue-distance", 0.0)
        config.set_property("saturation-distance", 1.0)
        config.set_property("value-distance", GRAIN)
        drawable.append_filter(f)
        drawable.merge_filter(f)
        print("Stage 5: grain " + str(GRAIN))

    # Stage 6: Subtle vignette — darkened edges
    if VIGNETTE:
        f = Gimp.DrawableFilter.new(drawable, "gegl:vignette", "vignette")
        config = f.get_config()
        config.set_property("softness", 4.0)
        config.set_property("shape", 2.0)
        drawable.append_filter(f)
        drawable.merge_filter(f)
        print("Stage 6: vignette")

    # Stage 7: Edge softening — reduce AI crispness with subtle blur
    if EDGE_SOFTEN > 0:
        f = Gimp.DrawableFilter.new(drawable, "gegl:gaussian-blur", "edge-soften")
        config = f.get_config()
        config.set_property("std-dev-x", EDGE_SOFTEN)
        config.set_property("std-dev-y", EDGE_SOFTEN)
        drawable.append_filter(f)
        drawable.merge_filter(f)
        print("Stage 7: edge soften " + str(EDGE_SOFTEN) + "px")

    image.flatten()
    out_file = Gio.File.new_for_path(OUTPUT_PATH)
    Gimp.file_save(Gimp.RunMode.NONINTERACTIVE, image, out_file)
    print("Graded successfully")
    print("Output: " + OUTPUT_PATH)
    image.delete()
"""

GIMP_CONSOLE = "/Applications/GIMP.app/Contents/MacOS/gimp-console"
GIMP_RC = os.path.expanduser("~/Library/Application Support/GIMP/3.0/batch-gimprc")


def grade_image(
    input_path: str | Path,
    output_path: str | Path | None = None,
    preset: str = "natural",
    desat_amount: float | None = None,
) -> str:
    """Apply photo grading to an image via GIMP batch mode.

    Args:
        input_path: Path to the source image.
        output_path: Where to save. Defaults to overwriting input.
        preset: Grading preset — "minimal", "natural", or "film".
        desat_amount: Override global desaturation (backward compat with --natural).

    Returns:
        Path to the graded image.
    """
    input_path = str(Path(input_path).expanduser().resolve())
    if output_path is None:
        output_path = input_path
    else:
        output_path = str(Path(output_path).expanduser().resolve())

    # Load preset config
    config = dict(PRESETS.get(preset, PRESETS["natural"]))

    # Backward compat: --natural 50 overrides global_desat
    if desat_amount is not None:
        config["global_desat"] = desat_amount

    script_content = _GRADE_SCRIPT.format(
        input_path=input_path,
        output_path=output_path,
        targeted_desat=config["targeted_desat"],
        global_desat=config["global_desat"],
        lift_blacks=config["lift_blacks"],
        warm_shift=config["warm_shift"],
        grain=config["grain"],
        vignette=config["vignette"],
        edge_soften=config["edge_soften"],
    )

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", prefix="imganary_grade_", delete=False
    ) as f:
        f.write(script_content)
        script_path = f.name

    try:
        cmd = [
            GIMP_CONSOLE,
            "-n", "-i", "--no-data", "--quit",
            f"--gimprc={GIMP_RC}",
            "--batch-interpreter=python-fu-eval",
            "-b", f"exec(open('{script_path}').read())",
        ]
        env = {**os.environ, "LSBackgroundOnly": "1"}
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120, env=env
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"GIMP grading failed (exit {result.returncode}): {result.stderr}"
            )
    finally:
        Path(script_path).unlink(missing_ok=True)

    return output_path
