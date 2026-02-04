# Contributing to MemProfilerX

Thank you for considering contributing to MemProfilerX! We welcome contributions from everyone.

## Code of Conduct

Be respectful, inclusive, and constructive. We're all here to build something great together.

## Ways to Contribute

### 🐛 Reporting Bugs

Found a bug? Please [open an issue](https://github.com/NightzDev/memprofilerx/issues/new) with:

- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version, MemProfilerX version)
- Code sample if applicable

### ✨ Suggesting Features

Have an idea? [Open a discussion](https://github.com/NightzDev/memprofilerx/discussions) or issue with:

- Clear description of the feature
- Use case and motivation
- Possible implementation approach (optional)
- Examples of similar features in other tools (optional)

### 🔧 Pull Requests

We love pull requests! Here's how to contribute code:

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/memprofilerx.git
cd memprofilerx
```

### 2. Install Dependencies

```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install --with dev,docs

# Install pre-commit hooks
poetry run pre-commit install
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

## Development Workflow

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage report
poetry run pytest --cov --cov-report=term-missing

# Run specific test file
poetry run pytest tests/test_tracker.py

# Run specific test
poetry run pytest tests/test_tracker.py::TestTrackMemory::test_basic_tracking

# Run tests in watch mode (requires pytest-watch)
poetry run ptw
```

### Code Quality Checks

```bash
# Format code with black
poetry run black src tests

# Format code with ruff
poetry run ruff format src tests

# Lint code
poetry run ruff check src tests

# Type check with mypy
poetry run mypy src

# Run all pre-commit checks
poetry run pre-commit run --all-files
```

### Building Documentation

```bash
# Serve documentation locally (live reload)
poetry run mkdocs serve
# Visit http://127.0.0.1:8000

# Build documentation
poetry run mkdocs build
```

## Coding Standards

### Python Style

- Follow PEP 8 (enforced by black and ruff)
- Use type hints everywhere (enforced by mypy strict mode)
- Write descriptive variable and function names
- Keep functions focused and small (< 50 lines when possible)

### Type Hints

```python
# ✅ Good - Complete type hints
def process_data(
    data: list[dict[str, Any]],
    threshold: float = 0.5
) -> dict[str, int]:
    """Process data and return statistics."""
    ...

# ❌ Bad - No type hints
def process_data(data, threshold=0.5):
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def analyze_memory(
    data: list[tuple[float, float]],
    min_threshold: float = 0.0
) -> dict[str, float]:
    """
    Analyze memory usage data and compute statistics.

    Args:
        data: List of (timestamp, memory_mb) tuples.
        min_threshold: Minimum memory value to consider.

    Returns:
        Dictionary with 'peak', 'average', and 'min' keys.

    Raises:
        ValueError: If data is empty or invalid.

    Example:
        >>> data = [(0, 23.5), (1, 45.2)]
        >>> stats = analyze_memory(data)
        >>> print(stats['peak'])
        45.2
    """
    ...
```

### Error Handling

```python
# ✅ Good - Specific exceptions with context
if not mem_data:
    raise ValueError("No memory data provided to analyze.")

try:
    process_data()
except FileNotFoundError as e:
    logger.error(f"Configuration file not found: {e}")
    raise IOError(f"Cannot load configuration: {e}") from e

# ❌ Bad - Bare except
try:
    process_data()
except:
    pass
```

### Testing

Every new feature or bug fix should include tests:

```python
# ✅ Good test structure
class TestMemoryTracker:
    """Tests for memory tracking functionality."""

    def test_basic_tracking(self) -> None:
        """Test basic memory tracking returns correct structure."""
        @track_memory(interval=0.1)
        def dummy() -> int:
            return 123

        result = dummy()
        assert result["result"] == 123
        assert len(result["memory_usage"]) > 0

    def test_invalid_interval_raises_error(self) -> None:
        """Test that negative interval raises ValueError."""
        with pytest.raises(ValueError, match="Interval must be positive"):
            @track_memory(interval=-1.0)
            def dummy() -> None:
                pass
```

## Pull Request Process

### 1. Make Your Changes

- Write clean, well-documented code
- Add tests for new functionality
- Update documentation if needed
- Follow the coding standards above

### 2. Commit Your Changes

Use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Feature
git commit -m "feat: add HTML export for memory reports"

# Bug fix
git commit -m "fix: handle empty memory data in plot_memory"

# Documentation
git commit -m "docs: add examples for CLI usage"

# Tests
git commit -m "test: add tests for CSV export functionality"

# Refactoring
git commit -m "refactor: simplify error handling in tracker"
```

### 3. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:

- Clear title describing the change
- Description of what changed and why
- Link to related issues (if any)
- Screenshots/examples for UI changes

### 4. Code Review

- Address review feedback promptly
- Keep discussions focused and constructive
- Update your branch with main if needed: `git rebase main`

### 5. Merge

Once approved, a maintainer will merge your PR. Thank you! 🎉

## Project Structure

```
memprofilerx/
├── src/memprofilerx/          # Main package
│   ├── __init__.py            # Package exports
│   ├── tracker.py             # Memory tracking decorators
│   ├── reporter.py            # Export and visualization
│   └── cli.py                 # CLI commands
├── tests/                     # Test suite
│   ├── conftest.py            # Pytest configuration
│   ├── test_tracker.py        # Tracker tests
│   └── test_reporter.py       # Reporter tests
├── examples/                  # Usage examples
├── docs/                      # Documentation
├── pyproject.toml             # Project configuration
├── mkdocs.yml                 # Documentation config
└── .pre-commit-config.yaml    # Pre-commit hooks
```

## Release Process (Maintainers Only)

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` with release notes
3. Commit: `git commit -m "chore: bump version to 0.2.0"`
4. Create tag: `git tag v0.2.0`
5. Push: `git push && git push --tags`
6. GitHub Actions will automatically publish to PyPI

## Questions?

- 💬 [Start a discussion](https://github.com/NightzDev/memprofilerx/discussions)
- 📧 Open an issue for specific questions
- 📖 Check the [documentation](https://nightzdev.github.io/memprofilerx/)

Thank you for contributing to MemProfilerX! 🙏
