"""CI gate for real deterministic benchmark fixtures, no timing thresholds."""

import json
from pathlib import Path

from tokenpropulsion.benchmarks.runner import run_offline

report = run_offline(Path("benchmarks/datasets/sample.jsonl"), repeats=2)
if report["failure_cases"]:
    raise SystemExit("Benchmark fixture failures")
stored = json.loads(Path("benchmarks/results/local.json").read_text(encoding="utf-8"))
if stored["dataset_sha256"] != report["dataset_sha256"]:
    raise SystemExit("Published benchmark dataset hash mismatch")
print("All synthetic formatting fixtures and the published dataset hash passed.")
