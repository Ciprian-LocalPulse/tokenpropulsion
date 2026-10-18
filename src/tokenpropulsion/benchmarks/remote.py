"""Explicit billable study with reservations. No hard provider-side cap is claimed."""

from pathlib import Path
from typing import Any

from ..budget import RequestBudget
from ..exceptions import InputError
from ..tokenizer import EstimatedTokenizer
from .laboratory import optimize_row, task_value
from .quality import evaluate
from .runner import load_dataset, run_remote


def run_xai_study(
    path: Path, adapter: Any, *, repeats: int = 3, billing_authorized: bool = False
) -> dict[str, Any]:
    if not billing_authorized or not isinstance(adapter.budget, RequestBudget):
        raise InputError("explicit billing authorization and RequestBudget required")
    rows = load_dataset(path)
    prepared = {}
    for row in rows:
        if not isinstance(row.get("expected_output"), str) or row.get(
            "output_evaluator", "exact"
        ) not in {"exact", "json"}:
            raise InputError("every remote row needs expected_output and exact/json evaluator")
        adapter._authorize(row["text"])
        task_value(row["text"], row)
        prepared[row["id"]] = optimize_row(row, EstimatedTokenizer())
        adapter._authorize(prepared[row["id"]].optimized_text)
    required = len(rows) * repeats * 2 * (1 + adapter.max_retries)
    if (
        required + adapter.budget.requests_reserved > adapter.budget.max_requests
        or adapter.budget.reserved_usd + required * adapter.budget.reservation_per_request_usd
        > adapter.budget.max_usd + 1e-12
    ):
        raise InputError("full study exceeds reserved request or spending limit")
    report = run_remote(
        path,
        adapter,
        lambda output, row: evaluate(
            output, row["expected_output"], row.get("output_evaluator", "exact")
        ),
        repeats=repeats,
        optimizer=lambda row: prepared[row["id"]],
    )
    observations = report["measurements"]
    loss = (
        (
            sum(m["original_success"] - m["optimized_success"] for m in observations)
            / len(observations)
        )
        if observations
        else None
    )
    report["quality_degradation"] = loss
    report["optimization_accepted_for_followup"] = (
        bool(observations)
        and all(m["optimized_success"] for m in observations)
        and not report["failure_cases"]
    )
    report["budget"] = adapter.budget.snapshot()
    report["generation"] = {
        "max_output_tokens": adapter.max_output_tokens,
        "temperature": adapter.temperature,
    }
    report["actual_billed_cost_difference"] = None
    report["cost_scope"] = "Provider-reported usage/cost is not invoice reconciliation."
    report["time_to_first_token"] = None
    return report
