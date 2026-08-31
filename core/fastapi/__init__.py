# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Initialization маршрутизаторов FastAPI
# =============================================================================
# Description:
#   Экспорт фабрик инициализации HTTP-роутеров ядра.
#
# File: __init__.py
# Project: ai-breadboard
# Package: core.fastapi
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from .router_auth import init_router as init_auth_router
from .router_chat import init_router as init_chat_router
from .router_control import init_router as init_control_router
from .router_tts import init_router as init_tts_router
from .router_logs import init_router as init_logs_router
from .router_keys import init_router as init_keys_router
from .router_admin import init_router as init_admin_router
from .router_agents import init_agents_router
from .router_openai import router as router_openai

__all__ = [
    "init_auth_router",
    "init_chat_router",
    "init_control_router",
    "init_tts_router",
    "init_logs_router",
    "init_keys_router",
    "init_admin_router",
    "init_agents_router",
    "router_openai",
]
