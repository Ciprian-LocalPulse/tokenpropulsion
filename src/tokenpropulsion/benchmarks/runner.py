"""Offline accounting and explicit, repeated remote task experiments."""

import hashlib
import json
import re
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..compressor import compress_prompt
from ..exceptions import InputError
from ..metrics import Pricing, percentile
from ..security import MAX_INPUT_BYTES, validate_input
from ..tokenizer import EstimatedTokenizer


def load_dataset(path: Path) -> list[dict[str, Any]]:
    if path.stat().st_size > 10 * MAX_INPUT_BYTES:
        raise InputError("dataset exceeds ten megabytes")
    rows: list[dict[str, Any]] = []
    ids: set[str] = set()
    with path.open("rb") as stream:
        raw = stream.read(10 * MAX_INPUT_BYTES + 1)
    if len(raw) > 10 * MAX_INPUT_BYTES:
        raise InputError("dataset exceeds ten megabytes")
    for line in raw.decode("utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except (ValueError, RecursionError):
            raise InputError("invalid dataset JSON") from None
        if not isinstance(row, dict) or not isinstance(row.get("id"), str):
            raise InputError("each dataset row requires a string id")
        if len(row["id"]) > 128 or len(rows) >= 4096:
            raise InputError("dataset id or row limit exceeded")
        if row["id"] in ids:
            raise InputError("dataset ids must be unique")
        if not isinstance(row.get("text"), str):
            raise InputError("each dataset row requires string text")
        validate_input(row["text"])
        ids.add(row["id"])
        rows.append(row)
    if not rows:
        raise InputError("dataset must contain at least one row")
    return rows


def run_offline(path: Path, repeats: int = 5, level: str = "medium") -> dict[str, Any]:
    if not 1 <= repeats <= 100:
        raise InputError("repeats must be in [1,100]")
    rows = load_dataset(path)
    counter = EstimatedTokenizer()
    reports = []
    durations = []
    for row in rows:
        result = compress_prompt(row["text"], level)
        times = []
        for _ in range(repeats):
            start = time.perf_counter()
            compress_prompt(row["text"], level)
            times.append(time.perf_counter() - start)
        durations.extend(times)
        expected = row.get("expected_optimized")
        passed = expected is None or result.optimized_text == expected
        reports.append(
            {
                "id": row["id"],
                "category": row.get("category", "unspecified"),
                "original_tokens": result.original_tokens,
                "optimized_tokens": result.optimized_tokens,
                "whitespace_baseline_tokens": counter.count(
                    re.sub(r"\s+", " ", row["text"]).strip()
                ),
                "fallback": result.fallback_triggered,
                "fixture_passed": passed,
                "fixture_assessed": expected is not None,
                "p50_local_seconds": percentile(times, 0.5),
                "p95_local_seconds": percentile(times, 0.95),
            }
        )
    before = sum(r["original_tokens"] for r in reports)
    after = sum(r["optimized_tokens"] for r in reports)
    unmeasured = None
    return {
        "mode": "offline",
        "dataset_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "tokenizer": counter.identity,
        "counts_exact": False,
        "repeats": repeats,
        "level": level,
        "rows": reports,
        "original_tokens": before,
        "optimized_tokens": after,
        "estimated_tokens_saved_percent": 100 * (before - after) / before if before else 0,
        "p50_local_seconds": percentile(durations, 0.5),
        "p95_local_seconds": percentile(durations, 0.95),
        "fallback_rate": sum(r["fallback"] for r in reports) / len(reports),
        "failure_cases": [r["id"] for r in reports if not r["fixture_passed"]],
        "actual_token_reduction": unmeasured,
        "end_to_end_latency": None,
        "input_cost_difference": None,
        "output_quality": None,
        "task_success_rate": None,
        "limitations": [
            "Estimated text counts, not provider usage.",
            "Fixtures test formatting behavior, not model output quality.",
            "Whitespace baseline is intentionally unsafe and never sent automatically.",
        ],
    }


def run_remote(
    path: Path,
    adapter: Any,
    evaluator: Callable[[str, dict[str, Any]], bool],
    *,
    repeats: int = 3,
    pricing: Pricing | None = None,
    optimizer: Callable[[dict[str, Any]], Any] | None = None,
) -> dict[str, Any]:
    """Opt-in through adapter. Costs money. Report contains no prompt/output text.

    Provider-reported usage differences include variable provider overhead. Pair order is
    alternated, but this is not a randomized controlled experiment.
    """
    if not 2 <= repeats <= 100:
        raise InputError("remote repeats must be in [2,100]")
    if pricing is not None and pricing.model != adapter.model:
        raise InputError("pricing model must match adapter model")
    rows = load_dataset(path)
    # Preflight the full dataset before sending any content.
    for row in rows:
        adapter._authorize(row["text"])
    measurements = []
    failures = []
    for row in rows:
        compression = optimizer(row) if optimizer else compress_prompt(row["text"])
        for repeat in range(repeats):
            pair: dict[str, Any] = {}
            variants = [("original", row["text"]), ("optimized", compression.optimized_text)]
            if repeat % 2:
                variants.reverse()
            try:
                start = time.perf_counter()
                for name, text in variants:
                    pair[name] = adapter.request(text)
                elapsed = time.perf_counter() - start
                original, optimized = pair["original"], pair["optimized"]
                measurements.append(
                    {
                        "id": row["id"],
                        "repeat": repeat,
                        "actual_input_token_difference": original.input_tokens
                        - optimized.input_tokens,
                        "original_input_tokens": original.input_tokens,
                        "optimized_input_tokens": optimized.input_tokens,
                        "original_cached_tokens": getattr(original, "cached_input_tokens", None),
                        "optimized_cached_tokens": getattr(optimized, "cached_input_tokens", None),
                        "original_reported_cost_usd": getattr(original, "reported_cost_usd", None),
                        "optimized_reported_cost_usd": getattr(
                            optimized, "reported_cost_usd", None
                        ),
                        "original_output_tokens": original.output_tokens,
                        "optimized_output_tokens": optimized.output_tokens,
                        "original_success": bool(evaluator(original.content, row)),
                        "optimized_success": bool(evaluator(optimized.content, row)),
                        "pair_remote_seconds": elapsed,
                        "original_remote_seconds": original.remote_seconds,
                        "optimized_remote_seconds": optimized.remote_seconds,
                        "original_end_to_end_seconds": original.remote_seconds,
                        "optimized_end_to_end_seconds": (
                            optimized.remote_seconds + compression.processing_seconds
                        ),
                        "compression_seconds": compression.processing_seconds,
                        "fallback": compression.fallback_triggered,
                        "input_cost_difference": pricing.input_difference(
                            original.input_tokens, optimized.input_tokens
                        )
                        if pricing
                        else None,
                    }
                )
            except Exception:
                failures.append({"id": row["id"], "repeat": repeat, "error": "experiment failed"})
    times = [m["pair_remote_seconds"] for m in measurements]
    return {
        "mode": "remote",
        "model": adapter.model,
        "repeats": repeats,
        "dataset_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "measurements": measurements,
        "failure_cases": failures,
        "p50_pair_remote_seconds": percentile(times, 0.5) if times else None,
        "p95_pair_remote_seconds": percentile(times, 0.95) if times else None,
        "task_success_rate": (sum(m["optimized_success"] for m in measurements) / len(measurements))
        if measurements
        else None,
        "limitations": [
            "Exact provider usage; output quality is evaluator-specific.",
            "Retries may incur duplicate charges; caching can affect usage.",
            "No LLMLingua comparison was executed.",
        ],
    }
