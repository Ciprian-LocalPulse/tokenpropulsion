"""Fail closed at prompt granularity: risky syntax disables all transformations.

Detection is deliberately broad and heuristic. Unknown syntax cannot be guaranteed safe.
"""

import re

from .security import looks_sensitive

_PATTERNS = {
    "quoted_literal": "[\"'“”‘’]",
    "markdown_hard_break": r" {2,}\r?\n",
    "code_or_structure": r"[`~{}\[\]<>]|^ *(?:[-*+] |#{1,6} |\d+[.)] )|[\t]|^ {4}",
    "structured_or_numeric": (
        r"[:=|,;\d]|\b(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|"
        r"TRUNCATE|GRANT|REVOKE|MERGE|WITH|PRAGMA|EXEC|CALL)\b"
    ),
    "address_or_identifier": r"https?://|www\.|@|[/\\_]|\$|\b\w+[.:-]\w+\b",
    "critical_instruction": (
        r"\b(?:not|never|no|only|exact|exactly|verbatim|preserve|must|shall|"
        r"system|developer|security|policy|ignore|override|and|or|if|unless|"
        r"nu|niciodată|doar|exact|sistem|politică)\b|[+*^%&!−≤≥]"
    ),
}
_COMPILED = [(name, re.compile(pattern, re.I | re.M)) for name, pattern in _PATTERNS.items()]


def protection_reasons(text: str) -> tuple[str, ...]:
    reasons = [name for name, pattern in _COMPILED if pattern.search(text)]
    if looks_sensitive(text):
        reasons.append("sensitive_content")
    # Unfamiliar scripts and control characters are preserved byte for byte.
    if any((ord(c) < 32 and c not in "\n\r\t") or ord(c) > 0x024F for c in text):
        reasons.append("unclassified_unicode")
    return tuple(reasons)
