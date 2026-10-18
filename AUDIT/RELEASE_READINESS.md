# Release readiness - research alpha

**Suitable for an explicitly limited 2.0.0a1 prerelease; not production ready.**

Implemented/tested: backward-compatible defaults, contract-gated advanced strategies,
structured contexts, reversible decoder, provenance labels, REST/CLI, mocked SDK/budget
behavior, measured synthetic laboratory. See [final audit](FINAL_TECHNICAL_AUDIT.md).
Local execution: 272 passing tests, coverage above 90%, static/security/build/install
checks recorded in [execution evidence](TEST_EXECUTION_REPORT.md).

Experimental: lexical rules, semantic backend and judge. Implemented but not independently
validated: real SDK behavior and checkpoint loading. Blocked on external prerequisites:
live provider/model/budget and reviewed local model weights. Not implemented: streaming
TTFT, invoice reconciliation, distributed rate limiting, real-world validation, LLMLingua
comparison. These are explicit alpha limitations, not waived stable release requirements.

Publication policy: preserve v1.0.0rc1 and its assets; create v2.0.0a1 as a prerelease
only after hosted CI passes. Publish source/wheel/sdist/PDF/evidence with checksums and
provenance. No PyPI workflow is dispatched. Timing reproducibility is procedural, not
an identical-runtime guarantee. Dataset/report hashes identify fixed evidence.
See GitHub Actions for the final tag's executed matrix; do not infer hosted success from
local results. Release assets and GitHub publication are verified after upload.


Review scope: internal second-pass engineering review of final code and actual outputs;
not external independent certification, peer review or production approval.
Version 2.0.0a1; baseline 1.0.0rc1. Raw execution evidence: [evidence-v2](evidence-v2/).
