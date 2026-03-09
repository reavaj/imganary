# Environment Setup

## Prerequisites

### 1. Python 3.12 (ARM)

Python 3.12 via ARM Homebrew is required on Apple Silicon for native PyTorch and MLX support.

```bash
# Install ARM Homebrew (if not already at /opt/homebrew)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.12
/opt/homebrew/bin/brew install python@3.12
/opt/homebrew/bin/python3.12 --version
```

### 2. Virtual Environment & Dependencies

```bash
cd imganary
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and add:
- `IMGANARY_AI_API_KEY` — Google Gemini API key (for prompt expansion)
- Other settings are optional (see `generators/config.py` and `models/config.py`)

### 4. GIMP 3.x with Python-Fu

```bash
brew install --cask gimp
```

GIMP batch mode on macOS requires special setup. See [gimp-batch-mode.md](gimp-batch-mode.md) for the full guide (filtered plugin directory, batch-gimprc, gimp-console usage).

### 5. Ollama (Local Vision Models)

```bash
brew install ollama
ollama pull llava
```

LLaVA is used for scene description and image analysis. YOLO and CLIP models auto-download on first use via Python packages.

### 6. HuggingFace Authentication (FLUX Models)

FLUX.1 models are gated — you must accept the terms on HuggingFace before downloading:

1. Create an account at [huggingface.co](https://huggingface.co)
2. Accept terms for [FLUX.1-schnell](https://huggingface.co/black-forest-labs/FLUX.1-schnell) and/or [FLUX.1-dev](https://huggingface.co/black-forest-labs/FLUX.1-dev)
3. Log in locally:

```bash
source .venv/bin/activate
huggingface-cli login
```

Models cache to `~/.cache/huggingface/hub/` (~12GB each).

### 7. Claude Code CLI

Follow the [Claude Code installation guide](https://docs.anthropic.com/en/docs/claude-code) to install the CLI. Claude Code skills provide GIMP automation (color grading, filters, text overlay, etc.).

## Verify Setup

```bash
source .venv/bin/activate

# Core tools
python3 --version          # 3.12.x
gimp --version             # 3.0.x
ollama --version

# FLUX generation
./generate.py "test prompt" --model schnell

# Vision analysis
./analyze.py ~/Desktop/test.jpg --model llava

# Prompt expansion (requires IMGANARY_AI_API_KEY)
./imagine.py "test vibe"
```

## Model Summary

| Model | Size | Download | Purpose |
|-------|------|----------|---------|
| FLUX.1-schnell | ~12GB | HuggingFace (gated) | Fast image generation (4 steps) |
| FLUX.1-dev | ~12GB | HuggingFace (gated) | High-quality generation (25 steps) |
| LLaVA | ~4GB | `ollama pull llava` | Scene description |
| YOLOv8n | ~6MB | Auto on first use | Object detection |
| CLIP | ~600MB | Auto on first use | Image-text similarity |
