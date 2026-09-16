# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: System Log Center Microservice Application
# =============================================================================
# Description:
#   Инициализация пакета микросервиса Центра системных журналов Windows.
#
# File: __init__.py
# Project: AI-Breadboard
# Package: apps.system_log_viewer
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Пакет микросервиса Центра системных журналов Windows."""

from src.api.router_system_logs import router, _intelligence_pipeline, _eventlog_collector


def init_router():
    """Возвращает инициализированный FastAPI роутер системных журналов."""
    return router


__all__ = ["init_router", "router", "_intelligence_pipeline", "_eventlog_collector"]
