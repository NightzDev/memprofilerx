"""Tests for the ASGI / WSGI memory middleware."""

import asyncio
import json
from typing import Any

import pytest

from memprofilerx.middleware import (
    MemoryMiddleware,
    MemoryStats,
    RequestMemoryEvent,
    WSGIMemoryMiddleware,
    normalize_path,
)

_HOARD: list[bytearray] = []


async def asgi_app(scope: dict[str, Any], _receive: Any, send: Any) -> None:
    if scope["type"] == "lifespan":
        return
    if scope["path"].startswith("/leak"):
        _HOARD.append(bytearray(2 * 1024 * 1024))
    if scope["path"] == "/boom":
        raise RuntimeError("boom")
    await send({"type": "http.response.start", "status": 200, "headers": []})
    await send({"type": "http.response.body", "body": b"ok"})


def call_asgi(app: Any, path: str, method: str = "GET", scope_type: str = "http") -> list[Any]:
    sent: list[Any] = []

    async def receive() -> dict[str, Any]:
        return {"type": "http.request", "body": b""}

    async def send(msg: Any) -> None:
        sent.append(msg)

    asyncio.run(app({"type": scope_type, "path": path, "method": method}, receive, send))
    return sent


def wsgi_app(environ: dict[str, Any], start_response: Any) -> list[bytes]:
    if environ["PATH_INFO"].startswith("/leak"):
        _HOARD.append(bytearray(2 * 1024 * 1024))
    start_response("201 Created", [("Content-Type", "text/plain")])
    return [b"ok"]


def call_wsgi(app: Any, path: str) -> tuple[str, list[tuple[str, str]], bytes]:
    captured: dict[str, Any] = {}

    def start_response(status: str, headers: list[tuple[str, str]], _exc: Any = None) -> None:
        captured["status"], captured["headers"] = status, headers

    result = app({"PATH_INFO": path, "REQUEST_METHOD": "GET"}, start_response)
    body = b"".join(result)
    if hasattr(result, "close"):
        result.close()
    return captured["status"], captured["headers"], body


@pytest.fixture(autouse=True)
def _clear() -> None:
    _HOARD.clear()


def test_normalize_path() -> None:
    assert normalize_path("/users/42/orders") == "/users/{id}/orders"
    assert normalize_path("/items/550e8400-e29b-41d4-a716-446655440000") == "/items/{id}"
    assert normalize_path("/obj/507f1f77bcf86cd799439011") == "/obj/{id}"
    assert normalize_path("/about") == "/about"


def test_asgi_records_routes_and_headers() -> None:
    events: list[RequestMemoryEvent] = []
    mw = MemoryMiddleware(asgi_app, add_headers=True, on_request=events.append)
    sent = call_asgi(mw, "/users/1")
    call_asgi(mw, "/users/2")
    headers = dict(sent[0]["headers"])
    assert b"x-memx-rss-mb" in headers and b"x-memx-delta-mb" in headers
    assert mw.stats.routes["GET /users/{id}"].requests == 2
    assert events[0].status == 200


def test_asgi_leak_suspect_and_alert() -> None:
    alerts: list[RequestMemoryEvent] = []
    mw = MemoryMiddleware(asgi_app, alert_threshold="1 MB", on_alert=alerts.append)
    for i in range(10):
        call_asgi(mw, f"/leak/{i}")
        call_asgi(mw, "/fine")
    suspects = [r for r, _ in mw.stats.leak_suspects(min_requests=5, min_retained_mb=5)]
    assert suspects == ["GET /leak/{id}"]
    assert alerts and all(a.route == "/leak/{id}" for a in alerts)
    assert "⚠ leak?" in mw.stats.report()


def test_asgi_stats_endpoint() -> None:
    mw = MemoryMiddleware(asgi_app, stats_path="/__memx__")
    call_asgi(mw, "/a")
    sent = call_asgi(mw, "/__memx__")
    data = json.loads(sent[1]["body"])
    assert "GET /a" in data["routes"] and data["rss_mb"] > 0


def test_asgi_passthrough_and_exclude() -> None:
    mw = MemoryMiddleware(asgi_app, exclude_paths=["/health"])
    call_asgi(mw, "/health")
    call_asgi(mw, "/", scope_type="lifespan")
    assert mw.stats.routes == {}


def test_asgi_exception_still_recorded() -> None:
    mw = MemoryMiddleware(asgi_app)
    with pytest.raises(RuntimeError):
        call_asgi(mw, "/boom")
    assert mw.stats.routes["GET /boom"].requests == 1


def test_callback_errors_do_not_break_app() -> None:
    def bad(_: RequestMemoryEvent) -> None:
        raise ValueError("x")

    mw = MemoryMiddleware(asgi_app, on_request=bad, on_alert=bad, alert_threshold=0)
    assert call_asgi(mw, "/x")[0]["status"] == 200


def test_wsgi_middleware() -> None:
    shared = MemoryStats()
    mw = WSGIMemoryMiddleware(wsgi_app, stats=shared, add_headers=True, stats_path="/__memx__")
    status, headers, body = call_wsgi(mw, "/leak/5")
    assert status == "201 Created" and body == b"ok"
    assert "X-MemX-Delta-MB" in dict(headers)
    assert shared.routes["GET /leak/{id}"].requests == 1
    _, _, stats_body = call_wsgi(mw, "/__memx__")
    assert "GET /leak/{id}" in json.loads(stats_body)["routes"]
    shared.reset()
    assert shared.routes == {}


def test_flask_integration() -> None:
    flask = pytest.importorskip("flask")
    app = flask.Flask(__name__)

    @app.get("/items/<int:item_id>")
    def item(item_id: int) -> str:
        return str(item_id)

    mw = WSGIMemoryMiddleware(app.wsgi_app)
    app.wsgi_app = mw  # type: ignore[method-assign]
    client = app.test_client()
    resp = client.get("/items/3")
    assert resp.data == b"3"
    resp.close()  # WSGI servers close the response; stats are recorded then
    assert mw.stats.routes["GET /items/{id}"].requests == 1


def test_starlette_integration() -> None:
    pytest.importorskip("starlette")
    pytest.importorskip("httpx")
    from starlette.applications import Starlette
    from starlette.responses import PlainTextResponse
    from starlette.routing import Route
    from starlette.testclient import TestClient

    async def home(_request: Any) -> PlainTextResponse:
        return PlainTextResponse("hi")

    app = Starlette(routes=[Route("/", home)])
    app.add_middleware(MemoryMiddleware, add_headers=True, stats_path="/__memx__")
    client = TestClient(app)
    resp = client.get("/")
    assert resp.text == "hi" and "x-memx-delta-mb" in resp.headers
    assert "GET /" in client.get("/__memx__").json()["routes"]
