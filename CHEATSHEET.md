# imagine.py Cheat Sheet

## Basic Usage

```bash
./imagine.py "a rabbit on a mountain"              # 512x512, schnell (fast)
./imagine.py "a rabbit on a mountain" --hd          # 1024x1024
./imagine.py "a rabbit on a mountain" --portrait    # 768x1152 (vertical)
```

## Models

| Flag | Model | Speed | Notes |
|------|-------|-------|-------|
| *(default)* | FLUX.1-schnell | ~83s | 4 steps, no guidance support |
| `--model dev` | FLUX.1-dev | ~45-90s | 25 steps, higher quality, supports guidance + LoRA |

Photo keywords in the vibe ("photo", "photograph", "photorealistic") auto-switch to dev with RealismLora + guidance 2.5.

## Flags Reference

| Flag | Default | Description |
|------|---------|-------------|
| `--hd` | — | 1024x1024 output |
| `--portrait` | — | 768x1152 vertical output |
| `--model dev\|schnell` | `schnell` | Which FLUX model to use |
| `--steps N` | 4 (schnell) / 25 (dev) | Inference steps |
| `--seed N` | random | Reproducible seed |
| `--guidance N` | 3.5 (dev) | CFG scale (dev only) |
| `--lora path` | — | LoRA weights (HF repo ID or local path) |
| `--width N` | 512 | Output width |
| `--height N` | 512 | Output height |
| `--output path` | `~/Desktop/flux_*.png` | Output file path |
| `--raw` | — | Skip Gemini prompt expansion, use vibe verbatim |
| `--style-image path` | — | Style reference image (auto-selects IP-Adapter engine) |
| `--style-image2 path` | — | Second style reference for dual fusion |
| `--style-strength N` | `0.7` | Style influence (0.0–1.0) |
| `--pose-image path` | — | Pose skeleton image (auto-selects pose ControlNet) |
| `--pose-strength N` | `0.8` | Pose adherence (0.0–1.0) |
| `--image path` | — | Img2img reference image |
| `--image2 path` | — | Second image for 50/50 pixel blend with --image |
| `--strength N` | `0.5` | Img2img strength (0.0–1.0) |
| `--grade preset` | — | GIMP grading: `minimal`, `natural`, `film` |
| `--natural [N]` | — | Shorthand for --grade natural (optional desat %) |

## LoRAs (Cached & Ready)

| LoRA | HF Repo ID | Use For |
|------|-----------|---------|
| **RealismLora** | `XLabs-AI/flux-RealismLora` | Photorealistic output (auto-applied for photo vibes) |
| **Koda** | `alvdansen/flux-koda` | Anime cel-shaded style |

```bash
# Manual LoRA usage
./imagine.py "a samurai" --model dev --lora "alvdansen/flux-koda"
./imagine.py "a woman in a cafe" --model dev --lora "XLabs-AI/flux-RealismLora" --guidance 2.5

# Multiple LoRAs (comma-separated)
./imagine.py "a portrait" --model dev --lora "XLabs-AI/flux-RealismLora,alvdansen/flux-koda"
```

Any HuggingFace LoRA repo ID works — it'll download and cache on first use at `~/Library/Caches/mflux/loras/`.

## Img2Img

```bash
./imagine.py "oil painting version" --image ~/Desktop/photo.jpg --strength 0.5 --hd
./imagine.py "blend these" --image img1.jpg --image2 img2.jpg --hd    # 50/50 blend
```

## Style Transfer (IP-Adapter)

```bash
# Single reference — absorb the visual DNA of one image
./imagine.py "portrait of a woman" --style-image ~/Desktop/monet.jpg --hd
./imagine.py "a city street" --style-image ~/Desktop/reference.jpg --style-strength 0.5 --hd

# Dual reference — fuse the visual DNA of two images into something new
./imagine.py "abstract fusion" --style-image ~/Desktop/img1.png --style-image2 ~/Desktop/img2.png --hd
./imagine.py "lyrical composition" --style-image ~/Desktop/aurora.png --style-image2 ~/Desktop/terracotta.png --style-strength 0.8 --hd
```

Auto-selects the IP-Adapter engine. `--style-strength` controls how much the reference images influence the output (0.0–1.0, default 0.7). Higher values (0.7–0.9) produce stronger stylistic influence.

**Single vs Dual:** Single reference transfers one image's style (palette, texture, mood). Dual reference encodes both images through the vision model separately, then the diffusion model attends to both — creating a genuine fusion rather than a pixel blend. The result inherits visual qualities from both sources but is neither.

## Pose Transfer (ControlNet)

```bash
# Step 1: Extract pose from a reference image
./pose.py ~/Desktop/dancer.jpg --width 1024 --height 1024

# Step 2: Generate with pose guidance
./imagine.py "a robot" --pose-image ~/Desktop/dancer_pose.png --hd
./imagine.py "a woman in a red dress" --pose-image ~/Desktop/pose.png --pose-strength 0.9 --hd
```

`--pose-strength` controls pose adherence (0.0–1.0, default 0.8). Uses diffusers FluxControlNetPipeline — slower but accurate.

## Segmentation & Compositing

Extract a subject from one image and place it on a different background:

```bash
# Step 1: Segment the foreground subject (outputs transparent PNG)
./segment.py ~/Desktop/subject.jpg

# Step 2: Composite onto a new background
./composite.py ~/Desktop/subject_segmented.png ~/Desktop/background.jpg

# Step 3: Harmonize with img2img at low strength
./imagine.py "the scene" --image ~/Desktop/composite.png --strength 0.3 --hd
```

**composite.py options:**
- `--scale N` — resize foreground (e.g., `--scale 0.5` for half size)
- `--x N` — horizontal center position (default: centered)
- `--y N` — vertical bottom position (default: bottom-aligned)
- `--output path` — output path (default: `~/Desktop/composite.png`)

## Post-Processing (GIMP Grading)

```bash
./imagine.py "a forest" --hd --natural          # Subtle: desat 30% + lift blacks + warm shift
./imagine.py "a forest" --hd --natural 50        # Custom desat amount
./imagine.py "a forest" --hd --grade minimal     # Just targeted desaturation
./imagine.py "a forest" --hd --grade film        # Full: desat + lift + warm + grain + vignette + edge soften
```

## Styles Library (130+ styles, auto-matched from vibe)

Styles are automatically matched to your vibe by Gemini. You don't need to specify them — just describe what you want.

**Named styles** (use these words in your vibe to trigger them):

| Category | Styles |
|----------|--------|
| **Fine Art** | oil-painting, pop-art, watercolor |
| **Illustration** | anime-cel, contour-line-drawing, editorial-magazine, madhubani-painting, ukiyo-e, vintage-poster |
| **Design** | constructivism, psychedelic, retro-newwave, steampunk, swiss-modernist |
| **Digital** | 3d-render, cyberpunk, dystopian, vaporwave |
| **Photography** | abandoned-decay, editorial-fashion, film-noir, food, golden-hour, infrared, interior-design, macro, period-1950s, period-1970s, portrait, rain-wet, signage-typography, street-documentary, studio-product, underwater |
| **Architecture** | art-deco, brutalist, metabolist |
| **Rendering** | cel-shaded, cross-hatched, double-exposed, expressionistic, graphic, halftoned, impressionistic, painterly, photorealistic, sketchy, solarized, stylized |
| **Lighting** | backlit, candlelit, chiaroscuro, diffused, fluorescent, harsh, overexposed, rim-lit, silhouetted, tungsten, underexposed, volumetric |
| **Color** | bleached, chromatic, complementary, desaturated, iridescent, jewel-toned, monochromatic, muted, neon, oxidized, pastel, saturated |
| **Mood** | austere, claustrophobic, desolate, eerie, ethereal, hallucinatory, intimate, melancholic, monumental, nostalgic, ominous, opulent, serene, whimsical |
| **Texture** | burnished, corroded, cracked, embossed, fabric-textile, glass-transparency, glossy, grainy, gritty, impasto, matte, metal-patina, stippled, translucent, weathered |
| **Composition** | asymmetrical, cluttered, cropped, fragmented, layered, minimal, panoramic, receding, symmetrical, towering |
| **Optical** | anamorphic, deep-focus, shallow-focus, soft-focus, telephoto, tilt-shift, wide-angle |
| **Form** | amorphous, angular, faceted, geometric, monolithic, organic, sinuous, skeletal |
| **Scale** | coarse, hyper-detailed, intricate, microscopic, ornate, sparse, stark, vast |
| **Time/Motion** | blurred, decayed, ephemeral, flickering, frozen, static |
| **Figure** | approachable, characterful, striking *(auto-injected for human subjects)* |

## Examples

```bash
# Quick sketches
./imagine.py "a cat sleeping on books"
./imagine.py "tokyo street at night, neon rain"

# Photorealistic (auto-detects "photo" keyword)
./imagine.py "photo of an old man fishing at dawn" --hd

# Stylized
./imagine.py "pop art portrait of a woman" --hd
./imagine.py "watercolor painting of a lighthouse in a storm" --hd
./imagine.py "cyberpunk alley, vaporwave palette" --hd
./imagine.py "ukiyo-e style wave with a cat riding it" --hd

# With specific LoRA
./imagine.py "anime girl with sword" --model dev --lora "alvdansen/flux-koda" --hd

# Pose-guided
./pose.py ~/Desktop/dancer.jpg --width 1024 --height 1024
./imagine.py "a marble statue" --pose-image ~/Desktop/dancer_pose.png --hd

# Style transfer from single reference
./imagine.py "a cityscape" --style-image ~/Desktop/van-gogh.jpg --style-strength 0.8 --hd

# Dual style fusion — merge visual DNA of two images
./imagine.py "abstract lyrical composition" --style-image ~/Desktop/aurora.png --style-image2 ~/Desktop/terracotta.png --style-strength 0.7 --hd

# Segment + composite + harmonize
./segment.py ~/Desktop/rabbit.jpg
./composite.py ~/Desktop/rabbit_segmented.png ~/Desktop/background.jpg
./imagine.py "rabbit in a groovy 1970s scene" --image ~/Desktop/composite.png --strength 0.3 --hd

# Film-graded portrait
./imagine.py "portrait of a jazz musician, moody lighting" --portrait --grade film
```
