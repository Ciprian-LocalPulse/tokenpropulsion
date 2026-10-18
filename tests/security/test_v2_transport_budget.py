import base64
import json
import math
import zlib
from concurrent.futures import ThreadPoolExecutor

import pytest

from tokenpropulsion.budget import RequestBudget
from tokenpropulsion.exceptions import InputError
from tokenpropulsion.reversible import pack_context, unpack_context, wire_accounting
from tokenpropulsion.tokenizer import EstimatedTokenizer


@pytest.mark.parametrize("text", ["", "Ștefan\r\n  literal", "العربية", "Stars shine. " * 1000])
def test_exact_transport_round_trip(text):
    envelope = pack_context(text)
    assert unpack_context(envelope.payload) == text
    assert envelope.wire_bytes == len(envelope.payload.encode())
    assert envelope.decoder_required and not envelope.provider_token_savings_claimed
    measured = wire_accounting(text, "Decoder instruction overhead", EstimatedTokenizer())
    assert measured["wire_plus_decoder_tokens"] >= EstimatedTokenizer().count(envelope.payload)
    assert not measured["actual_provider_savings_verified"]


@pytest.mark.parametrize(
    "payload",
    [
        "[]",
        "{}",
        "null",
        "not json",
        '{"codec":"wrong","data":""}',
        '{"codec":"tp-zlib-base64-v1","data":"!"}',
    ],
)
def test_malformed_envelopes(payload):
    with pytest.raises(InputError):
        unpack_context(payload)


def test_decompression_bomb_and_trailing_stream_rejected():
    raw = zlib.compress(b"x" * 1_000_001)
    for encoded in [raw, zlib.compress(b"x") + b"trailing", zlib.compress(b"x")[:-2]]:
        payload = json.dumps(
            {"codec": "tp-zlib-base64-v1", "data": base64.b64encode(encoded).decode()}
        )
        with pytest.raises(InputError):
            unpack_context(payload)


def test_budget_reservations_are_atomic_and_failures_not_refunded():
    budget = RequestBudget(0.10, 0.01, 10)

    def attempt(_):
        try:
            budget.reserve()
            return True
        except InputError:
            return False

    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(attempt, range(40))) == 10
    assert budget.requests_reserved == 10
    assert budget.snapshot()["reserved_usd"] == pytest.approx(0.10)
    assert not budget.snapshot()["provider_side_hard_cap"]
    with pytest.raises(InputError):
        budget.reserve()


def test_reported_cost_guard_and_validation():
    budget = RequestBudget(0.05, 0.01)
    budget.observe(None)
    budget.observe(0.06)
    assert budget.reported_limit_exceeded
    with pytest.raises(InputError):
        budget.reserve()
    for amount in [-1, math.nan, math.inf]:
        with pytest.raises(InputError):
            budget.observe(amount)
    for max_usd, reservation, requests in [
        (0, 0.1, 1),
        (0.1, 0, 1),
        (math.inf, 0.1, 1),
        (0.1, 0.1, 0),
    ]:
        with pytest.raises(InputError):
            RequestBudget(max_usd, reservation, requests)
