# -*- coding: utf-8 -*-
"""CORS configuration builder.

Reads settings from config.json (server.cors) and produces a dict
suitable for FastAPI's CORSMiddleware.

Usage:
    from src.app.cors import build_cors_config
    app.add_middleware(CORSMiddleware, **build_cors_config(server_cfg))
"""
from __future__ import annotations

import re
from types import SimpleNamespace
from typing import Any, Dict, List, Optional


def build_cors_config(server_cfg: SimpleNamespace) -> Dict[str, Any]:
    """Build CORS kwargs dict from *server_cfg*.

    Priority order for origins:
    1. Localhost / loopback (always included)
    2. server.cors.allow_origins list
    3. server.client_url
    4. server.user_domain http + https
    5. server.cors_origins extra list
    """
    cors_section: Optional[SimpleNamespace] = getattr(server_cfg, "cors", None)

    origins: List[str] = [
        "http://localhost",
        "https://localhost",
        "http://127.0.0.1",
        "https://127.0.0.1",
    ]

    def _add(url: str) -> None:
        cleaned = str(url).rstrip("/")
        if cleaned and cleaned not in origins:
            origins.append(cleaned)

    if cors_section:
        for o in getattr(cors_section, "allow_origins", []) or []:
            _add(o)

    client_url: str = getattr(server_cfg, "client_url", "") or ""
    _add(client_url)

    user_domain: str = getattr(server_cfg, "user_domain", "") or ""
    if user_domain:
        _add(f"http://{user_domain}")
        _add(f"https://{user_domain}")

    for o in getattr(server_cfg, "cors_origins", []) or []:
        _add(o)

    # Origin regex
    if cors_section and getattr(cors_section, "allow_origin_regex", None):
        origin_regex: Optional[str] = cors_section.allow_origin_regex
    else:
        domain_part = f"|{re.escape(user_domain)}" if user_domain else ""
        origin_regex = (
            r"^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|"
            r"192\.168\.\d{1,3}\.\d{1,3}|"
            r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
            r"172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}"
            f"{domain_part})(:\\d+)?$"
        )

    allow_credentials: bool = getattr(cors_section, "allow_credentials", True) if cors_section else True
    allow_methods_raw = getattr(cors_section, "allow_methods", ["*"]) if cors_section else ["*"]
    allow_headers_raw = getattr(cors_section, "allow_headers", ["*"]) if cors_section else ["*"]

    return {
        "allow_origins": origins,
        "allow_origin_regex": origin_regex,
        "allow_credentials": allow_credentials,
        "allow_methods": list(allow_methods_raw) if isinstance(allow_methods_raw, list) else [str(allow_methods_raw)],
        "allow_headers": list(allow_headers_raw) if isinstance(allow_headers_raw, list) else [str(allow_headers_raw)],
    }
