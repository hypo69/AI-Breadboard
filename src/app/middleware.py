# -*- coding: utf-8 -*-
"""HTTP middleware and request helpers for the application layer.

Middleware:
- auto_login_local_user  — auto-authenticate localhost / LAN requests as user_id=1
- metrics_middleware     — record latency + status in MetricsCollector

Helpers (used by routes):
- is_localhost(request) -> bool
- get_request_hostname(request) -> str
- is_authenticated_user(request) -> bool
"""
from __future__ import annotations

import time
from typing import Callable

from fastapi import Request, Response

from src.logger import logger


# ---------------------------------------------------------------------------
# Request helpers
# ---------------------------------------------------------------------------

def is_localhost(request: Request) -> bool:
    """Return True if request comes from localhost or a private LAN address."""
    host: str = (request.client.host if request.client else "") or ""
    return (
        host in ("127.0.0.1", "::1", "localhost", "testserver", "testclient", "0.0.0.0")
        or host.startswith("192.168.")
        or host.startswith("10.")
        or host.startswith("172.")
    )


def get_request_hostname(request: Request) -> str:
    """Return lowercase hostname from headers or URL."""
    raw: str = (
        request.headers.get("x-forwarded-host")
        or request.headers.get("host")
        or request.url.hostname
        or ""
    )
    return raw.split(":")[0].strip().lower()


def is_authenticated_user(request: Request) -> bool:
    """Return True if the request carries a valid JWT auth token."""
    token: str = request.cookies.get("auth_token", "")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:].strip()
        elif auth.startswith("Token "):
            token = auth[6:].strip()
    if not token:
        return False
    from src.api.router_auth import verify_jwt_token
    return verify_jwt_token(token) is not None


# ---------------------------------------------------------------------------
# Metrics middleware
# ---------------------------------------------------------------------------

async def metrics_middleware(request: Request, call_next: Callable) -> Response:
    """Record request latency and HTTP status into MetricsCollector."""
    t0 = time.perf_counter()
    response: Response = await call_next(request)
    latency_ms = (time.perf_counter() - t0) * 1000
    try:
        m = getattr(request.app.state, "metrics", None)
        if m is not None:
            m.record_request(request.url.path, latency_ms, response.status_code)
    except Exception:
        pass
    return response


# ---------------------------------------------------------------------------
# Auto-login middleware (disabled - explicit authentication required)
# ---------------------------------------------------------------------------

async def auto_login_local_user(request: Request, call_next: Callable) -> Response:
    """Pass-through middleware preserving explicit OAuth and credential authentication.

    Automatic localhost token generation is disabled in favor of proper OAuth/JWT authentication.
    """
    return await call_next(request)

