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
    """Собирает параметры CORS из *server_cfg* без предустановленных значений.

    Ожидает, что в конфиге явно указаны все необходимые поля:
    - server.cors.allow_origins (список строк)
    - server.client_url (строка)
    - server.user_domain (строка)
    - server.cors_origins (список строк)
    - server.cors.allow_origin_regex (строка или None)
    - server.cors.allow_credentials (bool)
    - server.cors.allow_methods (список строк)
    - server.cors.allow_headers (список строк)
    """
    cors_section: Optional[SimpleNamespace] = getattr(server_cfg, 'cors', None)
    origins: List[str] = []

    def _add(url: str) -> None:
        cleaned = str(url).rstrip('/')
        if cleaned and cleaned not in origins:
            origins.append(cleaned)
    if cors_section:
        for o in getattr(cors_section, 'allow_origins', []) or []:
            _add(o)
    client_url: str = getattr(server_cfg, 'client_url', '') or ''
    _add(client_url)
    user_domain: str = getattr(server_cfg, 'user_domain', '') or ''
    if user_domain:
        _add(f'http://{user_domain}')
        _add(f'https://{user_domain}')
    for o in getattr(server_cfg, 'cors_origins', []) or []:
        _add(o)
    origin_regex = getattr(cors_section, 'allow_origin_regex', None) if cors_section else None
    allow_credentials = getattr(cors_section, 'allow_credentials', True) if cors_section and getattr(cors_section, 'allow_credentials', None) is not None else True
    allow_methods_raw = getattr(cors_section, 'allow_methods', ['*']) if cors_section and getattr(cors_section, 'allow_methods', None) is not None else ['*']
    allow_headers_raw = getattr(cors_section, 'allow_headers', ['*']) if cors_section and getattr(cors_section, 'allow_headers', None) is not None else ['*']
    return {'allow_origins': origins, 'allow_origin_regex': origin_regex, 'allow_credentials': allow_credentials, 'allow_methods': allow_methods_raw, 'allow_headers': allow_headers_raw}