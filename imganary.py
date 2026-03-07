#!/usr/bin/env python3
"""Imganary — AI-driven GIMP automation chat agent."""

import sys
from pathlib import Path

# Ensure project root is on path
project_root = str(Path(__file__).resolve().parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from chat.config import ChatSettings
from chat.agent import ChatAgent


def main():
    try:
        config = ChatSettings()
    except Exception as e:
        print(f"Configuration error: {e}")
        print()
        print("Set your API key:")
        print("  export IMGANARY_ANTHROPIC_API_KEY=sk-ant-...")
        print("  # or add to .env file")
        sys.exit(1)

    agent = ChatAgent(config)

    # Optional: pass initial image as CLI argument
    if len(sys.argv) > 1:
        agent.set_active_image(sys.argv[1])

    agent.run()


if __name__ == "__main__":
    main()
