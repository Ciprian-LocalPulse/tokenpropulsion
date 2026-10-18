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


def validate_document_contract(original: str, candidate: str) -> bool:
    """Independent ordered-subsequence check of a declared idempotent JSON document."""
    import json

    from .protection import protection_reasons

    try:
        left, right = json.loads(original), json.loads(candidate)
        keys = {"instructions", "contexts", "question"}
        if set(left) != keys or set(right) != keys:
            return False
        if any(left[k] != right[k] for k in ("instructions", "question")):
            return False
        seen = set()
        position = 0
        for section in left["contexts"]:
            key = json.dumps(section, sort_keys=True)
            if position < len(right["contexts"]) and section == right["contexts"][position]:
                position += 1
            elif (
                section.get("idempotent") is not True
                or section.get("trust") != "untrusted"
                or key not in seen
                or protection_reasons(section["text"])
            ):
                return False
            seen.add(key)
        return position == len(right["contexts"])
    except (ValueError, TypeError, KeyError, AttributeError, RecursionError):
        return False
