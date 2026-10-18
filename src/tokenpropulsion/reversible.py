"""Exact bounded transport codec. Decode before inference: no LLM token savings claim."""

import base64
import binascii
import json
import zlib
from dataclasses import dataclass

from .exceptions import InputError
from .security import MAX_INPUT_BYTES, validate_input
from .tokenizer import Tokenizer


@dataclass(frozen=True)
class WireEnvelope:
    payload: str
    original_bytes: int
    wire_bytes: int
    decoder_required: bool = True
    provider_token_savings_claimed: bool = False


def pack_context(text: str) -> WireEnvelope:
    validate_input(text)
    compressed = base64.b64encode(zlib.compress(text.encode("utf-8"), level=9)).decode("ascii")
    payload = json.dumps({"codec": "tp-zlib-base64-v1", "data": compressed}, separators=(",", ":"))
    return WireEnvelope(payload, len(text.encode("utf-8")), len(payload.encode("utf-8")))


def unpack_context(payload: str) -> str:
    validate_input(payload, 2 * MAX_INPUT_BYTES)
    try:
        envelope = json.loads(payload)
        if set(envelope) != {"codec", "data"} or envelope["codec"] != "tp-zlib-base64-v1":
            raise ValueError
        encoded = base64.b64decode(envelope["data"], validate=True)
        decoder = zlib.decompressobj()
        raw = decoder.decompress(encoded, MAX_INPUT_BYTES + 1)
        if (
            len(raw) > MAX_INPUT_BYTES
            or not decoder.eof
            or decoder.unused_data
            or decoder.unconsumed_tail
        ):
            raise ValueError
        text = raw.decode("utf-8")
        validate_input(text)
        return text
    except (ValueError, TypeError, KeyError, zlib.error, binascii.Error, RecursionError):
        raise InputError("invalid or oversized transport envelope") from None


def wire_accounting(text: str, decoder_prompt: str, tokenizer: Tokenizer) -> dict[str, int | bool]:
    """Count the complete hypothetical wire + decoder text, never just compressed bytes."""
    packed = pack_context(text)
    return {
        "original_tokens": tokenizer.count(text),
        "wire_plus_decoder_tokens": tokenizer.count(packed.payload + decoder_prompt),
        "actual_provider_savings_verified": False,
    }
