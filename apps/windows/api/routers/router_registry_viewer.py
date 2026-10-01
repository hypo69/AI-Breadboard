# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Api Routers - Router Registry Viewer
# =============================================================================
# Description:
#   FastAPI роутер-адаптер для приложения Windows Registry Viewer (apps.windows.registry),
#
# Usage Examples:
#   Python API:
#     from apps.windows.api.routers.router_registry_viewer import init_router
#
#     res = init_router()
#
# File: router_registry_viewer.py
# Project: ai-breadboard
# Package: apps.windows.api.routers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""FastAPI роутер-адаптер для приложения Windows Registry Viewer (apps.windows.registry),"""

from fastapi import APIRouter
from apps.windows.registry import (
    BookmarkItem,
    RegistryKeyDetailsDTO,
    RegistryValueDTO,
    RegistryViewer,
    SearchMatchItem,
    SearchResponseDTO,
    init_router as init_app_router,
)

# Синглтон-роутер приложения
router: APIRouter = init_app_router()


def init_router() -> APIRouter:
    """Фабрика инициализации роутера Registry Viewer для регистрации в основном приложении."""
    return router


__all__ = [
    "init_router",
    "router",
    "RegistryValueDTO",
    "RegistryKeyDetailsDTO",
    "BookmarkItem",
    "SearchMatchItem",
    "SearchResponseDTO",
    "RegistryViewer",
]
