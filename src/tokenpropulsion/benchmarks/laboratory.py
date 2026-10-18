"""Controlled synthetic task laboratory. Offline task scores are not LLM quality."""

import csv
import hashlib
import json
import platform
import re
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .. import __version__, compress_prompt
from ..documents import ContextSection, PromptDocument, compress_document
from ..exceptions import InputError
from ..metrics import percentile
from ..strategies import TaskValidator
from ..tokenizer import EstimatedTokenizer, Tokenizer, count_metadata
from .reporting import write_report
from .runner import load_dataset


def task_value(text: str, row: dict[str, Any]) -> Any:
    contract = row.get("contract", "identity")
    if contract == "paragraph-set":
        return sorted(set(part for part in re.split(r"\n\n+", text) if part))
    if contract == "keyword-task":
        words = re.findall(r"\b\w+\b", text.casefold())
        return [key for key in row["keywords"] if key in words]
    if contract == "document-set":
        data = json.loads(text)
        contexts = []
        seen = set()
        for section in data["contexts"]:
            key = json.dumps(section, sort_keys=True, ensure_ascii=False)
            if section["idempotent"] and key in seen:
                continue
            seen.add(key)
            contexts.append(section)
        return {**data, "contexts": contexts}
    if contract != "identity":
        raise InputError("unknown laboratory task contract")
    return text


def optimize_row(row: dict[str, Any], counter: Tokenizer) -> Any:
    if "document" in row:
        data = row["document"]
        document = PromptDocument(
            data["instructions"],
            tuple(ContextSection(**item) for item in data["contexts"]),
            data["question"],
        )
        if document.render() != row["text"]:
            raise InputError("document and serialized text disagree")
        return compress_document(document, tokenizer=counter)
    validator = None
    if row.get("contract", "identity") != "identity":
        validator = TaskValidator(
            str(row["contract"]), lambda a, b: task_value(a, row) == task_value(b, row)
        )
    return compress_prompt(
        row["text"],
        level="adaptive",
        strategy=row.get("strategy"),
        task_validator=validator,
        tokenizer=counter,
    )


def timing_summary(values: list[float]) -> dict[str, Any]:
    if not values:
        raise InputError("timing observations required")
    mean = statistics.mean(values)
    variance = statistics.variance(values) if len(values) > 1 else 0.0
    half = 1.96 * (variance / len(values)) ** 0.5
    return {
        "mean_seconds": mean,
        "median_seconds": statistics.median(values),
        "p50_seconds": percentile(values, 0.5),
        "p95_seconds": percentile(values, 0.95),
        "sample_variance": variance,
        "normal_95_ci_mean_seconds": [max(0, mean - half), mean + half],
        "ci_caveat": "Descriptive normal approximation; correlated repeats and mixed lengths.",
    }


def run_laboratory(
    dataset: Path, output: Path, *, repeats: int = 10, tokenizer: Tokenizer | None = None
) -> dict[str, Any]:
    if type(repeats) is not int or not 2 <= repeats <= 100:
        raise InputError("laboratory repeats must be in [2,100]")
    if output.exists() and any(output.iterdir()):
        raise InputError("laboratory output directory must be empty; old evidence is immutable")
    rows = load_dataset(dataset)
    counter = tokenizer if tokenizer is not None else EstimatedTokenizer()
    if count_metadata(counter)["kind"] == "provider-exact":
        raise InputError("offline laboratory cannot use a network tokenizer")
    records = []
    all_times = []
    for row in rows:
        # Baseline includes no compression and the existing protected formatting strategy.
        legacy = compress_prompt(row["text"], tokenizer=counter)
        result = optimize_row(row, counter)
        times = []
        for _ in range(repeats):
            start = time.perf_counter()
            optimize_row(row, counter)
            times.append(time.perf_counter() - start)
        all_times.extend(times)
        original_value = task_value(row["text"], row)
        optimized_value = task_value(result.optimized_text, row)
        records.append(
            {
                "id": row["id"],
                "category": row["category"],
                "strategy": result.strategy,
                "contract": row.get("contract", "identity"),
                "original_tokens": result.original_tokens,
                "conservative_tokens": legacy.optimized_tokens,
                "whitespace_tokens": counter.count(re.sub(r"\s+", " ", row["text"]).strip()),
                "optimized_tokens": result.optimized_tokens,
                "saved_percent": result.saved_percent,
                "task_passed": original_value == optimized_value,
                "protected_identity": row.get("contract", "identity") != "identity"
                or result.optimized_text == row["text"],
                "invalid_transformation": any(not v.passed for v in result.validations),
                "fallback": result.fallback_triggered,
                "semantic_equivalence_assessed": result.semantic_equivalence_assessed,
                "timing": timing_summary(times),
            }
        )
    total_before = sum(r["original_tokens"] for r in records)
    total_after = sum(r["optimized_tokens"] for r in records)
    unmeasured = None
    summary = {
        "version": __version__,
        "mode": "offline-synthetic",
        "model": None,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": str(dataset.name),
        "dataset_sha256": hashlib.sha256(dataset.read_bytes()).hexdigest(),
        "dataset_license": "MIT; project-authored synthetic fixtures",
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "tokenizer": count_metadata(counter),
        "repeats": repeats,
        "original_tokens": total_before,
        "optimized_tokens": total_after,
        "saved_percent": 100 * (total_before - total_after) / total_before if total_before else 0,
        "timing": timing_summary(all_times),
        "rows": records,
        "quality_scope": "Deterministic declared synthetic tasks; no model outputs evaluated.",
        "task_success_rate": sum(r["task_passed"] for r in records) / len(records),
        "invalid_transformation_rate": sum(r["invalid_transformation"] for r in records)
        / len(records),
        "fallback_rate": sum(r["fallback"] for r in records) / len(records),
        "remote_latency": None,
        "time_to_first_token": unmeasured,
        "provider_billed_cost_difference": None,
        "grok_token_reduction": unmeasured,
        "model_output_quality": unmeasured,
    }
    output.mkdir(parents=True, exist_ok=True)
    write_report(summary, output / "optimized.json")
    write_report(
        {
            "version": __version__,
            "dataset_sha256": summary["dataset_sha256"],
            "tokenizer": summary["tokenizer"],
            "rows": [
                {
                    k: r[k]
                    for k in (
                        "id",
                        "category",
                        "original_tokens",
                        "conservative_tokens",
                        "whitespace_tokens",
                    )
                }
                for r in records
            ],
        },
        output / "baseline.json",
    )
    write_report(
        {
            k: summary[k]
            for k in (
                "quality_scope",
                "task_success_rate",
                "invalid_transformation_rate",
                "fallback_rate",
                "model_output_quality",
            )
        },
        output / "quality_report.json",
    )
    with (output / "comparison.csv").open("w", newline="", encoding="utf-8") as stream:
        columns = [
            "id",
            "category",
            "strategy",
            "original_tokens",
            "conservative_tokens",
            "optimized_tokens",
            "saved_percent",
            "task_passed",
            "fallback",
        ]
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    failed = [r["id"] for r in records if not r["task_passed"] or not r["protected_identity"]]
    (output / "failures.md").write_text(
        "# Observed failures\n\n"
        + (
            "\n".join(f"- {item}" for item in failed)
            if failed
            else "No failures in defined synthetic tasks."
        )
        + "\n\nThis does not establish semantic equivalence or production accuracy.\n",
        encoding="utf-8",
    )
    (output / "performance_summary.md").write_text(
        f"# Measured synthetic laboratory\n\nVersion {__version__}; "
        f"{len(records)} rows; {repeats} repeats.\n\n"
        f"Tokenizer: {counter.identity}; provenance: {count_metadata(counter)['kind']}.\n\n"
        f"Counts: {total_before} -> {total_after}; reduction {summary['saved_percent']:.3f}%.\n\n"
        f"p50 {summary['timing']['p50_seconds'] * 1000:.4f} ms; "
        f"p95 {summary['timing']['p95_seconds'] * 1000:.4f} ms.\n\n"
        "Quality covers declared synthetic contracts only. Grok usage, model output quality, "
        "Billing, remote latency and TTFT are unmeasured. See JSON for CI caveats.\n",
        encoding="utf-8",
    )
    _chart(records, output / "token-comparison.svg")
    return summary


def _chart(rows: list[dict[str, Any]], path: Path) -> None:
    # Scientific vector plot generated solely from measured count records; no image synthesis.
    from html import escape

    width, row_height = 1000, 30
    maximum = max(1, max(r["original_tokens"] for r in rows))
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{90 + len(rows) * row_height}" role="img">',
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        '<text x="24" y="28" font-size="18">Measured counts: original / optimized</text>',
        '<text x="24" y="51" font-size="12">Synthetic; not Grok usage or model quality.</text>',
    ]
    for i, row in enumerate(rows):
        y = 80 + i * row_height
        elements.append(f'<text x="24" y="{y + 10}" font-size="12">{escape(row["id"])}</text>')
        for field, color, offset in [
            ("original_tokens", "#94a3b8", 0),
            ("optimized_tokens", "#0284c7", 10),
        ]:
            bar = 650 * row[field] / maximum
            elements.append(
                f'<rect x="220" y="{y + offset}" width="{bar:.2f}" height="8" fill="{color}"/>'
            )
    elements.append("</svg>")
    path.write_text("\n".join(elements), encoding="utf-8")
