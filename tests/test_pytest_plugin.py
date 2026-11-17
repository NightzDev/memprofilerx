"""Tests for the pytest plugin, using pytester."""

import pytest

pytest_plugins = ["pytester"]

NO_LEAKS_TESTS = """
import pytest
LEAK = []

@pytest.mark.no_leaks(iterations=5, warmup=1)
def test_leaky():
    LEAK.append(b"x" * 50_000)

@pytest.mark.no_leaks(iterations=5)
def test_clean(tmp_path):
    data = [1] * 10_000
    del data
"""

MEMORY_LIMIT_TESTS = """
import pytest

@pytest.mark.memory_limit("1 MB")
def test_big():
    data = bytearray(5 * 1024 * 1024)

@pytest.mark.memory_limit("10 MB")
def test_small():
    data = bytearray(1024)
"""

FIXTURE_TESTS = """
SINK = []

def test_fixture(memx_leaks):
    memx_leaks(lambda: SINK.append(b"x" * 30_000), iterations=5)
"""


def test_no_leaks_marker(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(NO_LEAKS_TESTS)
    result = pytester.runpytest("-p", "no:cacheprovider")
    result.assert_outcomes(passed=1, failed=1)
    result.stdout.fnmatch_lines(["*leak suspect*", "*LEAK.append*"])


def test_memory_limit_marker(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(MEMORY_LIMIT_TESTS)
    result = pytester.runpytest("-p", "no:cacheprovider")
    result.assert_outcomes(passed=1, failed=1)
    result.stdout.fnmatch_lines(["*memory_limit exceeded*"])


def test_memx_leaks_fixture(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(FIXTURE_TESTS)
    result = pytester.runpytest("-p", "no:cacheprovider")
    result.assert_outcomes(failed=1)
