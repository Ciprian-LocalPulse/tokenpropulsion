"""Mechanical invariants are not an assessment of semantic equivalence."""

import re

from .models import ValidationResult


def validate_candidate(
    original: str, candidate: str, protected: bool
) -> tuple[ValidationResult, ...]:
    return (
        ValidationResult(
            "ordered_nonwhitespace_units",
            re.findall(r"\S+", original) == re.findall(r"\S+", candidate),
            "All nonwhitespace units remain identical and in order; meaning is unassessed.",
        ),
        ValidationResult(
            "protected_identity",
            not protected or original == candidate,
            "Protected prompts must remain byte-identical.",
        ),
    )
