# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: FastAPI router initialization and exports
# =============================================================================
# Description:
#   Exports factory initializers and router instances for core FastAPI
#   HTTP endpoints, WebSockets, authentication, chat, and administration services.
#
#   ARCHITECTURE NOTE: Routers from apps/ (trading_terminal, etc.) are intentionally
#   NOT imported here. They are registered directly in src/app/routes.py (or main.py)
#   to maintain clean layer separation — src/ must never depend on apps/.
#
# File: __init__.py
# Project: ai-breadboard
# Package: src.api
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from .router_auth import (
    init_router as init_auth_router,
    is_local_request,
    get_current_user_data,
    get_current_user_optional,
    require_admin_user,
)
from .router_chat import init_router as init_chat_router
from .router_sync import init_router as init_sync_router
from .router_control import init_router as init_control_router
from .router_tts import init_router as init_tts_router
from .router_logs import init_router as init_logs_router
from .router_keys import init_router as init_keys_router
from .router_admin import (
    init_router as init_admin_router,
    init_skills_router,
    init_plugins_router,
    init_apps_router,
)
from .router_mcp import init_admin_mcp_router, init_user_mcp_router
from .router_agents import init_agents_router
from .router_rag import init_router as init_rag_router
from .router_audio import init_router as init_audio_router
from .router_google_accounts import init_router as init_google_accounts_router
from .router_openai import router as router_openai
from .router_user_storage import init_router as init_user_storage_router
from .router_news import init_router as init_news_router
from .messenger import init_router as init_messenger_router
from .router_network import init_router as init_network_router
from .router_system import init_router as init_system_router
from .router_ifttt import init_router as init_ifttt_router
from .router_windows_admin import init_router as init_windows_admin_router
from .router_telegram_rag import init_router as init_telegram_rag_router
from .router_version import init_router as init_version_router
from .router_telemetry import init_router as init_telemetry_router
from .router_system_logs import init_router as init_system_logs_router
from .router_registry_viewer import init_router as init_registry_viewer_router
from .router_diagnostics import init_router as init_diagnostics_router
from .router_scenarios import init_router as init_scenarios_router
from .router_autolog import init_router as init_autolog_router
from .pixel_rag_router import get_pixel_rag_router

__all__ = [
    "get_pixel_rag_router",
    "init_diagnostics_router",
    "init_scenarios_router",
    "init_autolog_router",
    "init_auth_router",
    "is_local_request",
    "get_current_user_data",
    "get_current_user_optional",
    "require_admin_user",
    "init_chat_router",
    "init_sync_router",
    "init_control_router",
    "init_tts_router",
    "init_logs_router",
    "init_keys_router",
    "init_google_accounts_router",
    "init_admin_router",
    "init_skills_router",
    "init_plugins_router",
    "init_apps_router",
    "init_admin_mcp_router",
    "init_user_mcp_router",
    "init_agents_router",
    "init_rag_router",
    "init_audio_router",
    "init_user_storage_router",
    "init_news_router",
    "init_messenger_router",
    "init_network_router",
    "init_system_router",
    "init_ifttt_router",
    "init_windows_admin_router",
    "init_telegram_rag_router",
    "init_version_router",
    "init_telemetry_router",
    "init_system_logs_router",
    "init_registry_viewer_router",
    "router_openai",
]



