.PHONY: help install format lint check all

help:
	@echo "Makefile for managing the project."
	@echo ""
	@echo "Targets:"
	@echo "  install    Install development dependencies."
	@echo "  format     Format the code using black."
	@echo "  lint       Lint the code using ruff."
	@echo "  check      Run static type checking with mypy."
	@echo "  test       Run tests using pytest."
	@echo "  all        Run format, lint, check, and test."

install:
	.venv/bin/pip install -r requirements.txt
	.venv/bin/pip install -r requirements-dev.txt

all: format lint check test radon

format:
	.venv/bin/black src

lint:
	.venv/bin/ruff check src

check:
	.venv/bin/mypy src

test:
	PYTHONPATH=. .venv/bin/pytest tests/

radon:
	.venv/bin/radon cc src -a -nc