#!/bin/bash
# Generate 9 diverse portraits — varying age, gender, attractiveness
# Uses photo intent auto-detection (dev model + RealismLora + guidance 2.5)

set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DIR=~/Desktop/portraits_${TIMESTAMP}
mkdir -p "$DIR"

echo "=== Generating 9 portraits to $DIR ==="
echo

prompts=(
  "photograph of a weathered 70-year-old fisherman with deep wrinkles, sun-damaged skin, missing tooth, kind eyes"
  "photograph of a plain 40-year-old woman at a bus stop, tired eyes, no makeup, frizzy hair, slightly overweight"
  "photograph of a strikingly handsome 30-year-old man with sharp jawline, perfect stubble, confident smirk"
  "photograph of an 85-year-old grandmother with wispy white hair, age spots, thick glasses, warm gentle smile"
  "photograph of an average-looking 25-year-old woman with acne scars, crooked nose, messy ponytail, genuine laugh"
  "photograph of a beautiful 35-year-old woman with high cheekbones, freckles, green eyes, windswept auburn hair"
  "photograph of a pudgy 50-year-old man with receding hairline, double chin, reading glasses, patchy beard"
  "photograph of a gorgeous 28-year-old man with dark skin, bright white smile, athletic build, gold chain"
  "photograph of a 60-year-old woman with silver pixie cut, laugh lines, no-nonsense expression, weathered hands"
)

for i in "${!prompts[@]}"; do
  n=$((i + 1))
  echo "--- Portrait $n/9 ---"
  ./imagine.py "${prompts[$i]}" \
    --portrait \
    --output "$DIR/portrait_${n}.png"
  echo
  if [ $n -lt 9 ]; then
    echo "Cooling down 90s..."
    sleep 90
  fi
done

echo "=== Done. Portraits saved to $DIR ==="
