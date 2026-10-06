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
# Updated: 2026-10-06 17:41:00
# =============================================================================

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field

from logger import logger
from apps.windows.telemetry.sqlite import TelemetryStorage


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
    status: str = Field(default="ok", description="Статус ответа")
    foreground_window: ForegroundWindow = Field(..., description="Текущее активное окно")
    user_idle_seconds: float = Field(..., description="Время бездействия пользователя в секундах")
    camera_active_apps: list[AppAccessInfo] = Field(default_factory=list, description="Приложения, использующие камеру")
    microphone_active_apps: list[AppAccessInfo] = Field(default_factory=list, description="Приложения, использующие микрофон")
    userassist_top_apps: list[UserAssistApp] = Field(default_factory=list, description="Топ‑приложения UserAssist")


def _convert_snapshot_to_response(d: Dict[str, Any]) -> ForensicsResponse:
    """Преобразует сырые данные снимка SQLite в модель ответа ForensicsResponse."""
    fg = ForegroundWindow(
        title=d.get("foreground_window_title") or "Рабочий стол Windows",
        process_name=d.get("foreground_process_name") or "explorer.exe",
        pid=int(d.get("foreground_pid") or 0),
    )
    cam = [AppAccessInfo(**a) if isinstance(a, dict) else a for a in (d.get("camera_active_apps") or [])]
    mic = [AppAccessInfo(**a) if isinstance(a, dict) else a for a in (d.get("microphone_active_apps") or [])]
    ua = [UserAssistApp(**a) if isinstance(a, dict) else a for a in (d.get("userassist_top_apps") or [])]
    return ForensicsResponse(
        status="ok",
        foreground_window=fg,
        user_idle_seconds=float(d.get("user_idle_seconds") or 0.0),
        camera_active_apps=cam,
        microphone_active_apps=mic,
        userassist_top_apps=ua,
    )


def _perform_forensics_scan(storage: TelemetryStorage) -> ForensicsResponse:
    """Выполняет живой сбор форензики и сохраняет снимок в SQLite."""
    try:
        from apps.windows.telemetry.deep_diagnostics import DeepDiagnosticsEngine
        engine = DeepDiagnosticsEngine()
        rep = engine.collect_forensics_activity()
        snap_id = f"snap_forensics_{int(datetime.now(timezone.utc).timestamp())}"
        storage.save_forensics_snapshot(snap_id, {
            "foreground_window_title": rep.foreground_window.get("title", ""),
            "foreground_process_name": rep.foreground_window.get("process_name", ""),
            "foreground_pid": rep.foreground_window.get("pid", 0),
            "user_idle_seconds": int(rep.user_idle_seconds),
            "camera_active_apps": rep.camera_active_apps,
            "microphone_active_apps": rep.microphone_active_apps,
            "userassist_top_apps": rep.userassist_top_apps,
        })
        d = storage.get_latest_forensics_snapshot()
        if d:
            return _convert_snapshot_to_response(d)
        return ForensicsResponse(
            status="ok",
            foreground_window=ForegroundWindow(**rep.foreground_window),
            user_idle_seconds=rep.user_idle_seconds,
            camera_active_apps=[AppAccessInfo(**a) for a in rep.camera_active_apps],
            microphone_active_apps=[AppAccessInfo(**a) for a in rep.microphone_active_apps],
            userassist_top_apps=[UserAssistApp(**a) for a in rep.userassist_top_apps],
        )
    except Exception as ex:
        logger.debug(f"Ошибка сбора форензики: {ex}")
        return ForensicsResponse(
            status="ok",
            foreground_window=ForegroundWindow(),
            user_idle_seconds=0.0,
            camera_active_apps=[],
            microphone_active_apps=[],
            userassist_top_apps=[],
        )


def init_router(storage: Optional[TelemetryStorage] = None) -> APIRouter:
    """Инициализирует роутер Forensics с чтением из SQLite (< 5 мс).

    Путь: `/api/v1/system/diagnostics/forensics`
    """
    router = APIRouter(prefix="/api/v1/system/diagnostics", tags=["Forensics"])
    store = storage or TelemetryStorage.get_instance(read_only=True)

    @router.get("/forensics", response_model=ForensicsResponse)
    async def get_forensics() -> ForensicsResponse:
        """Возвращает срез активности пользователя и форензики из SQLite (< 5 мс)."""
        d = store.get_latest_forensics_snapshot()
        if not d:
            return await asyncio.to_thread(_perform_forensics_scan, store)
        return _convert_snapshot_to_response(d)

    @router.post("/forensics/refresh", response_model=ForensicsResponse)
    @router.post("/forensics/rescan", response_model=ForensicsResponse)
    async def refresh_forensics() -> ForensicsResponse:
        """Принудительно пересканирует форензик-активность и обновляет срез в SQLite."""
        return await asyncio.to_thread(_perform_forensics_scan, store)

    return router
