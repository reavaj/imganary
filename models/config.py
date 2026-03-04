from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class ModelSettings(BaseSettings):
    """Vision model configuration. Loaded from env vars or .env file."""

    # Ollama / LLaVA
    ollama_base_url: str = "http://localhost:11434"
    llava_model_name: str = "llava"
    llava_timeout_seconds: int = 120

    # YOLO
    yolo_model_path: str = "yolov8n.pt"
    yolo_confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)

    # CLIP
    clip_model_name: str = "openai/clip-vit-base-patch32"
    clip_candidate_labels: List[str] = Field(
        default=[
            "person", "animal", "vehicle", "building",
            "nature", "food", "text", "indoor", "outdoor",
        ]
    )

    # General
    log_level: str = "INFO"
    max_image_size_mb: int = 20

    model_config = {
        "env_prefix": "IMGANARY_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }
