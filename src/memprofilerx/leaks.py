"""Memory leak detection that points to the exact line of code that is leaking.

The classic pain: "memory keeps growing in production and I have no idea where".
This module runs a piece of code several times, compares ``tracemalloc``
snapshots between iterations and reports only the source lines whose
allocations grow *consistently* — i.e. real leaks, not one-off caches or
warm-up allocations.

Example:
    >>> from memprofilerx import find_leaks
    >>> cache = []
    >>> def handler():
    ...     cache.append("x" * 10_000)  # leaks on every call
    >>> report = find_leaks(handler, iterations=10)
    >>> print(report)  # doctest: +SKIP
    >>> report.assert_no_leaks()  # doctest: +SKIP
"""

from __future__ import annotations

import asyncio
import gc
import inspect
import os
import tracemalloc
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from types import TracebackType
from typing import Any

__all__ = [
    "LeakSuspect",
    "LeakReport",
    "MemoryLeakError",
    "find_leaks",
    "find_leaks_async",
    "LeakDetector",
    "parse_size",
]

_UNITS = {"b": 1, "kb": 1024, "k": 1024, "mb": 1024**2, "m": 1024**2, "gb": 1024**3, "g": 1024**3}


def parse_size(value: int | float | str) -> int:
    """Convert ``"10 MB"``, ``"512kb"`` or a number of bytes into bytes."""
    if isinstance(value, int | float):
        if value < 0:
            raise ValueError(f"Size must be non-negative, got {value}")
        return int(value)
    text = value.strip().lower().replace(" ", "")
    number = text.rstrip("abcdefghijklmnopqrstuvwxyz")
    unit = text[len(number) :] or "b"
    if unit not in _UNITS or not number:
        raise ValueError(f"Invalid size: {value!r} (use e.g. '512 KB', '10 MB')")
    return int(float(number) * _UNITS[unit])


def _fmt(n: float) -> str:
    sign = "-" if n < 0 else "+"
    n = abs(n)
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{sign}{n:.1f} {unit}" if unit != "B" else f"{sign}{int(n)} B"
        n /= 1024
    return f"{sign}{n:.1f} GB"  # pragma: no cover


class MemoryLeakError(AssertionError):
    """Raised when a leak (or memory budget violation) is detected."""

    def __init__(self, message: str, report: LeakReport | None = None) -> None:
        super().__init__(message)
        self.report = report


@dataclass(frozen=True)
class LeakSuspect:
    """A source line whose retained memory grows across iterations."""

    filename: str
    lineno: int
    growth_bytes: int
    growth_per_iteration: float
    count_growth: int
    growing_ratio: float
    code: str = ""

    @property
    def location(self) -> str:
        """``file:line``, relative to the current directory when possible."""
        path = self.filename
        try:
            rel = os.path.relpath(path)
            if not rel.startswith(".."):
                path = rel
        except ValueError:  # different drive on Windows
            pass
        return f"{path}:{self.lineno}"


@dataclass
class LeakReport:
    """Result of a leak hunt."""

    iterations: int
    warmup: int
    total_growth_bytes: int
    suspects: list[LeakSuspect] = field(default_factory=list)
    threshold_bytes: int = 0

    @property
    def growth_per_iteration(self) -> float:
        return self.total_growth_bytes / max(self.iterations, 1)

    @property
    def has_leaks(self) -> bool:
        return bool(self.suspects)

    def assert_no_leaks(self) -> None:
        """Raise :class:`MemoryLeakError` with a readable report if leaks were found."""
        if self.has_leaks:
            raise MemoryLeakError(str(self), report=self)

    def to_dict(self) -> dict[str, Any]:
        return {
            "iterations": self.iterations,
            "warmup": self.warmup,
            "total_growth_bytes": self.total_growth_bytes,
            "growth_per_iteration": self.growth_per_iteration,
            "has_leaks": self.has_leaks,
            "suspects": [
                {
                    "location": s.location,
                    "growth_bytes": s.growth_bytes,
                    "growth_per_iteration": s.growth_per_iteration,
                    "count_growth": s.count_growth,
                    "growing_ratio": s.growing_ratio,
                    "code": s.code,
                }
                for s in self.suspects
            ],
        }

    def __str__(self) -> str:
        head = (
            f"MemProfilerX leak report: {self.iterations} iterations "
            f"(after {self.warmup} warm-up), traced memory {_fmt(self.total_growth_bytes)} "
            f"({_fmt(self.growth_per_iteration)}/iteration)"
        )
        if not self.suspects:
            return head + "\n  ✔ no leaks detected"
        lines = [head, f"  ✘ {len(self.suspects)} leak suspect(s):"]
        for i, s in enumerate(self.suspects, 1):
            lines.append(
                f"  {i}. {s.location}  {_fmt(s.growth_bytes)} total, "
                f"{_fmt(s.growth_per_iteration)}/iter, +{s.count_growth} objects, "
                f"grew in {s.growing_ratio:.0%} of iterations"
            )
            if s.code:
                lines.append(f"       → {s.code}")
        return "\n".join(lines)


def _is_internal(filename: str) -> bool:
    return (
        filename == tracemalloc.__file__
        or filename.endswith(("memprofilerx/leaks.py", "memprofilerx\\leaks.py"))
        or "<frozen" in filename
    )


def _source_line(filename: str, lineno: int) -> str:
    import linecache

    return linecache.getline(filename, lineno).strip()


class _Collector:
    """Takes per-iteration snapshots and analyses growth per source line."""

    def __init__(self, threshold: int | float | str, min_growing_ratio: float) -> None:
        if not 0 < min_growing_ratio <= 1:
            raise ValueError("min_growing_ratio must be in (0, 1]")
        self.threshold = parse_size(threshold)
        self.min_growing_ratio = min_growing_ratio
        self.snapshots: list[dict[tuple[str, int], tuple[int, int]]] = []
        self.totals: list[int] = []
        self._started_tracing = False

    def start(self) -> None:
        if not tracemalloc.is_tracing():
            tracemalloc.start(1)
            self._started_tracing = True

    def stop(self) -> None:
        if self._started_tracing:
            tracemalloc.stop()
            self._started_tracing = False

    def snapshot(self) -> None:
        gc.collect()
        snap = tracemalloc.take_snapshot()
        per_line: dict[tuple[str, int], tuple[int, int]] = {}
        for stat in snap.statistics("lineno"):
            frame = stat.traceback[0]
            if _is_internal(frame.filename):
                continue
            per_line[(frame.filename, frame.lineno)] = (stat.size, stat.count)
        self.snapshots.append(per_line)
        self.totals.append(sum(size for size, _ in per_line.values()))

    def report(self, iterations: int, warmup: int, top: int) -> LeakReport:
        base, last = self.snapshots[0], self.snapshots[-1]
        steps = len(self.snapshots) - 1
        suspects: list[LeakSuspect] = []
        for key, (size, count) in last.items():
            b_size, b_count = base.get(key, (0, 0))
            growth = size - b_size
            if growth <= 0 or growth < self.threshold:
                continue
            growing = sum(
                1
                for prev, cur in zip(self.snapshots, self.snapshots[1:], strict=False)
                if cur.get(key, (0, 0))[0] > prev.get(key, (0, 0))[0]
            )
            ratio = growing / steps if steps else 0.0
            if ratio < self.min_growing_ratio:
                continue
            suspects.append(
                LeakSuspect(
                    filename=key[0],
                    lineno=key[1],
                    growth_bytes=growth,
                    growth_per_iteration=growth / iterations,
                    count_growth=count - b_count,
                    growing_ratio=ratio,
                    code=_source_line(*key),
                )
            )
        suspects.sort(key=lambda s: s.growth_bytes, reverse=True)
        return LeakReport(
            iterations=iterations,
            warmup=warmup,
            total_growth_bytes=self.totals[-1] - self.totals[0],
            suspects=suspects[:top],
            threshold_bytes=self.threshold,
        )


def _validate(iterations: int, warmup: int) -> None:
    if iterations < 2:
        raise ValueError(f"iterations must be >= 2, got {iterations}")
    if warmup < 0:
        raise ValueError(f"warmup must be >= 0, got {warmup}")


def find_leaks(
    func: Callable[..., Any],
    *args: Any,
    iterations: int = 20,
    warmup: int = 3,
    threshold: int | float | str = "1 KB",
    min_growing_ratio: float = 0.8,
    top: int = 10,
    **kwargs: Any,
) -> LeakReport:
    """Call ``func`` repeatedly and report source lines that leak memory.

    Args:
        func: The code under suspicion (a request handler, a job, a parser...).
        iterations: Measured calls. More iterations = more confidence.
        warmup: Unmeasured calls first, so lazy caches/imports aren't flagged.
        threshold: Ignore lines that grew less than this in total (e.g. ``"10 KB"``).
        min_growing_ratio: Fraction of iterations in which a line must grow to be
            reported. ``0.8`` filters out noise while catching real leaks.
        top: Maximum number of suspects in the report.

    Returns:
        A :class:`LeakReport`. Call ``report.assert_no_leaks()`` in tests.
    """
    if inspect.iscoroutinefunction(func):
        return asyncio.run(
            find_leaks_async(
                func,
                *args,
                iterations=iterations,
                warmup=warmup,
                threshold=threshold,
                min_growing_ratio=min_growing_ratio,
                top=top,
                **kwargs,
            )
        )
    _validate(iterations, warmup)
    collector = _Collector(threshold, min_growing_ratio)
    collector.start()
    try:
        for _ in range(warmup):
            func(*args, **kwargs)
        collector.snapshot()
        for _ in range(iterations):
            func(*args, **kwargs)
            collector.snapshot()
    finally:
        collector.stop()
    return collector.report(iterations, warmup, top)


async def find_leaks_async(
    func: Callable[..., Awaitable[Any]],
    *args: Any,
    iterations: int = 20,
    warmup: int = 3,
    threshold: int | float | str = "1 KB",
    min_growing_ratio: float = 0.8,
    top: int = 10,
    **kwargs: Any,
) -> LeakReport:
    """Async version of :func:`find_leaks` for coroutine functions."""
    _validate(iterations, warmup)
    collector = _Collector(threshold, min_growing_ratio)
    collector.start()
    try:
        for _ in range(warmup):
            await func(*args, **kwargs)
        collector.snapshot()
        for _ in range(iterations):
            await func(*args, **kwargs)
            collector.snapshot()
    finally:
        collector.stop()
    return collector.report(iterations, warmup, top)


class LeakDetector:
    """Context manager for loops you already have.

    Example:
        >>> with LeakDetector() as detector:  # doctest: +SKIP
        ...     for request in requests:
        ...         handle(request)
        ...         detector.checkpoint()
        >>> detector.report.assert_no_leaks()  # doctest: +SKIP
    """

    def __init__(
        self,
        threshold: int | float | str = "1 KB",
        min_growing_ratio: float = 0.8,
        top: int = 10,
        raise_on_leak: bool = False,
    ) -> None:
        self._collector = _Collector(threshold, min_growing_ratio)
        self._top = top
        self._raise = raise_on_leak
        self._report: LeakReport | None = None

    def __enter__(self) -> LeakDetector:
        self._collector.start()
        self._collector.snapshot()
        return self

    def checkpoint(self) -> None:
        """Mark the end of one iteration."""
        self._collector.snapshot()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        try:
            if len(self._collector.snapshots) < 2:
                self._collector.snapshot()
            iterations = len(self._collector.snapshots) - 1
            self._report = self._collector.report(iterations, 0, self._top)
        finally:
            self._collector.stop()
        if self._raise and exc_type is None:
            self._report.assert_no_leaks()

    @property
    def report(self) -> LeakReport:
        if self._report is None:
            raise RuntimeError("Report is only available after the 'with' block exits")
        return self._report
