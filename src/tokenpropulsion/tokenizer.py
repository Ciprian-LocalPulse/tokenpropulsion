"""Dependency-free fallback accounting, never represented as model tokens."""

import math
from dataclasses import dataclass, field
from typing import Protocol


class Tokenizer(Protocol):
    identity: str
    exact: bool

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
