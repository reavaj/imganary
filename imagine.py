#!/usr/bin/env python3
"""Generate an image from a vibe prompt — expands via Gemini, then renders via FLUX."""

import logging
import os
import random
import sys
import tempfile
import warnings
from datetime import datetime
from pathlib import Path

# Suppress noisy library warnings before any imports
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_DISABLE_EXPERIMENTAL_WARNING"] = "1"
os.environ["DO_NOT_TRACK"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings("ignore")
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("imganary.flux").setLevel(logging.WARNING)

from google import genai

from generators import GeneratorType, create_generator
from generators.config import GeneratorSettings
from prompts.style_researcher import classify_vibe, research_and_create_style

PROMPTS_DIR = Path(__file__).parent / "prompts"
EXPAND_PROMPT_PATH = PROMPTS_DIR / "expand.md"
STYLES_DIR = PROMPTS_DIR / "styles"


def style_index() -> str:
    """Return a compact list of style names for classification."""
    return ", ".join(
        f"{md.parent.name}/{md.stem}" for md in sorted(STYLES_DIR.rglob("*.md"))
    )


def load_styles(names: list[str]) -> str:
    """Load specific style definitions by 'category/name' keys."""
    # Build lookup: "category/stem" → path
    lookup = {
        f"{md.parent.name}/{md.stem}": md
        for md in STYLES_DIR.rglob("*.md")
    }
    sections = []
    for name in names:
        path = lookup.get(name)
        if path:
            sections.append(f"[{name}]\n{path.read_text().strip()}")
    return "\n\n---\n\n".join(sections)


def classify_and_resolve(vibe: str, settings: GeneratorSettings) -> list[str]:
    """Classify the vibe, auto-research if needed, return matched style names."""
    api_key = settings.ai_api_key or os.environ.get("AI_API_KEY", "")
    if not api_key:
        return []

    try:
        classification = classify_vibe(vibe, style_index(), settings)
    except Exception:
        return []

    matched = classification.get("matched_styles", [])

    if not classification.get("match", True):
        concept = classification.get("concept", "unknown")
        print(f"New style detected: {concept}")
        try:
            new_path = research_and_create_style(vibe, classification, settings)
            if new_path:
                # Add the newly created style to the matched list
                matched.append(f"{classification['category']}/{new_path.stem}")
            print()
        except Exception as e:
            print(f"Warning: Style research failed ({e}), continuing with existing styles.")

    return matched


NON_PHOTO_KEYWORDS = (
    "anime", "manga", "cartoon", "comic", "pop art", "pixel art",
    "watercolor", "oil painting", "sketch", "illustration", "vector",
    "abstract", "surreal", "cubist", "impressionist", "art deco",
    "art nouveau", "minimalist", "flat design", "cel shad", "ukiyo",
    "vaporwave", "synthwave", "retro", "vintage poster", "collage",
    "graffiti", "street art", "stained glass", "mosaic", "woodcut",
    "linocut", "etching", "engraving", "blueprint", "schematic",
)


def expand_prompt(vibe: str, settings: GeneratorSettings) -> str:
    """Expand a short vibe prompt into FLUX-optimized language via Gemini."""
    api_key = settings.ai_api_key or os.environ.get("AI_API_KEY", "")
    if not api_key:
        print("Warning: No AI API key found — skipping expansion.")
        print("Set IMGANARY_AI_API_KEY in .env or AI_API_KEY env var.")
        return vibe

    # Classify vibe → get relevant styles (auto-research if needed)
    matched_styles = classify_and_resolve(vibe, settings)

    # Non-photographic style categories — skip photo/figure defaults when these are matched
    non_photo_categories = ("illustration/", "fine-art/", "design/", "digital/")
    vibe_lower = vibe.lower()
    is_non_photo = (
        any(s.startswith(non_photo_categories) for s in matched_styles)
        or any(kw in vibe_lower for kw in NON_PHOTO_KEYWORDS)
    )

    # Strip photorealistic style if Gemini matched it on a non-photo vibe
    if is_non_photo:
        matched_styles = [s for s in matched_styles if s != "rendering/photorealistic"]

    # Auto-inject approachable figure style only when the vibe mentions a human subject
    # and no figure style is already matched
    human_keywords = (
        "person", "people", "man", "woman", "boy", "girl", "child", "kid",
        "portrait", "face", "figure", "model", "dancer", "athlete", "warrior",
        "elderly", "young", "old man", "old woman", "couple", "family",
        "worker", "musician", "soldier", "detective", "scientist", "chef",
    )
    has_human_subject = any(kw in vibe_lower for kw in human_keywords)
    if has_human_subject and not is_non_photo:
        has_figure_style = any(s.startswith("figure/") for s in matched_styles)
        if not has_figure_style:
            matched_styles.append("figure/approachable")

    # Only inject photorealistic rendering when the vibe explicitly mentions "photo"
    photo_keywords = ("photo", "photograph", "photorealistic", "photorealism")
    wants_photo = any(kw in vibe_lower for kw in photo_keywords)
    if wants_photo:
        has_rendering_style = any(s.startswith("rendering/") for s in matched_styles)
        if not has_rendering_style:
            matched_styles.append("rendering/photorealistic")

    # Separate figure styles from other styles for different injection framing
    figure_styles = [s for s in matched_styles if s.startswith("figure/")]
    other_styles = [s for s in matched_styles if not s.startswith("figure/")]

    system_prompt = EXPAND_PROMPT_PATH.read_text()
    if other_styles:
        style_content = load_styles(other_styles)
        system_prompt += (
            "\n\n---\n\n"
            "# Matched Style References\n\n"
            "Use these style definitions as your primary visual framework. "
            "Draw on their Visual DNA, textures, lighting, and FLUX keywords "
            "to build your expanded prompt. Blend them if appropriate.\n\n"
            f"{style_content}"
        )
    if figure_styles:
        figure_content = load_styles(figure_styles)
        system_prompt += (
            "\n\n---\n\n"
            "# MANDATORY Figure Rendering Style\n\n"
            "When describing human subjects, you MUST follow this figure style. "
            "This is NOT optional and overrides any tendency toward idealized beauty. "
            "Apply the key characteristics and FLUX keywords from this definition "
            "to every human subject in the expanded prompt.\n\n"
            f"{figure_content}"
        )

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=vibe,
        config=genai.types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=300,
        ),
    )
    return response.text.strip()


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: ./imagine.py <vibe> "
            "[--model dev|schnell] [--steps N] [--seed N] "
            "[--width N] [--height N] [--output path.png] [--raw] [--hd]\n"
            "       [--image path] [--image2 path] [--strength 0.0-1.0]\n"
            "       [--guidance N]  (CFG scale, default 3.5 — lower = less saturated, dev only)\n"
            "       [--lora path.safetensors]  (LoRA weights, comma-separated for multiple)\n"
            "       [--controlnet path]  (ControlNet canny edge reference image)\n"
            "       [--controlnet-strength 0.0-1.0]  (ControlNet influence, default 0.5)\n"
            "       [--grade minimal|natural|film]  (GIMP post-grading preset)\n"
            "       [--natural [AMOUNT]]  (shorthand for --grade natural)\n"
            "       [--portrait]  (tall aspect ratio for full-body shots: 768x1152)\n"
            "       [--engine mflux|ipadapter|pose]  (generation backend, default mflux)\n"
            "       [--style-image path]  (IP-Adapter style reference, auto-selects ipadapter)\n"
            "       [--style-strength 0.0-1.0]  (style transfer influence, default 0.7)\n"
            "       [--pose-image path]  (pose skeleton image, auto-selects pose engine)\n"
            "       [--pose-strength 0.0-1.0]  (pose ControlNet influence, default 0.8)"
        )
        sys.exit(1)

    vibe = sys.argv[1]

    # Parse optional flags
    def _flag(name: str, default=None):
        if name in sys.argv:
            idx = sys.argv.index(name)
            if idx + 1 < len(sys.argv):
                return sys.argv[idx + 1]
        return default

    raw = "--raw" in sys.argv
    hd = "--hd" in sys.argv
    portrait = "--portrait" in sys.argv
    natural = "--natural" in sys.argv
    if natural:
        # --natural can be bare (default 30) or --natural 50
        raw_amount = _flag("--natural")
        # If next arg is another flag or missing, use default
        if raw_amount is None or raw_amount.startswith("--"):
            natural_amount = 30.0
        else:
            natural_amount = float(raw_amount)
    else:
        natural_amount = None
    guidance_str = _flag("--guidance")
    lora_str = _flag("--lora")
    grade_preset = _flag("--grade")
    model = _flag("--model", "schnell")
    steps = _flag("--steps")
    seed = _flag("--seed")
    if portrait:
        default_width, default_height = "768", "1152"
    elif hd:
        default_width, default_height = "1024", "1024"
    else:
        default_width, default_height = "512", "512"
    width = _flag("--width", default_width)
    height = _flag("--height", default_height)
    output = _flag("--output")
    image = _flag("--image")
    image2 = _flag("--image2")
    strength = _flag("--strength", "0.5")
    controlnet = _flag("--controlnet")
    controlnet_strength = _flag("--controlnet-strength", "0.5")
    engine = _flag("--engine", "mflux")
    style_image = _flag("--style-image")
    style_image2 = _flag("--style-image2")
    style_strength = _flag("--style-strength", "0.7")
    pose_image = _flag("--pose-image")
    pose_strength = _flag("--pose-strength", "0.8")

    # --style-image implies standalone IP-Adapter engine (no server needed)
    if style_image and engine == "mflux":
        engine = "ipadapter"
        print("Style transfer requested — switching to standalone IP-Adapter engine")

    # --pose-image implies pose ControlNet engine
    if pose_image and engine == "mflux":
        engine = "pose"
        print("Pose transfer requested — switching to pose ControlNet engine")

    # Resolve generator type
    if engine == "pose":
        gen_type = GeneratorType.POSE
    elif engine == "ipadapter":
        gen_type = GeneratorType.IPADAPTER
    else:
        type_map = {"dev": GeneratorType.FLUX_DEV, "schnell": GeneratorType.FLUX_SCHNELL}
        gen_type = type_map.get(model)
        if gen_type is None:
            print(f"Error: Unknown model '{model}'. Use 'dev' or 'schnell'.")
            sys.exit(1)

    settings = GeneratorSettings()

    # Auto-detect photorealistic intent from vibe keywords
    # Applies realism LoRA + low guidance unless user explicitly overrides
    # Suppressed when non-photo styles are explicitly mentioned
    photo_keywords = ("photo", "photograph", "photorealistic")
    vibe_lower = vibe.lower()
    has_non_photo_style = any(kw in vibe_lower for kw in NON_PHOTO_KEYWORDS)
    is_photo_intent = (
        any(kw in vibe_lower for kw in photo_keywords) and not has_non_photo_style
    )
    if is_photo_intent:
        # Photo intent forces dev model (higher quality, supports guidance + LoRA)
        if model == "schnell":
            model = "dev"
            gen_type = type_map["dev"]
            print("Photo intent detected — switching to dev model")
        if not lora_str and not settings.flux_lora_paths:
            settings.flux_lora_paths = ["XLabs-AI/flux-RealismLora"]
            print("Photo intent detected — using RealismLora")
        if not guidance_str:
            settings.flux_guidance = 2.5
            print("Photo intent detected — guidance set to 2.5")

    # Apply CLI overrides to settings (these take precedence over auto-detection)
    if lora_str:
        settings.flux_lora_paths = [p.strip() for p in lora_str.split(",")]
    if guidance_str:
        settings.flux_guidance = float(guidance_str)

    # Expand or pass through
    # Detailed prompts (3+ sentences) are used verbatim — no Gemini rewrite
    sentence_count = len([s for s in vibe.replace("...", "…").split(".") if s.strip()])
    if raw or sentence_count > 2:
        prompt = vibe
        if not raw:
            print("Prompt is already detailed — using verbatim.")
        print(f"Prompt: {prompt}")
    else:
        print(f"Vibe:   {vibe}")
        print("Expanding...")
        prompt = expand_prompt(vibe, settings)

    print(f"Prompt: {prompt}")

    print()

    # Resolve seed early so it can be included in the filename
    if seed is None:
        seed = random.randint(0, 2**32 - 1)
    else:
        seed = int(seed)

    # Default output path
    if not output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = str(Path(f"~/Desktop/flux_{timestamp}_s{seed}.png").expanduser())

    # Blend two images if --image2 provided
    ref_image = image
    tmp_blend = None
    if image and image2:
        from PIL import Image as PILImage

        img1 = PILImage.open(Path(image).expanduser()).convert("RGB")
        img2 = PILImage.open(Path(image2).expanduser()).convert("RGB")
        img2 = img2.resize(img1.size)
        blended = PILImage.blend(img1, img2, alpha=0.5)
        tmp_blend = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        blended.save(tmp_blend.name)
        tmp_blend.close()
        ref_image = tmp_blend.name
        print(f"Blended: {image} + {image2}")

    if pose_image:
        print(f"Pose:   {pose_image}")
        print(f"Pose Strength: {pose_strength}")
    elif style_image:
        print(f"Style:  {style_image}")
        if style_image2:
            print(f"Style2: {style_image2}")
        print(f"Style Strength: {style_strength}")
        if ref_image and engine == "ipadapter":
            print(f"Base:   {ref_image}")
            print(f"Base Strength: {strength}")
    elif ref_image:
        print(f"Image:  {ref_image}")
        print(f"Strength: {strength}")

    if controlnet:
        print(f"ControlNet: {controlnet}")
        print(f"CN Strength: {controlnet_strength}")

    if engine == "pose":
        print("Engine: Pose ControlNet (diffusers)")
    elif engine == "ipadapter":
        print("Engine: IP-Adapter (standalone)")
    else:
        print(f"Model:  FLUX.1-{model}")
        if model == "dev":
            print(f"CFG:    {settings.flux_guidance}")
        if settings.flux_lora_paths:
            print(f"LoRA:   {', '.join(settings.flux_lora_paths)}")
    if grade_preset:
        print(f"Grade:  --grade {grade_preset}")
    elif natural:
        print(f"Grade:  --natural {natural_amount}%")
    print(f"Output: {output}")
    print()

    generator = create_generator(gen_type, settings)

    # Route image_path: style transfer uses style_image, otherwise use ref_image (img2img)
    if style_image:
        gen_image_path = style_image
        gen_image_strength = float(style_strength)
    elif ref_image:
        gen_image_path = ref_image
        gen_image_strength = float(strength)
    else:
        gen_image_path = None
        gen_image_strength = None

    # Route base_image_path: when --image + --style-image combined on ipadapter,
    # the ref_image becomes the img2img base (preserves likeness via initial latents)
    gen_base_image_path = None
    gen_base_image_strength = None
    if ref_image and style_image and engine == "ipadapter":
        gen_base_image_path = ref_image
        gen_base_image_strength = float(strength)

    # Pose image routes through controlnet_image_path on the pose generator
    # Style image2 also routes through controlnet_image_path for dual IP-Adapter
    if pose_image:
        effective_controlnet = pose_image
        effective_controlnet_strength = float(pose_strength)
    elif style_image2 and engine == "ipadapter":
        effective_controlnet = style_image2
        effective_controlnet_strength = None
    elif controlnet:
        effective_controlnet = controlnet
        effective_controlnet_strength = float(controlnet_strength)
    else:
        effective_controlnet = None
        effective_controlnet_strength = None

    result = generator.generate(
        prompt=prompt,
        output_path=output,
        width=int(width),
        height=int(height),
        steps=int(steps) if steps else None,
        seed=seed,
        image_path=gen_image_path,
        image_strength=gen_image_strength,
        guidance=settings.flux_guidance,
        controlnet_image_path=effective_controlnet,
        controlnet_strength=effective_controlnet_strength,
        base_image_path=gen_base_image_path,
        base_image_strength=gen_base_image_strength,
    )

    # Clean up temp blend file
    if tmp_blend:
        Path(tmp_blend.name).unlink(missing_ok=True)

    if result.error:
        print(f"Error: {result.error}")
        sys.exit(1)

    print(f"Generated {result.width}x{result.height} in {result.processing_time_ms:.0f}ms")
    if result.seed is not None:
        print(f"Seed:   {result.seed}")

    # Post-processing: GIMP photo grading
    # --grade <preset> takes priority; --natural is shorthand for --grade natural
    effective_preset = grade_preset
    effective_desat = None
    if not effective_preset and natural:
        effective_preset = "natural"
        effective_desat = natural_amount

    if effective_preset:
        from grade import grade_image

        print(f"Grading: {effective_preset} preset...")
        try:
            grade_image(
                result.output_path,
                preset=effective_preset,
                desat_amount=effective_desat,
            )
            print("Graded successfully.")
        except Exception as e:
            print(f"Warning: Grading failed ({e}), keeping ungraded image.")

    print(f"Saved to: {result.output_path}")


if __name__ == "__main__":
    main()
