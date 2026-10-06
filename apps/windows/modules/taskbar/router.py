# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Taskbar - Router
# =============================================================================
# Description:
#   FastAPI REST API маршрутизатор для управления панелью задач, окнами
#   и истории изменений в telemetry.db с поддержкой Rollback.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.taskbar.router import init_router
#
#     router = init_router()
#
# File: router.py
# Project: ai-breadboard
# Package: apps.windows.modules.taskbar
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 17:58:00
# =============================================================================

from __future__ import annotations
"""FastAPI REST API маршрутизатор для управления панелью задач и окнами Windows."""

import asyncio
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from logger import logger
from apps.windows.modules.taskbar.core.command_registry import (
    TaskbarCommandMetadata,
    get_command_by_id,
)
from apps.windows.modules.taskbar.core.manager import TaskbarController
from apps.windows.modules.taskbar.core.models import (
    AppLaunchRequest,
    AppPinRequest,
    CommandExecutionRequest,
    CommandExecutionResponse,
    PinnedAppItem,
    TaskbarOverlayRequest,
    TaskbarProgressRequest,
    TaskbarSettings,
    TaskbarSettingsUpdate,
    TaskbarSummaryReport,
    WindowBatchActionRequest,
    WindowItem,
    WindowMoveRequest,
)

router = APIRouter(prefix="/api/v1/taskbar", tags=["Taskbar & Windows Controller"])
_controller = TaskbarController()


@router.get("", response_model=TaskbarSummaryReport)
@router.get("/", response_model=TaskbarSummaryReport)
@router.get("/summary", response_model=TaskbarSummaryReport)
async def get_taskbar_summary() -> TaskbarSummaryReport:
    """Сводный статус панели задач, габариты, текущие параметры и список окон."""
    return await asyncio.to_thread(_controller.get_summary)


@router.get("/capabilities")
async def get_taskbar_capabilities() -> Dict[str, Any]:
    """Обнаружение доступных возможностей Taskbar / Win32 / COM на текущей сборке ОС."""
    summary = await asyncio.to_thread(_controller.get_summary)
    return {
        "os_version": summary.os_version,
        "is_win11": summary.is_win11,
        "features": {
            "taskbar_alignment": summary.is_win11,
            "widgets": True,
            "copilot": summary.is_win11,
            "itaskbarlist3_progress": True,
            "itaskbarlist3_overlay": True,
            "win32_window_management": True,
            "virtual_desktops": True,
            "telemetry_history_rollback": True,
        },
        "safety_tiers": ["OBSERVE", "DIAGNOSE", "CONTROL", "ADMIN", "DESTRUCTIVE"],
        "execution_classes": ["NATIVE", "COMPATIBILITY", "RESTRICTED", "INTERNAL"],
    }


@router.get("/commands", response_model=List[TaskbarCommandMetadata])
async def get_command_catalog(
    category: Optional[str] = Query(None, description="Фильтр по категории (window, taskbar, process, shell, policy)"),
    risk: Optional[str] = Query(None, description="Фильтр по риску (safe, caution, admin, high, unsupported)"),
    execution_class: Optional[str] = Query(None, description="Фильтр по классу (NATIVE, COMPATIBILITY, RESTRICTED, INTERNAL)"),
) -> List[TaskbarCommandMetadata]:
    """Машиночитаемый каталог поддерживаемых команд подсистемы Taskbar & Windows."""
    return await asyncio.to_thread(
        _controller.get_command_catalog,
        category=category,
        risk=risk,
        execution_class=execution_class,
    )


@router.get("/commands/{command_id}", response_model=TaskbarCommandMetadata)
async def get_command_metadata(command_id: str) -> TaskbarCommandMetadata:
    """Получение детальных метаданных конкретной команды по ее ID."""
    meta = get_command_by_id(command_id)
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Команда '{command_id}' не найдена в Command Registry",
        )
    return meta


@router.post("/execute", response_model=CommandExecutionResponse)
async def execute_taskbar_command(payload: CommandExecutionRequest) -> CommandExecutionResponse:
    """Универсальный эндпоинт выполнения команд через Windows Command Registry."""
    return await asyncio.to_thread(_controller.execute_command, payload)


# --- История и Rollback в telemetry.db ---

@router.get("/history")
async def get_action_history(
    limit: int = Query(50, ge=1, le=500, description="Количество записей"),
    command_id: Optional[str] = Query(None, description="Фильтр по команде"),
) -> List[Dict[str, Any]]:
    """Получение истории зафиксированных изменений из SQLite базы telemetry.db."""
    return await asyncio.to_thread(_controller.get_history, limit=limit, command_id=command_id)


@router.post("/history/{history_id}/rollback")
async def rollback_history_action(history_id: int) -> Dict[str, Any]:
    """Откат системы к состоянию до указанного изменения по ID в telemetry.db."""
    res = await asyncio.to_thread(_controller.rollback, history_id)
    if res.get("status") != "SUCCESS":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res.get("message", f"Не удалось выполнить откат для ID {history_id}"),
        )
    return res


@router.post("/history/rollback-last")
async def rollback_last_action() -> Dict[str, Any]:
    """Быстрый откат последнего совершенного изменения."""
    res = await asyncio.to_thread(_controller.rollback_last)
    if res.get("status") != "SUCCESS":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res.get("message", "Не удалось выполнить откат последнего действия"),
        )
    return res


# --- Настройки ---

@router.get("/settings", response_model=TaskbarSettings)
async def get_taskbar_settings() -> TaskbarSettings:
    """Получение текущих настроек панели задач Windows."""
    return await asyncio.to_thread(_controller.get_settings)


@router.put("/settings")
@router.post("/settings")
@router.patch("/settings")
async def update_taskbar_settings(payload: TaskbarSettingsUpdate) -> Dict[str, Any]:
    """Обновление настроек панели задач с записью истории в telemetry.db."""
    return await asyncio.to_thread(_controller.update_settings, payload)


# --- Окна ---

@router.get("/windows", response_model=List[WindowItem])
async def list_windows(
    only_visible: bool = Query(True, description="Только видимые окна"),
    only_taskbar: bool = Query(True, description="Только окна, отображаемые на панели задач"),
    title: Optional[str] = Query(None, description="Фильтр по части заголовка"),
    process: Optional[str] = Query(None, description="Фильтр по имени процесса"),
) -> List[WindowItem]:
    """Список открытых окон верхнего уровня рабочего стола."""
    return await asyncio.to_thread(
        _controller.list_windows,
        only_visible=only_visible,
        only_taskbar=only_taskbar,
        title_filter=title,
        process_filter=process,
    )


@router.get("/windows/{hwnd}", response_model=WindowItem)
async def get_window_details(hwnd: int) -> WindowItem:
    """Получение детальной информации об окне по HWND."""
    win = await asyncio.to_thread(_controller.get_window, hwnd)
    if not win:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Окно с HWND {hwnd} не найдено",
        )
    return win


@router.post("/windows/{hwnd}/activate")
async def activate_window(hwnd: int) -> Dict[str, Any]:
    """Активация и вывод окна на передний план."""
    res = await asyncio.to_thread(_controller.activate_window, hwnd)
    if res["status"] != "SUCCESS":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Не удалось активировать окно HWND {hwnd}",
        )
    return res


@router.post("/windows/{hwnd}/minimize")
async def minimize_window(hwnd: int) -> Dict[str, Any]:
    """Сворачивание окна."""
    res = await asyncio.to_thread(_controller.minimize_window, hwnd)
    if res["status"] != "SUCCESS":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Не удалось свернуть окно HWND {hwnd}",
        )
    return res


@router.post("/windows/{hwnd}/maximize")
async def maximize_window(hwnd: int) -> Dict[str, Any]:
    """Разворачивание окна на весь экран."""
    res = await asyncio.to_thread(_controller.maximize_window, hwnd)
    if res["status"] != "SUCCESS":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Не удалось развернуть окно HWND {hwnd}",
        )
    return res


@router.post("/windows/{hwnd}/restore")
async def restore_window(hwnd: int) -> Dict[str, Any]:
    """Восстановление нормального размера окна."""
    res = await asyncio.to_thread(_controller.restore_window, hwnd)
    if res["status"] != "SUCCESS":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Не удалось восстановить окно HWND {hwnd}",
        )
    return res


@router.post("/windows/{hwnd}/move")
async def move_window(hwnd: int, payload: WindowMoveRequest) -> Dict[str, Any]:
    """Перемещение и изменение размера окна."""
    res = await asyncio.to_thread(_controller.move_window, hwnd, payload)
    if res["status"] != "SUCCESS":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Не удалось переместить окно HWND {hwnd}",
        )
    return res


@router.delete("/windows/{hwnd}")
@router.post("/windows/{hwnd}/close")
async def close_window(hwnd: int) -> Dict[str, Any]:
    """Закрытие окна (WM_CLOSE)."""
    res = await asyncio.to_thread(_controller.close_window, hwnd)
    if res["status"] != "SUCCESS":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Не удалось закрыть окно HWND {hwnd}",
        )
    return res


@router.post("/windows/batch")
async def execute_batch_window_action(payload: WindowBatchActionRequest) -> Dict[str, Any]:
    """Пакетные операции над окнами (minimize_all, restore_all, minimize_all_except, close_by_process)."""
    return await asyncio.to_thread(_controller.execute_batch_window_action, payload)


# --- Приложения ---

@router.get("/apps", response_model=List[PinnedAppItem])
async def list_pinned_apps() -> List[PinnedAppItem]:
    """Список закрепленных на панели задач приложений."""
    return await asyncio.to_thread(_controller.list_pinned_apps)


@router.post("/apps/launch")
async def launch_application(payload: AppLaunchRequest) -> Dict[str, Any]:
    """Запуск приложения (с поддержкой UAC и аргументов)."""
    res = await asyncio.to_thread(_controller.launch_app, payload)
    if res["status"] != "SUCCESS":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=res.get("message", "Ошибка при запуске приложения"),
        )
    return res


@router.post("/apps/pin")
async def pin_application(payload: AppPinRequest) -> Dict[str, Any]:
    """Закрепление приложения на панели задач."""
    return await asyncio.to_thread(_controller.pin_app, payload)


@router.delete("/apps/pin")
async def unpin_application(target: str = Query(..., description="Путь или имя приложения")) -> Dict[str, Any]:
    """Открепление приложения от панели задач."""
    return await asyncio.to_thread(_controller.unpin_app, target)


@router.post("/ux/progress")
async def set_taskbar_progress(payload: TaskbarProgressRequest) -> Dict[str, Any]:
    """Установка индикатора выполнения ITaskbarList3 на кнопке панели задач."""
    return await asyncio.to_thread(_controller.set_progress, payload)


@router.post("/ux/overlay")
async def set_taskbar_overlay(payload: TaskbarOverlayRequest) -> Dict[str, Any]:
    """Установка оверлейной иконки-бейджа на кнопке панели задач."""
    return await asyncio.to_thread(_controller.set_overlay, payload)


def set_controller(controller: TaskbarController) -> None:
    """Устанавливает экземпляр TaskbarController для маршрутизатора."""
    global _controller
    _controller = controller


def init_router(controller: Optional[TaskbarController] = None) -> APIRouter:
    """Возвращает инициализированный FastAPI роутер."""
    if controller is not None:
        set_controller(controller)
    return router


__all__ = ["router", "init_router", "set_controller"]


