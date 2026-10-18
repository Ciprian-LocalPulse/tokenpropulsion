"""Immutable audit records. Records contain prompts; persist only with consent."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Transformation:
    name: str
    before: str
    after: str


@dataclass(frozen=True)
class ValidationResult:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class CompressionResult:
    original_text: str
    optimized_text: str
    original_tokens: int
    optimized_tokens: int
    tokens_saved_percent: float
    tokenizer: str
    counts_exact: bool
    processing_seconds: float
    transformations: tuple[Transformation, ...]
    warnings: tuple[str, ...]
    validations: tuple[ValidationResult, ...]
    fallback_triggered: bool
    semantic_equivalence_assessed: bool = False

    strategy: str = "conservative"
    validation_scope: str = "mechanical-only"
    confidence: str = "unassessed"
    count_kind: str = "heuristic"

    @property
    def saved_percent(self) -> float:
        return self.tokens_saved_percent

    def restore(self) -> str:
        return self.original_text

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
