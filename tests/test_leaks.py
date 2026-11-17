"""Tests for leak detection."""

import asyncio

import pytest

from memprofilerx import LeakDetector, MemoryLeakError, find_leaks, find_leaks_async
from memprofilerx.leaks import parse_size

_LEAK: list[bytes] = []


def leaky() -> None:
    _LEAK.append(b"x" * 20_000)  # LEAK-LINE


def clean() -> None:
    data = [b"x" * 20_000 for _ in range(5)]
    del data


@pytest.fixture(autouse=True)
def _reset() -> None:
    _LEAK.clear()


def test_detects_leak_and_points_to_line() -> None:
    report = find_leaks(leaky, iterations=10, warmup=1)
    assert report.has_leaks
    top = report.suspects[0]
    assert top.filename.endswith("test_leaks.py")
    assert "LEAK-LINE" in top.code
    assert top.growth_bytes >= 10 * 20_000
    assert top.growing_ratio == 1.0
    with pytest.raises(MemoryLeakError, match="test_leaks.py"):
        report.assert_no_leaks()


def test_clean_function_has_no_leaks() -> None:
    report = find_leaks(clean, iterations=10)
    assert not report.has_leaks
    report.assert_no_leaks()
    assert "no leaks detected" in str(report)


def test_one_off_cache_is_not_flagged() -> None:
    cache: dict[str, bytes] = {}

    def cached() -> None:
        cache.setdefault("k", b"x" * 100_000)

    assert not find_leaks(cached, iterations=10, warmup=0).has_leaks


def test_threshold_filters_small_growth() -> None:
    assert not find_leaks(leaky, iterations=5, threshold="10 MB").has_leaks


def test_async_function() -> None:
    async def aleaky() -> None:
        await asyncio.sleep(0)
        leaky()

    assert find_leaks(aleaky, iterations=5).has_leaks
    assert asyncio.run(find_leaks_async(aleaky, iterations=5)).has_leaks


def test_args_are_forwarded() -> None:
    sink: list[bytes] = []
    report = find_leaks(lambda s, n: s.append(b"x" * n), sink, 5000, iterations=5)
    assert report.has_leaks
    assert len(sink) == 5 + 3


def test_detector_context_manager() -> None:
    with LeakDetector() as det:
        for _ in range(8):
            leaky()
            det.checkpoint()
    assert det.report.has_leaks
    assert det.report.iterations == 8
    assert det.report.to_dict()["suspects"][0]["location"].endswith(
        f":{det.report.suspects[0].lineno}"
    )


def test_detector_raise_on_leak() -> None:
    with pytest.raises(MemoryLeakError), LeakDetector(raise_on_leak=True) as det:
        for _ in range(5):
            leaky()
            det.checkpoint()


def test_detector_report_before_exit() -> None:
    with pytest.raises(RuntimeError):
        _ = LeakDetector().report


@pytest.mark.parametrize(
    ("value", "expected"),
    [(10, 10), ("1 KB", 1024), ("2mb", 2 * 1024**2), ("1.5 GB", int(1.5 * 1024**3)), ("7", 7)],
)
def test_parse_size(value: int | str, expected: int) -> None:
    assert parse_size(value) == expected


@pytest.mark.parametrize("value", ["abc", "10 XB", -1, ""])
def test_parse_size_invalid(value: int | str) -> None:
    with pytest.raises(ValueError):
        parse_size(value)


def test_invalid_args() -> None:
    with pytest.raises(ValueError):
        find_leaks(clean, iterations=1)
    with pytest.raises(ValueError):
        find_leaks(clean, warmup=-1)
    with pytest.raises(ValueError):
        find_leaks(clean, min_growing_ratio=0)
