# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Api Routers - Router Forensics
# =============================================================================
# Description:
#   Роутер, предоставляющий данные о форензике для фронтенда вкладки Forensics.
#   Возвращает JSON со сведениями о текущем активном окне, времени бездействия
#   пользователя и приложениях, использующих камеру/микрофон, а также данными
#   UserAssist.
#
# Usage Examples:
#   Python API:
#     from apps.windows.api.routers.router_forensics import init_router
#
#   router = init_router()
#
# File: router_forensics.py
# Project: ai-breadboard
# Package: apps.windows.api.routers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 14:46:55
# =============================================================================

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from logger import logger

# Placeholder implementations – in production replace with real collectors.

class ForegroundWindow(BaseModel):
    """Информация о текущем активном окне."""
    title: str = Field(default="Рабочий стол Windows", description="Заголовок окна")
    process_name: str = Field(default="explorer.exe", description="Имя процесса")
    pid: int = Field(default=0, description="PID процесса")

class AppAccessInfo(BaseModel):
    """Приложение, имеющее доступ к камере или микрофону."""
    app_name: str = Field(..., description="Имя приложения")
    is_active_now: bool = Field(False, description="Активно в данный момент")

class UserAssistApp(BaseModel):
    """Запись UserAssist из реестра."""
    name: str = Field(..., description="Имя программы")
    run_count: int = Field(..., description="Количество запусков")
    focus_formatted: str = Field(..., description="Время фокуса (чч:мм:сс)")
    path: str = Field(..., description="Путь к исполняемому файлу")

class ForensicsResponse(BaseModel):
    """Ответ, ожидаемый фронтендом Forensics‑вкладки."""
    foreground_window: ForegroundWindow = Field(..., description="Текущее активное окно")
    user_idle_seconds: float = Field(..., description="Время бездействия пользователя в секундах")
    camera_active_apps: list[AppAccessInfo] = Field(default_factory=list, description="Приложения, использующие камеру")
    microphone_active_apps: list[AppAccessInfo] = Field(default_factory=list, description="Приложения, использующие микрофон")
    userassist_top_apps: list[UserAssistApp] = Field(default_factory=list, description="Топ‑приложения UserAssist")


def init_router() -> APIRouter:
    """Инициализирует роутер Forensics.

    Путь: `/api/v1/system/diagnostics/forensics`
    """
    router = APIRouter(prefix="/api/v1/system/diagnostics", tags=["Forensics"])

    @router.get("/forensics", response_model=ForensicsResponse)
    async def get_forensics() -> ForensicsResponse:
        """Возвращает текущие forensic‑данные.

        В текущей реализации возвращаются заглушки. При необходимости замените
        их на реальные данные, получаемые из SystemCollector, UserAssist и т.д.
        """
        logger.debug("[router_forensics] Запрос forensic‑данных")
        # Примерные заглушки
        fg = ForegroundWindow()
        idle = 12.3
        cam_apps = []
        mic_apps = []
        ua_apps = []
        return ForensicsResponse(
            foreground_window=fg,
            user_idle_seconds=idle,
            camera_active_apps=cam_apps,
            microphone_active_apps=mic_apps,
            userassist_top_apps=ua_apps,
        )

    return router
