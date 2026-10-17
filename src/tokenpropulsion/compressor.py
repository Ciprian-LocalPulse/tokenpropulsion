"""Auditable deterministic formatting with validation and original-text fallback."""

import re
import time
from collections.abc import Callable

from .models import CompressionResult, Transformation, ValidationResult
from .profiles import get_profile
from .protection import protection_reasons
from .security import validate_input
from .tokenizer import EstimatedTokenizer, Tokenizer
from .validators import validate_candidate


def compress_prompt(
    text: str,
    level: str = "medium",
    *,
    tokenizer: Tokenizer | None = None,
) -> CompressionResult:
    start = time.perf_counter()
    validate_input(text)
    profile = get_profile(level)
    counter = tokenizer if tokenizer is not None else EstimatedTokenizer()
    reasons = protection_reasons(text)
    warnings = []
    if not counter.exact:
        warnings.append("Token counts are estimates; model token savings are unverified.")
    warnings.append("Semantic equivalence has not been assessed.")
    if level == "high":
        warnings.append("High mode collapses prose spaces; review before model use.")
    steps: list[Transformation] = []
    candidate = text
    if reasons:
        warnings.append("Prompt preserved by protection: " + ", ".join(reasons))
    else:
        operations: list[tuple[str, Callable[[str], str]]] = [
            ("trailing_ascii_spaces", lambda s: re.sub(r" +(?=\r?$)", "", s, flags=re.M))
        ]
        if profile.collapse_blank_lines:
            operations.append(("blank_lines", lambda s: re.sub(r"(\r?\n){3,}", r"\1\1", s)))
        if profile.collapse_spaces:
            operations.append(("prose_spaces", lambda s: re.sub(r" {2,}", " ", s)))
        for name, operation in operations:
            updated = operation(candidate)
            if updated != candidate:
                steps.append(Transformation(name, candidate, updated))
                candidate = updated
    validations = list(validate_candidate(text, candidate, bool(reasons)))
    before, after = counter.count(text), counter.count(candidate)
    if not isinstance(before, int) or not isinstance(after, int) or min(before, after) < 0:
        raise ValueError("tokenizer must return nonnegative integer counts")
    validations.append(
        ValidationResult("nonincreasing_count", after <= before, "Same tokenizer used.")
    )
    fallback = not all(v.passed for v in validations)
    if fallback:
        candidate, after = text, before
        steps = []
        warnings.append("Validation failed; returned original text.")
    return CompressionResult(
        text,
        candidate,
        before,
        after,
        100 * (before - after) / before if before else 0.0,
        counter.identity,
        counter.exact,
        time.perf_counter() - start,
        tuple(steps),
        tuple(warnings),
        tuple(validations),
        fallback,
    )
