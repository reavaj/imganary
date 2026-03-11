#!/usr/bin/env python3
"""LoRA browser — search CivitAI, list cached, download FLUX LoRAs."""

import sys
import os
import json
from pathlib import Path
from textwrap import shorten

import httpx

CIVITAI_API = "https://civitai.com/api/v1"
LORA_DIR = Path(__file__).resolve().parent / "loras"
MFLUX_CACHE = Path.home() / "Library" / "Caches" / "mflux" / "loras"

# ── Helpers ──────────────────────────────────────────────────────────

def _api_get(endpoint: str, params: dict | None = None) -> dict:
    """GET from CivitAI API with timeout."""
    url = f"{CIVITAI_API}{endpoint}"
    api_key = os.environ.get("CIVITAI_API_KEY")
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    resp = httpx.get(url, params=params, headers=headers, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    return resp.json()


def _strip_html(text: str) -> str:
    """Crude HTML tag removal for CivitAI descriptions."""
    import re
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _fmt_size(kb: float) -> str:
    if kb >= 1024 * 1024:
        return f"{kb / (1024 * 1024):.1f} GB"
    if kb >= 1024:
        return f"{kb / 1024:.1f} MB"
    return f"{kb:.0f} KB"


def _fmt_count(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


# ── Commands ─────────────────────────────────────────────────────────

def cmd_search(query: str, base_model: str | None = "Flux.1 D", limit: int = 20,
               sort: str = "Most Downloaded", nsfw: bool = False):
    """Search CivitAI for FLUX LoRAs."""
    params = {
        "types": "LORA",
        "query": query,
        "sort": sort,
        "limit": min(limit, 100),
        "nsfw": str(nsfw).lower(),
    }
    if base_model:
        params["baseModels"] = base_model
    data = _api_get("/models", params)
    items = data.get("items", [])

    if not items:
        print(f"No LoRAs found for '{query}' (base: {base_model})")
        return

    print(f"\n{'#':>3}  {'Downloads':>10}  {'Rating':>7}  {'Name'}")
    print(f"{'─' * 3}  {'─' * 10}  {'─' * 7}  {'─' * 50}")

    for i, item in enumerate(items, 1):
        stats = item.get("stats", {})
        downloads = _fmt_count(stats.get("downloadCount", 0))
        ups = stats.get("thumbsUpCount", 0)
        downs = stats.get("thumbsDownCount", 0)
        total = ups + downs
        rating = f"{ups / total * 100:.0f}%" if total > 0 else "  —"
        name = shorten(item["name"], width=50, placeholder="…")

        # Get base model and version info
        versions = item.get("modelVersions", [])
        base = versions[0].get("baseModel", "?") if versions else "?"
        ver = versions[0].get("name", "") if versions else ""

        print(f"{i:>3}  {downloads:>10}  {rating:>7}  {name}")
        print(f"{'':>3}  {'':>10}  {'':>7}  ID: {item['id']}  |  {base}  |  {ver}")

    print(f"\n  Use './loras.py info <ID>' for details or './loras.py download <ID>' to download.")


def cmd_info(model_id: int):
    """Show details about a CivitAI model."""
    data = _api_get(f"/models/{model_id}")

    print(f"\n  {data['name']}")
    print(f"  {'─' * len(data['name'])}")
    print(f"  ID: {data['id']}  |  Type: {data['type']}  |  By: {data.get('creator', {}).get('username', '?')}")

    tags = data.get("tags", [])
    if tags:
        print(f"  Tags: {', '.join(tags[:10])}")

    stats = data.get("stats", {})
    print(f"  Downloads: {_fmt_count(stats.get('downloadCount', 0))}  |  "
          f"👍 {_fmt_count(stats.get('thumbsUpCount', 0))}  |  "
          f"👎 {_fmt_count(stats.get('thumbsDownCount', 0))}")

    desc = data.get("description", "")
    if desc:
        cleaned = _strip_html(desc)
        # Show first ~500 chars
        if len(cleaned) > 500:
            cleaned = cleaned[:500] + "…"
        print(f"\n  {cleaned}")

    versions = data.get("modelVersions", [])
    if versions:
        print(f"\n  Versions:")
        for v in versions[:5]:
            base = v.get("baseModel", "?")
            files = v.get("files", [])
            size = _fmt_size(files[0].get("sizeKB", 0)) if files else "?"
            trigger = v.get("trainedWords", [])
            trigger_str = f"  trigger: {', '.join(trigger)}" if trigger else ""
            print(f"    [{v['id']}] {v['name']}  |  {base}  |  {size}{trigger_str}")

    print(f"\n  https://civitai.com/models/{data['id']}")
    print(f"\n  Download: './loras.py download <VERSION_ID>'")
    print(f"  (Use a version ID from the list above, not the model ID)")


def cmd_download(version_id: int):
    """Download a LoRA by version ID to the loras/ directory."""
    # Get version info first
    data = _api_get(f"/model-versions/{version_id}")

    model_name = data.get("model", {}).get("name", "unknown")
    version_name = data.get("name", "unknown")
    base_model = data.get("baseModel", "unknown")
    trigger_words = data.get("trainedWords", [])
    files = data.get("files", [])

    if not files:
        print(f"No files found for version {version_id}")
        return

    # Find the safetensors file
    target = None
    for f in files:
        if f["name"].endswith(".safetensors"):
            target = f
            break
    if not target:
        target = files[0]

    filename = target["name"]
    size_kb = target.get("sizeKB", 0)
    download_url = data.get("downloadUrl", target.get("downloadUrl"))

    if not download_url:
        print("No download URL found")
        return

    print(f"\n  Model:    {model_name} ({version_name})")
    print(f"  Base:     {base_model}")
    print(f"  File:     {filename} ({_fmt_size(size_kb)})")
    if trigger_words:
        print(f"  Trigger:  {', '.join(trigger_words)}")

    # Sanitize filename — use model name + version
    safe_name = model_name.lower().replace(" ", "-").replace("/", "-")
    safe_name = "".join(c for c in safe_name if c.isalnum() or c in "-_")
    dest_name = f"{safe_name}.safetensors"
    dest = LORA_DIR / dest_name

    if dest.exists():
        print(f"\n  Already exists: {dest}")
        resp = input("  Overwrite? [y/N] ").strip().lower()
        if resp != "y":
            print("  Skipped.")
            return

    LORA_DIR.mkdir(exist_ok=True)

    print(f"\n  Downloading to {dest}...")

    api_key = os.environ.get("CIVITAI_API_KEY")
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    with httpx.stream("GET", download_url, headers=headers, timeout=300, follow_redirects=True) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        downloaded = 0
        with open(dest, "wb") as f:
            for chunk in resp.iter_bytes(chunk_size=1024 * 256):
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    pct = downloaded / total * 100
                    bar = "█" * int(pct / 2.5) + "░" * (40 - int(pct / 2.5))
                    print(f"\r  [{bar}] {pct:.0f}%  ({_fmt_size(downloaded / 1024)} / {_fmt_size(total / 1024)})", end="", flush=True)

    print(f"\n\n  Saved: {dest}")

    # Write metadata sidecar
    meta = {
        "civitai_model_id": data.get("modelId"),
        "civitai_version_id": version_id,
        "name": model_name,
        "version": version_name,
        "base_model": base_model,
        "trigger_words": trigger_words,
        "source_url": f"https://civitai.com/models/{data.get('modelId')}",
    }
    meta_path = dest.with_suffix(".json")
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    print(f"  Metadata: {meta_path}")
    print(f"\n  Use with: ./imagine.py \"your prompt\" --lora loras/{dest_name}")


def cmd_list():
    """List locally available LoRAs."""
    print("\n  Local LoRAs (loras/):")
    print(f"  {'─' * 60}")

    local_loras = []
    if LORA_DIR.exists():
        for f in sorted(LORA_DIR.glob("*.safetensors")):
            size = _fmt_size(f.stat().st_size / 1024)
            meta_path = f.with_suffix(".json")
            meta = {}
            if meta_path.exists():
                meta = json.loads(meta_path.read_text())

            name = meta.get("name", f.stem)
            base = meta.get("base_model", "?")
            trigger = meta.get("trigger_words", [])
            trigger_str = f"  trigger: {', '.join(trigger)}" if trigger else ""

            print(f"    {f.name}  ({size})  |  {base}{trigger_str}")
            print(f"      --lora loras/{f.name}")
            if meta.get("source_url"):
                print(f"      {meta['source_url']}")
            local_loras.append(f)

    if not local_loras:
        print("    (none)")

    # Also check mflux HuggingFace cache
    print(f"\n  Cached HuggingFace LoRAs (mflux):")
    print(f"  {'─' * 60}")

    hf_loras = []
    if MFLUX_CACHE.exists():
        for d in sorted(MFLUX_CACHE.iterdir()):
            if d.is_dir() and d.name.startswith("models--"):
                parts = d.name.replace("models--", "").split("--", 1)
                if len(parts) == 2:
                    repo_id = f"{parts[0]}/{parts[1]}"
                else:
                    repo_id = parts[0]

                # Find the actual safetensors file size
                size_str = "?"
                for st in d.rglob("*.safetensors"):
                    if not st.is_symlink():
                        size_str = _fmt_size(st.stat().st_size / 1024)
                    break

                print(f"    {repo_id}  ({size_str})")
                print(f"      --lora {repo_id}")
                hf_loras.append(repo_id)

    if not hf_loras:
        print("    (none)")

    total = len(local_loras) + len(hf_loras)
    print(f"\n  Total: {total} LoRA(s) available")


# ── CLI ──────────────────────────────────────────────────────────────

USAGE = """\
Usage: ./loras.py <command> [args]

Commands:
  search <query>       Search CivitAI for FLUX LoRAs
  info <model_id>      Show details about a CivitAI model
  download <version_id> Download a LoRA version to loras/
  list                 List locally available LoRAs

Options:
  --dev                Search for FLUX.1 Dev LoRAs (default)
  --schnell            Search for FLUX.1 Schnell LoRAs
  --all                Search all base models (not just FLUX)
  --sort <method>      Sort by: downloads, rating, newest (default: downloads)
  --limit N            Number of results (default: 20)
  --nsfw               Include NSFW results

Environment:
  CIVITAI_API_KEY      Optional API key for gated models

Examples:
  ./loras.py search realism
  ./loras.py search "anime style" --schnell --limit 10
  ./loras.py info 578935
  ./loras.py download 648723
  ./loras.py list
"""

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(USAGE)
        return

    cmd = args[0]

    # Parse global flags
    base_model = "Flux.1 D"
    if "--all" in args:
        base_model = None
        args.remove("--all")
    if "--schnell" in args:
        base_model = "Flux.1 S"
        args.remove("--schnell")
    if "--dev" in args:
        base_model = "Flux.1 D"
        args.remove("--dev")

    sort_map = {"downloads": "Most Downloaded", "rating": "Highest Rated", "newest": "Newest"}
    sort = "Most Downloaded"
    if "--sort" in args:
        idx = args.index("--sort")
        sort_val = args[idx + 1] if idx + 1 < len(args) else "downloads"
        sort = sort_map.get(sort_val, sort_val)
        args = args[:idx] + args[idx + 2:]

    limit = 20
    if "--limit" in args:
        idx = args.index("--limit")
        limit = int(args[idx + 1]) if idx + 1 < len(args) else 20
        args = args[:idx] + args[idx + 2:]

    nsfw = "--nsfw" in args
    if nsfw:
        args.remove("--nsfw")

    try:
        if cmd == "search":
            query = " ".join(args[1:])
            if not query:
                print("Usage: ./loras.py search <query>")
                return
            cmd_search(query, base_model=base_model, limit=limit, sort=sort, nsfw=nsfw)

        elif cmd == "info":
            if len(args) < 2:
                print("Usage: ./loras.py info <model_id>")
                return
            cmd_info(int(args[1]))

        elif cmd == "download":
            if len(args) < 2:
                print("Usage: ./loras.py download <version_id>")
                return
            cmd_download(int(args[1]))

        elif cmd == "list":
            cmd_list()

        else:
            # Treat unknown command as a search query
            cmd_search(" ".join(args), base_model=base_model, limit=limit, sort=sort, nsfw=nsfw)

    except httpx.HTTPStatusError as e:
        print(f"\nAPI error: {e.response.status_code} — {e.response.text[:200]}")
        sys.exit(1)
    except httpx.ConnectError:
        print("\nCould not connect to CivitAI API. Check your internet connection.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(0)


if __name__ == "__main__":
    main()
