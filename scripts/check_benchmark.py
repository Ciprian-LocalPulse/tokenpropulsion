"""CI gate for real deterministic benchmark fixtures, no timing thresholds."""

from pathlib import Path

from tokenpropulsion.benchmarks.runner import run_offline

report = run_offline(Path("benchmarks/datasets/sample.jsonl"), repeats=2)
if report["failure_cases"]:
    raise SystemExit("Benchmark fixture failures")
print("All synthetic formatting fixtures passed.")
