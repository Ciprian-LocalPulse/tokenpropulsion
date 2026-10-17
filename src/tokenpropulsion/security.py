"""Input limits and conservative sensitive-content hints, not a DLP system."""

import re

from .exceptions import InputError, NetworkDisabledError

MAX_INPUT_BYTES = 1_000_000
_SECRET = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----|\b(?:api[_ -]?key|password|secret|token)\s*[:=]",
    re.IGNORECASE,
)


def validate_input(text: str, max_bytes: int = MAX_INPUT_BYTES) -> None:
    if not isinstance(text, str):
        raise InputError("text must be a string")
    try:
        size = len(text.encode("utf-8"))
    except UnicodeEncodeError:
        raise InputError("text must contain valid Unicode scalars") from None
    if size > max_bytes:
        raise InputError("input exceeds the configured byte limit")
    if "\x00" in text:
        raise InputError("NUL characters are unsupported")


def looks_sensitive(text: str) -> bool:
    return bool(_SECRET.search(text))


def authorize_network(enabled: bool, text: str, allow_sensitive: bool = False) -> None:
    validate_input(text)
    if not enabled:
        raise NetworkDisabledError("network access requires allow_network=True")
    if looks_sensitive(text) and not allow_sensitive:
        raise NetworkDisabledError("sensitive content requires allow_sensitive=True")
