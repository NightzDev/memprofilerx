# MemProfilerX

**Professional Python memory profiler with live tracking and comprehensive export options.**

[![PyPI](https://img.shields.io/pypi/v/memprofilerx)](https://pypi.org/project/memprofilerx/)
[![Tests](https://github.com/NightzDev/memprofilerx/actions/workflows/ci.yml/badge.svg)](https://github.com/NightzDev/memprofilerx/actions)
[![License](https://img.shields.io/github/license/NightzDev/memprofilerx)](https://github.com/NightzDev/memprofilerx/blob/main/LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Overview

MemProfilerX is a modern, developer-friendly Python library designed to help you understand and optimize memory usage in your applications. Whether you're debugging memory leaks, optimizing performance, or just curious about your application's memory footprint, MemProfilerX provides the tools you need.

## Key Features

- **🎯 Simple Decorators**: Track memory with a single `@track_memory` or `@global_tracker` decorator
- **📊 Multiple Export Formats**: PNG visualizations, interactive HTML reports, CSV, and JSON
- **🧠 GC Analysis**: Inspect live Python objects grouped by type
- **⚡ CLI Tool**: Profile any Python script with `memx run script.py`
- **📈 Real-time Monitoring**: Track memory usage as your code executes
- **🔍 Type-safe**: Fully typed with mypy strict mode
- **🧪 Well-tested**: Comprehensive test suite with high coverage
- **📚 Great Documentation**: Detailed guides and examples

## Quick Example

```python
from memprofilerx import track_memory

@track_memory(interval=0.5, analyze_gc=True)
def process_large_dataset():
    data = [i for i in range(10_000_000)]
    return sum(data)

result = process_large_dataset()
print(f"Peak memory: {max(m for _, m in result['memory_usage']):.2f} MB")
```

## Why MemProfilerX?

### Compared to memory_profiler

- ✅ Modern Python (3.12+) with full type hints
- ✅ Multiple export formats (HTML, CSV, JSON, PNG)
- ✅ Built-in CLI tool
- ✅ Real-time monitoring with callbacks
- ✅ Professional HTML reports with interactive charts

### Compared to tracemalloc

- ✅ Higher-level API with decorators
- ✅ Automatic visualization and reporting
- ✅ Process-wide monitoring with `global_tracker`
- ✅ Integration with external tools via callbacks

## Installation

```bash
pip install memprofilerx
```

Or with Poetry:

```bash
poetry add memprofilerx
```

## What's New in v0.2.0

- 🎉 **CLI Tool**: New `memx` command for profiling any script
- 📊 **HTML Reports**: Interactive reports with Plotly visualizations
- 📁 **CSV Export**: Export data for analysis in spreadsheets
- 🔒 **Type Safety**: Complete type hints with strict mypy
- 🧪 **Better Testing**: Comprehensive test suite with 90%+ coverage
- 📚 **Documentation**: Full MkDocs documentation with examples
- 🛠️ **Better Errors**: Improved error handling and logging

## Community & Support

- 📖 [Documentation](https://nightzdev.github.io/memprofilerx/)
- 🐛 [Issue Tracker](https://github.com/NightzDev/memprofilerx/issues)
- 💬 [Discussions](https://github.com/NightzDev/memprofilerx/discussions)
- 📦 [PyPI Package](https://pypi.org/project/memprofilerx/)

## License

MIT License - use it freely, improve it openly.
