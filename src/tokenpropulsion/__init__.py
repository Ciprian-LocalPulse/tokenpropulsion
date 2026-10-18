"""TokenPropulsion: Less input. Measurable savings. Verified behavior."""

from .compressor import compress_prompt
from .documents import ContextSection, PromptDocument, compress_document
from .models import CompressionResult

__version__ = "2.0.0a1"
__all__ = [
    "CompressionResult",
    "__version__",
    "compress_prompt",
    "compress_document",
    "PromptDocument",
    "ContextSection",
]
