# Final technical audit - 2.0.0a1

## Implemented and tested

- Existing formatting API, flat CLI, result restoration and protected inputs retained.
  Original baseline: 191 passing tests; expanded suite: 272 passed, zero failures.
  See [test log](evidence-v2/pytest.txt), [JUnit](evidence-v2/tests.xml) and
  [baseline evidence](evidence-baseline/pytest.txt).
- Structural and lexical proposals require an explicit task validator; adaptive defaults
  to conservative behavior. Failure or increased count returns the original. Evidence:
  src/tokenpropulsion/engine.py and tests/unit/test_v2_engine.py.
- Structured context deduplication preserves instructions/question/source/trust and
  removes only exact declared-idempotent duplicates. Producer and independent validator:
  src/tokenpropulsion/documents.py, validators.py; tests/unit/test_v2_engine.py.
- Bounded reversible transport, mandatory decoder accounting, token provenance,
  request reservations, cached/provider cost extraction, sync/async integration,
  expanded CLI, REST process limiter and body timeout. Evidence: tests/security/
  test_v2_transport_budget.py and tests/integration/test_v2_interfaces.py.
- Remote study preflights every task before network use; all wrong answers and any
  optimized answer failure reject follow-up. Regression test:
  test_remote_wrong_answers_rejected_and_full_preflight.

## Measured local evidence

[Raw laboratory](../benchmarks/results/v2.0.0a1/optimized.json): 30 synthetic cases,
15 categories, 10 repeats. Exact unrelated cl100k_base counts 8871 -> 6249 (29.556983%).
Task-contract success 100%; fallback and invalid transformations 0%. This is neither
Grok usage nor model answer accuracy. Mean 2.450484 ms, p50 0.160750 ms,
p95 23.378860 ms. Token-weighted result is dominated by redundant long contexts.

## Implemented but not independently validated

Official SDK behavior is mocked in tests; no live provider call was performed. Compatible
local provenance is recognized but no compatible Grok tokenizer implementation/evidence
is provided. Audit findings are authored within the implementation session.

## Experimental

Lexical reductions, local embedding proposals, optional judge observations and the
synthetic laboratory's applicability to real-world tasks. Semantic backend loading is
stub-tested; no real checkpoint quality/performance result exists.

## Not implemented or externally blocked

No streaming TTFT, invoice reconciliation, distributed rate limiter, real-world corpus,
LLMLingua execution or stable/PyPI release. Live xAI and loaded-model evaluations require
reviewed credentials/model/budget or local weights. No paid call is authorized by the
absence of those prerequisites. See [limitations](REMAINING_LIMITATIONS.md).

Ruff, strict mypy, Bandit, dependency scan, build, Twine and clean installation are
recorded in the execution report. Alpha evaluation is appropriate; production readiness
is not established. Historical reports, v1 paper and v1 release remain preserved.


Review scope: internal second-pass engineering review of final code and actual outputs;
not external independent certification, peer review or production approval.
Version 2.0.0a1; baseline 1.0.0rc1. Raw execution evidence: [evidence-v2](evidence-v2/).
