class ImageAnalysisError(Exception):
    """Base exception for all model wrapper errors."""


class ModelNotAvailableError(ImageAnalysisError):
    """Raised when the backing model server is unreachable."""


class InvalidImageError(ImageAnalysisError):
    """Raised when the image path is invalid or the file is corrupt."""


class AnalysisTimeoutError(ImageAnalysisError):
    """Raised when model inference exceeds the configured timeout."""
