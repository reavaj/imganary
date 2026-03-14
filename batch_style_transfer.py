#!/usr/bin/env python3
"""Batch style transfer — random clips x random styles x creative prompts."""

import os
import random
import subprocess
import sys
from pathlib import Path

CLIPS_DIR = Path("/Users/reavaj/Desktop/clips")
STYLES_DIR = Path("/Users/reavaj/Documents/photo2024")
OUTPUT_DIR = Path("~/Desktop/style_batch").expanduser()
OUTPUT_DIR.mkdir(exist_ok=True)

STYLE_STRENGTH = 0.2
NUM_IMAGES = 20

# Creative prompts — wild, cinematic, atmospheric
PROMPTS = [
    "a cathedral made of frozen lightning, interior shot, stained glass refracting prismatic light across marble floors",
    "underwater ballroom where jellyfish waltz in formation, bioluminescent chandeliers, teal and violet",
    "a lone astronaut sitting on a park bench on Mars, reading a newspaper, dust storm in the distance",
    "enormous mechanical owl perched on a crumbling art deco skyscraper, copper patina, sunset",
    "a kitchen where all the food is alive and having a heated argument, dramatic chiaroscuro lighting",
    "forest of giant mushrooms with a tiny village built into the stems, morning fog, warm amber light",
    "an old woman playing chess against her younger self in a mirror, baroque interior, candlelight",
    "a whale swimming through clouds above a sleeping city, moonlit, ethereal silver and deep blue",
    "abandoned carnival at the edge of the sea, ferris wheel half-submerged, golden hour",
    "a violinist performing on a rooftop during a thunderstorm, rain-soaked, dramatic backlighting",
    "library where the books are flying off shelves and forming a tornado of pages, warm lamplight",
    "a fox wearing a tiny top hat serving tea to a bear in a snow-covered garden, absurdist Victorian",
    "crystal cave with a underground lake reflecting impossible constellations, turquoise and amethyst",
    "two samurai facing each other across a field of red spider lilies, pre-dawn mist, cinematic",
    "a street musician's saxophone notes becoming visible as golden ribbons flowing through a rainy alley",
    "enormous tree growing through the center of an abandoned cathedral, roots cracking stone, green light filtering through leaves",
    "a child discovering a door in the trunk of an ancient oak tree, fireflies everywhere, twilight",
    "decaying space station orbiting a gas giant, interior overgrown with alien vegetation, shafts of distant sunlight",
    "a painter's studio where the paintings have come to life and are painting the painter, recursive, warm ochre",
    "market stall selling bottled emotions on a cobblestone street, each bottle glows a different color, dusk",
    "a grand piano on a cliff edge overlooking a stormy ocean, single spotlight from above, dramatic",
    "robot grandmother knitting a scarf made of fiber optic cables, cozy living room, warm tungsten light",
    "a bridge between two mountains made entirely of books, tiny figures crossing, epic scale, misty",
    "venetian masquerade ball but all the guests are animals in elaborate costumes, candlelit palazzo",
    "a greenhouse on the moon, earth visible through the glass ceiling, plants thriving in alien light",
]

# Filter to usable image types
STYLE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
style_files = [f for f in STYLES_DIR.iterdir() if f.suffix.lower() in STYLE_EXTENSIONS]
clip_files = [f for f in CLIPS_DIR.iterdir() if f.suffix.lower() in STYLE_EXTENSIONS]

if not clip_files:
    print("No usable images in clips folder")
    sys.exit(1)
if not style_files:
    print("No usable images in styles folder")
    sys.exit(1)

print(f"Clips: {len(clip_files)} | Styles: {len(style_files)} | Prompts: {len(PROMPTS)}")
print(f"Generating {NUM_IMAGES} images with style strength {STYLE_STRENGTH}")
print(f"Output: {OUTPUT_DIR}")
print()

for i in range(NUM_IMAGES):
    clip = random.choice(clip_files)
    style = random.choice(style_files)
    prompt = random.choice(PROMPTS)
    seed = random.randint(0, 2**32 - 1)

    output_name = f"styled_{i+1:02d}_s{seed}.png"
    output_path = OUTPUT_DIR / output_name

    print(f"[{i+1}/{NUM_IMAGES}] {prompt[:60]}...")
    print(f"  Style: {style.name}")
    print(f"  Seed:  {seed}")

    cmd = [
        sys.executable, "imagine.py", prompt,
        "--style-image", str(style),
        "--style-strength", str(STYLE_STRENGTH),
        "--hd", "--raw",
        "--seed", str(seed),
        "--output", str(output_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"  ERROR: {result.stderr.strip()[-200:]}")
        # Print stdout too for our error messages
        for line in result.stdout.strip().split("\n")[-3:]:
            print(f"  {line}")
    else:
        # Extract timing from output
        for line in result.stdout.strip().split("\n"):
            if "Generated" in line or "Saved to" in line:
                print(f"  {line}")
    print()

print(f"Done. {NUM_IMAGES} images saved to {OUTPUT_DIR}")
