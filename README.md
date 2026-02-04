[![PyPI](https://img.shields.io/pypi/v/memprofilerx)](https://pypi.org/project/memprofilerx/)
[![Tests](https://github.com/NightzDev/memprofilerx/actions/workflows/ci.yml/badge.svg)](https://github.com/NightzDev/memprofilerx/actions)
[![License](https://img.shields.io/github/license/NightzDev/memprofilerx)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Code Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen.svg)]()
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://mypy-lang.org/)

# 🧠 MemProfilerX

**Professional Python memory profiler** — Track, visualize, and analyze memory usage in real time with production-grade tools.

Modern, type-safe, and developer-friendly. From quick debugging to production monitoring.

---

## ✨ What's New in v0.2.0

- 🎯 **CLI Tool**: `memx run script.py` - profile any script without code changes
- 📊 **Interactive HTML Reports**: Beautiful reports with Plotly visualizations and statistics
- 📁 **CSV Export**: Export data for analysis in Excel, Google Sheets, or pandas
- 🔒 **Type Safety**: Fully typed with strict mypy compliance
- 🧪 **Production Ready**: 90%+ test coverage, comprehensive error handling
- 📚 **Professional Docs**: Complete MkDocs documentation with guides and examples
- 🛠️ **Better DX**: Improved error messages, logging, and developer experience

---

## 🚀 Features

### Core Functionality
- 🎯 **Simple Decorators**: `@track_memory` and `@global_tracker` for zero-friction profiling
- ⚡ **CLI Tool**: Profile scripts with `memx run` - no code modifications needed
- 📊 **Multiple Formats**: Export to PNG, HTML, CSV, and JSON
- 🧠 **GC Analysis**: Deep inspection of live Python objects by type
- 📈 **Real-time Tracking**: Monitor memory as your code executes
- 🔔 **Callbacks**: React to memory changes in real-time

### Production Grade
- 🔒 **Type-safe**: Full type hints with mypy strict mode
- 🧪 **Well-tested**: Comprehensive test suite (90%+ coverage)
- 🛡️ **Robust**: Proper error handling and logging
- ⚡ **Low Overhead**: Minimal performance impact (~0.1-1% CPU)
- 📚 **Documented**: Complete documentation with examples
- 🔄 **CI/CD**: Automated testing, linting, and releases

---

## 💾 Installation

```bash
pip install memprofilerx
```

Or using Poetry:

```bash
poetry add memprofilerx
```

Requires Python 3.12 or higher.

---

## ⚙️ Usage

### Quick Start: Decorator API

```python
from memprofilerx import track_memory

@track_memory(interval=0.5, analyze_gc=True)
def process_data():
    data = [i * 2 for i in range(10_000_000)]
    return sum(data)

result = process_data()
print(f"Result: {result['result']}")
print(f"Peak memory: {max(m for _, m in result['memory_usage']):.2f} MB")
print(f"Live objects: {result['live_objects']}")
```

---

### Global Process Tracking

Monitor your entire application with all export formats:

```python
from memprofilerx import global_tracker

@global_tracker(
    interval=0.5,
    export_png="memory.png",      # Visualization
    export_html="report.html",     # Interactive report (via JSON + convert)
    export_csv="memory.csv",       # Spreadsheet data
    export_json="memory.json"      # Raw data
)
def main():
    # Your application code
    data = [i for i in range(10_000_000)]
    process(data)

main()
```

---

### CLI: Profile Any Script

No code modifications needed - just use the CLI:

```bash
# Basic profiling with PNG output
memx run my_script.py

# Custom interval and HTML report
memx run my_script.py --interval 0.5 --format html --output report

# Export all formats at once
memx run my_script.py --format all --output analysis

# Convert existing JSON to other formats
memx convert memory.json --format html --output report.html
```

---

### Interactive HTML Reports

Generate beautiful, interactive reports:

```python
from memprofilerx import global_tracker
from memprofilerx.reporter import export_to_html
import json

# Track with JSON export
@global_tracker(interval=0.3, export_json="memory.json")
def data_pipeline():
    # Your code here
    pass

data_pipeline()

# Convert to interactive HTML
with open("memory.json") as f:
    data = json.load(f)
export_to_html(data, "report.html")
```

The HTML report includes:
- 📊 Interactive Plotly charts
- 📈 Statistics (peak, average, min memory)
- 📋 Detailed timeline table with deltas
- 🎨 Beautiful dark theme UI

---

### Real-time Monitoring with Callbacks

React to memory changes as they happen:

```python
from memprofilerx import track_memory
import logging

def alert_on_high_memory(timestamp: float, memory: float) -> None:
    if memory > 500:  # 500 MB threshold
        logging.warning(f"⚠️ High memory: {memory:.2f} MB at {timestamp:.1f}s")
        # Send alert, trigger GC, etc.

@track_memory(interval=1.0, callback=alert_on_high_memory)
def long_running_task():
    # Your code
    pass
```

---

## 📊 Output Examples

### Decorator Output

```python
{
  "result": 49999995000000,
  "memory_usage": [
    [0.0, 23.1],
    [0.5, 130.5],
    [1.0, 130.7]
  ],
  "live_objects": {
    "list": {"count": 10003, "total_size_kb": 400.2},
    "dict": {"count": 12000, "total_size_kb": 800.5},
    "int": {"count": 150000, "total_size_kb": 3200.1}
  }
}
```

### CSV Format

```csv
timestamp_seconds,memory_mb
0.00,23.45
0.50,45.67
1.00,67.89
```

### HTML Report

See [example report](examples/report.html) - includes:
- Peak memory: 89.12 MB
- Average memory: 56.78 MB
- Duration: 5.23 seconds
- Interactive time-series chart
- Memory delta analysis

---

## 🗺️ Roadmap

### ✅ Completed (v0.2.0)
- [x] Memory tracking via decorator
- [x] Graph export (PNG)
- [x] GC object analysis
- [x] Global process tracker
- [x] CLI: `memx run my_script.py`
- [x] Export to HTML and CSV
- [x] Full type safety (mypy strict)
- [x] Comprehensive test suite
- [x] Professional documentation

### 🚧 In Progress
- [ ] Live dashboard (rich + curses)
- [ ] Memory diff between snapshots
- [ ] Integration with logging frameworks
- [ ] Prometheus exporter
- [ ] Sentry integration
- [ ] Memory flamegraphs

### 🔮 Future Ideas
- [ ] Memory leak detection algorithms
- [ ] Jupyter notebook integration
- [ ] VS Code extension
- [ ] Docker container profiling
- [ ] Comparative benchmarking tools
- [ ] AI-powered memory optimization suggestions

---

## 🛠️ Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/NightzDev/memprofilerx.git
cd memprofilerx

# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install --with dev,docs

# Install pre-commit hooks
poetry run pre-commit install
```

### Run Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov

# Run specific test file
poetry run pytest tests/test_tracker.py

# Run with verbose output
poetry run pytest -v
```

### Code Quality

```bash
# Format code
poetry run black src tests
poetry run ruff format src tests

# Lint code
poetry run ruff check src tests

# Type check
poetry run mypy src

# Run all checks (what CI runs)
poetry run pre-commit run --all-files
```

### Build Documentation

```bash
# Serve docs locally
poetry run mkdocs serve

# Build docs
poetry run mkdocs build
```

### Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create git tag: `git tag v0.2.0`
4. Push tag: `git push origin v0.2.0`
5. GitHub Actions will automatically publish to PyPI

---

## 📄 License

MIT License — use it freely, improve it openly.

See [LICENSE](LICENSE) for full details.

---

## 🤝 Contributing

Contributions are welcome! We appreciate:

- 🐛 Bug reports and fixes
- ✨ Feature suggestions and implementations
- 📚 Documentation improvements
- 🧪 Test coverage improvements
- 💡 Performance optimizations

### Contribution Guidelines

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`poetry run pytest && poetry run ruff check`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

See [CONTRIBUTING.md](docs/contributing.md) for detailed guidelines.

---

## 🙏 Acknowledgments

Built with:
- [psutil](https://github.com/giampaolo/psutil) - Cross-platform process utilities
- [matplotlib](https://matplotlib.org/) - Visualization library
- [rich](https://github.com/Textualize/rich) - Beautiful terminal output
- [typer](https://typer.tiangolo.com/) - CLI framework
- [pytest](https://pytest.org/) - Testing framework

Inspired by [memory_profiler](https://github.com/pythonprofilers/memory_profiler) and Python's built-in [tracemalloc](https://docs.python.org/3/library/tracemalloc.html).

---

## 📞 Support

- 📖 [Documentation](https://nightzdev.github.io/memprofilerx/)
- 🐛 [Issue Tracker](https://github.com/NightzDev/memprofilerx/issues)
- 💬 [Discussions](https://github.com/NightzDev/memprofilerx/discussions)
- 📦 [PyPI Package](https://pypi.org/project/memprofilerx/)

---

<div align="center">

**Made with ❤️ by developers, for developers**

[⭐ Star on GitHub](https://github.com/NightzDev/memprofilerx) • [📦 Install from PyPI](https://pypi.org/project/memprofilerx/)

</div>
