from typing import Optional

from pydantic_settings import BaseSettings


class GeneratorSettings(BaseSettings):
    """Image generator configuration. Loaded from env vars or .env file."""

    # FLUX.1
    flux_model_variant: str = "schnell"  # "dev" or "schnell"
    flux_default_steps: int = 4  # 4 for schnell, 25 for dev
    flux_quantization: Optional[int] = None  # None, 4, or 8
    flux_default_width: int = 1024
    flux_default_height: int = 1024
    flux_default_seed: Optional[int] = None
    flux_output_dir: str = "~/Desktop"

    # Gemini API (for prompt expansion)
    ai_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # General
    log_level: str = "INFO"

    model_config = {
        "env_prefix": "IMGANARY_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }
