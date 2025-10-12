### To-Do Checklist

**Priority Fixes:**

*   [x] **Fix File Handle Leak in `StreamingOutputGenerator`**: Implement context manager pattern to ensure file handles are closed. (Critical Bug #3)
*   [x] **Add Proper Error Handling in `main.py`**: Catch `CodeCombinerError` and `KeyboardInterrupt` for graceful program termination. (Critical Bug #1)
*   [x] **Fix Path Resolution in `_scan_files`**: Ensure `always_include` paths are correctly resolved, handling both absolute and relative paths. (Major Issue #9)
*   [x] **Add Missing Type Annotations**: Complete type annotations for methods like `_begin_output` and `_process_file`. (Major Issue #10)
*   [x] **Improve Binary File Detection**: Enhance `is_likely_binary` with content analysis (null byte check, non-text byte proportion). (Major Issue #12)

**Other Critical Bugs:**

*   [x] **Resolve Circular Import Risk**: Move `FormatType` and `ConvertType` to a new `src/types.py` module. (Critical Bug #2)
*   [x] **Reset `JSONFormatter` State**: Ensure `is_first` is reset in `begin_output` for correct JSON generation. (Critical Bug #4)
*   [x] **Fix Race Condition in `write_output`**: Implement a more atomic approach for file writing to prevent issues with `FileExistsError`. (Critical Bug #5)
*   [x] **Add Validation in `FilterChainBuilder`**: Ensure `config.output` is an absolute path. (Critical Bug #6)
*   [x] **Observer Notification Timing Bug**: This notification happens AFTER `write_output`, but observers expect to be notified during the generation phase. Also, the observer pattern expects observers to be subscribed before generation starts. (Critical Bug #7)

**Major Issues:**

*   [x] **Inconsistent Error Handling**: Some functions log errors, others raise exceptions, some do both. (Major Issue #8)
*   [x] **Move Config Validation Earlier**: Shift appropriate validations from `CombinerConfig.validate_config()` to `CombinerConfigBuilder.validate()`. (Major Issue #11)

**Design Issues:**

*   [x] **Observer Pattern Implementation Incomplete**: The `Publisher` class is good, but observers can't unsubscribe easily, and there's no error handling for failing observers. (Design Issue #13)
*   [x] **No Cleanup in Observers**: Progress bars and other resources aren't cleaned up properly if exceptions occur. (Design Issue #14)
*   [x] **FormatterFactory Doesn't Support Extension**: Adding a new formatter requires modifying the factory. (Design Issue #15)

**Performance Issues:**

*   [x] **Inefficient File Scanning**: `for file_path in self.config.directory_path.rglob("*")` loads all paths into memory before filtering. (Performance Issue #16)
*   [x] **Cache Redundant Path Resolution**: Implemented `functools.lru_cache` for `_resolve_path` in `src/code_combiner.py`. Encountered `black` parsing issues when attempting to apply to `src/filters.py`, so reverted those specific changes. (Performance Issue #17)

**Testing Gaps:**

*   [x] **Add Tests for Observer Pattern**: Create tests for the new observer pattern implementation. (Testing Gap #18)
*   [x] **Add Tests for Formatter Factory Registration**: Write tests to verify the formatter factory's registration mechanism. (Testing Gap #18)
*   [x] **Add Tests for Path Resolution Edge Cases**: Cover various scenarios for path resolution, including absolute/relative paths and non-existent paths. (Testing Gap #18)
*   [~] **Add Tests for Concurrent Access Scenarios**: Not applicable as the application is currently single-threaded. (Testing Gap #18)
*   [ ] **Add Tests for Extremely Large Files**: Test the script's behavior with very large input files. (Testing Gap #18)
*   [ ] **Add Integration Test for Refactored Architecture**: Implement an end-to-end test to validate the entire refactored flow. (Testing Gap #19)

**Documentation Issues:**

*   [ ] **Add Missing Docstrings**: Provide docstrings for `FilterChainBuilder.build()`, `Publisher.notify()`, and various observer `update()` methods. (Documentation Issue #20)
*   [ ] **Update Outdated Comments**: Revise comments in the proposal document and codebase to reflect the current architecture. (Documentation Issue #21)

**Improvement Suggestions:**

*   [ ] **Add Metrics Collection**: Implement `CombinerMetrics` and `MetricsObserver` to collect and report processing statistics. (Improvement Suggestion #22)
*   [ ] **Add Dry-Run Mode**: Implement a `--dry-run` argument to show processed files without actual combination. (Improvement Suggestion #23)
*   [ ] **Add Verbose Logging Mode**: Implement `-v` or `--verbose` argument to enable detailed logging. (Improvement Suggestion #24)
*   [ ] **Add Configuration Summary**: Implement a method to print a summary of the active configuration. (Improvement Suggestion #25)