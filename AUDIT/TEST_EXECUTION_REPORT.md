# Test execution report

Python 3.12.14, Windows x64, 2026-10-18. Final regression suite: **272 passed,
0 failed**, one Starlette httpx transport deprecation warning. Previous baseline:
191 passed. [JUnit](evidence-v2/tests.xml), [full output](evidence-v2/pytest.txt),
[coverage](evidence-v2/coverage.json). Coverage: **95.44% combined**, **96.52% lines**,
**91.95% branches** (final nonbehavioral cleanup can shift statement counts slightly).
The earlier failing preflight regression was fixed before this passing run; historical
attempts remain in the workspace rather than being misrepresented as final passes.

Commands: `pytest --cov=tokenpropulsion --cov-report=json --junitxml=tests.xml -q`;
`ruff check .`; `ruff format --check .`; `mypy`; `bandit -r src`;
`pip-audit --format json`; `python -m build --no-isolation --outdir dist/v2.0.0a1`;
`twine check dist/v2.0.0a1/*`; historical `check_whitepaper.py` and `check_benchmark.py`.
Static/build and fresh installation results are recorded in evidence-v2/checks.json.
The build explicitly targets Core Metadata 2.4 for compatibility with current Twine.

Final paper: 9 pages; all rendered and visually inspected; extracted text and page bounds
checked. The original v1 paper still passes its exact 10,000-word-body check. PDF rebuilds
can differ in metadata/timestamps; release checksums verify distributed bytes.
Hosted CI results must be checked against the exact release commit before publication.


Review scope: internal second-pass engineering review of final code and actual outputs;
not external independent certification, peer review or production approval.
Version 2.0.0a1; baseline 1.0.0rc1. Raw execution evidence: [evidence-v2](evidence-v2/).
