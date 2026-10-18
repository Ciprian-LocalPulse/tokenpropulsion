"""Explicit structured RAG contract; repeated instructions are never deduplicated."""

import json
import time
from dataclasses import asdict, dataclass

from .exceptions import InputError
from .models import CompressionResult, Transformation, ValidationResult
from .protection import protection_reasons
from .security import validate_input
from .tokenizer import EstimatedTokenizer, Tokenizer, count_metadata
from .validators import validate_document_contract


@dataclass(frozen=True)
class ContextSection:
    source: str
    text: str
    idempotent: bool = False
    trust: str = "untrusted"


@dataclass(frozen=True)
class PromptDocument:
    instructions: str
    contexts: tuple[ContextSection, ...]
    question: str

    def render(self) -> str:
        # JSON encodes boundary-looking strings as data; no role elevation.
        return json.dumps(asdict(self), ensure_ascii=False, separators=(",", ":"))


def compress_document(
    document: PromptDocument, *, tokenizer: Tokenizer | None = None
) -> CompressionResult:
    start = time.perf_counter()
    if not isinstance(document, PromptDocument) or len(document.contexts) > 4096:
        raise InputError("PromptDocument with at most 4096 contexts required")
    for section in document.contexts:
        if (
            not isinstance(section, ContextSection)
            or section.trust != "untrusted"
            or not section.source
            or type(section.idempotent) is not bool
        ):
            raise InputError("context requires source, untrusted boundary and boolean idempotence")
        validate_input(section.text)
        validate_input(section.source)
    validate_input(document.instructions)
    validate_input(document.question)
    original = document.render()
    validate_input(original)
    counter = tokenizer if tokenizer is not None else EstimatedTokenizer()
    retained = []
    seen: set[ContextSection] = set()
    for section in document.contexts:
        if section.idempotent and not protection_reasons(section.text) and section in seen:
            continue
        seen.add(section)
        retained.append(section)
    candidate = PromptDocument(document.instructions, tuple(retained), document.question).render()
    before, after = counter.count(original), counter.count(candidate)
    if any(type(n) is not int or n < 0 for n in (before, after)):
        raise InputError("tokenizer returned an invalid count")
    validations = (
        ValidationResult(
            "instruction_question_identity",
            json.loads(original)["instructions"] == json.loads(candidate)["instructions"]
            and json.loads(original)["question"] == json.loads(candidate)["question"],
            "Instruction and question strings retained exactly.",
        ),
        ValidationResult(
            "idempotent_context_contract",
            validate_document_contract(original, candidate),
            "Only declared idempotent, byte-identical untrusted contexts removed.",
        ),
        ValidationResult(
            "nonincreasing_count", after <= before, "Same counter including envelope."
        ),
    )
    fallback = not all(check.passed for check in validations)
    if fallback:
        candidate, after = original, before
    changes = (Transformation("idempotent_context_deduplication", original, candidate),)
    return CompressionResult(
        original,
        candidate,
        before,
        after,
        100 * (before - after) / before if before else 0,
        counter.identity,
        counter.exact,
        time.perf_counter() - start,
        changes if candidate != original else (),
        ("Declared set-valued context contract; no universal semantic assessment.",),
        validations,
        fallback,
        strategy="structural-document",
        validation_scope="declared-idempotent-context-set",
        confidence="contract-validated",
        count_kind=str(count_metadata(counter)["kind"]),
    )
