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

## `is_likely_binary` Function Limitations

**Purpose**: The `is_likely_binary` function (located in `src/utils.py`) is a heuristic used to quickly determine if a file is binary. This is crucial for preventing the processing of non-text files, which can lead to `UnicodeDecodeError` or other issues when attempting to read them as text.

**Limitations**:
-   **Heuristic-based**: This function relies on a combination of file extensions (e.g., `.bin`, `.png`) and content analysis (presence of null bytes, proportion of non-text characters). As such, it is a "likely" check and not foolproof.
-   **Misclassification**:
    -   **Text files with null bytes**: Some text files (e.g., certain legacy encodings or corrupted files) might contain null bytes, leading to them being misclassified as binary.
    -   **Binary files without common extensions or null bytes**: Conversely, some binary files might not have a recognized binary extension and might not contain null bytes in their initial chunks, leading to them being misclassified as text.
-   **Performance vs. Accuracy**: The function is optimized for performance, especially for large files, by only sampling the initial part of the file. This trade-off means it prioritizes speed over absolute accuracy.
-   **Encoding**: It assumes UTF-8 for text content analysis. Files with other text encodings might be misclassified if they contain byte patterns that trigger the binary heuristics.

**Recommendation**: While generally effective, users should be aware of these limitations. If specific files are consistently misclassified, they might need to be explicitly included or excluded using the `--always-include` or `--exclude` options, respectively.

## Pre-commit Hooks

Pre-commit hooks are configured to automatically run `ruff` (linting and formatting) and `mypy` (type checking) before each commit. This ensures that only high-quality, well-formatted, and type-safe code is committed to the repository.

**Installation**:

To install pre-commit hooks, run:

```bash
pre-commit install
```

This will set up the hooks to run automatically on `git commit`.
