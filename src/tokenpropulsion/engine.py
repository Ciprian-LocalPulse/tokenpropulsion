"""Second-generation acceptance gates; defaults retain the original safety policy."""

import time

from .exceptions import InputError
from .models import CompressionResult, Transformation, ValidationResult
from .profiles import get_profile
from .protection import protection_reasons
from .security import validate_input
from .strategies import CandidateValidator, SemanticBackend, lexical_candidate, structural_candidate
from .tokenizer import EstimatedTokenizer, Tokenizer, count_metadata


def advanced_compress(
    text: str,
    level: str,
    *,
    tokenizer: Tokenizer | None,
    strategy: str | None,
    validator: CandidateValidator | None,
    backend: SemanticBackend | None,
    preserve: tuple[str, ...],
) -> CompressionResult:
    from .compressor import compress_prompt

    start = time.perf_counter()
    if level != "adaptive":
        get_profile(level)
    chosen = strategy
    if chosen is None:
        chosen = (
            "structural" if validator and structural_candidate(text) != text else "conservative"
        )
    if chosen not in {"conservative", "structural", "lexical", "semantic"}:
        raise InputError("unknown compression strategy")
    if chosen == "conservative":
        return compress_prompt(
            text, "medium" if level == "adaptive" else level, tokenizer=tokenizer
        )
    counter = tokenizer if tokenizer is not None else EstimatedTokenizer()
    reasons = protection_reasons(text)
    warnings = ["No universal semantic-equivalence assessment; task checks have limited scope."]
    if not counter.exact:
        warnings.append("Token counts are heuristic estimates, not Grok usage.")
    validations = []
    candidate = text
    rejected = False
    if reasons:
        warnings.append("Prompt preserved by protection: " + ", ".join(reasons))
    elif validator is None:
        warnings.append("Advanced transformation refused: task validator required.")
        rejected = True
    else:
        try:
            if chosen == "structural":
                candidate = structural_candidate(text)
            elif chosen == "lexical":
                candidate = lexical_candidate(text)
            elif backend is None:
                raise InputError("semantic strategy needs an explicitly supplied backend")
            else:
                candidate = backend.propose(text)
            validate_input(candidate)
            if protection_reasons(candidate):
                raise InputError("candidate introduced protected syntax")
            preserved = all(text.count(span) == candidate.count(span) for span in preserve)
            passed = validator.validate(text, candidate) is True
            validations.extend(
                [
                    ValidationResult(
                        "explicit_preservation", preserved, "Caller-designated spans."
                    ),
                    ValidationResult(
                        "task:" + validator.name,
                        passed,
                        "Caller-owned task contract, not a semantic proof.",
                    ),
                ]
            )
            rejected = not preserved or not passed
        except Exception:
            rejected = True
            candidate = text
            validations.append(
                ValidationResult(
                    "proposal_validation",
                    False,
                    "Proposal or validator failed; details suppressed.",
                )
            )
    before, after = counter.count(text), counter.count(candidate)
    if any(type(n) is not int or n < 0 for n in (before, after)):
        raise InputError("tokenizer returned an invalid count")
    validations.append(ValidationResult("nonincreasing_count", after <= before, "Same counter."))
    rejected = rejected or after > before
    if rejected:
        candidate, after = text, before
        warnings.append("Unverifiable candidate rejected; original returned.")
    changed = candidate != text
    return CompressionResult(
        text,
        candidate,
        before,
        after,
        100 * (before - after) / before if before else 0,
        counter.identity,
        counter.exact,
        time.perf_counter() - start,
        (Transformation(chosen, text, candidate),) if changed else (),
        tuple(warnings),
        tuple(validations),
        rejected,
        strategy=chosen,
        validation_scope=("task:" + validator.name) if validator else "unassessed",
        confidence="task-validated" if changed else "unassessed",
        count_kind=str(count_metadata(counter)["kind"]),
    )
