import time
import gc
import sys
import json
import threading
from typing import Callable, Optional, Any
from functools import wraps
from collections import defaultdict

import psutil
from rich.console import Console

console = Console()


def track_memory(
    interval: float = 1.0,
    duration: Optional[float] = None,
    callback: Optional[Callable[[float, float], None]] = None,
    analyze_gc: bool = False
):
    """
    Decorator to monitor memory usage during function execution.

    Args:
        interval (float): Sampling interval in seconds.
        duration (float, optional): Max duration to monitor.
        callback (function, optional): Called on each sample with (timestamp, memory_in_MB).
        analyze_gc (bool): Whether to include post-execution GC analysis.
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs) -> dict[str, Any]:
            process = psutil.Process()
            mem_data = []
            stop_event = threading.Event()

            def monitor():
                start_time = time.time()
                while not stop_event.is_set():
                    mem = process.memory_info().rss / (1024 * 1024)
                    timestamp = time.time() - start_time
                    mem_data.append((timestamp, mem))
                    console.log(f"[memprofilerx] {timestamp:.1f}s → {mem:.2f} MB")

                    if callback:
                        try:
                            callback(timestamp, mem)
                        except Exception as e:
                            console.log(f"[memprofilerx] Callback error: {e}")

                    if duration and timestamp >= duration:
                        break
                    time.sleep(interval)

            thread = threading.Thread(target=monitor, daemon=True)
            thread.start()

            try:
                result = func(*args, **kwargs)
            finally:
                stop_event.set()
                thread.join()

            output = {
                "result": result,
                "memory_usage": mem_data
            }

            if analyze_gc:
                output["live_objects"] = analyze_live_objects()

            return output

        return wrapper
    return decorator


def analyze_live_objects(min_size_kb: int = 100) -> dict[str, dict[str, float]]:
    """
    Returns a summary of live Python objects grouped by type.

    Args:
        min_size_kb (int): Minimum size in KB to report a type.

    Returns:
        dict: type_name → {'count': int, 'total_size_kb': float}
    """
    stats = defaultdict(lambda: {'count': 0, 'total_size': 0})
    for obj in gc.get_objects():
        try:
            size = sys.getsizeof(obj)
            t = type(obj).__name__
            stats[t]['count'] += 1
            stats[t]['total_size'] += size
        except Exception:
            continue

    return {
        t: {
            'count': data['count'],
            'total_size_kb': round(data['total_size'] / 1024, 2)
        }
        for t, data in stats.items()
        if data['total_size'] / 1024 > min_size_kb
    }


def global_tracker(
    interval: float = 1.0,
    export_png: Optional[str] = None,
    export_json: Optional[str] = None
):
    """
    Decorator to monitor memory of the whole process while a function runs.
    Ideal for monitoring full apps (e.g. FastAPI main()).

    Args:
        interval (float): Sampling interval in seconds.
        export_png (str, optional): File path to export memory graph.
        export_json (str, optional): File path to export raw data.
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            process = psutil.Process()
            mem_data = []
            stop_event = threading.Event()

            def monitor():
                start_time = time.time()
                while not stop_event.is_set():
                    try:
                        mem = process.memory_info().rss / (1024 * 1024)
                        timestamp = time.time() - start_time
                        mem_data.append((timestamp, mem))
                        console.log(f"[global_tracker] {timestamp:.1f}s → {mem:.2f} MB")
                        time.sleep(interval)
                    except Exception as e:
                        console.log(f"[global_tracker] Error: {e}")
                        break

            thread = threading.Thread(target=monitor, daemon=True)
            thread.start()

            try:
                return func(*args, **kwargs)
            finally:
                stop_event.set()
                thread.join()

                if export_png:
                    try:
                        from .reporter import plot_memory
                        plot_memory(mem_data, output_path=export_png)
                    except ImportError:
                        console.log("[global_tracker] Could not import plot_memory")

                if export_json:
                    with open(export_json, "w") as f:
                        json.dump(mem_data, f, indent=2)

        return wrapper
    return decorator
