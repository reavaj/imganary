#!/usr/bin/env bash
# Generate 20 background-frame images across diverse styles for compositing
# Mix of symmetrical, asymmetrical, and varied compositions

PROMPTS=(
  # Earth tones & retro
  "Flat vector illustration in a groovy 1970s graphic design style. Overlapping circles, arcs, and sunburst rays filling the canvas asymmetrically, heavier on the left with a diagonal sweep of harvest gold across the frame. Burnt sienna, avocado green, chocolate brown, warm cream. Screen-printed texture with slight ink bleed. No figures, no text."
  "Art deco gold and black geometric background. Symmetrical ornate gilded fan patterns and stepped arches radiating outward from center. Rich black field with deep charcoal gradation. Gold leaf texture on decorative elements. Roaring twenties luxury. No figures, no text."
  "Warm terracotta and clay-toned abstract background. Organic curved shapes and earth-pigment washes sweeping diagonally from bottom-left to upper-right. Visible paper grain throughout. Mediterranean pottery palette — ochre, sienna, umber, dusty rose. No figures, no text."

  # Cool & moody
  "Cyberpunk neon cityscape background. Towering buildings and holographic signage dominating the left half, rain-slicked street reflections stretching across the bottom. Diffused neon glow in teal and magenta. Misty atmosphere softening the right side. Blade Runner mood. No figures, no text."
  "Deep ocean underwater background. Coral formations and kelp fronds rising from the bottom edge, bioluminescent organisms drifting throughout. Blue-green water with shafts of filtered sunlight angling from above. No figures, no text."
  "Northern lights aurora borealis background. Sweeping green and violet curtains of light arcing symmetrically across the sky like a cathedral ceiling. Dark starfield above. Snow-covered treeline silhouettes along the bottom third. No figures, no text."

  # Organic & natural
  "Watercolor botanical garden background. Lush tropical leaves and orchids cascading from the top-right corner, hanging vines trailing down the right edge. Wet-on-wet technique with paint bleeds and visible brushstrokes. Warm diffused light washing across the left side. No figures, no text."
  "Autumn forest canopy background. Branches heavy with amber, crimson, and gold leaves forming a canopy overhead framing the sky. Dappled golden light filtering through gaps. Oil painting texture with visible impasto throughout. No figures, no text."
  "Japanese zen garden background. Raked sand patterns flowing diagonally. Moss-covered stones and a bonsai clustered in the lower-right third. Muted greens, warm grays, cream. Ukiyo-e woodblock aesthetic with visible grain. No figures, no text."

  # Architectural & geometric
  "Gothic cathedral interior background. Symmetrical stone arches and ribbed vaulting soaring overhead, stained glass windows glowing on both sides. Warm candlelight and deep shadows creating dramatic depth. Looking straight down the nave. No figures, no text."
  "Brutalist concrete architecture background. Massive textured concrete forms creating geometric shadows, weight concentrated on the right side. Overcast diffused light. Raw gray concrete with weathering, water stains, and exposed aggregate. No figures, no text."
  "Moroccan tilework zellige mosaic background. Intricate geometric star patterns in cobalt blue, turquoise, saffron, and white filling the entire surface in a symmetrical mandala arrangement. Handcrafted ceramic texture with slight irregularity. No figures, no text."

  # Psychedelic & bold
  "Psychedelic concert poster background. Swirling organic patterns, paisley, and fractal forms in Day-Glo neon orange, electric purple, hot pink. Asymmetrical spiral composition radiating from the lower-left corner. Art Nouveau flowing lines filling the canvas. No figures, no text."
  "Pop art halftone background. Bold Ben-Day dots in primary red, yellow, blue, black. Diagonal composition — dense large dots in the upper-right dissolving to tiny sparse dots toward lower-left. Silk-screen printing aesthetic with color registration offset. No figures, no text."
  "Vaporwave aesthetic background. Retro grid receding symmetrically to a central horizon vanishing point. Pastel pink, cyan, and lavender palette. Chrome sun centered on the horizon. Palm silhouettes flanking both sides. Dreamy soft atmosphere. No figures, no text."

  # Texture & material
  "Steampunk brass and copper machinery background. Gears, pipes, pressure gauges, and riveted panels filling the bottom two-thirds. Warm amber light from gas lamps on the left. Steam and soft bokeh drifting upward. Burnished metal patina texture throughout. No figures, no text."
  "Stained glass cathedral window background. Jewel-toned glass panels in deep ruby, emerald, sapphire, and amber in a symmetrical rose window pattern. Lead came lines between pieces. Bright backlight streaming through, casting colored light. No figures, no text."
  "Vintage parchment and ink background. Aged yellowed paper with foxing marks and torn edges. Ornate hand-drawn botanical illustrations and filigree concentrated along the bottom and right edge, sparser toward upper-left. Sepia and iron gall ink tones. No figures, no text."

  # Abstract & painterly
  "Abstract expressionist background. Bold gestural brushstrokes and paint splatters in crimson, cobalt, and titanium white. Diagonal energy sweeping from lower-left to upper-right. Raw canvas showing through in patches. Franz Kline meets Joan Mitchell. No figures, no text."
  "Impressionist garden at golden hour background. Thick dabs of oil paint forming flowers, hedges, and a winding garden path receding into warm hazy distance. Monet palette of lavender, warm green, pale gold. Visible impasto texture throughout. Soft light suffusing the entire scene. No figures, no text."
)

echo "=== Generating 20 background frames ==="
echo ""

for i in "${!PROMPTS[@]}"; do
  num=$((i + 1))
  echo "--- Background $num/20 ---"
  ./imagine.py "${PROMPTS[$i]}" --hd --raw
  echo ""
done

echo "=== Done: 20 backgrounds generated ==="
