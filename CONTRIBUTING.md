# Contributing

Use Python 3.10+ and a virtual environment. Run `pip install -e '.[dev,api,xai]'`,
`ruff check .`, `mypy`, and `pytest --cov=tokenpropulsion --cov-report=term-missing`.
Run `bandit -r src`, `pip-audit`, `python scripts/secret_scan.py`, and
`python -m build`. See docs/release.md for installation and release gates.

Add behavior-focused tests for changes. Safety rules need adversarial fixtures.
Do not include private prompts or credentials. Network tests must use mocks by default.
Document compatibility, measurement methods, and limitations. Original contributions
are licensed under MIT; retain notices for any appropriately licensed third-party code.
