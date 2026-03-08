"""Auto-research pipeline: discover unknown visual styles via web search + LLaVA."""

import base64
import json
import tempfile
from pathlib import Path

import httpx
from ddgs import DDGS
from google import genai
from PIL import Image

from generators.config import GeneratorSettings
from models.config import ModelSettings

STYLES_DIR = Path(__file__).parent / "styles"

CLASSIFY_PROMPT = """\
You are a style classifier for a visual prompt expansion system.
Given a user's "vibe" prompt and a list of existing style definitions,
determine whether the existing styles adequately cover the visual concept.

Respond with ONLY a JSON object (no markdown fencing):
{
  "match": true or false,
  "matched_styles": ["category/name", "category/name"],
  "reason": "brief explanation",
  "concept": "the visual style/movement to research (if no match)",
  "category": "one of: photography, illustration, fine-art, design, digital, architecture",
  "search_query": "image search query to find visual references (if no match)"
}

Rules:
- "matched_styles" should list 1-3 existing styles that best fit the vibe (even if match=false).
- If the existing styles cover the vibe well enough (even through blending), set match=true.
- Only set match=false when the vibe references a specific visual tradition, movement,
  or aesthetic that is genuinely missing from the library.\
"""

COMPILE_PROMPT = """\
You are building a style reference card for a FLUX.1 image generation system.
Given visual analyses of reference images for a specific style/movement,
compile them into a structured style definition.

Output ONLY the style definition in this exact markdown format (no fencing):

# [Style Name]

[2-3 sentence definition of what this style IS — its origins, era, and visual philosophy.]

## Visual DNA
- **Lighting:** [typical lighting approaches]
- **Composition:** [framing, layout, spatial relationships]
- **Color palette:** [dominant colors, relationships, temperature]
- **Textures & materials:** [surfaces, media, physical qualities]
- **Mood:** [emotional tone, atmosphere]
- **Rendering:** [technique, level of detail, stylistic choices]

## FLUX keywords
[comma-separated keywords that FLUX.1 responds well to for this style]\
"""

LLAVA_STYLE_PROMPT = (
    "Analyze this image as a visual style reference. Describe in detail: "
    "the lighting approach, color palette, textures and materials, "
    "composition style, mood/atmosphere, and any distinctive visual techniques. "
    "Focus on reusable visual patterns, not the specific subject matter."
)


def classify_vibe(vibe: str, existing_styles: str, settings: GeneratorSettings) -> dict:
    """Ask Gemini whether existing styles match the vibe."""
    client = genai.Client(api_key=settings.ai_api_key)
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=f"Vibe: {vibe}\n\nExisting styles:\n{existing_styles}",
        config=genai.types.GenerateContentConfig(
            system_instruction=CLASSIFY_PROMPT,
            max_output_tokens=200,
        ),
    )
    text = response.text.strip()
    # Strip markdown fencing if present
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(text)


def search_reference_images(query: str, max_results: int = 3) -> list[str]:
    """Search DuckDuckGo for reference images, return URLs."""
    try:
        results = DDGS().images(query, max_results=max_results)
        return [r["image"] for r in results if r.get("image")]
    except Exception:
        return []


def download_image(url: str, timeout: float = 15.0) -> Path | None:
    """Download an image to a temp file, normalized to JPEG for LLaVA compatibility."""
    try:
        resp = httpx.get(url, timeout=timeout, follow_redirects=True)
        resp.raise_for_status()
        # Save raw bytes to temp, then convert to JPEG via Pillow
        raw_tmp = tempfile.NamedTemporaryFile(suffix=".raw", delete=False)
        raw_tmp.write(resp.content)
        raw_tmp.close()
        img = Image.open(raw_tmp.name).convert("RGB")
        # Resize large images to keep LLaVA fast
        img.thumbnail((1024, 1024))
        jpg_tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        img.save(jpg_tmp.name, "JPEG", quality=85)
        jpg_tmp.close()
        Path(raw_tmp.name).unlink(missing_ok=True)
        return Path(jpg_tmp.name)
    except Exception:
        return None


def analyze_with_llava(image_path: Path, model_settings: ModelSettings) -> str | None:
    """Use LLaVA to analyze a reference image for visual style patterns."""
    image_b64 = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    try:
        client = httpx.Client(
            base_url=model_settings.ollama_base_url,
            timeout=httpx.Timeout(10.0, read=300.0),
        )
        response = client.post(
            "/api/generate",
            json={
                "model": model_settings.llava_model_name,
                "prompt": LLAVA_STYLE_PROMPT,
                "images": [image_b64],
                "stream": False,
            },
        )
        response.raise_for_status()
        data = response.json()
        if data.get("error"):
            return None
        return data.get("response", "")
    except Exception:
        return None


def compile_style_definition(
    concept: str, analyses: list[str], settings: GeneratorSettings
) -> str:
    """Use Gemini to compile LLaVA analyses into a style .md definition."""
    analyses_text = "\n\n---\n\n".join(
        f"Reference image {i+1} analysis:\n{a}" for i, a in enumerate(analyses)
    )
    client = genai.Client(api_key=settings.ai_api_key)
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=f"Style/concept: {concept}\n\n{analyses_text}",
        config=genai.types.GenerateContentConfig(
            system_instruction=COMPILE_PROMPT,
            max_output_tokens=500,
        ),
    )
    return response.text.strip()


def research_and_create_style(
    vibe: str,
    classification: dict,
    settings: GeneratorSettings,
    callback=print,
) -> Path | None:
    """Full pipeline: search → download → LLaVA analyze → compile → save."""
    concept = classification["concept"]
    category = classification["category"]
    search_query = classification["search_query"]

    # Step 1: Search for reference images
    callback(f"Researching: {concept}")
    callback(f"Searching:  {search_query}")
    urls = search_reference_images(search_query)
    if not urls:
        callback("Warning: No reference images found. Using Gemini knowledge only.")
        # Fall back to Gemini-only generation
        return _create_style_from_gemini(concept, category, settings, callback)

    # Step 2: Download images
    images = []
    for url in urls:
        path = download_image(url)
        if path:
            images.append(path)
    if not images:
        callback("Warning: Could not download images. Using Gemini knowledge only.")
        return _create_style_from_gemini(concept, category, settings, callback)

    callback(f"Downloaded: {len(images)} reference images")

    # Step 3: Ask user whether to run LLaVA (slow) or use Gemini only (fast)
    try:
        answer = input("Analyze with LLaVA for richer style? (y/N) ").strip().lower()
    except EOFError:
        answer = "n"
    if answer != "y":
        # Clean up downloaded images
        for img_path in images:
            img_path.unlink(missing_ok=True)
        return _create_style_from_gemini(concept, category, settings, callback)

    callback("Analyzing with LLaVA...")
    model_settings = ModelSettings()
    analyses = []
    for i, img_path in enumerate(images, 1):
        callback(f"  LLaVA analyzing image {i}/{len(images)}...")
        analysis = analyze_with_llava(img_path, model_settings)
        if analysis and analysis.strip():
            analyses.append(analysis)
        # Clean up temp file
        img_path.unlink(missing_ok=True)

    if not analyses:
        callback("Warning: LLaVA analysis failed. Using Gemini knowledge only.")
        return _create_style_from_gemini(concept, category, settings, callback)

    callback(f"Analyzed:   {len(analyses)} images")

    # Step 4: Compile into style definition
    callback("Compiling style definition...")
    style_md = compile_style_definition(concept, analyses, settings)

    # Step 5: Save
    return _save_style(concept, category, style_md, callback)


def _create_style_from_gemini(
    concept: str, category: str, settings: GeneratorSettings, callback=print
) -> Path:
    """Fallback: generate style definition from Gemini's knowledge alone."""
    callback("Generating style from Gemini knowledge...")
    client = genai.Client(api_key=settings.ai_api_key)
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=f"Create a comprehensive visual style reference for: {concept}",
        config=genai.types.GenerateContentConfig(
            system_instruction=COMPILE_PROMPT,
            max_output_tokens=500,
        ),
    )
    style_md = response.text.strip()
    return _save_style(concept, category, style_md, callback)


def _save_style(concept: str, category: str, style_md: str, callback=print) -> Path:
    """Save a style definition to the correct category directory."""
    # Slugify the concept name
    slug = concept.lower().replace(" ", "-").replace("/", "-")
    slug = "".join(c for c in slug if c.isalnum() or c == "-")

    category_dir = STYLES_DIR / category
    category_dir.mkdir(parents=True, exist_ok=True)
    style_path = category_dir / f"{slug}.md"
    style_path.write_text(style_md + "\n")
    callback(f"Saved:      {style_path.relative_to(STYLES_DIR.parent.parent)}")
    return style_path
