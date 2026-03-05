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

### 2. Python 3.10

Python 3.10 is required (PyTorch 2.2.2 compatibility). Newer Python versions may not have PyTorch wheels available.

```bash
python3.10 --version
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
