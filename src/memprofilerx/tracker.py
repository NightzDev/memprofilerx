"""Memory tracking utilities for profiling Python applications."""

import gc
import json
import logging
import sys
import threading
import time
from collections import defaultdict
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any, ParamSpec, TypeVar

import psutil
from rich.console import Console

console = Console()
logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


def track_memory(
    interval: float = 1.0,
    duration: float | None = None,
    callback: Callable[[float, float], None] | None = None,
    analyze_gc: bool = False,
) -> Callable[[Callable[P, R]], Callable[P, dict[str, Any]]]:
    """
    Decorator to monitor memory usage during function execution.

    Args:
        interval: Sampling interval in seconds. Must be positive.
        duration: Max duration to monitor in seconds. If None, monitors until function completes.
        callback: Optional callback called on each sample with (timestamp, memory_in_MB).
        analyze_gc: Whether to include post-execution GC analysis of live objects.

    Returns:
        Decorated function that returns a dict with 'result', 'memory_usage', and
        optionally 'live_objects' keys.

    Raises:
        ValueError: If interval or duration are invalid.
        RuntimeError: If memory tracking fails.

    Example:
        >>> @track_memory(interval=0.5, analyze_gc=True)
        ... def process_data():
        ...     return [i for i in range(1000000)]
        >>> result = process_data()
        >>> print(result["memory_usage"])
    """
    if interval <= 0:
        raise ValueError(f"Interval must be positive, got {interval}")
    if duration is not None and duration <= 0:
        raise ValueError(f"Duration must be positive or None, got {duration}")

    def decorator(func: Callable[P, R]) -> Callable[P, dict[str, Any]]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> dict[str, Any]:
            try:
                process = psutil.Process()
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                logger.error(f"Failed to access process: {e}")
                raise RuntimeError(f"Cannot track memory: {e}") from e

            mem_data: list[tuple[float, float]] = []
            stop_event = threading.Event()
            monitor_error: Exception | None = None

            def monitor() -> None:
                nonlocal monitor_error
                start_time = time.time()
                while not stop_event.is_set():
                    try:
                        mem = process.memory_info().rss / (1024 * 1024)
                        timestamp = time.time() - start_time
                        mem_data.append((timestamp, mem))
                        console.log(f"[memprofilerx] {timestamp:.1f}s → {mem:.2f} MB")

                        if callback:
                            try:
                                callback(timestamp, mem)
                            except Exception as e:
                                logger.warning(f"Callback error: {e}")
                                console.log(f"[memprofilerx] Callback error: {e}")

                        if duration and timestamp >= duration:
                            break
                        time.sleep(interval)
                    except Exception as e:
                        monitor_error = e
                        logger.error(f"Monitor thread error: {e}")
                        break

            thread = threading.Thread(target=monitor, daemon=True, name="memprofilerx-monitor")
            thread.start()

            try:
                result = func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Function {func.__name__} raised exception: {e}")
                raise
            finally:
                stop_event.set()
                thread.join(timeout=5.0)
                if thread.is_alive():
                    logger.warning("Monitor thread did not terminate cleanly")

            if monitor_error:
                raise RuntimeError(f"Memory monitoring failed: {monitor_error}") from monitor_error

            output: dict[str, Any] = {"result": result, "memory_usage": mem_data}

            if analyze_gc:
                try:
                    output["live_objects"] = analyze_live_objects()
                except Exception as e:
                    logger.warning(f"GC analysis failed: {e}")
                    output["live_objects"] = {}

            return output

        return wrapper

    return decorator


def analyze_live_objects(min_size_kb: int = 100) -> dict[str, dict[str, int | float]]:
    """
    Analyze and summarize live Python objects grouped by type.

    This function uses the garbage collector to inspect all tracked objects,
    measuring their memory footprint and grouping by type.

    Args:
        min_size_kb: Minimum total size in KB for a type to be included in results.
                     Filters out noise from small object types.

    Returns:
        Dictionary mapping type names to their statistics:
        - 'count': Number of instances of this type
        - 'total_size_kb': Total memory used by all instances (in KB)

    Example:
        >>> stats = analyze_live_objects(min_size_kb=50)
        >>> print(stats['list'])
        {'count': 10003, 'total_size_kb': 400.2}

    Note:
        This can be slow for applications with many objects. Results are
        approximate as sys.getsizeof() doesn't account for referenced objects.
    """
    if min_size_kb < 0:
        raise ValueError(f"min_size_kb must be non-negative, got {min_size_kb}")

    stats: dict[str, dict[str, int]] = defaultdict(lambda: {"count": 0, "total_size": 0})

    for obj in gc.get_objects():
        try:
            size = sys.getsizeof(obj)
            type_name = type(obj).__name__
            stats[type_name]["count"] += 1
            stats[type_name]["total_size"] += size
        except (TypeError, AttributeError, ReferenceError):
            # Some objects may not support getsizeof or may be deleted during iteration
            continue
        except Exception as e:
            logger.debug(f"Unexpected error analyzing object: {e}")
            continue

    return {
        type_name: {
            "count": data["count"],
            "total_size_kb": round(data["total_size"] / 1024, 2),
        }
        for type_name, data in stats.items()
        if data["total_size"] / 1024 > min_size_kb
    }


def global_tracker(
    interval: float = 1.0,
    export_png: str | Path | None = None,
    export_json: str | Path | None = None,
    export_csv: str | Path | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to monitor memory of the entire process during function execution.

    Ideal for monitoring complete applications (e.g., FastAPI main(), CLI tools).
    Tracks memory continuously and optionally exports results to various formats.

    Args:
        interval: Sampling interval in seconds. Must be positive.
        export_png: File path to export memory visualization as PNG image.
        export_json: File path to export raw memory data as JSON.
        export_csv: File path to export memory data as CSV.

    Returns:
        Decorated function that monitors memory and exports data after execution.

    Raises:
        ValueError: If interval is invalid.
        RuntimeError: If memory tracking fails critically.
        IOError: If file export fails.

    Example:
        >>> @global_tracker(interval=0.5, export_png="memory.png")
        ... def main():
        ...     # Your application code
        ...     pass
        >>> main()
    """
    if interval <= 0:
        raise ValueError(f"Interval must be positive, got {interval}")

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                process = psutil.Process()
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                logger.error(f"Failed to access process: {e}")
                raise RuntimeError(f"Cannot track memory: {e}") from e

            mem_data: list[tuple[float, float]] = []
            stop_event = threading.Event()

            def monitor() -> None:
                start_time = time.time()
                while not stop_event.is_set():
                    try:
                        mem = process.memory_info().rss / (1024 * 1024)
                        timestamp = time.time() - start_time
                        mem_data.append((timestamp, mem))
                        console.log(f"[global_tracker] {timestamp:.1f}s → {mem:.2f} MB")
                        time.sleep(interval)
                    except Exception as e:
                        logger.error(f"Monitor thread error: {e}")
                        console.log(f"[global_tracker] Error: {e}")
                        break

            thread = threading.Thread(target=monitor, daemon=True, name="global-tracker-monitor")
            thread.start()

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                logger.error(f"Function {func.__name__} raised exception: {e}")
                raise
            finally:
                stop_event.set()
                thread.join(timeout=5.0)
                if thread.is_alive():
                    logger.warning("Monitor thread did not terminate cleanly")

                # Export data in requested formats
                if export_png:
                    try:
                        from .reporter import plot_memory

                        plot_memory(mem_data, output_path=str(export_png))
                        logger.info(f"Memory plot exported to {export_png}")
                    except ImportError as e:
                        logger.error(f"Could not import plot_memory: {e}")
                        console.log("[global_tracker] Could not import plot_memory")
                    except Exception as e:
                        logger.error(f"Failed to export PNG: {e}")
                        console.log(f"[global_tracker] Failed to export PNG: {e}")

                if export_json:
                    try:
                        export_path = Path(export_json)
                        export_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(export_path, "w", encoding="utf-8") as f:
                            json.dump(mem_data, f, indent=2)
                        logger.info(f"Memory data exported to {export_json}")
                    except OSError as e:
                        logger.error(f"Failed to export JSON: {e}")
                        console.log(f"[global_tracker] Failed to export JSON: {e}")

                if export_csv:
                    try:
                        export_path = Path(export_csv)
                        export_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(export_path, "w", encoding="utf-8") as f:
                            f.write("timestamp,memory_mb\n")
                            for timestamp, mem in mem_data:
                                f.write(f"{timestamp:.3f},{mem:.2f}\n")
                        logger.info(f"Memory data exported to {export_csv}")
                    except OSError as e:
                        logger.error(f"Failed to export CSV: {e}")
                        console.log(f"[global_tracker] Failed to export CSV: {e}")

        return wrapper

    return decorator
