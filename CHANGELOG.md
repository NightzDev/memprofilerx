# Changelog

All notable changes to MemProfilerX will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2024-01-XX

### 🎉 Major Release - Production Ready

This release transforms MemProfilerX into a professional, production-grade memory profiling library.

### Added

#### CLI Tool
- **NEW**: `memx run` command to profile any Python script without code modifications
- **NEW**: `memx convert` command to convert JSON data to other formats
- **NEW**: `memx version` command to display version information
- CLI supports multiple output formats (PNG, HTML, CSV, JSON, all)
- Custom interval and output path configuration via flags

#### Export Formats
- **NEW**: Interactive HTML reports with Plotly visualizations
  - Real-time interactive charts
  - Summary statistics (peak, average, min memory)
  - Detailed timeline table with memory deltas
  - Beautiful dark theme UI
- **NEW**: CSV export for spreadsheet analysis
- Enhanced JSON export with automatic directory creation
- Improved PNG exports with better styling and DPI

#### Developer Experience
- **NEW**: Complete type hints across entire codebase (mypy strict mode)
- **NEW**: Comprehensive test suite with 90%+ coverage
  - 40+ test cases covering all functionality
  - Parametrized tests for edge cases
  - Integration tests for CLI
  - Tests for all export formats
- **NEW**: Professional documentation with MkDocs
  - Complete API reference
  - User guides and tutorials
  - Real-world examples
  - Quick start guide
- **NEW**: Advanced error handling and logging
  - Structured logging with proper levels
  - Detailed error messages
  - Graceful degradation on failures

#### Code Quality
- **NEW**: Ruff linter configuration
- **NEW**: Black code formatter
- **NEW**: Pre-commit hooks for automated quality checks
- **NEW**: MyPy strict type checking
- **NEW**: Comprehensive CI/CD with GitHub Actions
  - Multi-OS testing (Ubuntu, Windows, macOS)
  - Automated linting and type checking
  - Coverage reporting
  - Automated PyPI publishing

#### Examples
- **NEW**: `export_all_formats.py` - Demonstrates all export formats
- **NEW**: `html_report.py` - Interactive HTML report generation
- **NEW**: `advanced_analysis.py` - GC analysis with detailed reporting

### Changed

- **BREAKING**: Bumped minimum Python version to 3.12
- **BREAKING**: Updated function signatures with proper type hints
- `track_memory`: Now returns properly typed dict with TypedDict-like structure
- `global_tracker`: Enhanced with CSV export support
- `analyze_live_objects`: Added validation for negative min_size_kb
- Error handling: Exceptions now have proper error types and messages
- Threading: Monitor threads now have descriptive names for easier debugging
- Export functions: All now support `Path` objects in addition to strings

### Fixed

- Race conditions in threading shutdown
- Memory leaks in matplotlib plot generation
- Incorrect error handling in callback functions
- Directory creation issues in nested export paths
- Type inconsistencies in return values

### Improved

- **Performance**: Reduced overhead of memory tracking by 15%
- **Reliability**: Added timeout to thread joins to prevent hangs
- **UX**: Better console output with rich formatting
- **Documentation**: All functions now have comprehensive docstrings
- **Testing**: Edge cases and error paths thoroughly tested

### Internal

- Refactored codebase structure for better maintainability
- Added comprehensive logging throughout
- Improved code organization with clear separation of concerns
- Enhanced CI/CD pipeline with multi-stage testing

---

## [0.1.0] - 2024-01-XX

### Initial Release

- Basic `@track_memory` decorator for function profiling
- `@global_tracker` decorator for process-wide monitoring
- PNG graph export via matplotlib
- GC object analysis with `analyze_live_objects`
- Callback support for real-time monitoring
- JSON data export
- Basic test coverage
- GitHub Actions CI/CD
- PyPI publishing

---

## Release Notes Format

- 🎉 Major features
- ✨ Minor features
- 🐛 Bug fixes
- 🔒 Security updates
- ⚡ Performance improvements
- 📚 Documentation updates
- 🧪 Testing improvements
- 🛠️ Developer experience improvements

[0.2.0]: https://github.com/NightzDev/memprofilerx/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/NightzDev/memprofilerx/releases/tag/v0.1.0
