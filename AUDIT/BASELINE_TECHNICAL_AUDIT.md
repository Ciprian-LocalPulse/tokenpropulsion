# Baseline technical audit - before 2.0 development

Author: Ciprian Ștefan Pleșca. Review date: 2026-10-17.
Baseline commit: `509683915b376613c8e711fc042ceebe3abb666e`. Branch main; initially clean working tree, fast-forwarded
to preserve the user's accepted dependency PRs. Existing published tag `v1.0.0rc1`
remains at 5f964e3; it is not overwritten. MIT license and original authorship retained.

## Inventory and inspection

All 86 tracked files were read and hashed before source changes;
see baseline-inventory.json. Inspection covered README, the complete 10,000-word
whitepaper, source, tests, synthetic dataset, reports, security policies, CLI examples,
PDF/render tooling, assets/provenance, CI and trusted-publishing configuration.
Binary PDF/image assets were inspected earlier and retained unchanged.

## Implemented and tested before development

- Dependency-free src-layout package; Python >=3.10; 1.0.0rc1 API.
- Low/medium/high deterministic formatting; whole-prompt regex protections.
- Frozen prompt-bearing results, ordered-nonwhitespace/protected-identity/count checks,
  original-text fallback, restoration and JSON serialization.
- UTF-8 byte/4 configurable estimate. Custom tokenizer protocol and explicit remote
  official xAI text tokenization; no compatible local Grok tokenizer established.
- Sync/async SDK requests, explicit network/sensitive opt-ins, environment key,
  bounded transient retries, sanitized errors; original/optimized comparison.
- CLI positional text, files/stdin, analyze, offline benchmark, JSON/stats, exit codes.
- Authenticated bounded FastAPI factory; docs disabled; sanitized validation errors.
- Nine-category synthetic fixtures; offline/remote benchmark functions, partial JSON
  schema checks, exact/JSON output evaluator and fixed-rate input cost arithmetic.
- Public repository/release, 8K upscaled artwork with provenance, 23-page whitepaper.
- Hosted CI Python 3.10-3.14 and Security passed on current baseline source.

## Executed baseline

Python 3.12.14, Windows x64. 191 tests passed,
0 failures, 0 errors.
Line coverage: 99.61%; combined coverage:
99.54%. Ruff, strict mypy, Bandit, sdist/wheel build
executed before development; logs and raw reports retained in work/phase0 and a
summary is preserved here. One Starlette httpx transport deprecation warning.
Published historical local benchmark remains untouched: 3829 -> 3578 heuristic
estimated tokens (6.5552%); no provider quality/cost/latency data.

## Limitations and findings to address

1. No structural, lexical, semantic or adaptive strategy; no task-validated acceptance.
2. Exactness boolean cannot distinguish provider counts, compatible local counts,
   unrelated vocabulary counts and heuristics; bool counts are accidentally accepted.
3. Provider usage is sometimes described as billed input even though no invoice
   reconciliation exists. Cached input and cost ticks are not exposed; retries may
   duplicate charges and partial failed pairs omit incurred usage. No study budget.
4. Remote benchmark is Python-only; CLI lacks requested subcommands and billable gates.
5. Whole-prompt protection deliberately over-refuses; no domain-specific guarantee.
   Legal/medical terminology is not an explicit category. Similarity cannot prove meaning.
6. Schema subset is documented but numerical NaN/Infinity require stricter checks;
   deeply nested JSON and dataset TOCTOU/resource bounds need review.
7. API lacks an application-level rate limiter; upstream deployment controls documented.
8. Nine synthetic rows and timing percentiles are not production-quality evidence;
   no confidence intervals, controlled 15-category laboratory, or measured charts.
9. Optional model backends, shared-dictionary wire formats, and decoder accounting absent.
10. Docs, version tests and scripts refer to 1.0.0rc1 and must preserve historical evidence
    while adding new editions. Dependency snapshots are dated observations, not locks.

## Development decisions

Implement an additive 2.0.0a1 prerelease, preserve low/medium/high defaults and old
reports. Structural/lexical/model changes require task-specific validation plus hard
protection; adaptive must refuse unverifiable changes. Reversible wire compression
requires decoding before model inference and cannot claim provider savings. Network
benchmarks require explicit billing authorization and conservative reservation limits.
No API key is printed, transmitted or retained; live xAI is pending when absent.
This is an internal engineering audit, not independent certification or peer review.
