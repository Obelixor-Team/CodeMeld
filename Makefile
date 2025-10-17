.PHONY: help install format lint check test coverage all radon check-strict audit

help:
	@echo "Makefile for managing the project."
	@echo ""
	@echo "Targets:"
	@echo "  install    Install development dependencies."
	@echo "  format     Format the code using black."
	@echo "  lint       Lint the code using ruff."
	@echo "  check      Run static type checking with mypy."
	@echo "  check-strict Run ruff check, mypy --strict, and pytest."
	@echo "  test       Run tests using pytest."
	@echo "  coverage   Run tests with coverage reporting."
	@echo "  all        Run format, lint, check, coverage, and radon."
	@echo "  radon      Run code complexity analysis."
	@echo "  audit      Run pip-audit to check for vulnerabilities."

install:
	.venv/bin/pip install -r requirements.txt
	.venv/bin/pip install -r requirements-dev.txt

all: format lint check coverage radon audit

format:
	.venv/bin/black src

lint:
	.venv/bin/ruff check . --fix

check:
	.venv/bin/mypy .

check-strict:
	.venv/bin/ruff check src
	.venv/bin/mypy --strict --package src
	PYTHONPATH=. .venv/bin/pytest tests/

test:
	PYTHONPATH=. .venv/bin/pytest tests/

coverage: PYTHONPATH=. .venv/bin/pytest --cov=src --cov-report=term-missing --cov-fail-under=90 --timeout=60 tests/

radon:
	.venv/bin/radon cc src -a -nc

audit:
	-.venv/bin/pip-audit