"""Stack detection and configuration."""

from agentpack.stack.detector import (
    AmbiguousStackError,
    NoStackDetectedError,
    StackError,
    detect_stack,
)

__all__ = [
    "AmbiguousStackError",
    "NoStackDetectedError",
    "StackError",
    "detect_stack",
]
