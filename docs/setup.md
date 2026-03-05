# Environment Setup

## Prerequisites

### 1. GIMP with Python-Fu

Install GIMP and ensure Python-Fu console is available under **Filters > Python-Fu > Console**.

- **macOS**: `brew install --cask gimp`
- **Linux**: `sudo apt install gimp`
- **Windows**: Download from [gimp.org](https://www.gimp.org/downloads/)

Verify Python-Fu works:

```bash
gimp -i -b '(gimp-version)' -b '(gimp-quit 0)'
```

### 2. Python 3.12 (ARM)

Python 3.12 via ARM Homebrew is recommended on Apple Silicon for native PyTorch support.

```bash
# Install ARM Homebrew (if not already at /opt/homebrew)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.12
/opt/homebrew/bin/brew install python@3.12
/opt/homebrew/bin/python3.12 --version
```

### 3. Ollama (Local Vision Models)

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh
```

Pull the LLaVA model:

```bash
ollama pull llava
```

### 4. Claude Code CLI

Follow the [Claude Code installation guide](https://docs.anthropic.com/en/docs/claude-code) to install the CLI.

### 5. Git

```bash
git --version
```

## Verify Setup

```bash
# Check all dependencies
gimp --version
python3 --version
ollama --version
git --version
```
