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
# Auto-login middleware
# ---------------------------------------------------------------------------

async def auto_login_local_user(request: Request, call_next: Callable) -> Response:
    """Automatically authenticate localhost / LAN requests as user_id=1.

    Works correctly in both modes:
    - Single-user (localhost): every request gets a fresh token for user 1
    - Multi-user (server):     external requests are untouched (not local)
    """
    hostname: str = request.url.hostname or ""
    is_local: bool = (
        hostname in ("127.0.0.1", "localhost", "::1", "testserver", "0.0.0.0")
        or hostname.startswith("192.168.")
        or hostname.startswith("10.")
        or hostname.startswith("172.")
    )

    skip = ("/login", "/auth/")
    if not is_local or any(request.url.path == p or request.url.path.startswith(p) for p in skip):
        return await call_next(request)

    # Validate existing token
    token: str = request.cookies.get("auth_token", "")
    token_valid = False
    if token:
        try:
            from src.api.router_auth import verify_jwt_token
            token_valid = bool(verify_jwt_token(token))
        except Exception:
            pass

    if token_valid:
        return await call_next(request)

    # Issue a fresh token for user_id=1
    try:
        from src.user_manager import user_manager
        db_user = user_manager.get_user_by_id(1)
        if db_user:
            from src.api.router_auth import TokenData, create_jwt_token
            token = create_jwt_token(
                TokenData(
                    email=db_user["email"],
                    name=db_user["name"],
                    picture=db_user.get("picture", ""),
                    id=db_user["id"],
                )
            )
            # Inject into request scope so handlers see it immediately
            raw_headers = list(request.scope.get("headers", []))
            cookie_bytes = f"auth_token={token}".encode("utf-8")
            new_headers = []
            found = False
            for k, v in raw_headers:
                if k.lower() == b"cookie":
                    new_headers.append((k, v + b"; " + cookie_bytes))
                    found = True
                else:
                    new_headers.append((k, v))
            if not found:
                new_headers.append((b"cookie", cookie_bytes))
            request.scope["headers"] = new_headers
            if hasattr(request, "_cookies"):
                delattr(request, "_cookies")

            response = await call_next(request)
            response.set_cookie(
                "auth_token", token,
                httponly=True, secure=False, samesite="lax",
                max_age=3600 * 24 * 30,
            )
            return response
    except Exception as exc:
        logger.error(f"[auto_login_local_user] error: {exc}")

    return await call_next(request)
