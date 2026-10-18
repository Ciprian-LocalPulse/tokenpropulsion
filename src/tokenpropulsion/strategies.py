"""Opt-in proposals. Only caller-provided task validation can accept word removal."""

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from .exceptions import InputError


class CandidateValidator(Protocol):
    @property
    def name(self) -> str: ...

    def validate(self, original: str, candidate: str) -> bool: ...


@dataclass(frozen=True)
class TaskValidator:
    """Caller-owned deterministic application contract, not universal equivalence."""

    name: str
    check: Callable[[str, str], bool] = field(repr=False)

    def validate(self, original: str, candidate: str) -> bool:
        return self.check(original, candidate) is True


class SemanticBackend(Protocol):
    @property
    def identity(self) -> str: ...

    def propose(self, text: str) -> str: ...


def structural_candidate(text: str) -> str:
    """Remove byte-identical repeated paragraphs. Never reorder surviving boundaries."""
    parts = re.split(r"(\n[ \r]*\n+)", text)
    seen: set[str] = set()
    kept: list[str] = []
    for index in range(0, len(parts), 2):
        block = parts[index]
        if block in seen and block.strip():
            continue
        seen.add(block)
        if kept:
            kept.append(parts[index - 1])
        kept.append(block)
    return "".join(kept)


LEXICAL_RULES = (
    ("in order to", "to"),
    ("at this point in time", "now"),
    ("due to the fact that", "because"),
    ("a large number of", "many"),
)


def lexical_candidate(text: str) -> str:
    candidate = text
    for source, replacement in LEXICAL_RULES:
        candidate = re.sub(r"\b" + re.escape(source) + r"\b", replacement, candidate)
    return candidate


class SentenceTransformerBackend:
    """Optional local-weight sentence redundancy proposal. Similarity is not proof.

    No download, remote code, or network fallback. Model weights have separate licenses.
    Quadratic comparisons are bounded to 128 sentences of at most 512 characters.
    """

    def __init__(self, model_path: str, threshold: float = 0.97) -> None:
        if not 0.8 <= threshold <= 1 or not Path(model_path).is_dir():
            raise InputError("existing local model directory and threshold [0.8,1] required")
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise InputError(
                "install tokenpropulsion[semantic] for local embedding proposals"
            ) from None
        self._model: Any = SentenceTransformer(
            model_path,
            local_files_only=True,
            trust_remote_code=False,
        )
        self.threshold = threshold
        self.identity = "sentence-transformers:local-unverified"

    def propose(self, text: str) -> str:
        sentences = re.split(r"(?<=[.!?]) +", text)
        if len(sentences) > 128 or any(len(s) > 512 for s in sentences):
            raise InputError("semantic proposal sentence limit exceeded")
        vectors = self._model.encode(sentences, normalize_embeddings=True).tolist()
        keep: list[int] = []
        for i, vector in enumerate(vectors):
            if not any(
                sum(float(a) * float(b) for a, b in zip(vector, vectors[j], strict=True))
                >= self.threshold
                for j in keep
            ):
                keep.append(i)
        return " ".join(sentences[i] for i in keep)
