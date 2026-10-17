# Executed validation — 2026-10-17

Release candidate: **1.0.0rc1**. Validated locally on Windows x64, Python 3.12.14.
The original local snapshot below predates public CI. Live xAI success is not claimed.
The hosted validation supplement records the subsequently executed public checks.

| Gate | Executed result |
| --- | --- |
| pytest unit / integration / regression / security | 191 passed; 0 failures, 0 errors, 0 skips |
| Meaningful line coverage | 99.61% (509/511 statements) |
| Combined line/branch coverage | 99.54% |
| Ruff check and formatting | Passed |
| Strict mypy | Passed, 20 package source modules |
| Bandit source security scan | 0 findings, no suppressions |
| pip-audit | 0 known vulnerabilities across resolved audited dependencies |
| Bounded repository secret scan | 0 high-confidence findings |
| Build | Wheel and source distribution built; wheel built from source distribution |
| Fresh install | Dependency-free wheel installed; Python API and installed CLI passed |
| Pipeline / file smoke | UTF-8 stdout, stderr statistics, protected CRLF bytes passed |
| Offline benchmark | All nine synthetic category fixtures passed; ten repetitions per row |
| Workflow source | YAML structure parsed; all third-party action refs are immutable SHAs |
| Python 3.10 syntax | All 20 package modules parsed using 3.10 grammar |

See [machine-readable tests](test-results.json), [coverage](coverage.json),
[Bandit](bandit.json), [dependency audit](dependency-audit.json),
[installation smoke](install-smoke.json), and [local benchmark](../benchmarks/results/local.json).
The exact resolved validation environment is recorded in requirements-tested-py312-windows.txt;
it is a Windows/Python 3.12 snapshot, not a portable lock file.

## Qualifications and outstanding release gates

- Local tests ran on Python 3.12. The initial public hosted matrix subsequently passed
  on Python 3.10-3.14. Syntax parsing alone is not runtime compatibility testing.
- xai-sdk **1.20.0** real SDK signatures and usage protobuf fields were inspected
  and exercised through mocks. XAI_API_KEY was absent. No provider calls were made;
  live authentication, model support, tokenization, retry behavior, quality, billing,
  and latency remain unverified.
- Offline counts use an explicitly uncalibrated UTF-8-byte estimator. No actual model
  token, quality, or cost savings are claimed. Model-output quality and task success
  fields remain null offline. Formatting fixtures do not establish semantic equivalence.
- One non-failing warning: Starlette deprecates its httpx test transport in favor of
  httpx2. No warning was hidden. The current installed transport passed all API tests.
- pip-audit skipped the unpublished local distribution itself because no PyPI advisory
  record exists. The original source was checked with Bandit and reviewed; this is
  not an independent audit or certification. Audit results are time-sensitive.
- An initial Bandit false positive mistook a nullable token-reduction metric for a
  credential. The code now names the unmeasured value explicitly, without suppressing
  any security rules. Final scan has no findings.
- Secret scanning is heuristic, with size/binary/generated-artifact exclusions; no claim
  of exhaustive secret detection is made. Included prompts are project-created synthetic
  fixtures. Neither the supplied request file nor credentials are included.
- No LLMLingua comparison was executed. Compression never removes repeated words or
  instructions; medium/high are limited to documented formatting transformations.

## Publication and naming

Read-only public checks on 2026-10-17 returned HTTP 404 for
`https://pypi.org/pypi/tokenpropulsion/json` and
`https://api.github.com/repos/Ciprian-LocalPulse/tokenpropulsion`.
A preliminary exact-name web search found no known conflict. These checks do not reserve
names or establish trademark clearance; recheck immediately before publication.

Initial authentication checks inside the restricted sandbox incorrectly appeared invalid.
A subsequent network-enabled `gh auth status` and `gh api user` confirmed authorized
access to Ciprian-LocalPulse. The public repository and release status can be checked
at https://github.com/Ciprian-LocalPulse/tokenpropulsion . Original local measurements
above remain a dated evidence snapshot; hosted CI is additional evidence, not assumed.
The version remains a release candidate because live provider behavior is unverified.

## Environment issues resolved during validation

The system Python launcher had no registered interpreter; the bundled Python runtime
was used with workspace-local virtual environments. Windows sandbox restrictions blocked
asyncio's local socketpair and default temporary directories. Offline/mocked integration
tests passed outside that sandbox with a workspace temporary directory. These failures
were environmental; no external model endpoint was contacted to work around them.


## Hosted validation supplement

Public source commit `bcef50652c1381840cfa62a19db276d27c9fed8f` completed:

- [CI: Python 3.10, 3.11, 3.12, 3.13, and 3.14](https://github.com/Ciprian-LocalPulse/tokenpropulsion/actions/runs/39001323055): success for all five jobs, including tests, lint, typing, build, and fresh wheel smoke checks.
- [Security](https://github.com/Ciprian-LocalPulse/tokenpropulsion/actions/runs/39001322777): success.

Later commits preserve JSONL serialization and enforce the published benchmark hash.
Their run results are visible in [current Actions](https://github.com/Ciprian-LocalPulse/tokenpropulsion/actions).
A successful initial run does not imply that uncompleted later runs have passed.
The first GitHub release remains 1.0.0rc1 because live provider behavior is unverified.
