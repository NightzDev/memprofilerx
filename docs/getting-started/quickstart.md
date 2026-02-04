# Quick Start

Get up and running with MemProfilerX in minutes!

## Installation

Install via pip:

```bash
pip install memprofilerx
```

Or with Poetry:

```bash
poetry add memprofilerx
```

## Your First Memory Profile

### 1. Track a Function

The simplest way to use MemProfilerX is with the `@track_memory` decorator:

```python
from memprofilerx import track_memory

@track_memory(interval=0.5)
def my_function():
    # Your code here
    data = [i * 2 for i in range(1_000_000)]
    return sum(data)

result = my_function()
print(f"Function returned: {result['result']}")
print(f"Memory samples: {len(result['memory_usage'])}")
```

### 2. Export Visualizations

Add automatic PNG export:

```python
from memprofilerx import global_tracker

@global_tracker(interval=0.5, export_png="memory.png")
def main():
    # Your application code
    data = process_large_dataset()
    return data

main()
# memory.png is created automatically!
```

### 3. Generate HTML Reports

Create interactive reports:

```python
from memprofilerx import global_tracker

@global_tracker(
    interval=0.3,
    export_json="memory.json",
)
def data_pipeline():
    # Your data processing code
    pass

data_pipeline()

# Convert to HTML
from memprofilerx.reporter import export_to_html
import json

with open("memory.json") as f:
    data = json.load(f)

export_to_html(data, "report.html")
```

### 4. Use the CLI

Profile any Python script without modifying it:

```bash
# Basic profiling
memx run my_script.py

# With custom interval and HTML export
memx run my_script.py --interval 0.5 --format html --output report

# Export all formats
memx run my_script.py --format all --output analysis
```

## Next Steps

- 📖 Read the [User Guide](../guide/tracking-functions.md) for detailed usage
- 🔍 Check out [Examples](../examples/basic.md) for real-world scenarios
- 🛠️ Explore the [API Reference](../api/tracker.md) for all features
- 💡 Learn about [GC Analysis](../guide/gc-analysis.md) to understand object lifecycles

## Common Patterns

### Pattern 1: Debug Memory Leak

```python
from memprofilerx import track_memory

@track_memory(interval=1.0, analyze_gc=True)
def suspect_function():
    # Function you suspect has memory leak
    pass

result = suspect_function()

# Check growing memory
memory_usage = result['memory_usage']
if memory_usage[-1][1] > memory_usage[0][1] * 2:
    print("⚠️ Memory doubled during execution!")
    print("Live objects:", result['live_objects'])
```

### Pattern 2: Benchmark Different Approaches

```python
from memprofilerx import track_memory

@track_memory(interval=0.1)
def approach_1():
    return [x * 2 for x in range(1_000_000)]

@track_memory(interval=0.1)
def approach_2():
    return list(map(lambda x: x * 2, range(1_000_000)))

r1 = approach_1()
r2 = approach_2()

peak1 = max(m for _, m in r1['memory_usage'])
peak2 = max(m for _, m in r2['memory_usage'])

print(f"Approach 1 peak: {peak1:.2f} MB")
print(f"Approach 2 peak: {peak2:.2f} MB")
```

### Pattern 3: Production Monitoring

```python
from memprofilerx import track_memory
import logging

def alert_callback(timestamp: float, memory: float) -> None:
    if memory > 500:  # 500 MB threshold
        logging.warning(f"High memory usage: {memory:.2f} MB at {timestamp:.1f}s")

@track_memory(interval=5.0, callback=alert_callback)
def long_running_task():
    # Your production code
    pass
```

## Tips

!!! tip "Choosing the Right Interval"
    - **Development**: 0.1-0.5s for detailed tracking
    - **Testing**: 0.5-1.0s for balance
    - **Production**: 5-30s for low overhead

!!! warning "Performance Impact"
    Memory tracking adds minimal overhead (~0.1-1% CPU), but very short intervals (< 0.1s) can impact performance.

!!! info "GC Analysis"
    Enable `analyze_gc=True` only when debugging - it's slower but provides deep insights into object lifecycles.
