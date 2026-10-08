# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows API - Server & Router Auto-Discovery
# =============================================================================
# Description:
#   Слой 7: FastAPI сервер и механизм динамического Auto-Discovery роутеров.
#
# Usage Examples:
#   Python API:
#     from apps.windows.api.server import create_app, discover_and_register_routers
#
# File: server.py
# Project: ai-breadboard
# Package: apps.windows.api
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 09:38:00
# =============================================================================

from __future__ import annotations
"""FastAPI серверная фабрика и автоматическое обнаружение REST API роутеров."""

import importlib
import json
import pkgutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, APIRouter, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from logger import logger

# Пути к статике и конфигурации
_MODULE_DIR = Path(__file__).resolve().parent
_CONFIG_PATH = _MODULE_DIR / "config.json"
_WEBGUI_DIR = _MODULE_DIR / "webgui"
_TC_INDEX = _WEBGUI_DIR / "apps" / "index.html"


def load_config() -> Dict[str, Any]:
    """Загружает конфигурацию сервиса из config.json."""
    if _CONFIG_PATH.is_file():
        try:
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            logger.warning(f"[API Server] Ошибка чтения конфигурации {_CONFIG_PATH}: {exc}")
    return {}


def discover_and_register_routers(app: FastAPI, package_path: str = "apps.windows") -> None:
    """Динамическое сканирование и подсоединение REST API роутеров."""
    try:
        package = importlib.import_module(package_path)
    except Exception as err:
        logger.error(f"[AutoDiscovery] Не удалось импортировать базовый пакет {package_path}: {err}")
        return

    if not hasattr(package, "__path__"):
        return

    for _, module_name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        if (
            module_name.endswith(".router")
            or "routers.router_" in module_name
            or module_name.endswith(".router_capabilities")
            or module_name.endswith(".system_inspector_router")
        ):
            try:
                mod = importlib.import_module(module_name)
                router = getattr(mod, "router", None)
                if router is None and hasattr(mod, "init_router"):
                    try:
                        router = mod.init_router()
                    except Exception:
                        pass
                if isinstance(router, APIRouter):
                    # Проверяем, не добавлен ли уже роутер
                    if router not in app.routes:
                        app.include_router(router)
                        logger.debug(f"[AutoDiscovery] Успешно зарегистрирован роутер: {module_name}")
            except Exception as router_err:
                logger.warning(f"[AutoDiscovery] Пропуск роутера {module_name} из-за ошибки: {router_err}")


def create_app() -> FastAPI:
    """Создаёт и конфигурирует масштабируемый FastAPI-сервис Windows API с Auto-Discovery."""
    config = load_config()
    server_cfg = config.get("server", {})

    app = FastAPI(
        title=server_cfg.get("title", "AI-Breadboard Windows Internal API"),
        description=server_cfg.get("description", "Сервис TC/Windows: телеметрия, дашборды, диагностика."),
        version="2.0.0",
        docs_url="/docs",
        redoc_url=None,
        openapi_url="/openapi.json",
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1",
            "https://127.0.0.1",
            "http://localhost",
            "https://localhost",
        ],
        allow_origin_regex=r"https?://(127\.0\.0\.1|localhost)(:\d+)?",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 1. Сначала регистрируем явно сконфигурированные роутеры из config.json (для кастомных параметров)
    routers_list: List[Dict[str, Any]] = config.get("routers", [])
    registered_modules = set()
    for entry in routers_list:
        if not entry.get("enabled", True):
            continue
        module_path = entry.get("module")
        if not module_path:
            continue
        factory_name = entry.get("factory", "init_router")
        kwargs = dict(entry.get("kwargs") or {})
        if entry.get("inject_app"):
            kwargs["app"] = app
            kwargs.setdefault("state", None)

        try:
            mod = importlib.import_module(module_path)
            factory = getattr(mod, factory_name)
            router = factory(**kwargs)
            if isinstance(router, APIRouter):
                app.include_router(router)
                registered_modules.add(module_path)
        except Exception as exc:
            logger.warning(f"[API Server] Ошибка регистрации роутера {module_path}: {exc}")

    # 2. Затем выполняем динамическое обнаружение (Auto-Discovery) для всех модулей apps.windows
    discover_and_register_routers(app, "apps.windows")

    # TC UI точка входа
    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    @app.get("/tc", response_class=HTMLResponse, include_in_schema=False)
    @app.get("/tc/", response_class=HTMLResponse, include_in_schema=False)
    @app.get("/apps", response_class=HTMLResponse, include_in_schema=False)
    @app.get("/apps/", response_class=HTMLResponse, include_in_schema=False)
    @app.get("/su", response_class=HTMLResponse, include_in_schema=False)
    @app.get("/su/", response_class=HTMLResponse, include_in_schema=False)
    async def tc_index() -> Response:
        """Возвращает главную HTML-страницу Test Computer интерфейса."""
        if _TC_INDEX.exists():
            return FileResponse(
                _TC_INDEX,
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                },
            )
        return HTMLResponse("<h1>TC WebGUI (apps/index.html) not found</h1>", status_code=404)

    # Health-check
    @app.get("/health", tags=["system"])
    @app.get("/internal/health", tags=["system"], include_in_schema=False)
    async def health() -> dict:
        return {
            "status": "ok",
            "service": "windows-internal-api",
            "webgui_dir": str(_WEBGUI_DIR),
            "webgui_exists": _WEBGUI_DIR.exists(),
            "tc_index_exists": _TC_INDEX.exists(),
            "configured_routers_count": len(routers_list),
        }

    # Статические файлы TC
    if _WEBGUI_DIR.exists():
        app.mount("/webinterface", StaticFiles(directory=_WEBGUI_DIR), name="tc-webinterface")
        app.mount("/html", StaticFiles(directory=_WEBGUI_DIR), name="tc-html")
        if (_WEBGUI_DIR / "apps").exists():
            app.mount("/apps/static", StaticFiles(directory=_WEBGUI_DIR / "apps"), name="tc-apps-static")

    return app


# Алиас для совместимости
create_internal_app = create_app

__all__ = [
    "create_app",
    "create_internal_app",
    "discover_and_register_routers",
    "load_config",
]
