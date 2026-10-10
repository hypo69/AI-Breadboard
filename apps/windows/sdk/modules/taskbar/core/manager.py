# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Taskbar - Manager
# =============================================================================
# Description:
#   Главный контроллер панели задач Windows (TaskbarController) с автоматической
#   фиксацией изменений в SQLite telemetry.db и поддержкой отката (Rollback).
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.taskbar.core.manager import TaskbarController
#
#     controller = TaskbarController()
#     controller.update_settings(...)
#     controller.rollback_last()
#
# File: manager.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.taskbar.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 17:58:00
# =============================================================================

from __future__ import annotations
"""Единый контроллер панели задач (TaskbarController) с аудитом в telemetry.db."""

import platform
import sys
from typing import Any, Dict, List, Optional

from logger import logger
from apps.windows.sdk.modules.taskbar.core.app_manager import TaskbarAppManager
from apps.windows.sdk.modules.taskbar.core.command_registry import (
    TaskbarCommandMetadata,
    get_command_by_id,
    get_taskbar_command_catalog,
)
from apps.windows.sdk.modules.taskbar.core.history_manager import TaskbarHistoryManager
from apps.windows.sdk.modules.taskbar.core.models import (
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
from apps.windows.sdk.modules.taskbar.core.settings_manager import TaskbarSettingsManager
from apps.windows.sdk.modules.taskbar.core.taskbar_list_com import (
    TaskbarList3Wrapper,
    TaskbarProgressFlag,
)
from apps.windows.sdk.modules.taskbar.core.window_manager import WindowManager


class TaskbarController:
    """
    Главный управляющий контроллер панели задач Windows 10/11.
    
    Объединяет управление настройками, окнами, закрепленными приложениями,
    UX-индикаторами и автоматической записью истории/отката в telemetry.db.
    """

    def __init__(
        self,
        settings_mgr: Optional[TaskbarSettingsManager] = None,
        window_mgr: Optional[WindowManager] = None,
        app_mgr: Optional[TaskbarAppManager] = None,
        taskbar_com: Optional[TaskbarList3Wrapper] = None,
        history_mgr: Optional[TaskbarHistoryManager] = None,
    ) -> None:
        """Инициализирует TaskbarController с явным внедрением зависимостей (DI)."""
        self.settings_mgr = settings_mgr or TaskbarSettingsManager()
        self.window_mgr = window_mgr or WindowManager()
        self.app_mgr = app_mgr or TaskbarAppManager()
        self.taskbar_com = taskbar_com or TaskbarList3Wrapper()
        self.history_mgr = history_mgr or TaskbarHistoryManager()

    def get_summary(self) -> TaskbarSummaryReport:
        """Генерирует комплексный сводный отчет о панели задач и окнах."""
        os_ver = platform.platform()
        is_win11 = self.settings_mgr.is_win11
        tb_rect = self.window_mgr.get_taskbar_rect()
        settings = self.settings_mgr.get_settings()
        windows = self.window_mgr.list_windows(only_visible=False, only_taskbar=False)
        vis_windows = [w for w in windows if w.is_visible and w.title]
        fg_win = self.window_mgr.get_foreground_window()
        pinned = self.app_mgr.list_pinned_apps()

        return TaskbarSummaryReport(
            os_version=os_ver,
            is_win11=is_win11,
            taskbar_rect=tb_rect,
            settings=settings,
            windows_count=len(windows),
            visible_windows_count=len(vis_windows),
            foreground_window=fg_win,
            pinned_apps_count=len(pinned),
        )

    def get_command_catalog(
        self,
        category: Optional[str] = None,
        risk: Optional[str] = None,
        execution_class: Optional[str] = None,
    ) -> List[TaskbarCommandMetadata]:
        """Возвращает структурированный машиночитаемый каталог команд."""
        return get_taskbar_command_catalog(
            category=category,
            risk=risk,
            execution_class=execution_class,
        )

    # --- Настройки с фиксацией в telemetry.db ---

    def get_settings(self) -> TaskbarSettings:
        """Возвращает текущие настройки панели задач."""
        return self.settings_mgr.get_settings()

    def update_settings(
        self,
        patch: TaskbarSettingsUpdate,
        record_telemetry: bool = True,
    ) -> Dict[str, Any]:
        """Обновляет параметры панели задач с фиксацией в telemetry.db."""
        prev_settings = self.get_settings().model_dump() if record_telemetry else None
        res = self.settings_mgr.update_settings(patch)

        if record_telemetry and res.get("status") == "SUCCESS":
            new_settings = res.get("current_settings", {})
            rec_id = self.history_mgr.record_action(
                command_id="TASKBAR.SET_SETTINGS",
                category="taskbar",
                action_type="update_settings",
                previous_state=prev_settings,
                new_state=new_settings,
                details=res.get("applied_changes"),
                status="SUCCESS",
            )
            res["history_id"] = rec_id

        return res

    # --- Окна с фиксацией в telemetry.db ---

    def list_windows(
        self,
        only_visible: bool = True,
        only_taskbar: bool = True,
        title_filter: Optional[str] = None,
        process_filter: Optional[str] = None,
    ) -> List[WindowItem]:
        """Возвращает список окон с опциональной фильтрацией."""
        return self.window_mgr.list_windows(
            only_visible=only_visible,
            only_taskbar=only_taskbar,
            title_filter=title_filter,
            process_filter=process_filter,
        )

    def get_window(self, hwnd: int) -> Optional[WindowItem]:
        """Возвращает информацию об окне по HWND."""
        return self.window_mgr.get_window_by_hwnd(hwnd)

    def activate_window(self, hwnd: int, record_telemetry: bool = True) -> Dict[str, Any]:
        """Активирует окно и переводит его на передний план."""
        ok = self.window_mgr.activate_window(hwnd)
        status_str = "SUCCESS" if ok else "ERROR"
        if record_telemetry and ok:
            self.history_mgr.record_action(
                command_id="WINDOW.ACTIVATE",
                category="window",
                action_type="activate",
                target_hwnd=hwnd,
                status=status_str,
            )
        return {"status": status_str, "hwnd": hwnd, "action": "activate"}

    def minimize_window(self, hwnd: int, record_telemetry: bool = True) -> Dict[str, Any]:
        """Сворачивает окно."""
        win = self.get_window(hwnd) if record_telemetry else None
        prev_state = {"is_minimized": win.is_minimized, "is_maximized": win.is_maximized} if win else None

        ok = self.window_mgr.minimize_window(hwnd)
        status_str = "SUCCESS" if ok else "ERROR"
        if record_telemetry and ok:
            self.history_mgr.record_action(
                command_id="WINDOW.MINIMIZE",
                category="window",
                action_type="minimize",
                target_hwnd=hwnd,
                previous_state=prev_state,
                new_state={"is_minimized": True, "is_maximized": False},
                status=status_str,
            )
        return {"status": status_str, "hwnd": hwnd, "action": "minimize"}

    def maximize_window(self, hwnd: int, record_telemetry: bool = True) -> Dict[str, Any]:
        """Разворачивает окно."""
        win = self.get_window(hwnd) if record_telemetry else None
        prev_state = {"is_minimized": win.is_minimized, "is_maximized": win.is_maximized} if win else None

        ok = self.window_mgr.maximize_window(hwnd)
        status_str = "SUCCESS" if ok else "ERROR"
        if record_telemetry and ok:
            self.history_mgr.record_action(
                command_id="WINDOW.MAXIMIZE",
                category="window",
                action_type="maximize",
                target_hwnd=hwnd,
                previous_state=prev_state,
                new_state={"is_minimized": False, "is_maximized": True},
                status=status_str,
            )
        return {"status": status_str, "hwnd": hwnd, "action": "maximize"}

    def restore_window(self, hwnd: int, record_telemetry: bool = True) -> Dict[str, Any]:
        """Восстанавливает размер окна."""
        win = self.get_window(hwnd) if record_telemetry else None
        prev_state = {"is_minimized": win.is_minimized, "is_maximized": win.is_maximized} if win else None

        ok = self.window_mgr.restore_window(hwnd)
        status_str = "SUCCESS" if ok else "ERROR"
        if record_telemetry and ok:
            self.history_mgr.record_action(
                command_id="WINDOW.RESTORE",
                category="window",
                action_type="restore",
                target_hwnd=hwnd,
                previous_state=prev_state,
                new_state={"is_minimized": False, "is_maximized": False},
                status=status_str,
            )
        return {"status": status_str, "hwnd": hwnd, "action": "restore"}

    def move_window(
        self,
        hwnd: int,
        req: WindowMoveRequest,
        record_telemetry: bool = True,
    ) -> Dict[str, Any]:
        """Перемещает окно и задает новые размеры."""
        win = self.get_window(hwnd) if record_telemetry else None
        prev_state = win.rect.model_dump() if win else None

        ok = self.window_mgr.move_window(hwnd, req)
        status_str = "SUCCESS" if ok else "ERROR"
        if record_telemetry and ok:
            self.history_mgr.record_action(
                command_id="WINDOW.MOVE",
                category="window",
                action_type="move",
                target_hwnd=hwnd,
                previous_state=prev_state,
                new_state=req.model_dump(),
                status=status_str,
            )
        return {"status": status_str, "hwnd": hwnd, "action": "move", "details": req.model_dump()}

    def close_window(self, hwnd: int, record_telemetry: bool = True) -> Dict[str, Any]:
        """Отправляет окну сообщение закрытия WM_CLOSE."""
        win = self.get_window(hwnd) if record_telemetry else None
        ok = self.window_mgr.close_window(hwnd)
        status_str = "SUCCESS" if ok else "ERROR"
        if record_telemetry and ok:
            self.history_mgr.record_action(
                command_id="WINDOW.CLOSE",
                category="window",
                action_type="close",
                target_hwnd=hwnd,
                details={"title": win.title if win else "", "process": win.process_name if win else ""},
                status=status_str,
            )
        return {"status": status_str, "hwnd": hwnd, "action": "close"}

    def execute_batch_window_action(
        self,
        req: WindowBatchActionRequest,
        record_telemetry: bool = True,
    ) -> Dict[str, Any]:
        """Выполняет пакетное действие над окнами рабочего стола."""
        res = self.window_mgr.batch_action(req)
        if record_telemetry and res.get("status") == "SUCCESS":
            self.history_mgr.record_action(
                command_id="WINDOW.BATCH_ACTION",
                category="window",
                action_type=req.action,
                details=res,
                status="SUCCESS",
            )
        return res

    # --- Приложения ---

    def list_pinned_apps(self) -> List[PinnedAppItem]:
        """Возвращает список закрепленных на панели задач приложений."""
        return self.app_mgr.list_pinned_apps()

    def launch_app(self, req: AppLaunchRequest, record_telemetry: bool = True) -> Dict[str, Any]:
        """Запускает приложение."""
        res = self.app_mgr.launch_app(req)
        if record_telemetry and res.get("status") == "SUCCESS":
            self.history_mgr.record_action(
                command_id="SHELL.LAUNCH_APP",
                category="shell",
                action_type="launch",
                details=req.model_dump(),
                status="SUCCESS",
            )
        return res

    def pin_app(self, req: AppPinRequest, record_telemetry: bool = True) -> Dict[str, Any]:
        """Закрепляет приложение на панели задач."""
        res = self.app_mgr.pin_app(req)
        if record_telemetry and res.get("status") == "SUCCESS":
            self.history_mgr.record_action(
                command_id="TASKBAR.PIN_APP",
                category="shell",
                action_type="pin",
                details=req.model_dump(),
                status="SUCCESS",
            )
        return res

    def unpin_app(self, target_name_or_path: str, record_telemetry: bool = True) -> Dict[str, Any]:
        """Открепляет приложение от панели задач."""
        res = self.app_mgr.unpin_app(target_name_or_path)
        if record_telemetry:
            self.history_mgr.record_action(
                command_id="TASKBAR.UNPIN_APP",
                category="shell",
                action_type="unpin",
                details={"target": target_name_or_path},
                status=res.get("status", "SUCCESS"),
            )
        return res

    # --- Taskbar UX / COM ---

    def set_progress(self, req: TaskbarProgressRequest, record_telemetry: bool = True) -> Dict[str, Any]:
        """Управляет индикатором прогресса ITaskbarList3 на кнопке окна."""
        state_map = {
            "no_progress": TaskbarProgressFlag.TBPF_NOPROGRESS,
            "indeterminate": TaskbarProgressFlag.TBPF_INDETERMINATE,
            "normal": TaskbarProgressFlag.TBPF_NORMAL,
            "error": TaskbarProgressFlag.TBPF_ERROR,
            "paused": TaskbarProgressFlag.TBPF_PAUSED,
        }
        flag = state_map.get(req.state.lower(), TaskbarProgressFlag.TBPF_NORMAL)
        ok_state = self.taskbar_com.set_progress_state(req.hwnd, flag)
        ok_val = self.taskbar_com.set_progress_value(req.hwnd, req.completed, req.total)
        status_str = "SUCCESS" if (ok_state or ok_val) else "COMPLETED"
        if record_telemetry:
            self.history_mgr.record_action(
                command_id="TASKBAR.PROGRESS_SET",
                category="taskbar",
                action_type="progress",
                target_hwnd=req.hwnd,
                details=req.model_dump(),
                status=status_str,
            )
        return {
            "status": status_str,
            "hwnd": req.hwnd,
            "state": req.state,
            "completed": req.completed,
            "total": req.total,
        }

    def set_overlay(self, req: TaskbarOverlayRequest, record_telemetry: bool = True) -> Dict[str, Any]:
        """Устанавливает оверлейную иконку бейджа на кнопке окна."""
        ok = self.taskbar_com.set_overlay_icon(req.hwnd, None, req.description)
        status_str = "SUCCESS" if ok else "COMPLETED"
        if record_telemetry:
            self.history_mgr.record_action(
                command_id="TASKBAR.OVERLAY_SET",
                category="taskbar",
                action_type="overlay",
                target_hwnd=req.hwnd,
                details=req.model_dump(),
                status=status_str,
            )
        return {
            "status": status_str,
            "hwnd": req.hwnd,
            "description": req.description,
        }

    # --- История и откат (Rollback) ---

    def get_history(self, limit: int = 50, command_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Возвращает историю изменений из telemetry.db."""
        return self.history_mgr.get_history(limit=limit, command_id=command_id)

    def rollback(self, history_id: int) -> Dict[str, Any]:
        """Откатывает действие по ID записи в telemetry.db."""
        return self.history_mgr.rollback(history_id, self)

    def rollback_last(self) -> Dict[str, Any]:
        """Откатывает последнее совершенное действие."""
        return self.history_mgr.rollback_last(self)

    # --- Универсальный Command Execution Engine ---

    def execute_command(self, req: CommandExecutionRequest) -> CommandExecutionResponse:
        """
        Универсальный диспетчер выполнения команд из Command Registry.
        
        Выполняет валидацию прав, подтверждений SafeOps и маршрутизирует вызов.
        """
        meta = get_command_by_id(req.command)
        if not meta:
            return CommandExecutionResponse(
                status="ERROR",
                command_id=req.command,
                message=f"Команда '{req.command}' не найдена в Command Registry",
            )

        if meta.requires_confirmation and not req.confirmed_by_user:
            return CommandExecutionResponse(
                status="REJECTED",
                command_id=req.command,
                message=f"Для выполнения '{req.command}' (риск: {meta.risk}) требуется явное подтверждение (confirmed_by_user=True)",
            )

        cmd = meta.id.upper()
        p = req.params

        try:
            if cmd == "WINDOW.ACTIVATE":
                hwnd = int(p.get("hwnd", 0))
                res = self.activate_window(hwnd)
                return CommandExecutionResponse(status=res["status"], command_id=cmd, details=res)

            elif cmd == "WINDOW.MINIMIZE":
                hwnd = int(p.get("hwnd", 0))
                res = self.minimize_window(hwnd)
                return CommandExecutionResponse(status=res["status"], command_id=cmd, details=res)

            elif cmd == "WINDOW.MAXIMIZE":
                hwnd = int(p.get("hwnd", 0))
                res = self.maximize_window(hwnd)
                return CommandExecutionResponse(status=res["status"], command_id=cmd, details=res)

            elif cmd == "WINDOW.RESTORE":
                hwnd = int(p.get("hwnd", 0))
                res = self.restore_window(hwnd)
                return CommandExecutionResponse(status=res["status"], command_id=cmd, details=res)

            elif cmd == "WINDOW.CLOSE":
                hwnd = int(p.get("hwnd", 0))
                res = self.close_window(hwnd)
                return CommandExecutionResponse(status=res["status"], command_id=cmd, details=res)

            elif cmd == "WINDOW.MOVE":
                hwnd = int(p.get("hwnd", 0))
                m_req = WindowMoveRequest(
                    x=int(p.get("x", 0)),
                    y=int(p.get("y", 0)),
                    width=int(p.get("width", 800)),
                    height=int(p.get("height", 600)),
                )
                res = self.move_window(hwnd, m_req)
                return CommandExecutionResponse(status=res["status"], command_id=cmd, details=res)

            elif cmd == "WINDOW.BATCH_ACTION":
                b_req = WindowBatchActionRequest(
                    action=str(p.get("action", "minimize_all")),
                    target_hwnd=p.get("target_hwnd"),
                    process_name=p.get("process_name"),
                )
                res = self.execute_batch_window_action(b_req)
                return CommandExecutionResponse(status=res["status"], command_id=cmd, details=res)

            elif cmd == "TASKBAR.SET_ALIGNMENT":
                val = int(p.get("value", 1))
                res = self.update_settings(TaskbarSettingsUpdate(alignment=val))
                return CommandExecutionResponse(status=res["status"], command_id=cmd, details=res)

            elif cmd == "TASKBAR.SET_AUTOHIDE":
                val = bool(p.get("value", True))
                res = self.update_settings(TaskbarSettingsUpdate(auto_hide=val))
                return CommandExecutionResponse(status=res["status"], command_id=cmd, details=res)

            elif cmd == "TASKBAR.SET_WIDGETS":
                val = bool(p.get("value", True))
                res = self.update_settings(TaskbarSettingsUpdate(widgets_visible=val))
                return CommandExecutionResponse(status=res["status"], command_id=cmd, details=res)

            elif cmd == "TASKBAR.SET_SEARCH":
                val = int(p.get("value", 1))
                res = self.update_settings(TaskbarSettingsUpdate(search_mode=val))
                return CommandExecutionResponse(status=res["status"], command_id=cmd, details=res)

            elif cmd == "SHELL.LAUNCH_APP":
                l_req = AppLaunchRequest(
                    app_path=str(p.get("app_path", "")),
                    arguments=p.get("arguments"),
                    working_dir=p.get("working_dir"),
                    admin=bool(p.get("admin", False)),
                )
                res = self.launch_app(l_req)
                return CommandExecutionResponse(status=res["status"], command_id=cmd, details=res)

            elif cmd == "TASKBAR.PROGRESS_SET":
                prog_req = TaskbarProgressRequest(
                    hwnd=int(p.get("hwnd", 0)),
                    state=str(p.get("state", "normal")),
                    completed=int(p.get("completed", 0)),
                    total=int(p.get("total", 100)),
                )
                res = self.set_progress(prog_req)
                return CommandExecutionResponse(status=res["status"], command_id=cmd, details=res)

            elif cmd == "TASKBAR.OVERLAY_SET":
                ov_req = TaskbarOverlayRequest(
                    hwnd=int(p.get("hwnd", 0)),
                    description=str(p.get("description", "")),
                )
                res = self.set_overlay(ov_req)
                return CommandExecutionResponse(status=res["status"], command_id=cmd, details=res)

            else:
                return CommandExecutionResponse(
                    status="SUCCESS",
                    command_id=cmd,
                    message=f"Команда '{cmd}' зарегистрирована (метаданные возвращены)",
                    details={"metadata": meta.model_dump()},
                )

        except Exception as exc:
            logger.error(f"[TaskbarController] Ошибка при выполнении команды {cmd}: {exc}")
            return CommandExecutionResponse(
                status="ERROR",
                command_id=cmd,
                message=str(exc),
            )
