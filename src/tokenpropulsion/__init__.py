"""TokenPropulsion: Less input. Measurable savings. Verified behavior."""

from .compressor import compress_prompt
from .models import CompressionResult

__version__ = "1.0.0rc1"
__all__ = ["CompressionResult", "__version__", "compress_prompt"]
