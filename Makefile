.PHONY: help install format lint check test coverage all check-strict audit run build clean-build clean uninstall update lizard pre-commit pre-commit-update

help:
	@echo "Makefile for managing the project."
	@echo ""
	@echo "Targets:"
	@echo "  install    Install development dependencies."
	@echo "  format     Format the code using ruff."
	@echo "  lint       Lint the code using ruff."
	@echo "  check      Run static type checking with mypy."
	@echo "  check-strict Run ruff check, mypy, pytest, and lizard."
	@echo "  test       Run tests using pytest."
	@echo "  coverage   Run tests with coverage reporting."
	@echo "  run        Run the codemeld tool (e.g., make run ARGS='.')"
	@echo "  build       Build a standalone executable with PyInstaller."
	@echo "  clean        Remove Python cache, bytecode, pytest/mypy/ruff caches, and build artifacts."
	@echo "  clean-build  Remove build artifacts only."
	@echo "  uninstall    Remove virtual environment, lock file, and all caches to save disk space."
	@echo "  update       Update dependencies to the latest versions."
	@echo "  pre-commit   Install and run pre-commit hooks."
	@echo "  pre-commit-update Update pre-commit hooks to latest versions."
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
	uv venv --python 3.14.4 --clear
	$(MAKE) install
	@echo ""
	@echo "--- Setup finished ---"
	@echo ""

lizard:
	@echo ""
	@echo "--- Starting lizard complexity analysis ---"
	@echo ""
	uv run lizard .
	@echo ""
	@echo "--- Finished lizard analysis ---"
	@echo ""

all:
	@echo ""
	@echo "--- Starting all checks ---"
	@echo ""
	$(MAKE) format
	$(MAKE) lint
	$(MAKE) check
	$(MAKE) coverage
	$(MAKE) lizard
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
	@echo "--- Starting check (ruff, mypy) ---"
	@echo ""
	uv run ruff check .
	uv run mypy .
	@echo ""
	@echo "--- Finished check (ruff, mypy) ---"
	@echo ""

check-strict: 
	@echo ""
	@echo "--- Starting strict checks (ruff, mypy, pytest, lizard) ---"
	@echo ""
	uv run ruff check .
	uv run mypy .
	uv run pytest tests/
	uv run lizard .
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
	uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=90 tests/
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
 
build:
	@echo ""
	@echo "--- Building standalone executable ---"
	@echo ""
	uv run pyinstaller main.py --onefile --name codemeld --distpath build/dist --hidden-import=tiktoken_ext --hidden-import=tiktoken_ext.openai_public
	@echo ""
	@echo "--- Build finished. Executable is in build/dist/ ---"
	@echo ""
 
clean-build: 
	@echo ""
	@echo "--- Cleaning build artifacts ---"
	@echo ""
	rm -rf build/ dist/
	@echo ""
	@echo "--- Clean finished ---"
	@echo ""

clean: clean-build
	@echo ""
	@echo "--- Cleaning Python cache and bytecode ---"
	@echo ""
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage.*" -delete 2>/dev/null || true
	rm -rf htmlcov/
	@echo ""
	@echo "--- Clean finished ---"
	@echo ""

uninstall: clean
	@echo ""
	@echo "--- Uninstalling virtual environment and all dependencies ---"
	@echo ""
	rm -rf .venv/
	rm -f uv.lock
	@echo ""
	@echo "--- Virtual environment removed ---"
	@echo "--- Run 'make setup' to recreate the environment ---"
	@echo ""
 
update: 
	@echo ""
	@echo "--- Updating dependencies ---"
	@echo ""
	uv pip install --upgrade -r requirements.txt
	uv pip install --upgrade -r requirements-dev.txt
	$(MAKE) check-strict
	@echo ""
	@echo "--- Update finished ---"
	@echo ""

pre-commit:
	@echo ""
	@echo "--- Installing pre-commit hooks ---"
	@echo ""
	pre-commit install
	@echo ""
	@echo "--- Running pre-commit on all files ---"
	@echo ""
	pre-commit run --all-files
	@echo ""
	@echo "--- Pre-commit hooks installed and checked ---"
	@echo ""

pre-commit-update:
	@echo ""
	@echo "--- Updating pre-commit hooks ---"
	@echo ""
	pre-commit autoupdate
	@echo ""
	@echo "--- Pre-commit hooks updated ---"
	@echo ""


