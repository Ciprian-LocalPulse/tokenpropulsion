import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from tokenpropulsion.api.app import create_app
from tokenpropulsion.benchmarks.laboratory import run_laboratory, task_value, timing_summary
from tokenpropulsion.benchmarks.remote import run_xai_study
from tokenpropulsion.budget import RequestBudget
from tokenpropulsion.cli import main
from tokenpropulsion.exceptions import InputError


@pytest.mark.parametrize("command", ["version", "doctor", "compress", "compare", "analyze"])
def test_new_cli_commands(command, capsys):
    args = [command] if command in {"version", "doctor"} else [command, "Stars shine.   "]
    assert main(args) == 0
    output = capsys.readouterr().out
    if command == "version":
        assert output.strip() == "2.0.0a1"
    elif command == "doctor":
        assert json.loads(output)["offline_default"]
    elif command in {"analyze", "compare"}:
        assert json.loads(output)["optimized_text"] == "Stars shine."
    else:
        assert output == "Stars shine."


def test_cli_contract_and_billing_gates(capsys, tmp_path):
    assert (
        main(
            [
                "compress",
                "Stars shine.\n\nStars shine.",
                "--level",
                "adaptive",
                "--contract",
                "paragraph-set",
            ]
        )
        == 0
    )
    assert capsys.readouterr().out == "Stars shine."
    assert (
        main(
            [
                "benchmark",
                "--provider",
                "xai",
                "--dataset",
                "benchmarks/datasets/remote_smoke.jsonl",
            ]
        )
        == 2
    )
    assert "invalid" in capsys.readouterr().err
    report = tmp_path / "report"
    assert (
        main(
            [
                "benchmark",
                "--dataset",
                "benchmarks/datasets/evaluation.jsonl",
                "--report",
                str(report),
                "--repeats",
                "2",
            ]
        )
        == 0
    )
    assert (report / "comparison.csv").exists()
    capsys.readouterr()
    assert (
        main(
            [
                "benchmark",
                "--dataset",
                "benchmarks/datasets/evaluation.jsonl",
                "--report",
                str(report),
            ]
        )
        == 2
    )


def test_laboratory_synthetic_contracts_and_evidence_preservation(tmp_path):
    dataset = Path("benchmarks/datasets/evaluation.jsonl")
    report = run_laboratory(dataset, tmp_path / "first", repeats=2)
    assert len(report["rows"]) == 30
    assert len({r["category"] for r in report["rows"]}) == 15
    assert report["task_success_rate"] == 1
    assert report["optimized_tokens"] < report["original_tokens"]
    assert report["model_output_quality"] is None
    assert report["grok_token_reduction"] is None
    assert report["invalid_transformation_rate"] == 0
    assert "<svg" in (tmp_path / "first/token-comparison.svg").read_text()
    assert "text" not in report["rows"][0]
    with pytest.raises(InputError):
        run_laboratory(dataset, tmp_path / "first", repeats=2)
    with pytest.raises(InputError):
        run_laboratory(dataset, tmp_path / "bad", repeats=1)
    provider = SimpleNamespace(identity="remote", exact=True, count_kind="provider-exact")
    with pytest.raises(InputError):
        run_laboratory(dataset, tmp_path / "net", tokenizer=provider)
    assert timing_summary([0.1])["sample_variance"] == 0
    with pytest.raises(InputError):
        timing_summary([])
    with pytest.raises(InputError):
        task_value("text", {"contract": "unsupported"})


def test_api_rate_limit_and_adaptive():
    token = "test-token-with-at-least-thirty-two-characters"
    client = TestClient(create_app(api_token=token, requests_per_minute=2))
    client.headers["Authorization"] = "Bearer " + token
    assert (
        client.post("/compress", json={"text": "Stars shine.   ", "level": "adaptive"}).status_code
        == 200
    )
    assert client.get("/health").status_code == 200
    response = client.get("/health")
    assert response.status_code == 429 and response.headers["Retry-After"] == "60"
    with pytest.raises(ValueError):
        create_app(api_token=token, requests_per_minute=0)


def test_remote_study_mocked_usage_cost_and_quality(tmp_path):
    from tokenpropulsion.adapters.xai import ProviderResult

    class Fake:
        model = "fake"
        max_retries = 0
        max_output_tokens = 16
        temperature = 0
        budget = RequestBudget(0.25, 0.01, 10)

        def _authorize(self, text):
            pass

        def request(self, text):
            self.budget.reserve()
            return ProviderResult(
                "OK", 4, 1, 5, 0.01, self.model, cached_input_tokens=2, reported_cost_usd=0.001
            )

    path = Path("benchmarks/datasets/remote_smoke.jsonl")
    with pytest.raises(InputError):
        run_xai_study(path, Fake())
    report = run_xai_study(path, Fake(), repeats=2, billing_authorized=True)
    assert report["task_success_rate"] == 1
    assert report["optimization_accepted_for_followup"]
    assert report["actual_billed_cost_difference"] is None
    assert report["measurements"][0]["original_cached_tokens"] == 2
    small = Fake()
    small.budget = RequestBudget(0.01, 0.01, 1)
    with pytest.raises(InputError):
        run_xai_study(path, small, repeats=2, billing_authorized=True)
    bad = tmp_path / "bad.jsonl"
    bad.write_text('{"id":"a","text":"text"}')
    with pytest.raises(InputError):
        run_xai_study(bad, Fake(), billing_authorized=True)


def test_remote_wrong_answers_rejected_and_full_preflight(tmp_path):
    from tokenpropulsion.adapters.xai import ProviderResult

    class Fake:
        model = "fake"
        max_retries = 0
        max_output_tokens = 16
        temperature = 0

        def __init__(self):
            self.budget = RequestBudget(0.25, 0.01, 10)
            self.calls = 0

        def _authorize(self, text):
            pass

        def request(self, text):
            self.calls += 1
            self.budget.reserve()
            return ProviderResult("WRONG", 4, 1, 5, 0.01, self.model)

    fake = Fake()
    report = run_xai_study(
        Path("benchmarks/datasets/remote_smoke.jsonl"),
        fake,
        repeats=2,
        billing_authorized=True,
    )
    assert report["quality_degradation"] == 0
    assert not report["optimization_accepted_for_followup"]
    rows = [
        {"id": "a", "text": "Reply OK.", "expected_output": "OK"},
        {"id": "b", "text": "text", "expected_output": "OK", "contract": "unsupported"},
    ]
    path = tmp_path / "invalid.jsonl"
    path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    fake = Fake()
    with pytest.raises(InputError):
        run_xai_study(path, fake, repeats=2, billing_authorized=True)
    assert fake.calls == 0


def test_schema_huge_integer_and_nonfinite():
    from tokenpropulsion.benchmarks.quality import validate_schema

    assert validate_schema(10**1000, {"type": "number"})
    assert not validate_schema(float("nan"), {"type": "number"})
    assert not validate_schema(True, {"type": "number"})


def test_api_body_timeout_is_sanitized(monkeypatch):
    import asyncio

    async def expired(coroutine, timeout):
        coroutine.close()
        raise asyncio.TimeoutError

    monkeypatch.setattr("tokenpropulsion.api.app.asyncio.wait_for", expired)
    token = "test-token-with-at-least-thirty-two-characters"
    client = TestClient(create_app(api_token=token))
    response = client.post(
        "/compress", json={"text": "PRIVATE"}, headers={"Authorization": "Bearer " + token}
    )
    assert response.status_code == 408
    assert "PRIVATE" not in response.text
