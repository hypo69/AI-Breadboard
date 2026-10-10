# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard App - Application Factory and Router Assembly
# =============================================================================
# Description:
#   Фабрика сборки и инициализации главного FastAPI приложения AI-Breadboard.
#
#   Зачем нужен этот модуль:
#     1. Централизованная сборка приложения (Application Factory): создание экземпляра FastAPI,
#        подключение базовых middleware (CORS, обработка ошибок, контекст запросов).
#     2. Динамическая регистрация роутеров и страниц: автоматическое подключение всех модулей API
#        (core, tc, apps, helpdesk, memory_io), статических ассетов и HTML-страниц интерфейса.
#     3. Управление общим состоянием (AppState): создание и внедрение разделяемых сервисов,
#        хранилищ сессий и конфигураций в контекст `app.state`.
#
# Usage Examples:
#   Python API:
#     from src.app import create_app, register_routers, register_pages, AppState
#
#     app = create_app()
#     state = AppState()
#     app.state.app_state = state
#     register_routers(app, state)
#     register_pages(app)
#
# File: __init__.py
# Project: ai-breadboard
# Package: src.app
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 04:11:30
# =============================================================================

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from src.config import server_cfg, is_app_enabled
from logger import logger
if TYPE_CHECKING:
    from src.app.state import AppState
__root__ = Path(__file__).resolve().parents[2]
webinterface_dir = Path(__file__).resolve().parents[1] / 'api' / 'webgui'
from src.app.state import AppState
from src.app.cors import build_cors_config
from src.app.middleware import auto_login_local_user, metrics_middleware
from src.app.metrics import create_metrics, MetricsCollector
from src.app.ws_hub import WSHub
__all__ = ['create_app', 'register_routers', 'register_pages', 'register_config_api', 'AppState', 'build_cors_config', 'auto_login_local_user', 'metrics_middleware', 'create_metrics', 'MetricsCollector', 'WSHub']
mount_static_files = lambda app: _mount_static_files(app)
setup_favicon = lambda app: None

def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance.
    
    Returns:
        FastAPI: Configured application instance ready for router registration.
    """
    cors_config = build_cors_config(server_cfg)
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, title='AI-Breadboard API', description='AI-powered breadboard development platform with multiple AI providers', version='1.0.0')
    app.add_middleware(CORSMiddleware, **cors_config)
    app.middleware('http')(auto_login_local_user)
    app.middleware('http')(metrics_middleware)

    @app.middleware('http')
    async def add_no_cache_headers(request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith('/html/') or request.url.path.startswith('/webinterface/'):
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response
    return app

def register_routers(app: FastAPI, state: 'AppState') -> None:
    """Attach all routers to *app*, injecting model instances where needed.
    
    Args:
        app: FastAPI application instance to register routers with.
        state: AppState instance with initialized models and services.
    """
    # Импортируем только нужные роутеры, остальные будут автоматически обнаружены
    from src.api import init_auth_router, init_chat_router, init_news_router, init_system_router
    from src.api.router_loader import discover_routers

    # Регистрация роутеров, требующих параметры state
    app.include_router(init_chat_router(state.chat_model, state.narrator_model))
    app.include_router(init_news_router(state.chat_model))
    app.include_router(init_system_router(state.chat_model))
    # Регистрация роутера без параметров
    app.include_router(init_auth_router())
    # Автоматическое обнаружение остальных роутеров
    for router in discover_routers():
        app.include_router(router)
    # ------------------------------------------------------------------i)
    # ------------------------------------------------------------------
    # Регистрация агентов из AGENT_REGISTRY
    # ------------------------------------------------------------------
    from src.ai.agents import AGENT_REGISTRY
    for agent_name, agent_cls in AGENT_REGISTRY.items():
        slug = agent_name.lower()
        try:
            if hasattr(app, "register_agent"):
                app.register_agent(slug, agent_cls)
                logger.debug(f"[register_agents] Агент '{slug}' зарегистрирован")
            else:
                logger.warning(f"FastAPI app не поддерживает register_agent; агент '{slug}' не зарегистрирован")
        except Exception as exc:
            logger.warning(f"Не удалось зарегистрировать агент '{slug}': {exc}")
    if is_app_enabled('enterprise_knowledge'):
        try:
            from apps.enterprise_knowledge.routers.router import init_router as init_enterprise_knowledge_router
            app.include_router(init_enterprise_knowledge_router())
        except (ImportError, Exception) as e:
            logger.debug(f'Enterprise knowledge router not registered: {e}')
    if is_app_enabled('chat'):
        try:
            from apps.chat.routers.router import init_router as init_chat_router
            app.include_router(init_chat_app_router(state.chat_model if hasattr(state, 'chat_model') else None, state.narrator_model if hasattr(state, 'narrator_model') else None))
        except (ImportError, Exception) as e:
            logger.debug(f'Chat app router not registered: {e}')
    if is_app_enabled('cloudflared_monitor'):
        try:
            from apps.cloudflared_monitor.routers.router import init_router as init_cloudflared_monitor_router
            app.include_router(init_cloudflared_router())
        except (ImportError, Exception) as e:
            logger.debug(f'Cloudflared monitor router not registered: {e}')
    if is_app_enabled('google_user_desktop'):
        try:
            from apps.google_user_desktop.routers.router import init_router as init_google_desktop_router
            app.include_router(init_google_desktop_router())
        except (ImportError, Exception) as e:
            logger.debug(f'Google User Desktop router not registered: {e}')
    if is_app_enabled('windows') or is_app_enabled('about_system') or is_app_enabled('windows_sysadmin'):
        try:
            from apps.windows.router import init_router as init_windows_router
            app.include_router(init_windows_router(app, state))
        except (ImportError, Exception) as e:
            logger.debug(f'Windows AI center router not registered: {e}')
    if is_app_enabled('windows_sysadmin'):
        try:
            from apps.windows.sysadmin.router import init_router as init_windows_sysadmin_router
            app.include_router(init_windows_sysadmin_router())
        except (ImportError, Exception) as e:
            logger.debug(f'Windows sysadmin router not registered: {e}')
    if is_app_enabled('network_terminal'):
        try:
            from apps.windows.network.router import init_router as init_network_terminal_router
            app.include_router(init_network_terminal_router())
        except (ImportError, Exception) as e:
            logger.debug(f'Network terminal router not registered: {e}')
    if is_app_enabled('system_inspector'):
        try:
            from apps.windows.system_inspector_router import init_router as init_system_inspector_router
            app.include_router(init_system_inspector_router())
        except (ImportError, Exception) as e:
            logger.debug(f'System inspector router not registered: {e}')
    if is_app_enabled('system_control_center'):
        try:
            from apps.windows.system_control_center.router import init_router as init_system_control_center_router
            app.include_router(init_system_control_center_router())
        except (ImportError, Exception) as e:
            logger.debug(f'System control center router not registered: {e}')
    if is_app_enabled('gcloud_monitor'):
        try:
            from apps.gcloud_monitor.routers.router import init_router as init_gcloud_monitor_router
            app.include_router(gcloud_monitor_router)
        except (ImportError, Exception) as e:
            logger.debug(f'Google Cloud monitor router not registered: {e}')
    if is_app_enabled('website_monitor'):
        try:
            from apps.website_monitor.routers.router import init_router as init_website_monitor_router
            app.include_router(init_website_monitor_router())
        except (ImportError, Exception) as e:
            logger.debug(f'Website monitor router not registered: {e}')
    if is_app_enabled('user_assistant'):
        try:
            from apps.user_assistant.routers.router import init_router as init_user_assistant_router
            app.include_router(init_user_assistant_router())
        except (ImportError, Exception) as e:
            logger.debug(f'User assistant router not registered: {e}')
    if is_app_enabled('research_and_statistic'):
        try:
            from apps.research_and_statistic.routers.router import init_router as init_research_and_statistic_router
            app.include_router(init_research_app_router(state))
        except (ImportError, Exception) as e:
            logger.debug(f'Research and statistic app router not registered: {e}')
    if is_app_enabled('wikipedia_research'):
        try:
            from apps.wikipedia_research.routers.router import init_router as init_wikipedia_research_router
            app.include_router(init_wiki_app_router(state))
        except (ImportError, Exception) as e:
            logger.debug(f'Wikipedia research app router not registered: {e}')
    if is_app_enabled('ai_breadboard_admin'):
        try:
            from apps.ai_breadboard_admin.routers.router import init_router as init_ai_breadboard_admin_router
            app.include_router(init_ai_breadboard_admin_router())
        except (ImportError, Exception) as e:
            logger.debug(f'AI Breadboard admin router not registered: {e}')
    if is_app_enabled('windows_startup_auditor'):
        try:
            from apps.windows.startup.router import init_router as init_startup_auditor_router
            app.include_router(init_startup_auditor_router())
        except (ImportError, Exception) as e:
            logger.debug(f'Windows startup auditor router not registered: {e}')
    if is_app_enabled('windows_backup_manager'):
        try:
            from apps.windows.sdk.modules.backup_manager.router import init_router as init_backup_manager_router
            app.include_router(init_backup_manager_router())
        except (ImportError, Exception) as e:
            logger.debug(f'Windows backup manager router not registered: {e}')
        try:
            from apps.windows.sdk.modules.backup_manager.versions_router import init_router as init_file_versions_router
            app.include_router(init_file_versions_router())
        except (ImportError, Exception) as e:
            logger.debug(f'Windows file versions router not registered: {e}')
        try:
            from apps.windows.sdk.modules.focus_policy.router import init_router as init_focus_policy_router
            app.include_router(init_focus_policy_router())
        except (ImportError, Exception) as e:
            logger.debug(f'Windows focus policy router not registered: {e}')
    if is_app_enabled('windows_defender'):
        try:
            from apps.windows.sdk.modules.defender.router import init_router as init_windows_defender_router
            app.include_router(init_windows_defender_router())
        except (ImportError, Exception) as e:
            logger.debug(f'Windows defender router not registered: {e}')
    if is_app_enabled('software_transparency_scanner'):
        try:
            from apps.windows.sdk.core.software_transparency import init_software_transparency_router as init_transparency_scanner_router
            app.include_router(init_transparency_scanner_router(state.chat_model if hasattr(state, 'chat_model') else None))
        except (ImportError, Exception) as e:
            logger.debug(f'Software transparency scanner router not registered: {e}')
    if is_app_enabled('windows_system_checkpoints'):
        try:
            from apps.windows.system_checkpoints.router import init_router as init_checkpoints_router
            app.include_router(init_checkpoints_router(app, state))
        except (ImportError, Exception) as e:
            logger.debug(f'Windows system checkpoints router not registered: {e}')
    _auto_discover_routers(app)
    _mount_static_files(app)

def _mount_static_files(app: FastAPI) -> None:
    """Mount static files directories to the application.
    
    Args:
        app: FastAPI application instance to mount files to.
    """
    mounted_paths = {getattr(route, 'path', '') for route in getattr(app, 'routes', [])}
    if '/webinterface' not in mounted_paths:
        webinterface_dir.mkdir(parents=True, exist_ok=True)
        app.mount('/webinterface', StaticFiles(directory=webinterface_dir), name='webinterface')
    if '/html' not in mounted_paths:
        app.mount('/html', StaticFiles(directory=webinterface_dir), name='html')
    simple_assistant_dir = __root__ / 'SANDBOX' / 'AI Assistant' / 'Simple Assistant'
    if simple_assistant_dir.exists() and '/simple-assistant' not in mounted_paths:
        app.mount('/simple-assistant', StaticFiles(directory=simple_assistant_dir, html=True), name='simple-assistant')
    if '/favicon.ico' not in mounted_paths:

        @app.get('/favicon.ico', include_in_schema=False)
        async def favicon() -> Response:
            fav = webinterface_dir / 'favicon.ico'
            if not fav.exists():
                fav = webinterface_dir / 'assets' / 'favicon.ico'
            if fav.exists():
                return FileResponse(fav)
            return Response(status_code=204)

def _auto_discover_routers(app: FastAPI) -> None:
    """Automatically discover and initialize all routers in src/app/routers/."""
    import importlib
    import pkgutil
    routers_dir = Path(__file__).parent / 'routers'
    if not routers_dir.exists():
        return
    for module_info in pkgutil.walk_packages([str(routers_dir)], prefix='src.app.routers.'):
        module_name = module_info.name
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, 'router'):
                app.include_router(module.router)
                logger.debug(f'Auto-discovered router: {module_name}')
        except Exception as e:
            logger.warning(f'Failed to load router module {module_name}: {e}')

def register_pages(app: FastAPI) -> None:
    """Register all page handlers from src/app/pages/.
    
    Args:
        app: FastAPI application instance to register pages with.
    """
    import importlib
    import pkgutil
    try:
        from src.app import pages
        if hasattr(pages, 'register_pages'):
            pages.register_pages(app)
            logger.debug('Registered pages from src.app.pages')
    except Exception as e:
        logger.warning(f'Failed to load src.app.pages: {e}')
    pages_dir = Path(__file__).parent / 'pages'
    if not pages_dir.exists():
        logger.warning(f'Pages directory not found: {pages_dir}')
        return
    for module_info in pkgutil.walk_packages([str(pages_dir)], prefix='src.app.pages.'):
        module_name = module_info.name
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, 'register_pages'):
                module.register_pages(app)
                logger.debug(f'Registered pages from {module_name}')
        except Exception as e:
            logger.warning(f'Failed to load pages module {module_name}: {e}')

def register_config_api(app: FastAPI) -> None:
    """Register AI provider configuration endpoints.
    
    Args:
        app: FastAPI application instance to register endpoints with.
    """
    try:
        from src.app.config_api import setup_config_endpoints
        setup_config_endpoints(app)
    except ImportError:
        logger.warning('config_api module not available')
    except Exception as e:
        logger.warning(f'Failed to register config API: {e}')