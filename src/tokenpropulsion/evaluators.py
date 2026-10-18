"""Optional similarity/judge observations, deliberately separate from acceptance gates."""

import json
import math
from typing import Any

from .budget import RequestBudget
from .exceptions import InputError
from .models import ValidationResult
from .security import validate_input


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or len(left) != len(right) or len(left) > 4096:
        raise InputError("equal nonempty vectors with at most 4096 dimensions required")
    if not all(math.isfinite(x) for x in left + right):
        raise InputError("nonfinite similarity input")
    denominator = math.sqrt(sum(x * x for x in left) * sum(x * x for x in right))
    if not denominator:
        raise InputError("nonzero vectors required")
    return max(-1.0, min(1.0, sum(a * b for a, b in zip(left, right, strict=True)) / denominator))


class LLMJudge:
    """Explicit billable non-deterministic observation. Not a CandidateValidator.

    A judge can be prompt-injected or wrong and cannot by itself approve compression.
    The caller must configure an authorized provider, a budget, and review the content.
    """

    def __init__(self, provider: Any, *, billing_authorized: bool = False) -> None:
        if not billing_authorized or not isinstance(
            getattr(provider, "budget", None), RequestBudget
        ):
            raise InputError("explicit billing authorization and RequestBudget required")
        self.provider = provider

    def assess(self, original: str, candidate: str) -> ValidationResult:
        validate_input(original)
        validate_input(candidate)
        request = json.dumps(
            {
                "task": "Compare meaning; reply exactly SAME or DIFFERENT",
                "untrusted_original": original,
                "untrusted_candidate": candidate,
            }
        )
        validate_input(request)
        response = self.provider.request(request)
        return ValidationResult(
            "llm-judge:nondeterministic",
            response.content == "SAME",
            "Non-deterministic model opinion, not equivalence proof or acceptance.",
        )
