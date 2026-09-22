"""
Application builder for AI-Breadboard FastAPI application.

This module provides the main application factory pattern that:
- Initializes FastAPI app with middleware and configuration
- Registers all routers with automatic discovery
- Mounts static files and UI pages
- Configures OpenAPI/Swagger documentation

Usage:
    from src.app import create_app, register_routers
    
    app = create_app()
    state = AppState()
    app.state.app_state = state
    register_routers(app, state)
    uvicorn.run(app, host="0.0.0.0", port=8000)

Architecture:
    src/app/
    ├── __init__.py          # Application factory
    ├── state.py             # AppState dataclass
    ├── middleware.py        # HTTP middleware
    ├── cors.py              # CORS configuration
    ├── metrics.py           # Metrics collector
    ├── ws_hub.py            # WebSocket hub
    ├── routers/             # API routers (auto-discovered)
    │   ├── __init__.py
    │   └── *.py            # Individual routers
    ├── pages/               # UI page handlers
    │   ├── __init__.py
    │   └── *.py            # Individual page handlers
    ├── config_api.py        # AI provider configuration endpoints
    ├── versioning.py        # Version check and update logic
    └── tests/               # Application tests
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles

from src.config import server_cfg
from src.logger import logger

if TYPE_CHECKING:
    from src.app.state import AppState

__root__ = Path(__file__).resolve().parents[2]
webinterface_dir = Path(__file__).resolve().parents[1] / 'api' / 'webgui'

# Re-export for convenience
from src.app.state import AppState
from src.app.cors import build_cors_config
from src.app.middleware import auto_login_local_user, metrics_middleware
from src.app.metrics import create_metrics, MetricsCollector
from src.app.ws_hub import WSHub

__all__ = [
    "create_app",
    "register_routers",
    "register_pages",
    "register_config_api",
    "AppState",
    "build_cors_config",
    "auto_login_local_user",
    "metrics_middleware",
    "create_metrics",
    "MetricsCollector",
    "WSHub",
]

# Legacy compatibility - export static mounting functions for pages module
mount_static_files = lambda app: _mount_static_files(app)
setup_favicon = lambda app: None  # Now handled in _mount_static_files


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance.
    
    Returns:
        FastAPI: Configured application instance ready for router registration.
    """
    # CORS configuration
    cors_config = build_cors_config(server_cfg)
    
    # Initialize FastAPI
    app = FastAPI(
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        title="AI-Breadboard API",
        description="AI-powered breadboard development platform with multiple AI providers",
        version="1.0.0",
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        **cors_config
    )
    
    # Add auto-login middleware for localhost
    app.middleware("http")(auto_login_local_user)
    
    # Add metrics middleware
    app.middleware("http")(metrics_middleware)
    
    return app


def register_routers(app: FastAPI, state: "AppState") -> None:
    """Attach all routers to *app*, injecting model instances where needed.
    
    Args:
        app: FastAPI application instance to register routers with.
        state: AppState instance with initialized models and services.
    """
    from src.api import (
        init_auth_router,
        init_chat_router,
        init_sync_router,
        init_control_router,
        init_tts_router,
        init_logs_router,
        init_keys_router,
        init_google_accounts_router,
        init_admin_router,
        init_skills_router,
        init_plugins_router,
        init_apps_router,
        init_admin_mcp_router,
        init_user_mcp_router,
        init_agents_router,
        init_rag_router,
        init_audio_router,
        init_user_storage_router,
        init_news_router,
        init_messenger_router,
        init_system_router,
        init_ifttt_router,
        init_windows_admin_router,
        init_telegram_rag_router,
        init_telemetry_router,
        init_system_logs_router,
        init_registry_viewer_router,
        init_diagnostics_router,
        init_scenarios_router,
        init_autolog_router,
        init_sysautolog_router,
        init_user_directories_router,
        get_pixel_rag_router,
        router_openai,
    )
    from src.api.router_version import init_router as init_version_router
    from apps.enterprise_knowledge.router import init_router as init_enterprise_knowledge_router

    # Routers that receive model instances
    app.include_router(init_chat_router(state.chat_model, state.narrator_model))
    app.include_router(init_news_router(state.chat_model))
    app.include_router(init_system_router(state.chat_model))

    # Stateless routers
    for factory in (
        init_auth_router,
        init_sync_router,
        init_control_router,
        init_tts_router,
        init_logs_router,
        init_keys_router,
        init_google_accounts_router,
        init_admin_router,
        init_skills_router,
        init_plugins_router,
        init_apps_router,
        init_admin_mcp_router,
        init_user_mcp_router,
        init_agents_router,
        init_rag_router,
        init_audio_router,
        init_user_storage_router,
        init_messenger_router,
        init_ifttt_router,
        init_windows_admin_router,
        init_telegram_rag_router,
        init_version_router,
        init_telemetry_router,
        init_system_logs_router,
        init_registry_viewer_router,
        init_diagnostics_router,
        init_scenarios_router,
        init_autolog_router,
        init_sysautolog_router,
        init_user_directories_router,
        get_pixel_rag_router
    ):
        app.include_router(factory())

    app.include_router(router_openai)
    app.include_router(init_enterprise_knowledge_router())

    # apps/ — registered here for shared software server mode
    try:
        from apps.trading_terminal import init_router as init_trading_router
        app.include_router(init_trading_router())
    except (ImportError, Exception) as e:
        logger.debug(f"Trading terminal router not registered: {e}")

    try:
        from apps.cloudflared_monitor.router import init_router as init_cloudflared_router
        app.include_router(init_cloudflared_router())
    except (ImportError, Exception) as e:
        logger.debug(f"Cloudflared monitor router not registered: {e}")

    try:
        from apps.windows.router import init_router as init_windows_router
        app.include_router(init_windows_router(app, state))
    except (ImportError, Exception) as e:
        logger.debug(f"Windows AI center router not registered: {e}")

    try:
        from apps.windows_sysadmin.router import init_router as init_windows_sysadmin_router
        app.include_router(init_windows_sysadmin_router())
    except (ImportError, Exception) as e:
        logger.debug(f"Windows sysadmin router not registered: {e}")

    try:
        from apps.network_terminal.router import init_router as init_network_terminal_router
        app.include_router(init_network_terminal_router())
    except (ImportError, Exception) as e:
        logger.debug(f"Network terminal router not registered: {e}")

    try:
        from apps.system_inspector.router import init_router as init_system_inspector_router
        app.include_router(init_system_inspector_router())
    except (ImportError, Exception) as e:
        logger.debug(f"System inspector router not registered: {e}")

    try:
        from apps.system_control_center.router import init_router as init_system_control_center_router
        app.include_router(init_system_control_center_router())
    except (ImportError, Exception) as e:
        logger.debug(f"System control center router not registered: {e}")

    try:
        from apps.gcloud_monitor.router import router as gcloud_monitor_router
        app.include_router(gcloud_monitor_router)
    except (ImportError, Exception) as e:
        logger.debug(f"Google Cloud monitor router not registered: {e}")

    try:
        from apps.website_monitor.router import init_router as init_website_monitor_router
        app.include_router(init_website_monitor_router())
    except (ImportError, Exception) as e:
        logger.debug(f"Website monitor router not registered: {e}")

    try:
        from apps.user_assistant.router import init_router as init_user_assistant_router
        app.include_router(init_user_assistant_router())
    except (ImportError, Exception) as e:
        logger.debug(f"User assistant router not registered: {e}")

    try:
        from apps.research_and_statistic.router import init_router as init_research_app_router
        app.include_router(init_research_app_router(state))
    except (ImportError, Exception) as e:
        logger.debug(f"Research and statistic app router not registered: {e}")

    try:
        from apps.wikipedia_research.router import init_router as init_wiki_app_router
        app.include_router(init_wiki_app_router(state))
    except (ImportError, Exception) as e:
        logger.debug(f"Wikipedia research app router not registered: {e}")

    try:
        from apps.ai_breadboard_admin.router import init_router as init_ai_breadboard_admin_router
        app.include_router(init_ai_breadboard_admin_router())
    except (ImportError, Exception) as e:
        logger.debug(f"AI Breadboard admin router not registered: {e}")

    try:
        from apps.windows_startup_auditor.router import init_router as init_startup_auditor_router
        app.include_router(init_startup_auditor_router())
    except (ImportError, Exception) as e:
        logger.debug(f"Windows startup auditor router not registered: {e}")

    try:
        from apps.windows_backup_manager.router import init_router as init_backup_manager_router
        app.include_router(init_backup_manager_router())
    except (ImportError, Exception) as e:
        logger.debug(f"Windows backup manager router not registered: {e}")

    try:
        from apps.windows_defender.router import init_router as init_windows_defender_router
        app.include_router(init_windows_defender_router())
    except (ImportError, Exception) as e:
        logger.debug(f"Windows defender router not registered: {e}")

    try:
        from apps.software_transparency_scanner.router import init_router as init_transparency_scanner_router
        app.include_router(init_transparency_scanner_router(state.chat_model if hasattr(state, "chat_model") else None))
    except (ImportError, Exception) as e:
        logger.debug(f"Software transparency scanner router not registered: {e}")

    try:
        from apps.smartmontools.router import init_router as init_smartmontools_router
        app.include_router(init_smartmontools_router())
    except (ImportError, Exception) as e:
        logger.debug(f"smartmontools router not registered: {e}")

    try:
        from apps.librehardwaremonitor.router import init_router as init_lhm_router
        app.include_router(init_lhm_router())
    except (ImportError, Exception) as e:
        logger.debug(f"LibreHardwareMonitor router not registered: {e}")

    try:
        from apps.ai_benchmark.router import init_router as init_ai_benchmark_router
        app.include_router(init_ai_benchmark_router())
    except (ImportError, Exception) as e:
        logger.debug(f"AI Benchmark router not registered: {e}")

    # Auto-discover additional routers in src/app/routers/
    _auto_discover_routers(app)
    
    # Mount static files after routers
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
    
    # Mount Simple Assistant
    simple_assistant_dir = __root__ / 'SANDBOX' / 'AI Assistant' / 'Simple Assistant'
    if simple_assistant_dir.exists() and '/simple-assistant' not in mounted_paths:
        app.mount('/simple-assistant', StaticFiles(directory=simple_assistant_dir, html=True), name='simple-assistant')
    
    # Setup favicon
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
                logger.debug(f"Auto-discovered router: {module_name}")
        except Exception as e:
            logger.warning(f"Failed to load router module {module_name}: {e}")


def register_pages(app: FastAPI) -> None:
    """Register all page handlers from src/app/pages/.
    
    Args:
        app: FastAPI application instance to register pages with.
    """
    import importlib
    import pkgutil
    
    # Register base pages module
    try:
        from src.app import pages
        if hasattr(pages, 'register_pages'):
            pages.register_pages(app)
            logger.debug("Registered pages from src.app.pages")
    except Exception as e:
        logger.warning(f"Failed to load src.app.pages: {e}")

    pages_dir = Path(__file__).parent / 'pages'
    
    if not pages_dir.exists():
        logger.warning(f"Pages directory not found: {pages_dir}")
        return
    
    for module_info in pkgutil.walk_packages([str(pages_dir)], prefix='src.app.pages.'):
        module_name = module_info.name
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, 'register_pages'):
                module.register_pages(app)
                logger.debug(f"Registered pages from {module_name}")
        except Exception as e:
            logger.warning(f"Failed to load pages module {module_name}: {e}")


def register_config_api(app: FastAPI) -> None:
    """Register AI provider configuration endpoints.
    
    Args:
        app: FastAPI application instance to register endpoints with.
    """
    try:
        from src.app.config_api import setup_config_endpoints
        setup_config_endpoints(app)
    except ImportError:
        logger.warning("config_api module not available")
    except Exception as e:
        logger.warning(f"Failed to register config API: {e}")
