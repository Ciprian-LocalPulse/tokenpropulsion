.PHONY: test lint security build benchmark demo

test:
	python -m pytest --cov=tokenpropulsion --cov-report=term-missing

lint:
	python -m ruff check .
	python -m ruff format --check .
	python -m mypy

security:
	python -m bandit -r src
	python -m pip_audit
	python scripts/secret_scan.py

build:
	python -m build

benchmark:
	python -m tokenpropulsion benchmark --dataset benchmarks/datasets/sample.jsonl --repeats 10 -o benchmarks/results/local.json

demo:
	python examples/demo.py
