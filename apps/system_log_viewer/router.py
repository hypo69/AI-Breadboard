# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: System Log Center FastAPI Router Bridge
# =============================================================================
# Description:
#   Роутер микросервиса Центра системных журналов Windows, предоставляющий
#   доступ к API обнаружения каналов логов, потокам событий, корреляции инцидентов
#   и адаптивному поиску по логам.
#
# Examples:
#   >>> from fastapi import FastAPI
#   >>> from apps.system_log_viewer.router import init_router
#   >>> app = FastAPI()
#   >>> app.include_router(init_router())
#
# File: router.py
# Project: AI-Breadboard
# Package: apps.system_log_viewer
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI роутер для микросервиса System Log Center."""

from __future__ import annotations

from fastapi import APIRouter
from src.api.router_system_logs import router as _system_logs_router


def init_router() -> APIRouter:
    """Возвращает инициализированный FastAPI роутер системных журналов."""
    return _system_logs_router
