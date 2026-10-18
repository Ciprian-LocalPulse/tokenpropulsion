# Remaining limitations

- No live xAI study: no verified Grok token savings, remote latency, answer quality,
  cached-cost behavior, streaming TTFT or invoice savings. No paid calls were made.
- No real-world corpus; synthetic long redundant contexts dominate the 29.557% result.
  The complex_reasoning category is only a keyword-preservation lexical toy.
- Semantic backend tested with a stub only. No real checkpoint, throughput, license
  validation or installed-semantic-extra dependency audit was performed.
- No verified-compatible local Grok tokenizer. cl100k_base is unrelated-tokenizer.
- Validators are scoped contracts, not semantic-equivalence proofs. Caller callbacks
  can be weak; duplicate contexts can influence downstream model behavior.
- Regex protection can over-refuse and miss sensitive meaning. Arabic/unfamiliar-script
  preservation is conservative and limits opportunities to compress multilingual inputs.
- Reversible encoding requires a programmatic decoder; no automatic LLM decoding claim.
- Budgets reserve estimated costs, do not guarantee provider billing caps, and cannot
  reconcile all partial-failure costs. Use provider-side controls.
- REST controls are per process and require reverse-proxy/TLS/concurrency configuration.
- No external audit, complete penetration test, peer review, LLMLingua benchmark or
  production workload study. Internal second-pass review is not third-party validation.
- Normal timing CI is descriptive; repeated mixed workloads are correlated.
- Stable and PyPI publication remain intentionally pending further validation.


Review scope: internal second-pass engineering review of final code and actual outputs;
not external independent certification, peer review or production approval.
Version 2.0.0a1; baseline 1.0.0rc1. Raw execution evidence: [evidence-v2](evidence-v2/).
