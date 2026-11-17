"""Find the exact line that leaks memory."""

from memprofilerx import find_leaks

_cache: dict[int, dict[str, object]] = {}
_counter = [0]


def handle_request() -> None:
    _counter[0] += 1
    _cache[_counter[0]] = {"body": "x" * 5000}  # forgotten cache -> leak


if __name__ == "__main__":
    report = find_leaks(handle_request, iterations=30)
    print(report)
