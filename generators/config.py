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
    flux_guidance: float = 3.5  # CFG scale (dev only, ignored for schnell)
    flux_lora_paths: list[str] = []  # .safetensors LoRA file paths
    flux_lora_scales: list[float] = []  # weight per LoRA (default 1.0 each)
    flux_output_dir: str = "~/Desktop"

    # ComfyUI
    comfyui_url: str = "http://127.0.0.1:8000"
    comfyui_timeout: int = 600  # seconds (first run loads ~12GB model)
    comfyui_model_name: str = "flux1-dev.safetensors"
    comfyui_clip_name1: str = "t5xxl_fp16.safetensors"
    comfyui_clip_name2: str = "clip_l.safetensors"
    comfyui_vae_name: str = "ae.safetensors"
    comfyui_ipadapter_name: str = "ip-adapter.bin"

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
