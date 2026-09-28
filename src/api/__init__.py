"""Модуль инициализации API‑роутеров.

Содержит импорт глобальных роутеров, которые относятся ко всей системе.
Остальные роутеры находятся в соответствующих приложениях (`apps/*`) или плагинах
и автоматически обнаруживаются через `src.api.router_loader.discover_routers`.
"""

from .routers.core.router_auth import init_router as init_auth_router, is_local_request, get_current_user_data, get_current_user_optional, require_admin_user
from .routers.core.router_chat import init_router as init_chat_router
from .routers.core.router_control import init_router as init_control_router
from .routers.core.router_tts import init_router as init_tts_router
from .routers.core.router_logs import init_router as init_logs_router
from .routers.core.router_keys import init_router as init_keys_router
from .routers.core.router_admin import (
    init_router as init_admin_router,
    init_skills_router,
    init_plugins_router,
    init_apps_router,
    init_user_storage_router,
    init_sync_router,
)
from .routers.core.router_google_accounts import init_router as init_google_accounts_router
from .routers.core.router_mcp import init_admin_mcp_router, init_user_mcp_router
from .routers.core.router_agents import init_router as init_agents_router
from .routers.core.router_rag import init_router as init_rag_router
from .routers.core.router_audio import init_router as init_audio_router
from .routers.core.router_openai import router as router_openai
from .routers.core.router_news import init_router as init_news_router
from .routers.core.router_system import init_router as init_system_router
from .routers.core.router_ifttt import init_router as init_ifttt_router
from .routers.tc.router_windows_admin import init_router as init_windows_admin_router
from .routers.core.router_telegram_rag import init_router as init_telegram_rag_router
from .routers.core.router_version import init_router as init_version_router
from .routers.tc.telemetry.router_telemetry import init_router as init_telemetry_router
from .routers.core.router_system_logs import init_router as init_system_logs_router
from .routers.core.router_registry_viewer import init_router as init_registry_viewer_router
from .routers.core.router_diagnostics import init_router as init_diagnostics_router
from .routers.core.router_scenarios import init_router as init_scenarios_router
from .routers.core.router_autolog import init_router as init_autolog_router
from .routers.core.router_sysautologging import init_router as init_sysautolog_router
from .routers.core.router_user_directories import init_router as init_user_directories_router
from .routers.core.router_menu import init_router as init_menu_router
from .pixel_rag_router import get_pixel_rag_router
from .routers.core.router_ninite import init_router as init_ninite_router
from .routers.core.router_recovery import init_router as init_recovery_router
from .routers.tc.router_tc import init_router as init_tc_router

__all__ = [
    "get_pixel_rag_router",
    "init_menu_router",
    "init_diagnostics_router",
    "init_scenarios_router",
    "init_tc_router",
    "init_autolog_router",
    "init_sysautolog_router",
    "init_auth_router",
    "is_local_request",
    "get_current_user_data",
    "get_current_user_optional",
    "require_admin_user",
    "init_chat_router",
    "init_control_router",
    "init_tts_router",
    "init_logs_router",
    "init_keys_router",
    "init_admin_router",
    "init_skills_router",
    "init_plugins_router",
    "init_apps_router",
    "init_google_accounts_router",
    "init_user_storage_router",
    "init_sync_router",
    "init_admin_mcp_router",
    "init_user_mcp_router",
    "init_agents_router",
    "init_rag_router",
    "init_audio_router",
    "init_news_router",
    "init_system_router",
    "init_ifttt_router",
    "init_windows_admin_router",
    "init_telegram_rag_router",
    "init_version_router",
    "init_telemetry_router",
    "init_system_logs_router",
    "init_registry_viewer_router",
    "init_user_directories_router",
    "router_openai",
    "init_ninite_router",
    "init_recovery_router",
],