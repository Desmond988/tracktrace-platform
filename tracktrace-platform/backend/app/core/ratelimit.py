"""Small in-memory sliding-window rate limiter.

LIMITATION: state is per-process. With several workers/instances the effective limit multiplies.
For multi-instance production use a shared store (Redis) and/or Cloudflare rate-limiting rules as well.
"""
import threading
import time
from collections import defaultdict, deque

from fastapi import Request

from app.core.config import settings
from app.core.errors import AppError

_lock = threading.Lock()
_hits: dict[str, deque] = defaultdict(deque)
ENABLED = True  # tests toggle this


def client_ip(request: Request) -> str:
    if settings.TRUSTED_PROXY_HEADERS:
        cf = request.headers.get("cf-connecting-ip")
        if cf:
            return cf.strip()
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check(key: str, spec: str) -> None:
    limit_s, window_s = spec.split("/")
    limit, window = int(limit_s), int(window_s)
    now = time.monotonic()
    with _lock:
        q = _hits[key]
        while q and q[0] <= now - window:
            q.popleft()
        if len(q) >= limit:
            retry = max(1, int(window - (now - q[0])))
            raise AppError(429, "RATE_LIMITED", "Too many requests. Please wait a moment and try again.",
                           extra={"retry_after": retry}, headers={"Retry-After": str(retry)})
        q.append(now)


def limiter(name: str, spec_attr: str):
    """FastAPI dependency factory: limit per client IP."""

    def dep(request: Request) -> None:
        if not ENABLED:
            return
        check(f"{name}:{client_ip(request)}", getattr(settings, spec_attr))

    return dep


def reset() -> None:
    with _lock:
        _hits.clear()
