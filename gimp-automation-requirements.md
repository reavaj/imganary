Project Overview
Build a structured, extensible automation framework integrating Claude Code with GIMP to enable AI-driven image editing workflows. The system generates reusable scripts, grows a persistent library, and is version-controlled on GitHub.

Core Goals

Automate GIMP image manipulation using Claude Code skills
Generate and save reusable GIMP Python-Fu/Script-Fu scripts to a growing library
Integrate local image recognition models so Claude understands image context before editing
Maintain everything in a well-organized GitHub repo for long-term storage and potential community sharing


GitHub Repository Structure
gimp-claude-automation/
├── skills/               # Claude Code skill definitions
│   ├── gimp-core/
│   ├── image-analysis/
│   └── workflow/
├── scripts/              # Generated GIMP Python-Fu scripts
│   ├── color/
│   ├── transform/
│   ├── filters/
│   └── compositing/
├── models/               # Local vision/recognition models + README
├── docs/
│   ├── skill-index.md    # Maps skills to the scripts they generate
│   └── setup.md
└── README.md

Skills Framework
Categories to build:

GIMP Core — CLI and Python-Fu wrappers for common ops (resize, crop, color, filters, format conversion)
Batch Processing — Automate repetitive tasks across image folders
Script Generation — Natural language → Python-Fu script, auto-saved to library
Image Analysis — Invoke local vision models, return scene context
Pipeline Orchestration — Chain analysis → context → GIMP transformation

Design principles: Each skill self-contained, script-generating skills auto-save to scripts/, skills composable into larger workflows.

Local Image Recognition Integration
Purpose: Let Claude understand image content before generating edits (e.g., "sharpen the background behind the subject").
Suggested models:

LLaVA — General purpose local vision-language model (run via Ollama)
YOLO — Object detection
CLIP — Semantic image understanding

Flow: image path → local model → scene description → Claude generates targeted GIMP script → script saved to library

Script Library Management

Scripts saved to scripts/ with descriptive filenames, organized by category
docs/skill-index.md documents what each script does and which skill generated it
Commit regularly to GitHub to build a permanent, growing library


Git Workflow
bashgit add skills/ scripts/ docs/
git commit -m "Add: [description of new skill or script]"
git push origin main
Use descriptive commit messages. Tag milestones like v0.1-core-skills.

Environment Requirements

Claude Code (CLI)
GIMP with Python-Fu support enabled
Python 3.x
Ollama (for running LLaVA locally)
Git


Future Extensions

Web UI for browsing and running saved scripts
Automated tagging of scripts by image type or use case
Community sharing via the public repo