from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings


class ChatSettings(BaseSettings):
    """Chat agent configuration. Loaded from env vars or .env file."""

    # Claude API
    anthropic_api_key: SecretStr
    claude_model: str = "claude-sonnet-4-20250514"

    # Safety limits
    max_turns: int = 100
    max_response_tokens: int = 4096

    # Paths
    project_root: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent.parent
    )
    gimp_console_path: str = (
        "/Applications/GIMP.app/Contents/MacOS/gimp-console"
    )
    gimp_gimprc_path: str = (
        "~/Library/Application Support/GIMP/3.0/batch-gimprc"
    )

    model_config = {
        "env_prefix": "IMGANARY_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

    @property
    def scripts_dir(self) -> Path:
        return self.project_root / "scripts"
