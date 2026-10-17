import math

import pytest

from tokenpropulsion import __version__, compress_prompt
from tokenpropulsion.exceptions import InputError
from tokenpropulsion.metrics import Pricing, percentile
from tokenpropulsion.protection import protection_reasons
from tokenpropulsion.tokenizer import EstimatedTokenizer
from tokenpropulsion.validators import validate_candidate


@pytest.mark.parametrize("level", ["low", "medium", "high"])
@pytest.mark.parametrize("text", ["", " ", "   ", "\n\n\n", "Hello.", "Explică stelele.  "])
def test_basic(text, level):
    result = compress_prompt(text, level)
    assert result.restore() == text
    assert result.optimized_tokens <= result.original_tokens
    assert not result.semantic_equivalence_assessed
    assert not result.counts_exact
    assert result.processing_seconds >= 0
    assert all(v.passed for v in result.validations)
    assert result.to_dict()["original_text"] == text
    assert __version__ == "1.0.0rc1"


def test_profiles_and_audit():
    text = "Explain  stars.\n\n\nWrite  simply.   "
    low = compress_prompt(text, "low")
    medium = compress_prompt(text)
    high = compress_prompt(text, "high")
    assert low.optimized_text == "Explain  stars.\n\n\nWrite  simply."
    assert medium.optimized_text == "Explain  stars.\n\nWrite  simply."
    assert high.optimized_text == "Explain stars.\n\nWrite simply."
    assert [s.name for s in high.transformations] == [
        "trailing_ascii_spaces",
        "blank_lines",
        "prose_spaces",
    ]
    assert high.transformations[0].before == text
    assert high.transformations[-1].after == high.optimized_text
    assert any("High" in w for w in high.warnings)


def test_no_word_deletion_and_idempotence():
    text = "Explain stars.\n\n\nExplain stars.   "
    result = compress_prompt(text)
    assert result.optimized_text.count("Explain stars.") == 2
    assert compress_prompt(result.optimized_text).optimized_text == result.optimized_text


@pytest.mark.parametrize(
    "text",
    [None, 2, b"hello", "\ud800", "a\0b", "a" * 1_000_001],
    ids=["none", "integer", "bytes", "surrogate", "nul", "oversized"],
)
def test_invalid_inputs(text):
    with pytest.raises(InputError):
        compress_prompt(text)


def test_invalid_level():
    with pytest.raises(InputError):
        compress_prompt("hello", "maximum")


def test_long_valid():
    text = "Stars shine.\n\n\n" * 50000
    result = compress_prompt(text)
    assert len(result.optimized_text) < len(text)
    assert result.optimized_text.count("Stars shine.") == 50000


@pytest.mark.parametrize("scale", [0, -1, math.inf, math.nan])
def test_bad_estimator(scale):
    with pytest.raises(ValueError):
        EstimatedTokenizer(scale)


def test_estimator_unicode():
    tokenizer = EstimatedTokenizer()
    assert tokenizer.count("") == 0
    assert tokenizer.count("a" * 5) == 2
    assert tokenizer.count("🌍") == 1
    assert tokenizer.count("ă" * 3) == 2
    assert "4" in tokenizer.identity


def test_exact_custom_counter_and_fallback():
    class Counting:
        identity = "test:character"
        exact = True

        def count(self, text):
            return len(text)

    result = compress_prompt("Hello.   ", tokenizer=Counting())
    assert result.counts_exact
    assert result.original_tokens == 9
    assert result.optimized_tokens == 6
    assert not any("estimates" in w for w in result.warnings)

    class Increasing(Counting):
        def count(self, text):
            return 1 if text.endswith(" ") else 10

    failed = compress_prompt("Hello.   ", tokenizer=Increasing())
    assert failed.fallback_triggered
    assert failed.optimized_text == failed.original_text
    assert failed.transformations == ()
    assert failed.original_tokens == failed.optimized_tokens

    class Invalid(Counting):
        def count(self, text):
            return -1

    with pytest.raises(ValueError):
        compress_prompt("Hello", tokenizer=Invalid())


def test_mechanical_validator():
    assert not validate_candidate("never do", "do", False)[0].passed
    assert not validate_candidate("a ", "a", True)[1].passed
    assert protection_reasons("password=EXAMPLE")


def test_pricing_and_percentiles():
    pricing = Pricing("test", 2, "USD", "https://example.org/prices", "2026-10-17")
    assert pricing.input_difference(1000000, 500000) == 1
    with pytest.raises(ValueError):
        pricing.input_difference(-1, 0)
    for rate in [-1, math.inf, math.nan]:
        with pytest.raises(ValueError):
            Pricing("test", rate, "USD", "source", "date")
    with pytest.raises(ValueError):
        Pricing("", 1, "USD", "", "")
    assert percentile([4, 1, 3, 2], 0.5) == 2.5
    assert percentile([1, 2, 3], 0.95) == pytest.approx(2.9)
    assert percentile([1], 0.95) == 1
    for values, q in [([], 0.5), ([1], -1), ([1], 2)]:
        with pytest.raises(ValueError):
            percentile(values, q)


def test_long_blank_lines():
    result = compress_prompt("\n" * 100_000)
    assert result.optimized_text == "\n\n"


def test_estimator_cannot_claim_exact():
    with pytest.raises(TypeError):
        EstimatedTokenizer(exact=True)
