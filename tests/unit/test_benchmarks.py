import json
from pathlib import Path

import pytest

from tokenpropulsion.benchmarks.quality import evaluate, validate_schema
from tokenpropulsion.benchmarks.reporting import write_report
from tokenpropulsion.benchmarks.runner import load_dataset, run_offline, run_remote
from tokenpropulsion.exceptions import InputError
from tokenpropulsion.metrics import Pricing


def test_offline_and_report(tmp_path):
    path = Path("benchmarks/datasets/sample.jsonl")
    first, second = run_offline(path, 2), run_offline(path, 2)
    assert first["dataset_sha256"] == second["dataset_sha256"]
    assert first["failure_cases"] == []
    assert first["original_tokens"] == second["original_tokens"]
    assert first["actual_token_reduction"] is None
    assert len(first["rows"]) == 9
    out = tmp_path / "nested" / "report.json"
    write_report(first, out)
    assert json.loads(out.read_text())["counts_exact"] is False
    assert '"text"' not in out.read_text()
    with pytest.raises(InputError):
        run_offline(path, 0)


@pytest.mark.parametrize(
    "content",
    ["", "[]", "{}", '{"id":"a","text":2}', '{"id":"a","text":"x"}\n{"id":"a","text":"y"}'],
)
def test_bad_dataset(content, tmp_path):
    path = tmp_path / "data"
    path.write_text(content)
    with pytest.raises(InputError):
        load_dataset(path)


def test_large_and_empty_dataset(tmp_path):
    path = tmp_path / "data"
    path.write_bytes(b"x" * 10000001)
    with pytest.raises(InputError):
        load_dataset(path)
    path.write_text('\n{"id":"a","text":""}\n')
    report = run_offline(path, 1)
    assert report["estimated_tokens_saved_percent"] == 0
    path.write_text('{"id":"a","text":"x","expected_optimized":"y"}')
    assert run_offline(path, 1)["failure_cases"] == ["a"]


def test_evaluators():
    assert evaluate("OK", "OK")
    assert not evaluate("ok", "OK")
    assert evaluate('{"x":1}', '{ "x": 1 }', "json")
    assert not evaluate("no", "{}", "json")
    assert not evaluate("true", "1", "json")
    assert not evaluate("NaN", "NaN", "json")
    assert not evaluate('{"x":1,"x":2}', '{"x":2}', "json")
    with pytest.raises(ValueError):
        evaluate("x", "x", "semantic")
    schema = {
        "type": "object",
        "properties": {"x": {"type": "integer"}},
        "required": ["x"],
        "additionalProperties": False,
    }
    assert validate_schema({"x": 1}, schema)
    assert not validate_schema({"x": True}, schema)
    assert not validate_schema({}, schema)
    assert not validate_schema({"x": 1, "y": 2}, schema)
    assert not validate_schema([], schema)
    for kind, value in [
        ("null", None),
        ("boolean", True),
        ("string", "a"),
        ("array", []),
        ("number", 1.2),
    ]:
        assert validate_schema(value, {"type": kind})
    with pytest.raises(ValueError):
        validate_schema(1, {"type": "integer", "minimum": 0})
    with pytest.raises(ValueError):
        validate_schema(1, {"type": "unknown"})


def test_remote_measurement_with_fake_provider(tmp_path):
    from tokenpropulsion.adapters.xai import ProviderResult

    path = tmp_path / "data"
    path.write_text('{"id":"a","text":"Hello.   ","expected_output":"OK"}')

    class Fake:
        model = "fake"

        def _authorize(self, text):
            pass

        def request(self, text):
            return ProviderResult("OK", len(text), 1, len(text) + 1, 0.01, self.model)

    report = run_remote(
        path,
        Fake(),
        lambda text, row: text == row["expected_output"],
        repeats=2,
        pricing=Pricing("fake", 1, "USD", "source", "date"),
    )
    assert report["task_success_rate"] == 1
    assert report["measurements"][0]["actual_input_token_difference"] == 3
    assert report["measurements"][0]["input_cost_difference"] == 0.000003
    assert run_remote(path, Fake(), lambda text, row: True, repeats=2)["measurements"]
    with pytest.raises(InputError):
        run_remote(path, Fake(), lambda text, row: True, repeats=1)
    with pytest.raises(InputError):
        run_remote(
            path,
            Fake(),
            lambda text, row: True,
            pricing=Pricing("different", 1, "USD", "source", "date"),
        )

    class Failing(Fake):
        def request(self, text):
            raise RuntimeError("private provider details")

    failed = run_remote(path, Failing(), lambda text, row: True, repeats=2)
    assert len(failed["failure_cases"]) == 2
    assert failed["p50_pair_remote_seconds"] is None
    assert "private" not in json.dumps(failed)
