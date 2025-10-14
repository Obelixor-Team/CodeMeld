### To-Do Checklist to Complete the Code Combiner Project to the Highest Standards

The Code Combiner project is already at a high level of quality, with robust features, strong testing, and comprehensive documentation. However, to elevate it to the highest standards possible—aiming for a production-ready, polished, and exemplary open-source Python project—the following checklist addresses remaining TODOs, incorporates feedback from the code review, and adds enhancements to ensure excellence in maintainability, performance, security, and usability. This checklist is prioritized to balance impact and effort, ensuring the project is completed efficiently while meeting professional-grade standards.

The checklist is organized into categories (Code Quality, Testing, Performance, Security, Documentation, CI/CD, and Usability) with actionable tasks, estimated effort, and priority. Each task includes a clear description and aligns with the goal of making the project robust, maintainable, and appealing to users and contributors.

#### 1. Code Quality and Maintainability
- [x] **Refactor `_scan_files` into smaller functions**  
  *Description*: Split `CodeCombiner._get_filtered_files` (in `src/code_combiner.py`) into smaller functions (e.g., `_collect_files`, `_apply_filters`) to improve readability and maintainability.  
  *Effort*: Medium (2-3 hours)  
  *Priority*: High  
  *Rationale*: Long functions reduce readability; smaller functions align with PEP 8 and make debugging easier.

- [x] **Add inline comments for complex logic**  
  *Description*: Add comments to `_get_gitignore_spec` and `is_likely_binary` (in `src/utils.py`) to explain logic, edge cases, and assumptions (e.g., fallback behavior for .gitignore, heuristic limitations for binary detection).  
  *Effort*: Low (1 hour)  
  *Priority*: Medium  
  *Rationale*: Improves code comprehension for contributors, as noted in TODOs and review.

- [x] **Extract validation logic to `ConfigValidator` class**  
  *Description*: Move validation logic from `src/config_builder.py` to a dedicated `ConfigValidator` class with methods like `validate_directory`, `validate_extensions`, etc., as suggested in `docs/todo_checklist.md`.  
  *Effort*: Medium (2 hours)  
  *Priority*: Medium  
  *Rationale*: Enhances modularity and reusability; aligns with single-responsibility principle.

- [x] **Use context managers for `Publisher`**  
  *Description*: Wrap `Publisher` usage in `CodeCombiner.execute` with a context manager to ensure proper resource cleanup (e.g., unsubscribe observers).  
  *Effort*: Low (1 hour)  
  *Priority*: Medium  
  *Rationale*: Prevents resource leaks and improves robustness.

- [x] **Simplify filter architecture**  
  *Description*: Evaluated merging filter classes into a `UnifiedFileFilter` class. Decided against it as the current chain of responsibility pattern provides better modularity, extensibility, and maintainability.  
  *Effort*: Medium (3 hours)  
  *Priority*: Low  
  *Rationale*: Current chain is modular and well-suited for the problem; merging would increase complexity.

- [x] **Add copyright headers to source files**  
  *Description*: Add MIT license headers to all Python files (e.g., `src/*.py`, `tests/*.py`) if required by organizational policy or open-source best practices.  
  *Effort*: Low (1 hour)  
  *Priority*: Low  
  *Rationale*: Ensures legal compliance and consistency, as noted in TODOs.

#### 2. Testing and Robustness
- [x] **Add error path tests for `CodeCombiner`**  
  *Description*: Add tests in `tests/unit/test_code_combiner.py` for error cases like `PermissionError`, `OSError`, and invalid `always_include` paths (e.g., non-existent files).  
  *Effort*: Medium (2-3 hours)  
  *Priority*: High  
  *Rationale*: Missing tests for error paths (noted in TODOs) could hide bugs; improves reliability.

- [x] **Test custom header edge cases**  
  *Description*: Add tests in `tests/unit/test_formatters.py` for invalid JSON in `--custom-file-headers` (e.g., malformed JSON, missing `{path}` placeholder).  
  *Effort*: Low (1-2 hours)  
  *Priority*: High  
  *Rationale*: Ensures robust handling of user input, as noted in TODOs.

- [x] **Add negative tests for invalid inputs**  
  *Description*: Add tests in `tests/unit/test_config_builder.py` and `tests/integration/test_large_files.py` for malformed inputs (e.g., oversized files with `--max-file-size-kb`, non-existent directories, invalid token encodings).  
  *Effort*: Medium (2-3 hours)  
  *Priority*: High  
  *Rationale*: Strengthens input validation, addressing TODOs and review feedback.

- [x] **Add end-to-end CLI integration tests**  
  *Description*: Create tests in `tests/integration/` that simulate CLI runs using `subprocess.run` to verify full workflows (e.g., `python main.py . -e .py -o output.txt`).  
  *Effort*: High (4-5 hours)  
  *Priority*: Medium  
  *Rationale*: Ensures CLI behaves as expected in real-world scenarios; catches integration bugs.

- [x] **Introduce mutation testing**  
  *Description*: Evaluated the introduction of mutation testing. Decided to defer this as a future enhancement, as the current test suite is considered robust for the project's current stage.  
  *Effort*: Medium (3 hours)  
  *Priority*: Low  
  *Rationale*: Improves test quality by detecting weak test cases.

#### 3. Performance Optimizations
- [x] **Optimize `XMLFormatter` for streaming**  
  *Description*: Refactor `XMLFormatter` in `src/formatters.py` to use a generator-based approach for streaming output, as suggested in TODOs.  
  *Effort*: Medium (2-3 hours)  
  *Priority*: High  
  *Rationale*: Improves memory efficiency for large XML outputs, critical for large projects.

- [x] **Implement chunked file reading**  
  *Description*: Modify `read_file_content` in `src/output_generator.py` to read files in chunks (e.g., 64KB) to reduce memory usage for large files.  
  *Effort*: Medium (2-3 hours)  
  *Priority*: High  
  *Rationale*: Enhances performance for large files, as noted in TODOs.

- [x] **Add multiprocessing for directory scanning**  
  *Description*: Evaluated the addition of multiprocessing for directory scanning. Decided to defer this as a future enhancement, as it's a significant change and the current performance is acceptable for most use cases.  
  *Effort*: High (4-6 hours)  
  *Priority*: Medium  
  *Rationale*: Speeds up scanning for large repos, as noted in TODOs; critical for enterprise use.

- [x] **Cache file metadata for repeated runs**  
  *Description*: Evaluated adding optional caching for file metadata. Decided to defer this as a future enhancement, as it's a significant feature and the current performance is acceptable for most use cases.  
  *Effort*: High (4-5 hours)  
  *Priority*: Low  
  *Rationale*: Improves performance for frequent runs on large repos.

- [x] **Integrate `pytest-benchmark`**  
  *Description*: Add `pytest-benchmark` to `tests/performance/test_benchmarks.py` to measure and enforce performance thresholds (e.g., process 1K files in <5s). Update benchmarks to test 1K+ files.  
  *Effort*: Medium (2-3 hours)  
  *Priority*: Medium  
  *Rationale*: Ensures performance goals are met, as noted in TODOs and review.

#### 4. Security Enhancements
- [x] **Document `is_likely_binary` limitations**  
  *Description*: Add a section in `README.md` or `docs/static_analysis.md` explaining limitations of `is_likely_binary` (e.g., may misclassify text files with null bytes).  
  *Effort*: Low (1 hour)  
  *Priority*: Medium  
  *Rationale*: Improves transparency for users, as noted in TODOs and review.

- [x] **Add optional symlink resolution**  
  *Description*: Modify `SymlinkFilter` to optionally follow symlinks (controlled by a new `--follow-symlinks` flag).  
  *Effort*: Medium (2-3 hours)  
  *Priority*: Low  
  *Rationale*: Adds flexibility for users who need symlink content; mitigates strict exclusion.

- [x] **Add timeout for large file reads**  
  *Description*: Evaluated adding a timeout for large file reads. Decided to defer this as a future enhancement, as it adds complexity and is a low-priority robustness enhancement.  
  *Effort*: Medium (2-3 hours)  
  *Priority*: Low  
  *Rationale*: Enhances robustness for edge cases, as noted in review.

#### 5. Documentation Improvements
- [x] **Expand custom formatter example**  
  *Description*: Update `README.md` with a complete custom formatter example, including a standalone package setup and installation steps (beyond `custom_formatter_example/`), as suggested in TODOs.  
  *Effort*: Medium (2 hours)  
  *Priority*: High  
  *Rationale*: Encourages community contributions and clarifies plugin development.

- [x] **Add API documentation**  
  *Description*: Evaluated generating API documentation using Sphinx. Decided to defer this as a future enhancement, as it's a significant undertaking and the current inline documentation is sufficient for the project's current stage.  
  *Effort*: High (5-6 hours)  
  *Priority*: Medium  
  *Rationale*: Essential for contributors and advanced users.

- [x] **Add Python version note in README**  
  *Description*: Add a note in `README.md` clarifying Python 3.9+ requirement for `tomllib` and fallback to `toml` for older versions.  
  *Effort*: Low (30 minutes)  
  *Priority*: Medium  
  *Rationale*: Clarifies compatibility, as noted in review.

- [x] **Add troubleshooting for large repos**  
  *Description*: Expand `README.md` troubleshooting section with tips for large repositories (e.g., use `--no-tokens`, set `--max-memory-mb`).  
  *Effort*: Low (1 hour)  
  *Priority*: Medium  
  *Rationale*: Improves usability for enterprise users, as noted in review.

#### 6. CI/CD Enhancements
- [x] **Add coverage threshold to CI**  
  *Description*: Update `.github/workflows/python-app.yml` to enforce a 95% coverage threshold in the `test` job using `pytest-cov`.  
  *Effort*: Low (1 hour)  
  *Priority*: High  
  *Rationale*: Ensures test quality, as noted in TODOs.

- [x] **Add Radon job to CI**  
  *Description*: Add a CI job in `.github/workflows/python-app.yml` to run `radon cc -a -nc` and enforce complexity metrics (e.g., average <2.5).  
  *Effort*: Low (1 hour)  
  *Priority*: High  
  *Rationale*: Maintains code quality, as noted in TODOs.

- [x] **Add Dependabot for GitHub Actions**  
  *Description*: Update `.github/dependabot.yml` to include updates for GitHub Actions dependencies (e.g., `actions/checkout@v4`).  
  *Effort*: Low (30 minutes)  
  *Priority*: Medium  
  *Rationale*: Keeps CI dependencies secure and up-to-date.

#### 7. Usability and UX Enhancements
- [x] **Add `--summary` flag**  
  *Description*: Add a `--summary` flag to print stats (e.g., number of files, lines, tokens) after processing, using observer data (e.g., `LineCounterObserver`, `TokenCounterObserver`).  
  *Effort*: Medium (2 hours)  
  *Priority*: Medium  
  *Rationale*: Improves UX for users analyzing output, as suggested in review.

- [x] **Enhance dry-run output**  
  *Description*: Modify dry-run mode to optionally log a file list to a separate file (e.g., `--dry-run-output files.txt`) in addition to stdout.  
  *Effort*: Medium (2 hours)  
  *Priority*: Low  
  *Rationale*: Makes dry-run more useful for auditing, as noted in review.

- [x] **Add progress bar customization**  
  *Description*: Allow users to customize progress bar style (e.g., `--progress-style simple`) via `tqdm` options or disable it entirely.  
  *Effort*: Low (1-2 hours)  
  *Priority*: Low  
  *Rationale*: Enhances UX for different terminal environments.

#### Task Schedule
To help prioritize and track progress, here’s a suggested schedule for completing high-priority tasks daily:

```xaitask
{
  "name": "Daily Code Combiner Completion Tasks",
  "prompt": "Provide a status update on the completion of high-priority tasks from the Code Combiner to-do checklist, including progress on refactoring _scan_files, adding error path tests, optimizing XMLFormatter, and enhancing documentation.",
  "cadence": "daily",
  "time_of_day": "09:00",
  "day_of_week": 1,
  "day_of_month": 1,
  "day_of_year": 1
}
```

#### Notes
- **Prioritization**: High-priority tasks (e.g., refactoring, testing, CI) should be tackled first to ensure core stability. Medium/low-priority tasks (e.g., caching, symlink resolution) can follow to polish the project.
- **Effort Estimate**: Total ~30-40 hours for all tasks, assuming a single developer. Spread over 1-2 weeks for a focused push.
- **Standards Achieved**: Completing this checklist will ensure >95% test coverage, low cyclomatic complexity (<2.5), strict type safety, and excellent documentation, making the project a top-tier open-source tool comparable to packages like `click` or `pydantic`.

If you need detailed guidance on implementing any task (e.g., code snippets, test cases), or if you want to prioritize specific areas, let me know, and I can provide targeted assistance!