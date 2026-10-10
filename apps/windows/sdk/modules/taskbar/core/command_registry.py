# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Taskbar - Command Registry
# =============================================================================
# Description:
#   Машиночитаемый реестр команд и возможностей Windows Desktop Control Plane.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.taskbar.core.command_registry import get_taskbar_command_catalog
#
#     catalog = get_taskbar_command_catalog()
#
# File: command_registry.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.taskbar.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 17:35:00
# =============================================================================

from __future__ import annotations
"""Машиночитаемый каталог и реестр команд управления панелью задач и окнами."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CommandApiDetails(BaseModel):
    """Описание системных API интерфейсов для выполнения команды."""
    win32: Optional[str] = None
    com: Optional[str] = None
    registry: Optional[str] = None
    powershell: Optional[str] = None


class CommandPythonDetails(BaseModel):
    """Описание Python реализации для выполнения команды."""
    module: str
    method: str


class TaskbarCommandMetadata(BaseModel):
    """Метаданные отдельной операции управления Windows Desktop Control Plane."""
    id: str = Field(..., description="Уникальный идентификатор команды (например, WINDOW.MOVE)")
    category: str = Field(..., description="Категория (window, taskbar, process, shell, tray, jumplist, desktop, monitor, dwm)")
    description: str = Field(..., description="Человекочитаемое описание операции")
    platform: List[str] = Field(default_factory=lambda: ["Windows 10", "Windows 11"])
    privilege: str = Field("user", description="Требуемые привилегии: user, admin, user_or_admin")
    risk: str = Field("safe", description="Уровень риска: safe, caution, admin, high, unsupported")
    execution_class: str = Field("NATIVE", description="Класс выполнения: NATIVE, COMPATIBILITY, RESTRICTED, INTERNAL")
    api: CommandApiDetails = Field(default_factory=CommandApiDetails)
    python: CommandPythonDetails = Field(default_factory=lambda: CommandPythonDetails(module="", method=""))
    requires_confirmation: bool = Field(False, description="Требуется ли явное подтверждение пользователя")
    supports_rollback: bool = Field(False, description="Поддерживается ли откат операции")
    endpoint: str = Field("", description="FastAPI REST эндпоинт")


# Базовый каталог системных команд
_BASE_COMMANDS: List[TaskbarCommandMetadata] = [
    # 1. WINDOWS BASE (001-020)
    TaskbarCommandMetadata(
        id="WINDOW.ENUMERATE",
        category="window",
        description="Перечисление всех открытых окон рабочего стола",
        privilege="user",
        risk="safe",
        execution_class="NATIVE",
        api=CommandApiDetails(win32="EnumWindows", powershell="Get-Process | Where MainWindowHandle"),
        python=CommandPythonDetails(module="apps.windows.sdk.modules.taskbar.core.window_manager", method="list_windows"),
        endpoint="GET /api/v1/taskbar/windows",
    ),
    TaskbarCommandMetadata(
        id="WINDOW.GET_TITLE",
        category="window",
        description="Получение текстового заголовка окна по HWND",
        privilege="user",
        risk="safe",
        execution_class="NATIVE",
        api=CommandApiDetails(win32="GetWindowTextW"),
        python=CommandPythonDetails(module="apps.windows.sdk.modules.taskbar.core.window_manager", method="get_window_by_hwnd"),
        endpoint="GET /api/v1/taskbar/windows/{hwnd}",
    ),
    TaskbarCommandMetadata(
        id="WINDOW.GET_RECT",
        category="window",
        description="Получение экранных координат и размеров окна",
        privilege="user",
        risk="safe",
        execution_class="NATIVE",
        api=CommandApiDetails(win32="GetWindowRect"),
        python=CommandPythonDetails(module="apps.windows.sdk.modules.taskbar.core.window_manager", method="get_window_by_hwnd"),
        endpoint="GET /api/v1/taskbar/windows/{hwnd}",
    ),
    TaskbarCommandMetadata(
        id="WINDOW.GET_FOREGROUND",
        category="window",
        description="Получение дескриптора и свойств окна переднего плана",
        privilege="user",
        risk="safe",
        execution_class="NATIVE",
        api=CommandApiDetails(win32="GetForegroundWindow"),
        python=CommandPythonDetails(module="apps.windows.sdk.modules.taskbar.core.window_manager", method="get_foreground_window"),
        endpoint="GET /api/v1/taskbar/summary",
    ),
    # 2. WINDOWS ACTIONS (021-040)
    TaskbarCommandMetadata(
        id="WINDOW.ACTIVATE",
        category="window",
        description="Активация и вывод окна на передний план",
        privilege="user",
        risk="safe",
        execution_class="NATIVE",
        api=CommandApiDetails(win32="SetForegroundWindow / BringWindowToTop"),
        python=CommandPythonDetails(module="apps.windows.sdk.modules.taskbar.core.window_manager", method="activate_window"),
        endpoint="POST /api/v1/taskbar/windows/{hwnd}/activate",
    ),
    TaskbarCommandMetadata(
        id="WINDOW.MINIMIZE",
        category="window",
        description="Сворачивание окна на панель задач",
        privilege="user",
        risk="safe",
        execution_class="NATIVE",
        api=CommandApiDetails(win32="ShowWindow(SW_MINIMIZE)"),
        python=CommandPythonDetails(module="apps.windows.sdk.modules.taskbar.core.window_manager", method="minimize_window"),
        endpoint="POST /api/v1/taskbar/windows/{hwnd}/minimize",
    ),
    TaskbarCommandMetadata(
        id="WINDOW.MAXIMIZE",
        category="window",
        description="Разворачивание окна на весь экран",
        privilege="user",
        risk="safe",
        execution_class="NATIVE",
        api=CommandApiDetails(win32="ShowWindow(SW_MAXIMIZE)"),
        python=CommandPythonDetails(module="apps.windows.sdk.modules.taskbar.core.window_manager", method="maximize_window"),
        endpoint="POST /api/v1/taskbar/windows/{hwnd}/maximize",
    ),
    TaskbarCommandMetadata(
        id="WINDOW.RESTORE",
        category="window",
        description="Восстановление исходного размера окна",
        privilege="user",
        risk="safe",
        execution_class="NATIVE",
        api=CommandApiDetails(win32="ShowWindow(SW_RESTORE)"),
        python=CommandPythonDetails(module="apps.windows.sdk.modules.taskbar.core.window_manager", method="restore_window"),
        endpoint="POST /api/v1/taskbar/windows/{hwnd}/restore",
    ),
    TaskbarCommandMetadata(
        id="WINDOW.MOVE",
        category="window",
        description="Перемещение и изменение размера окна",
        privilege="user",
        risk="safe",
        execution_class="NATIVE",
        api=CommandApiDetails(win32="MoveWindow / SetWindowPos"),
        python=CommandPythonDetails(module="apps.windows.sdk.modules.taskbar.core.window_manager", method="move_window"),
        supports_rollback=True,
        endpoint="POST /api/v1/taskbar/windows/{hwnd}/move",
    ),
    TaskbarCommandMetadata(
        id="WINDOW.CLOSE",
        category="window",
        description="Корректное закрытие окна отправкой WM_CLOSE",
        privilege="user",
        risk="safe",
        execution_class="NATIVE",
        api=CommandApiDetails(win32="PostMessageW(WM_CLOSE)"),
        python=CommandPythonDetails(module="apps.windows.sdk.modules.taskbar.core.window_manager", method="close_window"),
        endpoint="DELETE /api/v1/taskbar/windows/{hwnd}",
    ),
    TaskbarCommandMetadata(
        id="WINDOW.FORCE_CLOSE",
        category="window",
        description="Принудительное завершение процесса окна",
        privilege="user_or_admin",
        risk="high",
        execution_class="RESTRICTED",
        api=CommandApiDetails(win32="TerminateProcess"),
        python=CommandPythonDetails(module="psutil", method="Process.kill"),
        requires_confirmation=True,
        endpoint="POST /api/v1/taskbar/windows/batch",
    ),
    TaskbarCommandMetadata(
        id="WINDOW.BATCH_ACTION",
        category="window",
        description="Пакетные операции над окнами (minimize_all, restore_all, minimize_all_except)",
        privilege="user",
        risk="safe",
        execution_class="NATIVE",
        api=CommandApiDetails(win32="EnumWindows + ShowWindow"),
        python=CommandPythonDetails(module="apps.windows.sdk.modules.taskbar.core.window_manager", method="batch_action"),
        endpoint="POST /api/v1/taskbar/windows/batch",
    ),
    # 3. TASKBAR DISCOVERY & SETTINGS (051-080)
    TaskbarCommandMetadata(
        id="TASKBAR.GET_SUMMARY",
        category="taskbar",
        description="Сводный отчет о панели задач, габаритах и активных окнах",
        privilege="user",
        risk="safe",
        execution_class="NATIVE",
        api=CommandApiDetails(win32="FindWindowW + GetWindowRect"),
        python=CommandPythonDetails(module="apps.windows.sdk.modules.taskbar.core.manager", method="get_summary"),
        endpoint="GET /api/v1/taskbar",
    ),
    TaskbarCommandMetadata(
        id="TASKBAR.GET_SETTINGS",
        category="taskbar",
        description="Получение всех текущих настроек панели задач",
        privilege="user",
        risk="safe",
        execution_class="NATIVE",
        api=CommandApiDetails(registry="HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced"),
        python=CommandPythonDetails(module="apps.windows.sdk.modules.taskbar.core.settings_manager", method="get_settings"),
        endpoint="GET /api/v1/taskbar/settings",
    ),
    TaskbarCommandMetadata(
        id="TASKBAR.SET_ALIGNMENT",
        category="taskbar",
        description="Выравнивание значков панели задач (0=слева, 1=центр)",
        privilege="user",
        risk="caution",
        execution_class="COMPATIBILITY",
        api=CommandApiDetails(registry="HKCU\\...\\Explorer\\Advanced (TaskbarAl)"),
        python=CommandPythonDetails(module="apps.windows.sdk.modules.taskbar.core.settings_manager", method="update_settings"),
        supports_rollback=True,
        endpoint="PUT /api/v1/taskbar/settings",
    ),
    TaskbarCommandMetadata(
        id="TASKBAR.SET_AUTOHIDE",
        category="taskbar",
        description="Автоматическое скрытие панели задач",
        privilege="user",
        risk="caution",
        execution_class="COMPATIBILITY",
        api=CommandApiDetails(win32="SHAppBarMessage(ABM_SETSTATE, ABS_AUTOHIDE)"),
        python=CommandPythonDetails(module="apps.windows.sdk.modules.taskbar.core.settings_manager", method="set_auto_hide_state"),
        supports_rollback=True,
        endpoint="PUT /api/v1/taskbar/settings",
    ),
    TaskbarCommandMetadata(
        id="TASKBAR.SET_SEARCH",
        category="taskbar",
        description="Режим строки поиска панели задач",
        privilege="user",
        risk="caution",
        execution_class="COMPATIBILITY",
        api=CommandApiDetails(registry="HKCU\\...\\Search (SearchboxTaskbarMode)"),
        python=CommandPythonDetails(module="apps.windows.sdk.modules.taskbar.core.settings_manager", method="update_settings"),
        endpoint="PUT /api/v1/taskbar/settings",
    ),
    TaskbarCommandMetadata(
        id="TASKBAR.SET_WIDGETS",
        category="taskbar",
        description="Отображение виджетов погоды и новостей на панели задач",
        privilege="user",
        risk="caution",
        execution_class="COMPATIBILITY",
        api=CommandApiDetails(registry="HKCU\\...\\Explorer\\Advanced (TaskbarDa)"),
        python=CommandPythonDetails(module="apps.windows.sdk.modules.taskbar.core.settings_manager", method="update_settings"),
        endpoint="PUT /api/v1/taskbar/settings",
    ),
    TaskbarCommandMetadata(
        id="TASKBAR.SET_COPILOT",
        category="taskbar",
        description="Отображение кнопки Copilot на панели задач",
        privilege="user",
        risk="caution",
        execution_class="COMPATIBILITY",
        api=CommandApiDetails(registry="HKCU\\...\\Explorer\\Advanced (ShowCopilotButton)"),
        python=CommandPythonDetails(module="apps.windows.sdk.modules.taskbar.core.settings_manager", method="update_settings"),
        endpoint="PUT /api/v1/taskbar/settings",
    ),
    # 4. PINNED APPS & SHELL (096-128)
    TaskbarCommandMetadata(
        id="TASKBAR.GET_PINNED",
        category="shell",
        description="Список закрепленных на панели ярлыков",
        privilege="user",
        risk="safe",
        execution_class="COMPATIBILITY",
        api=CommandApiDetails(com="WScript.Shell"),
        python=CommandPythonDetails(module="apps.windows.sdk.modules.taskbar.core.app_manager", method="list_pinned_apps"),
        endpoint="GET /api/v1/taskbar/apps",
    ),
    TaskbarCommandMetadata(
        id="SHELL.LAUNCH_APP",
        category="shell",
        description="Запуск приложения с поддержкой аргументов и прав администратора",
        privilege="user_or_admin",
        risk="safe",
        execution_class="NATIVE",
        api=CommandApiDetails(win32="ShellExecuteW(runas) / subprocess"),
        python=CommandPythonDetails(module="apps.windows.sdk.modules.taskbar.core.app_manager", method="launch_app"),
        endpoint="POST /api/v1/taskbar/apps/launch",
    ),
    TaskbarCommandMetadata(
        id="TASKBAR.PIN_APP",
        category="shell",
        description="Закрепление приложения на панели задач (Interactive Shell)",
        privilege="user",
        risk="unsupported",
        execution_class="INTERNAL",
        api=CommandApiDetails(com="Shell.Application (Verbs)"),
        python=CommandPythonDetails(module="apps.windows.sdk.modules.taskbar.core.app_manager", method="pin_app"),
        endpoint="POST /api/v1/taskbar/apps/pin",
    ),
    TaskbarCommandMetadata(
        id="TASKBAR.UNPIN_APP",
        category="shell",
        description="Открепление приложения от панели задач",
        privilege="user",
        risk="unsupported",
        execution_class="INTERNAL",
        api=CommandApiDetails(com="Shell.Application (Verbs)"),
        python=CommandPythonDetails(module="apps.windows.sdk.modules.taskbar.core.app_manager", method="unpin_app"),
        endpoint="DELETE /api/v1/taskbar/apps/pin",
    ),
    # 5. TASKBAR API COM (129-143)
    TaskbarCommandMetadata(
        id="TASKBAR.PROGRESS_SET",
        category="taskbar",
        description="Установка значения и режима индикатора прогресса на кнопке окна",
        privilege="user",
        risk="safe",
        execution_class="NATIVE",
        api=CommandApiDetails(com="ITaskbarList3::SetProgressValue"),
        python=CommandPythonDetails(module="apps.windows.sdk.modules.taskbar.core.taskbar_list_com", method="set_progress_value"),
        endpoint="POST /api/v1/taskbar/ux/progress",
    ),
    TaskbarCommandMetadata(
        id="TASKBAR.OVERLAY_SET",
        category="taskbar",
        description="Установка значка-оверлея бейджа на кнопке окна панели задач",
        privilege="user",
        risk="safe",
        execution_class="NATIVE",
        api=CommandApiDetails(com="ITaskbarList3::SetOverlayIcon"),
        python=CommandPythonDetails(module="apps.windows.sdk.modules.taskbar.core.taskbar_list_com", method="set_overlay_icon"),
        endpoint="POST /api/v1/taskbar/ux/overlay",
    ),
    # 6. POLICIES & GPO (081-095)
    TaskbarCommandMetadata(
        id="POLICY.TASKBAR_LOCK",
        category="policy",
        description="Блокировка изменения панели задач политикой GPO",
        privilege="admin",
        risk="admin",
        execution_class="RESTRICTED",
        api=CommandApiDetails(registry="HKCU\\Software\\Policies\\Microsoft\\Windows\\Explorer (TaskbarLockAll)"),
        python=CommandPythonDetails(module="apps.windows.sdk.modules.taskbar.core.settings_manager", method="update_settings"),
        requires_confirmation=True,
        endpoint="PUT /api/v1/taskbar/settings",
    ),
    TaskbarCommandMetadata(
        id="POLICY.DISABLE_NOTIFICATION_CENTER",
        category="policy",
        description="Отключение центра уведомлений Windows",
        privilege="admin",
        risk="admin",
        execution_class="RESTRICTED",
        api=CommandApiDetails(registry="HKCU\\Software\\Policies\\Microsoft\\Windows\\Explorer (DisableNotificationCenter)"),
        python=CommandPythonDetails(module="apps.windows.sdk.modules.taskbar.core.settings_manager", method="update_settings"),
        requires_confirmation=True,
        endpoint="PUT /api/v1/taskbar/settings",
    ),
]


def get_taskbar_command_catalog(
    category: Optional[str] = None,
    risk: Optional[str] = None,
    execution_class: Optional[str] = None,
) -> List[TaskbarCommandMetadata]:
    """Возвращает машиночитаемый каталог команд с опциональной фильтрацией."""
    result = list(_BASE_COMMANDS)
    if category:
        cat_lower = category.lower()
        result = [c for c in result if c.category.lower() == cat_lower]
    if risk:
        risk_lower = risk.lower()
        result = [c for c in result if c.risk.lower() == risk_lower]
    if execution_class:
        exec_lower = execution_class.lower()
        result = [c for c in result if c.execution_class.lower() == exec_lower]
    return result


def get_command_by_id(command_id: str) -> Optional[TaskbarCommandMetadata]:
    """Поиск метаданных команды по ее уникальному идентификатору."""
    c_clean = command_id.strip().upper()
    for cmd in _BASE_COMMANDS:
        if cmd.id.upper() == c_clean:
            return cmd
    return None
