# Static Analysis Guidelines

This document outlines the static analysis tools and guidelines used in the Code Combiner project to ensure code quality, maintainability, and type safety.

## Ruff (Linting and Formatting)

**Purpose**: Ruff is used for both linting (identifying code quality issues and potential bugs) and formatting (ensuring consistent code style).

**Configuration**: Ruff's configuration is defined in `pyproject.toml` under the `[tool.ruff]` and `[tool.ruff.lint]` sections. This includes:

-   **Line Length**: Enforced to 88 characters, consistent with Black.
-   **Error Codes**: Specific error codes are enabled or disabled to tailor linting rules to the project's needs.
-   **Exclusions**: Directories and files to be ignored by the linter (e.g., virtual environments, cache directories).

**Usage**:

-   To check for linting issues:
    ```bash
    ruff check .
    ```
-   To automatically fix fixable issues:
    ```bash
    ruff check --fix .
    ```
-   To check code formatting:
    ```bash
    ruff format --check .
    ```

## MyPy (Static Type Checking)

**Purpose**: MyPy performs static type checking to catch type-related bugs before runtime, improving code reliability and readability.

**Configuration**: MyPy's configuration is defined in `pyproject.toml` under the `[tool.mypy]` section. Key settings include:

-   **`--strict` mode**: Enabled in CI to enforce the highest level of type safety.
-   **`--ignore-missing-imports`**: Used for libraries that do not provide type hints.
-   **`--disallow-untyped-defs`**: Ensures all function definitions have type annotations.

**Usage**:

-   To run type checking:
    ```bash
    mypy src/
    ```
-   In CI, `--strict` mode is used:
    ```bash
    mypy --strict src/
    ```

## Radon (Code Complexity Analysis)

**Purpose**: Radon is used to analyze code complexity metrics, such as Cyclomatic Complexity, which helps identify areas of the codebase that may be difficult to understand or maintain.

**Configuration**: Radon is configured via command-line arguments or a configuration file (though typically used via `Makefile` in this project).

**Usage**:

-   To run cyclomatic complexity analysis:
    ```bash
    radon cc src/ -a -nc
    ```

## Pre-commit Hooks

Pre-commit hooks are configured to automatically run `ruff` (linting and formatting) and `mypy` (type checking) before each commit. This ensures that only high-quality, well-formatted, and type-safe code is committed to the repository.

**Installation**:

To install pre-commit hooks, run:

```bash
pre-commit install
```

This will set up the hooks to run automatically on `git commit`.
