# Compression validation

| Path | Acceptance contract | Evidence | Limit |
|---|---|---|---|
| Conservative | ordered nonwhitespace/protection/count checks | tests/unit/test_core.py | formatting can carry meaning |
| Structural | explicit paragraph-set or caller contract | tests/unit/test_v2_engine.py | duplicates can be meaningful |
| Structured | independent ordered duplicate-section check | documents.py; validators.py; v2 engine tests | caller must establish idempotence |
| Lexical | explicit task callback, protection/count checks | test_v2_engine.py | four phrase rules; experimental |
| Semantic | local proposal plus explicit task callback | test_optional_local_model_backend | stub only, no real weights |
| Reversible | exact bounded decode | tests/security/test_v2_transport_budget.py | decoder overhead; not model-readable |

The [quality report](../benchmarks/results/v2.0.0a1/quality_report.json) records all
synthetic contracts passing. They cover set-like contexts, keywords and identity, not
natural language entailment or model output quality. Twenty protected rows are unchanged.
Caller preservation spans must retain occurrence counts. Validator exceptions, protected
candidate syntax and larger token counts cause original-text fallback.

Confidence labels are descriptive. `semantic_equivalence_assessed` remains false.
Cosine similarity and the separately authorized LLMJudge are observations, not acceptance
gates. Remote follow-up requires every optimized output to pass and no failed pair;
aggregate zero degradation alone is insufficient. No provider trial was executed.


Review scope: internal second-pass engineering review of final code and actual outputs;
not external independent certification, peer review or production approval.
Version 2.0.0a1; baseline 1.0.0rc1. Raw execution evidence: [evidence-v2](evidence-v2/).
