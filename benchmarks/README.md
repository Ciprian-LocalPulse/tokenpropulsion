# Benchmarks

Run `tokenpropulsion benchmark --dataset benchmarks/datasets/sample.jsonl --repeats 10
-o benchmarks/results/local.json` on one line. Dataset contents are synthetic, created
for this project and licensed MIT. No customer or private prompts are included.

The generated report contains estimates, measured local times, deterministic formatting
checks, unchanged and naive-whitespace baselines, and explicit null remote metrics.
Reproduce dataset hashes and behavior; timing values naturally vary. See docs/evaluation.md.
