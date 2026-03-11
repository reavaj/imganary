#!/bin/bash
# Batch generate: 20 line art drawings of varied subjects
# Using schnell for speed since these are stylistic, not photorealistic

set -e
cd "$(dirname "$0")"
source .venv/bin/activate

COUNT=0
TOTAL=20

run() {
    COUNT=$((COUNT + 1))
    echo ""
    echo "=== [$COUNT/$TOTAL] ==="
    echo "y" | ./imagine.py "$1" --model schnell --hd
    if [ $COUNT -lt $TOTAL ]; then
        echo "Cooling down (60s)..."
        sleep 60
    fi
}

# --- Animals ---
run "line art drawing of a heron standing in shallow water, single continuous ink line, minimal detail, white background"
run "line art illustration of a fox curling up to sleep, delicate pen strokes, botanical border, white background"
run "line art octopus with tentacles flowing across the page, fine crosshatching on the body, white background"

# --- People ---
run "line art portrait of an elderly man with deep wrinkles, expressive single-weight ink line, white background"
run "line art drawing of a dancer mid-leap, fluid gestural lines, minimal detail, white background"
run "line art sketch of two hands clasped together, anatomical detail in the tendons, white background"

# --- Architecture ---
run "line art drawing of a Japanese temple gate, precise architectural lines, slight ink wash shadow, white background"
run "line art illustration of a crumbling stone archway overgrown with ivy, fine pen detail, white background"
run "line art cityscape of rooftops and water towers, loose sketchy style, white background"

# --- Nature ---
run "line art botanical illustration of a monstera leaf, clean vector-weight lines, scientific precision, white background"
run "line art drawing of a gnarled old oak tree, detailed bark texture in crosshatch, white background"
run "line art mountain landscape with a winding river, varying line weight from thick foreground to thin distance, white background"

# --- Objects ---
run "line art drawing of a vintage bicycle, technical illustration style, precise mechanical detail, white background"
run "line art still life of a wine bottle and two glasses, single continuous contour line, white background"
run "line art illustration of an old rotary telephone, crosshatched shadows, retro feel, white background"

# --- Fantastical ---
run "line art drawing of a dragon coiled around a tower, intricate scale detail, medieval manuscript style, white background"
run "line art illustration of a lighthouse in a storm, dramatic wave lines, woodcut inspired, white background"

# --- Patterns & Abstract ---
run "line art mandala pattern, geometric and organic forms intertwined, ultra-fine pen detail, white background"
run "line art drawing of a human skull transforming into flowers, stipple shading, memento mori style, white background"
run "line art map of an imaginary island, cartographic style with sea monsters and compass rose, white background"

echo ""
echo "=== Done! Generated $TOTAL images ==="
