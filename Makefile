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
	@echo ""
	@echo "--- Starting install ---"
	@echo ""
	.venv/bin/pip install -r requirements.txt
	.venv/bin/pip install -r requirements-dev.txt
	@echo ""
	@echo "--- Finished install ---"
	@echo ""

all: 
	@echo ""
	@echo "--- Starting all checks ---"
	@echo ""
	$(MAKE) format
	$(MAKE) lint
	$(MAKE) check
	$(MAKE) coverage
	$(MAKE) radon
	$(MAKE) audit
	@echo ""
	@echo "--- Finished all checks ---"
	@echo ""

format:
	@echo ""
	@echo "--- Starting format ---"
	@echo ""
	.venv/bin/black src
	@echo ""
	@echo "--- Finished format ---"
	@echo ""

lint:
	@echo ""
	@echo "--- Starting lint ---"
	@echo ""
	.venv/bin/ruff check . --fix
	@echo ""
	@echo "--- Finished lint ---"
	@echo ""

check:
	@echo ""
	@echo "--- Starting check (mypy) ---"
	@echo ""
	.venv/bin/mypy --strict .
	@echo ""
	@echo "--- Finished check (mypy) ---"
	@echo ""

check-strict:
	@echo ""
	@echo "--- Starting strict checks (ruff, mypy, pytest) ---"
	@echo ""
	.venv/bin/ruff check src
	.venv/bin/mypy --strict --package src
	PYTHONPATH=. .venv/bin/pytest tests/
	@echo ""
	@echo "--- Finished strict checks ---"
	@echo ""

test:
	@echo ""
	@echo "--- Starting tests ---"
	@echo ""
	PYTHONPATH=. .venv/bin/pytest tests/
	@echo ""
	@echo "--- Finished tests ---"
	@echo ""

coverage:
	@echo ""
	@echo "--- Starting coverage report ---"
	@echo ""
	PYTHONPATH=. .venv/bin/pytest --cov=src --cov-report=term-missing --cov-fail-under=90 --timeout=60 tests/
	@echo ""
	@echo "--- Finished coverage report ---"
	@echo ""

radon:
	@echo ""
	@echo "--- Starting radon complexity analysis ---"
	@echo ""
	.venv/bin/radon cc src -a -nc
	@echo ""
	@echo "--- Finished radon complexity analysis ---"
	@echo ""

audit:
	@echo ""
	@echo "--- Starting pip-audit ---"
	@echo ""
	-.venv/bin/pip-audit
	@echo ""
	@echo "--- Finished pip-audit ---"
	@echo ""