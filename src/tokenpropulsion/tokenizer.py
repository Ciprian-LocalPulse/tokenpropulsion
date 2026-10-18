"""Dependency-free fallback accounting, never represented as model tokens."""

import math
from dataclasses import dataclass, field
from typing import Protocol


class Tokenizer(Protocol):
    @property
    def identity(self) -> str: ...

    @property
    def exact(self) -> bool: ...

    def count(self, text: str) -> int: ...


@dataclass(frozen=True)
class EstimatedTokenizer:
    """UTF-8 byte estimate. Not a bound or calibrated model tokenizer."""

    bytes_per_token: float = 4.0
    exact: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if not math.isfinite(self.bytes_per_token) or self.bytes_per_token <= 0:
            raise ValueError("bytes_per_token must be finite and positive")

    @property
    def identity(self) -> str:
        return f"estimate:utf8-bytes/{self.bytes_per_token:g}"

    def count(self, text: str) -> int:
        return math.ceil(len(text.encode("utf-8")) / self.bytes_per_token)


def count_metadata(tokenizer: Tokenizer) -> dict[str, str | bool]:
    kind = getattr(
        tokenizer, "count_kind", "custom-unspecified" if tokenizer.exact else "heuristic"
    )
    allowed = {
        "provider-exact",
        "compatible-local",
        "unrelated-tokenizer",
        "heuristic",
        "custom-unspecified",
    }
    if kind not in allowed:
        raise ValueError("unknown tokenizer provenance kind")
    return {"identity": tokenizer.identity, "exact": tokenizer.exact, "kind": kind}


class TiktokenTokenizer:
    """Exact local vocabulary counts, explicitly unrelated to Grok billing.

    Preloaded encodings work offline. Factory downloads need explicit authorization.
    """

    exact = True
    count_kind = "unrelated-tokenizer"

    def __init__(self, encoding: object) -> None:
        from typing import Any, cast

        self._encoding = cast(Any, encoding)
        self.identity = "tiktoken:" + str(self._encoding.name)

    def count(self, text: str) -> int:
        return len(self._encoding.encode(text, disallowed_special=()))

    @classmethod
    def load(cls, name: str = "cl100k_base", *, allow_network: bool = False) -> "TiktokenTokenizer":
        try:
            import tiktoken
            from tiktoken.registry import ENCODINGS
        except ImportError:
            raise ValueError("install tokenpropulsion[tokenizers]") from None
        if name not in ENCODINGS and not allow_network:
            raise ValueError("preload encoding or explicitly allow tokenizer downloads")
        return cls(tiktoken.get_encoding(name))
