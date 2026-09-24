# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Registry Viewer Router Bridge
# =============================================================================
# Description:
#   FastAPI роутер-адаптер для приложения Windows Registry Viewer (apps.windows.registry),
#   обеспечивающий интеграцию с общим бэкендом AI-Breadboard и веб-интерфейсом.
#
# File: router_registry_viewer.py
# Project: ai-breadboard
# Package: src.api
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI роутер-мост для приложения Registry Viewer."""

from __future__ import annotations

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
