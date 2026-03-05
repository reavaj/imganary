#!/usr/bin/env python3
"""Analyze an image using all vision models and print a report."""

import contextlib
import logging
import os
import sys
import warnings
from pathlib import Path

# Suppress noisy library warnings before any imports
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
os.environ["HF_HUB_DISABLE_EXPERIMENTAL_WARNING"] = "1"
os.environ["DO_NOT_TRACK"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["ULTRALYTICS_VERBOSE"] = "false"
warnings.filterwarnings("ignore")
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("ultralytics").setLevel(logging.ERROR)

# Pre-create loggers at WARNING before models package initializes them with handlers
for _name in ("imganary.llava", "imganary.yolo", "imganary.clip"):
    logging.getLogger(_name).setLevel(logging.WARNING)

from models import create_analyzer, AnalyzerType
from models.config import ModelSettings


def _suppress_stderr():
    """Context manager to silence stderr (for noisy C-level library warnings)."""
    return contextlib.redirect_stderr(open(os.devnull, "w"))


def main():
    if len(sys.argv) < 2:
        print("Usage: ./analyze.py <image_path> [--model llava|yolo|clip]")
        sys.exit(1)

    image_path = sys.argv[1]
    if not Path(image_path).is_file():
        print(f"Error: File not found: {image_path}")
        sys.exit(1)

    # Optional: run a single model
    selected = None
    if "--model" in sys.argv:
        idx = sys.argv.index("--model")
        if idx + 1 < len(sys.argv):
            selected = sys.argv[idx + 1].lower()

    models_to_run = (
        [AnalyzerType(selected)] if selected else list(AnalyzerType)
    )

    settings = ModelSettings(llava_timeout_seconds=300)
    print(f"Analyzing: {image_path}\n")

    for model_type in models_to_run:
        print(f"{'=' * 50}")
        print(f"  {model_type.value.upper()}")
        print(f"{'=' * 50}")

        try:
            analyzer = create_analyzer(model_type, settings)
            with _suppress_stderr():
                result = analyzer.analyze(image_path)

            if result.error:
                print(f"  Error: {result.error}")
            elif result.scene_description:
                print(f"  {result.scene_description.description}")
            elif result.detected_objects is not None:
                if not result.detected_objects:
                    print("  No objects detected")
                for obj in result.detected_objects:
                    print(
                        f"  {obj.label}: {obj.confidence:.0%}"
                        f"  [{obj.bounding_box.x_min:.0f},"
                        f"{obj.bounding_box.y_min:.0f},"
                        f"{obj.bounding_box.x_max:.0f},"
                        f"{obj.bounding_box.y_max:.0f}]"
                    )
            elif result.semantic_matches:
                for match in result.semantic_matches:
                    bar = "#" * int(match.score * 30)
                    print(f"  {match.label:>12}: {bar} {match.score:.1%}")
            else:
                print("  No results")

            print(f"\n  Time: {result.processing_time_ms:.0f}ms")
        except Exception as e:
            print(f"  Error: {e}")

        print()


if __name__ == "__main__":
    main()
