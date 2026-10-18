# Ecosystem final engineering audit

2026-10-18. Internal second-pass review of actual artifacts and executed results;
not an external independent certification. Public Core behavior/version preserved.

## 1. Public Core

https://github.com/Ciprian-LocalPulse/tokenpropulsion remains public/MIT. Released
v2.0.0a1 and prior v1 assets/tags are unchanged. Regression rerun: 272 passed, zero failed,
95.44% combined coverage. Evidence: evidence-ecosystem/core-regression.txt and core-coverage.json.
Existing release-commit hosted CI passed Python 3.10-3.14 and Security.

## 2. Private Enterprise

A separate repository was created and verified PRIVATE before and after source push.
Its URL and internal business documents are omitted from this public report. Version
0.1.0a1 is a foundation, not a stable Enterprise release. No private code is in Core/site.

## 3. Implemented Enterprise foundation

Functional composition over pinned MIT Core; organization/role access boundaries;
server-side signed entitlement verification; bounded prompt-free provenance-separated
analytics; explicit provider consent/budget boundary; optional authenticated API;
local synthetic analytics dashboard. Private tests: 25 passed; 99.46% combined coverage.
Ruff/format/mypy/Bandit pass. Private CI passes on Python 3.10, 3.12 and 3.14.
Build and clean offline wheel integration are verified in the private audit.

## 4. Public website

https://github.com/Ciprian-LocalPulse/tokenpropulsion-site contains an original dark,
responsive, accessible static landing page, safety/benchmark disclosures, API/CLI examples,
open-source/Enterprise research descriptions, documentation, FAQ and non-confidential
GitHub inquiry links. No invented contact address, customer logos or endorsement.

## 5. Verified deployment

https://ciprian-localpulse.github.io/tokenpropulsion-site/ is deployed with GitHub Pages.
Index, recordings, both MP4s and captions matched canonical public Git blob hashes.
Twelve external links returned HTTP 200. Raw results: evidence-ecosystem/site-deployment.json.

## 6. Interactive recorded demonstration

Five real Python-engine recordings, selectable read-only inputs/outputs, counts, percentage,
recorded duration, strategy, tokenizer, warnings and scoped validation. Static recording
labels are explicit. No browser imitation of compression or arbitrary-input processing.

## 7. Video production

Two actual 35.000-second, 30fps H.264/AAC MP4s: 1920x1080 and 1080x1920. Original motion
and quiet ambient score, offline generic English narration, actual word-event synchronized
SRT/WebVTT/burned-in captions. Full CLI stdout, script, storyboard, poster, audio and
reproducible render source/QC are in the public site's video/ directory.
All 1050 frames per video were decoded for structural checks; representative decoded
scenes visually reviewed. No clipped audio samples detected. Human listening/creative
review and broadcast loudness certification were not performed.

## 8. Website tests and accessibility

Three Node data/resource tests passed. Six Chromium flows passed locally and against
the deployed site: 320/390/768/1440px reflow, all recorded example values, keyboard,
reduced motion, axe WCAG 2 A/AA + 2.1 AA subset and actual MP4 playback/English track.
No automated accessibility violations in tested views; not full accessibility certification.
Website audit/evidence and video/VIDEO_QC.json provide actual outputs.

## 9. Security findings

No known vulnerabilities in audited installed dependencies and npm development packages.
The initial Enterprise Python 3.10 runner had vulnerable preinstalled setuptools 79.0.1;
upgrading tooling to >=83 resolved the CI audit without suppressing the advisory.
Public scanning/least-privilege workflow controls are enabled where supported. Private
GitHub plan restrictions remain documented privately, with PRIVATE visibility preserved.
No provider credential or paid call was used. Deployment still needs workload-specific
operational review before any production Enterprise service.

## 10. Separation

See PUBLIC_PRIVATE_BOUNDARY_REPORT.md and evidence-ecosystem/boundary-check.json.
No private source/business document content, private imports or internal dashboard event
IDs were found in the public artifacts. No private repository URL is in the host bundle.

## 11. Licensing

MIT Core remains MIT; site original code/content includes MIT notice. Enterprise additions
are separately identified, proprietary and private. Third-party licenses remain theirs.
Font/voice/FFmpeg binaries are not redistributed. No model checkpoint is bundled.

## 12. Measurements and remaining limits

Historical exact unrelated cl100k_base: 8871 -> 6249, 29.556983%, synthetic 30 cases/15
categories; mean 2.450484 ms and p95 23.378860 ms. Reexecuted counts match exactly;
new mean 2.528551 ms/p95 24.797800 ms vary with machine state. Both observations are
preserved; neither measures Grok billing, provider usage or model-output quality.
Recheck evidence: evidence-ecosystem/core-benchmark-recheck.json.
No live xAI trial, representative private/customer corpus, external penetration test,
loaded semantic checkpoint validation, SSO, durable billing or production SLA.

## 13. Readiness

Public presentation/demo/video are published and validated within stated checks.
Enterprise is a private research-alpha foundation; no stable release or PyPI publication.
No universal semantic-equivalence, financial-savings or production-readiness claim.

## 14. Next priorities

Independent workload/security review; human audiovisual review; account-appropriate private
repository protections; issuer key management/revocation; SSO and tenant-scoped persistent
storage; explicit provider account budgets and approved live evaluation; operational TLS,
rate/concurrency limits and recovery testing before any commercial production deployment.
