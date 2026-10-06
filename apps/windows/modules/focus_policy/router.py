# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Focus_Policy - Router
# =============================================================================
# Description:
#   REST API Focus Policy Engine: /api/v1/focus/{status,suppressed-notifications,profiles,request-listener-access}.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.focus_policy.router import init_router
#
#     router = init_router()
#
# File: router.py
# Project: ai-breadboard
# Package: apps.windows.modules.focus_policy
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 22:05:00
# =============================================================================

from __future__ import annotations
"""FastAPI роутер Focus Policy Engine."""

import asyncio
from typing import Any, Dict, List, Optional

from fastapi import APIRouter

from apps.windows.modules.focus_policy.controller import WindowsFocusController
from apps.windows.modules.focus_policy.models import FocusProfile, FocusStatus, SuppressedNotification


def init_router(controller: Optional[WindowsFocusController] = None) -> APIRouter:
    """Создает роутер; контроллер можно внедрить явно (тесты)."""
    router = APIRouter(prefix='/api/v1/focus', tags=['Windows Focus Policy'])
    state: Dict[str, Optional[WindowsFocusController]] = {'c': controller}

    def ctrl() -> WindowsFocusController:
        if state['c'] is None:
            state['c'] = WindowsFocusController()
        return state['c']

    @router.get('/status', response_model=FocusStatus)
    async def get_status() -> FocusStatus:
        """Состояние контроллера и активной сессии."""
        return await asyncio.to_thread(ctrl().status)

    @router.get('/suppressed-notifications', response_model=List[SuppressedNotification])
    async def get_suppressed(session_id: Optional[str] = None) -> List[SuppressedNotification]:
        """Архив подавленных уведомлений сессии."""
        return await asyncio.to_thread(ctrl().list_suppressed, session_id)

    @router.post('/profiles', response_model=FocusProfile)
    async def save_profile(profile: FocusProfile) -> FocusProfile:
        """Создает/обновляет профиль и перерегистрирует задачи Task Scheduler."""
        return await asyncio.to_thread(ctrl().save_profile, profile)

    @router.post('/request-listener-access')
    async def request_access() -> Dict[str, Any]:
        """Запрашивает права UserNotificationListener."""
        return {'status': await asyncio.to_thread(ctrl().request_listener_access)}

    return router


__all__ = ['init_router']
