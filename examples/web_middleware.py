"""Per-endpoint memory tracking for any ASGI app (FastAPI, Starlette, Litestar...).

Run:  pip install fastapi uvicorn && uvicorn web_middleware:app
Then: curl localhost:8000/leak/1 ; curl localhost:8000/__memx__
"""

from fastapi import FastAPI

from memprofilerx import MemoryMiddleware

app = FastAPI()
app.add_middleware(
    MemoryMiddleware,
    stats_path="/__memx__",  # don't expose publicly
    alert_threshold="20 MB",
    on_alert=lambda e: print(f"⚠ {e.method} {e.path} grew {e.delta_mb:.1f} MB"),
    exclude_paths=["/health"],
)

_hoard: list[bytes] = []


@app.get("/leak/{item_id}")
def leak(item_id: int) -> dict[str, int]:
    _hoard.append(b"x" * 1_000_000)
    return {"item": item_id}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
