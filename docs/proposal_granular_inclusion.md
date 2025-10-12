**Proposal: Granular Inclusion of Specific Files**

**Problem:**
The current `--include-hidden` option is a global setting, either including all hidden files or none. Users require the ability to explicitly include specific files (even if hidden or otherwise filtered out by default rules) while maintaining general filtering for other files. The previous attempt to implement an `AlwaysIncludeFilter` within the Chain of Responsibility pattern led to unexpected behavior where non-explicitly included files were prematurely filtered out.

**Proposed Solution:**
The most robust and flexible solution is to handle explicit file inclusions at the file scanning stage (`CodeCombiner._scan_files`) before the main filter chain is applied. This ensures that specified files are always added to the processing list, regardless of subsequent filtering rules, while allowing the existing filter chain to operate normally on all other discovered files.

**Implementation Steps:**

1.  **Modify `CombinerConfig` (src/config.py):**
    *   Add a new field `always_include: list[str] = field(default_factory=list)` to store a list of file paths that should always be included.

2.  **Modify `CombinerConfigBuilder` (src/config_builder.py):**
    *   Update the `__init__` method to include `always_include` in the default configuration.
    *   Update the `with_cli_args` method to populate `always_include` from a new command-line argument.

3.  **Modify `parse_arguments()` (src/code_combiner.py):**
    *   Add a new command-line argument: `--always-include <path> [path ...]`. This argument will accept one or more file paths.

4.  **Modify `CodeCombiner._scan_files` (src/code_combiner.py):**
    *   Initialize an empty list, `files_to_process`.
    *   Create a set of resolved absolute paths from `config.always_include` for efficient lookup.
    *   **First Pass (Explicit Inclusions):** Iterate through the `config.always_include` list. For each path:
        *   Resolve the path relative to `config.directory_path`.
        *   If the path points to an existing file, add it to `files_to_process`.
    *   **Second Pass (General Scan):** Iterate through `config.directory_path.rglob("*")` to discover all other files. For each discovered `file_path`:
        *   Resolve its absolute path.
        *   If this `resolved_file_path` is *not* in the set of `always_include` paths (to avoid duplicates), then apply the existing `self.filter_chain.should_process(file_path, context)`.
        *   If the filter chain allows the file, add it to `files_to_process`.
    *   Return the `files_to_process` list.

**Benefits of this approach:**

*   **Clear Precedence:** Explicitly included files are guaranteed to be processed first and bypass all other filters.
*   **Maintainability:** The core filter chain remains focused on general filtering rules.
*   **Flexibility:** Users can precisely control which specific files are included, even if they would normally be excluded by other rules (e.g., `.gitignore`, hidden file rules, extension filters).
*   **Simplicity:** Avoids complex logic within the `FileFilter` chain itself for this specific inclusion override.
