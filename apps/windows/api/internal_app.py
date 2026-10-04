# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Api - Internal App
# =============================================================================
# Description:
#   Главный FastAPI сервер управления подсистемой Windows AI-Breadboard.
#
# Usage Examples:
#   Python API:
#     from apps.windows.api.internal_app import load_config
#
#     res = load_config()
#
# File: internal_app.py
# Project: ai-breadboard
# Package: apps.windows.api
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 04:38:00
# =============================================================================

from __future__ import annotations
"""Главный FastAPI сервер управления подсистемой Windows AI-Breadboard."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from logger import logger

# Каталог модуля API и статических файлов TC-вкладок
_MODULE_DIR = Path(__file__).resolve().parent
_CONFIG_PATH = _MODULE_DIR / 'config.json'
_WEBGUI_DIR = _MODULE_DIR / 'webgui'
# Корневой index.html TC-приложения (Test Computer / Apps Hub)
_TC_INDEX = _WEBGUI_DIR / 'apps' / 'index.html'


def load_config() -> Dict[str, Any]:
    """Загружает конфигурацию сервиса и роутеров из config.json.

    Returns:
        Dict[str, Any]: Словарь с конфигурацией сервиса и списком роутеров.
    """
    if _CONFIG_PATH.is_file():
        try:
            with open(_CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as exc:
            logger.warning(f'[InternalApp] Ошибка чтения конфигурации {_CONFIG_PATH}: {exc}')
    return {}


def create_internal_app() -> FastAPI:
    """Создаёт и конфигурирует выделенный FastAPI-сервис Windows Internal API.

    Регистрирует все роутеры Windows-стека на основе config.json,
    монтирует статику TC-вкладок и настраивает CORS.

    Returns:
        FastAPI: Настроенное приложение, готовое к запуску через uvicorn.
    """
    config = load_config()
    server_cfg = config.get('server', {})

    app = FastAPI(
        title=server_cfg.get('title', 'AI-Breadboard Windows Internal API'),
        description=server_cfg.get('description', 'Сервис TC/Windows: телеметрия, дашборды, диагностика.'),
        version='1.0.0',
        docs_url='/docs',
        redoc_url=None,
        openapi_url='/openapi.json',
    )

    # ------------------------------------------------------------------
    # CORS: только localhost
    # ------------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            'http://127.0.0.1',
            'https://127.0.0.1',
            'http://localhost',
            'https://localhost',
        ],
        allow_origin_regex=r'https?://(127\.0\.0\.1|localhost)(:\d+)?',
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    # ------------------------------------------------------------------
    # Регистрация роутеров из конфигурации config.json
    # ------------------------------------------------------------------
    routers_list: List[Dict[str, Any]] = config.get('routers', [])
    for entry in routers_list:
        if not entry.get('enabled', True):
            continue

        module_path = entry.get('module')
        if not module_path:
            continue

        factory_name = entry.get('factory', 'init_router')
        kwargs = dict(entry.get('kwargs') or {})

        if entry.get('inject_app'):
            kwargs['app'] = app
            kwargs.setdefault('state', None)

        if entry.get('inject_models'):
            try:
                from src.ai.model_manager import get_available_models
                models = get_available_models('gemini')
                if models:
                    kwargs.setdefault('chat_model', models[0])
                    kwargs.setdefault('narrator_model', models[0])
            except Exception:
                logger.debug(f'[InternalApp] Не удалось разрешить модели для {module_path}')

        _register(app, module_path, factory_name, kwargs=kwargs)

    # ------------------------------------------------------------------
    # Точка входа TC UI: GET /tc, /apps, / → apps/index.html
    # ------------------------------------------------------------------
    @app.get('/', response_class=HTMLResponse, include_in_schema=False)
    @app.get('/tc', response_class=HTMLResponse, include_in_schema=False)
    @app.get('/tc/', response_class=HTMLResponse, include_in_schema=False)
    @app.get('/apps', response_class=HTMLResponse, include_in_schema=False)
    @app.get('/apps/', response_class=HTMLResponse, include_in_schema=False)
    @app.get('/su', response_class=HTMLResponse, include_in_schema=False)
    @app.get('/su/', response_class=HTMLResponse, include_in_schema=False)
    async def tc_index() -> Response:
        """Возвращает главную HTML-страницу Test Computer интерфейса с отключенным кэшированием."""
        if _TC_INDEX.exists():
            return FileResponse(
                _TC_INDEX,
                headers={
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0',
                },
            )
        return HTMLResponse('<h1>TC WebGUI (apps/index.html) not found</h1>', status_code=404)

    # ------------------------------------------------------------------
    # Health-check
    # ------------------------------------------------------------------
    @app.get('/health', tags=['system'])
    @app.get('/internal/health', tags=['system'], include_in_schema=False)
    async def health() -> dict:
        """Проверка работоспособности сервиса."""
        return {
            'status': 'ok',
            'service': 'windows-internal-api',
            'webgui_dir': str(_WEBGUI_DIR),
            'webgui_exists': _WEBGUI_DIR.exists(),
            'tc_index_exists': _TC_INDEX.exists(),
            'configured_routers_count': len(routers_list),
        }

    # ------------------------------------------------------------------
    # Статические файлы TC-вкладок (/webinterface/*, /html/*, /apps/*)
    # ------------------------------------------------------------------
    if _WEBGUI_DIR.exists():
        app.mount(
            '/webinterface',
            StaticFiles(directory=_WEBGUI_DIR),
            name='tc-webinterface',
        )
        app.mount(
            '/html',
            StaticFiles(directory=_WEBGUI_DIR),
            name='tc-html',
        )
        if (_WEBGUI_DIR / 'apps').exists():
            app.mount(
                '/apps/static',
                StaticFiles(directory=_WEBGUI_DIR / 'apps'),
                name='tc-apps-static',
            )
        logger.debug(f'[InternalApp] Статика TC смонтирована: {_WEBGUI_DIR}')
    else:
        logger.warning(f'[InternalApp] Каталог webgui не найден: {_WEBGUI_DIR}')

    return app


def _register(
    app: FastAPI,
    module_path: str,
    factory_name: str,
    kwargs: Optional[dict] = None,
) -> None:
    """Безопасно импортирует роутер и регистрирует его в приложении.

    При ошибке импорта или регистрации пишет предупреждение в лог
    и продолжает работу (fail-safe).

    Args:
        app: Экземпляр FastAPI.
        module_path: Строка пути Python-модуля (через точки).
        factory_name: Имя функции-фабрики роутера в модуле.
        kwargs: Именованные аргументы для фабрики (опционально).
    """
    try:
        import importlib
        module = importlib.import_module(module_path)
        factory = getattr(module, factory_name)
        router = factory(**(kwargs or {}))
        if router is not None:
            app.include_router(router)
            logger.debug(f'[InternalApp] Роутер зарегистрирован: {module_path}')
    except (ImportError, AttributeError, Exception) as exc:
        logger.warning(f'[InternalApp] Роутер пропущен ({module_path}): {exc}')


__all__ = ['create_internal_app', 'load_config']
