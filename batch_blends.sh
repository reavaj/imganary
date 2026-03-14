#!/usr/bin/env bash
# Generate 5 random 50/50 blends from the bkg folder with vector graphic futurism prompt

BKG_DIR=~/Desktop/bkg
FILES=($(ls "$BKG_DIR"/*.png | sort -R))

echo "=== Generating 5 random blends ==="
echo ""

for i in $(seq 0 4); do
  # Pick two different random images
  idx1=$((RANDOM % ${#FILES[@]}))
  idx2=$((RANDOM % ${#FILES[@]}))
  while [ "$idx2" -eq "$idx1" ]; do
    idx2=$((RANDOM % ${#FILES[@]}))
  done

  img1="${FILES[$idx1]}"
  img2="${FILES[$idx2]}"

  num=$((i + 1))
  echo "--- Blend $num/5 ---"
  echo "  Image 1: $(basename "$img1")"
  echo "  Image 2: $(basename "$img2")"
  ./imagine.py "Abstract lyrical composition, flowing non-representational forms dissolving into each other, no recognizable objects no buildings no landscapes no figures, pure color fields and organic geometry merging, tension between structure and entropy, chromatic resonance and spatial ambiguity" --image "$img1" --image2 "$img2" --strength 0.8 --hd --raw
  echo ""
done

echo "=== Done: 5 blends generated ==="
