"""Framework-agnostic memory middleware (ASGI + WSGI).

Works with anything that speaks ASGI or WSGI — no framework-specific code:

* ASGI: FastAPI, Starlette, Litestar, Quart, Django (asgi), Sanic (asgi), BlackSheep...
* WSGI: Flask, Django (wsgi), Bottle, Falcon, Pyramid...

It answers the question devs actually ask in production:
*"which endpoint is eating my memory?"*

Example (FastAPI / Starlette)::

    from memprofilerx.middleware import MemoryMiddleware
    app.add_middleware(MemoryMiddleware, stats_path="/__memx__")

Example (Flask)::

    from memprofilerx.middleware import WSGIMemoryMiddleware
    app.wsgi_app = WSGIMemoryMiddleware(app.wsgi_app, stats_path="/__memx__")

Example (Django, ``asgi.py`` or ``wsgi.py``)::

    application = MemoryMiddleware(get_asgi_application())
    # or
    application = WSGIMemoryMiddleware(get_wsgi_application())

Note:
    RSS is a process-wide number. Under heavy concurrency a request's delta also
    includes what concurrent requests allocated. The per-route *aggregates*
    (retained growth over many requests) remain a reliable signal of which route
    is responsible for growth.
"""

from __future__ import annotations

import json
import logging
import re
import threading
import time
from collections.abc import Awaitable, Callable, Iterable, MutableMapping
from dataclasses import dataclass, field
from typing import Any

import psutil

from .leaks import parse_size

__all__ = [
    "MemoryMiddleware",
    "WSGIMemoryMiddleware",
    "MemoryStats",
    "RouteStats",
    "RequestMemoryEvent",
    "normalize_path",
]

logger = logging.getLogger(__name__)

_MB = 1024 * 1024
_ID_SEGMENT = re.compile(
    r"^(?:\d+|[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
    r"|[0-9a-fA-F]{24,})$"
)


def normalize_path(path: str) -> str:
    """Collapse ids/uuids/hashes so ``/users/42`` and ``/users/7`` share stats."""
    parts = [("{id}" if _ID_SEGMENT.match(p) else p) for p in path.split("/")]
    return "/".join(parts) or "/"


@dataclass(frozen=True)
class RequestMemoryEvent:
    """Passed to ``on_request`` / ``on_alert`` callbacks."""

    method: str
    path: str
    route: str
    status: int | None
    rss_before_mb: float
    rss_after_mb: float
    duration_s: float

    @property
    def delta_mb(self) -> float:
        return self.rss_after_mb - self.rss_before_mb


@dataclass
class RouteStats:
    """Aggregated memory behaviour of one route (``METHOD /path``)."""

    requests: int = 0
    total_delta_mb: float = 0.0
    max_delta_mb: float = 0.0
    growing_requests: int = 0
    total_duration_s: float = 0.0

    @property
    def avg_delta_mb(self) -> float:
        return self.total_delta_mb / self.requests if self.requests else 0.0

    @property
    def growing_ratio(self) -> float:
        return self.growing_requests / self.requests if self.requests else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "requests": self.requests,
            "retained_mb": round(self.total_delta_mb, 3),
            "avg_delta_mb": round(self.avg_delta_mb, 4),
            "max_delta_mb": round(self.max_delta_mb, 3),
            "growing_ratio": round(self.growing_ratio, 3),
            "avg_duration_ms": (
                round(self.total_duration_s / self.requests * 1000, 2) if self.requests else 0.0
            ),
        }


@dataclass
class MemoryStats:
    """Thread-safe store of per-route memory statistics. Shareable between apps."""

    routes: dict[str, RouteStats] = field(default_factory=dict)
    started_at: float = field(default_factory=time.time)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def record(self, event: RequestMemoryEvent) -> None:
        key = f"{event.method} {event.route}"
        with self._lock:
            stats = self.routes.setdefault(key, RouteStats())
            stats.requests += 1
            stats.total_delta_mb += event.delta_mb
            stats.max_delta_mb = max(stats.max_delta_mb, event.delta_mb)
            stats.total_duration_s += event.duration_s
            if event.delta_mb > 0:
                stats.growing_requests += 1

    def reset(self) -> None:
        with self._lock:
            self.routes.clear()
            self.started_at = time.time()

    def leak_suspects(
        self, min_requests: int = 10, min_retained_mb: float = 1.0, min_growing_ratio: float = 0.5
    ) -> list[tuple[str, RouteStats]]:
        """Routes that keep memory after most requests — the usual leak signature."""
        with self._lock:
            items = list(self.routes.items())
        suspects = [
            (route, s)
            for route, s in items
            if s.requests >= min_requests
            and s.total_delta_mb >= min_retained_mb
            and s.growing_ratio >= min_growing_ratio
        ]
        return sorted(suspects, key=lambda kv: kv[1].total_delta_mb, reverse=True)

    def snapshot(self) -> dict[str, Any]:
        try:
            rss = psutil.Process().memory_info().rss / _MB
        except (psutil.Error, OSError):  # pragma: no cover
            rss = -1.0
        with self._lock:
            routes = {k: v.to_dict() for k, v in self.routes.items()}
        ordered = dict(sorted(routes.items(), key=lambda kv: kv[1]["retained_mb"], reverse=True))
        return {
            "rss_mb": round(rss, 2),
            "uptime_s": round(time.time() - self.started_at, 1),
            "routes": ordered,
            "leak_suspects": [route for route, _ in self.leak_suspects()],
        }

    def report(self, top: int = 10) -> str:
        """Human-readable table, sorted by retained memory."""
        snap = self.snapshot()
        lines = [f"MemProfilerX — RSS {snap['rss_mb']} MB, uptime {snap['uptime_s']}s"]
        lines.append(f"{'route':<40} {'reqs':>6} {'retained':>10} {'avg':>9} {'max':>9}")
        for route, s in list(snap["routes"].items())[:top]:
            flag = "  ⚠ leak?" if route in snap["leak_suspects"] else ""
            lines.append(
                f"{route[:40]:<40} {s['requests']:>6} {s['retained_mb']:>8.2f}MB "
                f"{s['avg_delta_mb']:>7.3f}MB {s['max_delta_mb']:>7.2f}MB{flag}"
            )
        return "\n".join(lines)


class _Core:
    """Shared logic between the ASGI and WSGI middlewares."""

    def __init__(
        self,
        stats: MemoryStats | None,
        stats_path: str | None,
        alert_threshold: int | float | str | None,
        on_request: Callable[[RequestMemoryEvent], None] | None,
        on_alert: Callable[[RequestMemoryEvent], None] | None,
        add_headers: bool,
        exclude_paths: Iterable[str],
        path_normalizer: Callable[[str], str],
    ) -> None:
        self.stats = stats if stats is not None else MemoryStats()
        self.stats_path = stats_path
        self.alert_mb = parse_size(alert_threshold) / _MB if alert_threshold is not None else None
        self.on_request = on_request
        self.on_alert = on_alert
        self.add_headers = add_headers
        self.exclude = tuple(exclude_paths)
        self.normalize = path_normalizer
        self.process = psutil.Process()

    def rss_mb(self) -> float:
        return float(self.process.memory_info().rss) / _MB

    def skip(self, path: str) -> bool:
        return any(path.startswith(prefix) for prefix in self.exclude)

    def stats_body(self) -> bytes:
        return json.dumps(self.stats.snapshot(), indent=2).encode()

    def finish(self, event: RequestMemoryEvent) -> None:
        self.stats.record(event)
        if self.on_request is not None:
            try:
                self.on_request(event)
            except Exception as e:  # never break the user's app
                logger.warning(f"memprofilerx on_request callback failed: {e}")
        if self.alert_mb is not None and event.delta_mb >= self.alert_mb:
            logger.warning(
                f"memprofilerx: {event.method} {event.path} grew RSS by "
                f"{event.delta_mb:.2f} MB (threshold {self.alert_mb:.2f} MB)"
            )
            if self.on_alert is not None:
                try:
                    self.on_alert(event)
                except Exception as e:
                    logger.warning(f"memprofilerx on_alert callback failed: {e}")


_Scope = MutableMapping[str, Any]
_Message = MutableMapping[str, Any]
_Receive = Callable[[], Awaitable[_Message]]
_Send = Callable[[_Message], Awaitable[None]]
_ASGIApp = Callable[[_Scope, _Receive, _Send], Awaitable[None]]


class MemoryMiddleware:
    """ASGI middleware tracking memory per request and per route.

    Args:
        app: The ASGI application to wrap.
        stats: Optional shared :class:`MemoryStats` (e.g. to read it from your own code).
        stats_path: If set (e.g. ``"/__memx__"``), serves a JSON report at that path.
            Leave ``None`` in public deployments or protect it behind auth.
        alert_threshold: Log a warning (and call ``on_alert``) when a single request
            grows RSS by at least this much, e.g. ``"50 MB"``.
        on_request: Callback receiving a :class:`RequestMemoryEvent` for every request.
        on_alert: Callback for requests above ``alert_threshold``.
        add_headers: Add ``X-MemX-RSS-MB`` / ``X-MemX-Delta-MB`` response headers.
        exclude_paths: Path prefixes to ignore (health checks, static files...).
        path_normalizer: Maps a raw path to a route key (default collapses ids).
    """

    def __init__(
        self,
        app: _ASGIApp,
        stats: MemoryStats | None = None,
        stats_path: str | None = None,
        alert_threshold: int | float | str | None = None,
        on_request: Callable[[RequestMemoryEvent], None] | None = None,
        on_alert: Callable[[RequestMemoryEvent], None] | None = None,
        add_headers: bool = False,
        exclude_paths: Iterable[str] = (),
        path_normalizer: Callable[[str], str] = normalize_path,
    ) -> None:
        self.app = app
        self._core = _Core(
            stats,
            stats_path,
            alert_threshold,
            on_request,
            on_alert,
            add_headers,
            exclude_paths,
            path_normalizer,
        )

    @property
    def stats(self) -> MemoryStats:
        return self._core.stats

    async def __call__(self, scope: _Scope, receive: _Receive, send: _Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        core = self._core
        path: str = scope.get("path", "/")

        if core.stats_path is not None and path == core.stats_path:
            body = core.stats_body()
            await send(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"content-length", str(len(body)).encode()),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": body})
            return

        if core.skip(path):
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()
        before = core.rss_mb()
        status: int | None = None

        async def send_wrapper(message: _Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message.get("status")
                if core.add_headers:
                    now = core.rss_mb()
                    headers = list(message.get("headers", []))
                    headers.append((b"x-memx-rss-mb", f"{now:.2f}".encode()))
                    headers.append((b"x-memx-delta-mb", f"{now - before:.3f}".encode()))
                    message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            core.finish(
                RequestMemoryEvent(
                    method=scope.get("method", "GET"),
                    path=path,
                    route=core.normalize(path),
                    status=status,
                    rss_before_mb=before,
                    rss_after_mb=core.rss_mb(),
                    duration_s=time.perf_counter() - start,
                )
            )


class WSGIMemoryMiddleware:
    """WSGI version of :class:`MemoryMiddleware` (Flask, Django WSGI, Bottle, Falcon...).

    Accepts the same arguments as :class:`MemoryMiddleware`.
    """

    def __init__(
        self,
        app: Callable[..., Iterable[bytes]],
        stats: MemoryStats | None = None,
        stats_path: str | None = None,
        alert_threshold: int | float | str | None = None,
        on_request: Callable[[RequestMemoryEvent], None] | None = None,
        on_alert: Callable[[RequestMemoryEvent], None] | None = None,
        add_headers: bool = False,
        exclude_paths: Iterable[str] = (),
        path_normalizer: Callable[[str], str] = normalize_path,
    ) -> None:
        self.app = app
        self._core = _Core(
            stats,
            stats_path,
            alert_threshold,
            on_request,
            on_alert,
            add_headers,
            exclude_paths,
            path_normalizer,
        )

    @property
    def stats(self) -> MemoryStats:
        return self._core.stats

    def __call__(
        self, environ: dict[str, Any], start_response: Callable[..., Any]
    ) -> Iterable[bytes]:
        core = self._core
        path: str = environ.get("PATH_INFO", "/") or "/"

        if core.stats_path is not None and path == core.stats_path:
            body = core.stats_body()
            start_response(
                "200 OK",
                [("Content-Type", "application/json"), ("Content-Length", str(len(body)))],
            )
            return [body]

        if core.skip(path):
            return self.app(environ, start_response)

        start = time.perf_counter()
        before = core.rss_mb()
        status: list[int | None] = [None]

        def start_response_wrapper(
            status_line: str, headers: list[tuple[str, str]], exc_info: Any = None
        ) -> Any:
            try:
                status[0] = int(status_line.split(" ", 1)[0])
            except ValueError:
                status[0] = None
            if core.add_headers:
                now = core.rss_mb()
                headers = [
                    *headers,
                    ("X-MemX-RSS-MB", f"{now:.2f}"),
                    ("X-MemX-Delta-MB", f"{now - before:.3f}"),
                ]
            if exc_info is not None:
                return start_response(status_line, headers, exc_info)
            return start_response(status_line, headers)

        def finish() -> None:
            core.finish(
                RequestMemoryEvent(
                    method=environ.get("REQUEST_METHOD", "GET"),
                    path=path,
                    route=core.normalize(path),
                    status=status[0],
                    rss_before_mb=before,
                    rss_after_mb=core.rss_mb(),
                    duration_s=time.perf_counter() - start,
                )
            )

        try:
            result = self.app(environ, start_response_wrapper)
        except BaseException:
            finish()
            raise
        return _ClosingIterator(result, finish)


class _ClosingIterator:
    """Records stats once the response body has been fully consumed / closed."""

    def __init__(self, iterable: Iterable[bytes], on_close: Callable[[], None]) -> None:
        self._iterable = iterable
        self._iterator = iter(iterable)
        self._on_close = on_close
        self._closed = False

    def __iter__(self) -> _ClosingIterator:
        return self

    def __next__(self) -> bytes:
        return next(self._iterator)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            close = getattr(self._iterable, "close", None)
            if close is not None:
                close()
        finally:
            self._on_close()
