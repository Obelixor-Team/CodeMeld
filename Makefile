.PHONY: help install format lint check test coverage all check-strict audit run

help:
	@echo "Makefile for managing the project."
	@echo ""
	@echo "Targets:"
	@echo "  install    Install development dependencies."
	@echo "  format     Format the code using ruff."
	@echo "  lint       Lint the code using ruff."
	@echo "  check      Run static type checking with ty."
	@echo "  check-strict Run ruff check, ty check, and pytest."
	@echo "  test       Run tests using pytest."
	@echo "  coverage   Run tests with coverage reporting."
	@echo "  run        Run the codemeld tool (e.g., make run ARGS='.')"
	@echo "  all        Run format, lint, check, coverage, and audit."
	@echo "  audit      Run pip-audit to check for vulnerabilities."
	@echo ""

install:
	@echo ""
	@echo "--- Starting install ---"
	@echo ""
	uv pip install -r requirements.txt
	uv pip install -r requirements-dev.txt
	@echo ""
	@echo "--- Finished install ---"
	@echo ""

setup:
	@echo ""
	@echo "--- Setting up environment with uv ---"
	@echo ""
	uv venv --python 3.14.4
	$(MAKE) install
	@echo ""
	@echo "--- Setup finished ---"
	@echo ""

all: 
	@echo ""
	@echo "--- Starting all checks ---"
	@echo ""
	$(MAKE) format
	$(MAKE) lint
	$(MAKE) check
	$(MAKE) coverage
	$(MAKE) audit
	@echo ""
	@echo "--- Finished all checks ---"
	@echo ""

format:
	@echo ""
	@echo "--- Starting format ---"
	@echo ""
	uv run ruff format .
	@echo ""
	@echo "--- Finished format ---"
	@echo ""

lint:
	@echo ""
	@echo "--- Starting lint ---"
	@echo ""
	uv run ruff check . --fix
	@echo ""
	@echo "--- Finished lint ---"
	@echo ""

check:
	@echo ""
	@echo "--- Starting check (ty) ---"
	@echo ""
	uv run ty check .
	@echo ""
	@echo "--- Finished check (ty) ---"
	@echo ""

check-strict:
	@echo ""
	@echo "--- Starting strict checks (ruff, mypy, pytest) ---"
	@echo ""
	uv run ruff check .
	uv run ty check .
	uv run pytest tests/
	@echo ""
	@echo "--- Finished strict checks ---"
	@echo ""

test:
	@echo ""
	@echo "--- Starting tests ---"
	@echo ""
	uv run pytest tests/
	@echo ""
	@echo "--- Finished tests ---"
	@echo ""

coverage:
	@echo ""
	@echo "--- Starting coverage report ---"
	@echo ""
	uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=90 --timeout=60 tests/
	@echo ""
	@echo "--- Finished coverage report ---"
	@echo ""

audit:
	@echo ""
	@echo "--- Starting pip-audit ---"
	@echo ""
	uv run pip-audit
	@echo ""
	@echo "--- Finished pip-audit ---"
	@echo ""
	@echo ""

run:
	uv run main.py $(ARGS)
	@echo ""
	@echo "--- Finished running codemeld ---"
	@echo ""
	@echo "--- Finished running codemeld ---"
	@echo ""
