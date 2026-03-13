# ComfyUI Integration Setup

ComfyUI serves as an alternative generation backend for FLUX.1 image generation, specifically enabling **IP-Adapter style transfer** which fails on Apple Silicon with the diffusers pipeline (MPS tuple bug in CLIP vision encoder outputs).

## Installation

### ComfyUI Desktop App

```bash
arch -arm64 brew install --cask comfyui
```

- Must use `arch -arm64` prefix — Rosetta brew will fail with ARM Homebrew prefix errors.
- On first launch, set the user directory to `~/Documents/vscode_projects/comfy_ui/user`.

### Server Details

| Setting | Value |
|---------|-------|
| URL | `http://127.0.0.1:8000` |
| Default port | 8000 (ComfyUI Desktop app; standard ComfyUI uses 8188) |
| Python venv | `~/Documents/vscode_projects/comfy_ui/.venv/bin/python` |
| User directory | `~/Documents/vscode_projects/comfy_ui/user` |
| Models directory | `~/Documents/vscode_projects/comfy_ui/models/` |
| Custom nodes | `~/Documents/vscode_projects/comfy_ui/custom_nodes/` |
| Input/Output | `~/Documents/vscode_projects/comfy_ui/input/` and `output/` |
| Logs | `~/Library/Logs/ComfyUI/comfyui.log` |

## Model Files

FLUX model files must be consolidated single `.safetensors` files. The HuggingFace cache stores FLUX.1-dev in sharded multi-part format which ComfyUI cannot use — download separately.

| File | Size | Directory | Source |
|------|------|-----------|--------|
| `flux1-dev.safetensors` | ~12 GB | `models/diffusion_models/` | `black-forest-labs/FLUX.1-dev` |
| `t5xxl_fp16.safetensors` | ~9.5 GB | `models/text_encoders/` | `comfyanonymous/flux_text_encoders` |
| `clip_l.safetensors` | ~246 MB | `models/text_encoders/` | `comfyanonymous/flux_text_encoders` |
| `ae.safetensors` | ~335 MB | `models/vae/` | `black-forest-labs/FLUX.1-dev` |
| `ip-adapter.bin` | ~4.9 GB | `models/ipadapter-flux/` | `InstantX/FLUX.1-dev-IP-Adapter` |

Download example (requires HF token for gated repos):

```bash
HF_TOKEN="hf_..."
curl -L -H "Authorization: Bearer $HF_TOKEN" \
  "https://huggingface.co/black-forest-labs/FLUX.1-dev/resolve/main/flux1-dev.safetensors" \
  -o ~/Documents/vscode_projects/comfy_ui/models/diffusion_models/flux1-dev.safetensors
```

## Custom Nodes

### ComfyUI-Manager (pre-installed)

Ships with the Desktop app. Provides the "Manage Extensions" UI for installing other nodes.

### comfyui_ipadapter_plus (cubiq)

General-purpose IP-Adapter node for SDXL/SD1.5. **Does not support FLUX models** (no FLUX code paths at all). Installed via ComfyUI Manager UI.

- Repo: https://github.com/cubiq/ComfyUI_IPAdapter_plus
- **Not used by this project** — kept installed but irrelevant for FLUX.

### ComfyUI-IPAdapter-Flux (Shakker-Labs) — REQUIRED

The correct FLUX IP-Adapter node. Works with InstantX `ip-adapter.bin` weights.

```bash
cd ~/Documents/vscode_projects/comfy_ui/custom_nodes
git clone https://github.com/Shakker-Labs/ComfyUI-IPAdapter-Flux.git
```

**Dependencies** — must be installed into ComfyUI's venv (not the system or project venv):

```bash
~/Documents/vscode_projects/comfy_ui/.venv/bin/python -m pip install diffusers einops sentencepiece protobuf
```

Without `diffusers`, the node silently fails to load (`Cannot import ... module for custom nodes: No module named 'diffusers'` in the ComfyUI log).

**Restart ComfyUI after installing** — custom nodes are only loaded at startup.

#### Compatibility patches (ComfyUI Desktop v1.x)

The Shakker-Labs node was written for an older ComfyUI version. Two fixes are needed for the current ComfyUI Desktop app:

1. **`flux/layers.py` line 31** — `DoubleStreamBlock` no longer has `flipped_img_txt`:
   ```python
   # Before (crashes):
   self.flipped_img_txt = original_block.flipped_img_txt
   # After:
   self.flipped_img_txt = getattr(original_block, 'flipped_img_txt', False)
   ```

2. **`utils.py` `forward_orig_ipa` signature** — ComfyUI now passes `timestep_zero_index`:
   ```python
   # Add this parameter after control=None:
   timestep_zero_index=None,
   ```

#### Node class names (API-format workflows)

| Node | Class Name | Purpose |
|------|-----------|---------|
| Loader | `IPAdapterFluxLoader` | Loads IP-Adapter weights + SigLIP CLIP vision |
| Apply | `ApplyIPAdapterFlux` | Applies style transfer to the FLUX model |

Loader inputs:
- `ipadapter`: filename from `models/ipadapter-flux/` (e.g., `ip-adapter.bin`)
- `clip_vision`: `"google/siglip-so400m-patch14-384"` (auto-downloaded from HF on first use)
- `provider`: `"mps"` for Apple Silicon, `"cuda"` for NVIDIA, `"cpu"` for fallback

Apply inputs:
- `model`: FLUX UNet model (from `UNETLoader`)
- `ipadapter_flux`: loaded adapter (from `IPAdapterFluxLoader`)
- `image`: style reference image (from `LoadImage`)
- `weight`: style transfer strength (0.0–1.0, default 0.7)
- `start_percent`: when to start applying (0.0)
- `end_percent`: when to stop applying (1.0)

#### IP-Adapter folder naming

Shakker-Labs looks for weights in `models/ipadapter-flux/` (with hyphen), **not** `models/ipadapter/`. The `ip-adapter.bin` file must be in the correct folder.

#### XLabs alternative (not used)

XLabs-AI also offers FLUX IP-Adapter via `x-flux-comfyui`, but it uses different weights (`XLabs-AI/flux-ip-adapter`), not the InstantX `ip-adapter.bin`. Different ecosystem, not interchangeable.

## ComfyUI API (HTTP)

ComfyUI exposes a REST API for programmatic workflow execution:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/system_stats` | GET | Health check |
| `/prompt` | POST | Queue a workflow for execution |
| `/history/{prompt_id}` | GET | Poll for workflow completion |
| `/view?filename=...&subfolder=...&type=output` | GET | Download generated image |
| `/upload/image` | POST | Upload reference image (multipart form) |

### Workflow format (API)

Workflows submitted via `/prompt` use a flat dict format, **not** the visual UI format:

```json
{
  "prompt": {
    "1": {
      "class_type": "UNETLoader",
      "inputs": {
        "unet_name": "flux1-dev.safetensors",
        "weight_dtype": "default"
      }
    },
    "2": {
      "class_type": "DualCLIPLoader",
      "inputs": {
        "clip_name1": "t5xxl_fp16.safetensors",
        "clip_name2": "clip_l.safetensors",
        "type": "flux"
      }
    }
  }
}
```

Node connections are represented as `["source_node_id", output_index]` tuples.

### FLUX node stack (txt2img)

```
UNETLoader → BasicGuider ← CLIPTextEncode ← DualCLIPLoader
                ↓
VAELoader → VAEDecode ← SamplerCustomAdvanced ← BasicScheduler (← UNETLoader)
                                ↑          ↑
                          KSamplerSelect  RandomNoise
                                          EmptySD3LatentImage
```

For IP-Adapter style transfer, `IPAdapterFluxLoader` + `ApplyIPAdapterFlux` sit between `UNETLoader` and `BasicGuider`, modifying the model before it enters the sampler.

## CLI Usage

```bash
# Plain txt2img via ComfyUI
./imagine.py "a rabbit on a mountain" --engine comfyui --hd

# Style transfer (auto-selects ComfyUI engine)
./imagine.py "portrait of a woman" --style-image ~/Desktop/monet.jpg --style-strength 0.7 --hd

# Explicit engine + style
./imagine.py "still life" --engine comfyui --style-image ~/Desktop/reference.png --style-strength 0.5
```

## Troubleshooting

### "ComfyUI server not reachable"
ComfyUI Desktop app is not running. Launch it from Applications.

### "Cannot import ... module for custom nodes"
Missing Python dependency. Check `~/Library/Logs/ComfyUI/comfyui.log` for the specific module, then install into ComfyUI's venv:
```bash
~/Documents/vscode_projects/comfy_ui/.venv/bin/python -m pip install <module>
```

### Custom node not appearing in `/object_info`
ComfyUI only loads custom nodes at startup. Restart after installing.

### IP-Adapter model not found
Ensure `ip-adapter.bin` is in `models/ipadapter-flux/` (not `models/ipadapter/`).

### SigLIP CLIP vision download hangs
First run downloads `google/siglip-so400m-patch14-384` (~878 MB) from HuggingFace. This is automatic but may take time on slow connections.

## Headless Mode

To run ComfyUI without the Desktop app UI (e.g., from a terminal or script):

```bash
~/Documents/vscode_projects/comfy_ui/.venv/bin/python \
  /Applications/ComfyUI.app/Contents/Resources/ComfyUI/main.py \
  --listen 127.0.0.1 --port 8000 \
  --base-directory ~/Documents/vscode_projects/comfy_ui \
  --disable-auto-launch
```

Key flags:
- `--base-directory` — **required** for custom nodes, models, input/output to resolve correctly. Without it, ComfyUI only loads custom nodes from the app bundle path, missing user-installed nodes like IPAdapter-Flux.
- `--disable-auto-launch` — prevents opening the browser.
- `--user-directory` is NOT sufficient — it sets user config but doesn't affect custom_nodes/models resolution.

One-time prerequisite: `pip install comfyui-frontend-package` into the venv (the Desktop app bundles this, but headless mode needs it explicitly).

The API is identical in headless mode.

## Performance Notes

On Apple Silicon (M1 Max), ComfyUI FLUX generation takes ~7-8 minutes per 1024x1024 image (including first model load). Subsequent runs with models cached in memory are faster but still significantly slower than mflux (~1.5 min for equivalent quality).

**Recommendation**: Use mflux for regular txt2img/img2img generation. Only use ComfyUI when IP-Adapter style transfer is needed — it's the only working path on macOS.
