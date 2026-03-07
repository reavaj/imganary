class ChatError(Exception):
    """Base exception for chat agent errors."""


class ToolExecutionError(ChatError):
    """A tool failed to execute."""


class GimpExecutionError(ChatError):
    """GIMP batch execution failed."""


class LibraryError(ChatError):
    """Script library operation failed."""
