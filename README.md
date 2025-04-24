[![PyPI](https://img.shields.io/pypi/v/memprofilerx)](https://pypi.org/project/memprofilerx/)
[![Tests](https://github.com/NightzDev/memprofilerx/actions/workflows/ci.yml/badge.svg)](https://github.com/NightzDev/memprofilerx/actions)
[![License](https://img.shields.io/github/license/NightzDev/memprofilerx)](LICENSE)

# 🧠 memprofilerx

**memprofilerx** is a modern, developer-friendly Python library to **monitor memory usage** in real time — with zero friction and pro-level insights.

Track, visualize, and analyze memory in your scripts, APIs, and large-scale apps with just one decorator.

---

## 🚀 Features

- 🧪 `@track_memory`: monitor memory during function execution
- 📊 Auto-export graphs (PNG)
- 🧠 Optional analysis of live Python objects with `gc`
- 🔥 `@global_tracker`: monitor the whole process (great for FastAPI, CLI, etc)
- 📈 Graph generation with `matplotlib`
- 🧩 Extensible via callback or future plugins

---

## 💾 Installation

```bash
pip install memprofilerx
```

> Or using poetry:

```bash
poetry add memprofilerx
```

---

## ⚙️ Usage

### 1. Track a single function

```python
from memprofilerx.tracker import track_memory

@track_memory(interval=1.0, analyze_gc=True)
def process_data():
    x = [i for i in range(10_000_000)]
    return "Done"

result = process_data()

print(result["memory_usage"])     # List of (timestamp, memory_in_MB)
print(result["live_objects"])     # GC summary (if enabled)
```

---

### 2. Track the full runtime of an app

```python
from memprofilerx.tracker import global_tracker

@global_tracker(interval=1.0, export_png="memory.png")
def main():
    import time
    data = [i for i in range(10_000_000)]
    time.sleep(5)

main()
```

Generates:

- 📄 `memory.png`: chart of memory usage over time

---

## 📈 Generate memory graph manually

```python
from memprofilerx.reporter import plot_memory

data = [(0, 21.4), (1, 33.8), (2, 56.0)]
plot_memory(data, output_path="custom_graph.png")
```

---

## 🧠 Output Example

```json
{
  "result": "Done",
  "memory_usage": [
    [0.0, 23.1],
    [1.0, 130.5],
    [2.0, 130.7]
  ],
  "live_objects": {
    "list": {"count": 10003, "total_size_kb": 400.2},
    "dict": {"count": 12000, "total_size_kb": 800.5}
  }
}
```

---

## 🔧 Roadmap

- [x] Memory tracking via decorator
- [x] Graph export (PNG)
- [x] GC object analysis
- [x] Global tracker
- [ ] CLI: `memx run my_script.py`
- [ ] Live chart (rich + curses)
- [ ] Export to HTML or CSV
- [ ] Integration with logging/Prometheus/Sentry

---

## 📄 License

MIT — use it freely, improve it openly.

---

## ✨ Contribute

Pull requests are welcome! If you have ideas for advanced tooling, CLI integration, or observability plugins — open an issue or fork away.
