# Release preparation

Version is `1.0.0rc1`. Do not tag 1.0.0 until every intended release gate passes,
including hosted supported-Python CI, current dependency audit, manual review, and
live optional provider compatibility if claiming that support is verified.

```bash
python -m pip install -e '.[dev,api,xai]'
ruff check .
mypy
pytest --cov=tokenpropulsion --cov-report=term-missing --cov-report=xml
bandit -r src
pip-audit
python scripts/secret_scan.py
python -m tokenpropulsion benchmark --dataset benchmarks/datasets/sample.jsonl \
  --repeats 10 -o benchmarks/results/local.json
python -m build
python -m venv /tmp/tokenpropulsion-smoke
/tmp/tokenpropulsion-smoke/bin/pip install dist/tokenpropulsion-1.0.0rc1-py3-none-any.whl
/tmp/tokenpropulsion-smoke/bin/tokenpropulsion --help
```

Recheck availability immediately before publication. PyPI 404 does not reserve a name,
and GitHub account/repository availability does not establish trademark clearance.
No known conflict was found in preliminary search; trademark clearance is unverified.

GitHub access was subsequently verified with network-enabled authentication. For reproduction, review
all tracked files and use these commands from the repository root. They do not overwrite
an existing remote; stop if a repository already exists.

```bash
gh auth login --hostname github.com
git init -b main
git add .
git diff --cached --stat
python scripts/secret_scan.py
git commit -m "Prepare TokenPropulsion 1.0.0rc1"
gh repo create tokenpropulsion --public --source=. --remote=origin --push \
  --description "Less input. Measurable savings. Verified behavior. Independent prompt formatting and evaluation for Python."
gh repo edit --add-topic python --add-topic llm --add-topic prompt-optimization \
  --add-topic tokenization --add-topic grok
```

Configure branch protection, a protected `pypi` environment, and a PyPI trusted publisher
matching the repository and `publish.yml`. Run hosted CI/security checks first. Then:

```bash
git tag v1.0.0rc1
git push origin v1.0.0rc1
gh release create v1.0.0rc1 dist/* --prerelease --title "TokenPropulsion 1.0.0rc1" \
  --notes-file docs/release-notes.md
```

The manually dispatched publishing workflow checks out the selected prerelease tag,
runs release gates, builds, and uses trusted publishing. A public repository alone
does not authorize a final 1.0.0 claim; inspect all gates first.
