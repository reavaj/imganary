class ImageGenerationError(Exception):
    """Base exception for all generator errors."""


class GenerationTimeoutError(ImageGenerationError):
    """Raised when image generation exceeds a reasonable time limit."""


class InvalidPromptError(ImageGenerationError):
    """Raised when the prompt is empty or invalid."""
