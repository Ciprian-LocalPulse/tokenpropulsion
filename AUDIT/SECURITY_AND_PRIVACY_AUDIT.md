# Security and privacy audit

## Scope and evidence

Reviewed source, resource bounds, optional dependency isolation, credential access,
provider authorization, transport decoding, report contents, CI and package metadata.
[Bandit JSON](evidence-v2/bandit.json), [dependency audit](evidence-v2/dependency-audit.json),
[test output](evidence-v2/pytest.txt), source under src/tokenpropulsion and tests/security
provide evidence. A dependency database observation is dated, not a security guarantee.

## Controls implemented and tested

One-megabyte UTF-8 text limits; bounded datasets/row counts; protected-input identity;
strict independent document contract; bounded zlib decoding; constant-time HTTP bearer
comparison; sanitized exceptions; no input reflection in validation errors; encoded-body
rejection; process-level request limiter; ten-second body-read deadline. API deployment
still needs TLS, connection/concurrency bounds and a shared limiter across workers.

Core code performs no network I/O. xAI requires explicit network permission and sensitive
content opt-in; CLI studies additionally require billing authorization, model and budget.
Remote preflight covers original and optimized inputs. Retry reservations count failed
attempts and are not refunded. Actual cost may exceed a reservation; provider account
caps are required. Keys are read from the environment and never written into repository
reports. Original text remains in result objects and applications must control logging.

## Findings and disposition

The initial Bandit run produced low-severity false positives for null token metrics and
an XML escape import used only to emit SVG. Null metrics now use a named unmeasured
value, and SVG uses html.escape without an XML parser. Final Bandit has no findings.
Dependency scan found zero known vulnerabilities among audited installed dependencies;
the local unpublished project is skipped. The uninstalled semantic extra/model weights
are not covered by that installed-environment scan. No secrets found by the project
high-confidence scanner; pattern scanning cannot establish absence of every secret.

Second-pass review fixed all-wrong quality acceptance, whole-study preflight, remaining
budget accounting, explicit judge billing gates, huge integer schema checks and slow
body reads. Tests cover quality and preflight regressions. No complete penetration test,
external review, adversarial model study or production load test was performed.


Review scope: internal second-pass engineering review of final code and actual outputs;
not external independent certification, peer review or production approval.
Version 2.0.0a1; baseline 1.0.0rc1. Raw execution evidence: [evidence-v2](evidence-v2/).
