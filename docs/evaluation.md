# Evaluation methodology

The checked-in synthetic JSONL dataset contains nine categories and deterministic
`expected_optimized` formatting fixtures. Offline reports record a dataset SHA-256,
profile, estimator identity, repetitions, unchanged-input baseline, naive whitespace
baseline, protected formatting counts, local p50/p95, fallback rate, and fixture failures.
Percentiles use linear interpolation over sorted observations. Timings include interpreter
and system noise; no fixed performance threshold is claimed. IDs and counts are exported,
not prompt text. The simple whitespace baseline may damage code and exact outputs.

Offline counts are estimates. `actual_token_reduction`, remote end-to-end latency,
cost difference, output quality, and task success are null rather than invented.
Fixture correctness describes formatting, not model task success or semantic equivalence.

`run_remote(path, adapter, evaluator, repeats=3, pricing=None)` preflights the full dataset,
then performs original/optimized pairs with alternating order, identical model parameters,
provider usage, separate per-request and paired remote latency, local compression latency,
output-token usage, evaluator-specific task success, failures, and optional input cost.
Add compression time to optimized request latency for per-variant end-to-end comparisons.
Use reviewed synthetic datasets and explicit network opt-in; transmitted prompts may be
retained under the provider's policies. `allow_sensitive` is not a substitute for review.
Remote failures remain reported; successful-only latency summaries have selection bias.

Exact-output checks and a deliberately small strict schema validator are included.
The schema helper accepts a documented subset, not all JSON Schema. Supply a full
validator externally when tasks require it. Numeric tasks can use exact checks or
caller-written numeric tolerances. No universal output-quality score is claimed.

No LLMLingua run was performed. A future comparison must pin its code and model,
respect licenses, use identical tasks and provider configuration, measure its own CPU/GPU
overhead, and report task quality and failure cases. No live xAI measurements were made.
