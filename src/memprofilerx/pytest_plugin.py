"""Pytest plugin: catch memory leaks and memory regressions in CI.

Installed automatically with memprofilerx (``pytest11`` entry point).

Markers::

    @pytest.mark.memory_limit("50 MB")
    def test_import_csv():
        # fails if Python allocations peak above 50 MB during the test
        ...

    @pytest.mark.no_leaks(iterations=20, threshold="10 KB")
    def test_handler():
        # the test body is run repeatedly; fails pointing to the leaking line
        handle_request()

Fixture::

    def test_service(memx_leaks):
        memx_leaks(service.process, payload, iterations=50)
"""

from __future__ import annotations

import tracemalloc
from collections.abc import Callable, Generator
from typing import Any

import pytest

from .leaks import LeakReport, MemoryLeakError, find_leaks, parse_size


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "memory_limit(limit): fail if peak Python allocations during the test exceed "
        "limit (bytes or a string like '50 MB').",
    )
    config.addinivalue_line(
        "markers",
        "no_leaks(iterations=20, warmup=3, threshold='1 KB'): run the test body repeatedly "
        "and fail if memory keeps growing, reporting the leaking source lines.",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem: pytest.Function) -> bool | None:
    marker = pyfuncitem.get_closest_marker("no_leaks")
    if marker is None:
        return None
    if marker.args:
        raise pytest.UsageError("no_leaks only accepts keyword arguments")
    func = pyfuncitem.obj
    argnames = pyfuncitem._fixtureinfo.argnames
    funcargs = {name: pyfuncitem.funcargs[name] for name in argnames}
    report = find_leaks(lambda: func(**funcargs), **marker.kwargs)
    report.assert_no_leaks()
    return True


@pytest.hookimpl(wrapper=True)
def pytest_runtest_call(item: pytest.Item) -> Generator[None, object, object]:
    marker = item.get_closest_marker("memory_limit")
    if marker is None:
        return (yield)
    if not marker.args:
        raise pytest.UsageError("memory_limit requires a limit, e.g. memory_limit('50 MB')")
    limit = parse_size(marker.args[0])
    started = not tracemalloc.is_tracing()
    if started:
        tracemalloc.start()
    tracemalloc.reset_peak()
    baseline, _ = tracemalloc.get_traced_memory()
    try:
        result = yield
        _, peak = tracemalloc.get_traced_memory()
    finally:
        if started:
            tracemalloc.stop()
    used = peak - baseline
    if used > limit:
        raise MemoryLeakError(
            f"memory_limit exceeded: test peaked at {used / 1024 / 1024:.2f} MB "
            f"(limit {limit / 1024 / 1024:.2f} MB)"
        )
    return result


@pytest.fixture
def memx_leaks() -> Callable[..., LeakReport]:
    """Run ``func(*args, **kwargs)`` repeatedly and fail the test if it leaks."""

    def check(func: Callable[..., Any], *args: Any, **kwargs: Any) -> LeakReport:
        report = find_leaks(func, *args, **kwargs)
        report.assert_no_leaks()
        return report

    return check
