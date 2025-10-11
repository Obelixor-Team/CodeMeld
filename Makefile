.PHONY: help install format lint check all

help:
	@echo "Makefile for managing the project."
	@echo ""
	@echo "Targets:"
	@echo "  install    Install development dependencies."
	@echo "  format     Format the code using black."
	@echo "  lint       Lint the code using ruff."
	@echo "  check      Run static type checking with mypy."
	@echo "  all        Run format, lint, and check."

install:
	.venv/bin/pip install -r requirements.txt
	.venv/bin/pip install -r requirements-dev.txt

format:
	.venv/bin/black src

lint:
	.venv/bin/ruff check src

check:
	.venv/bin/mypy src

all: format lint check