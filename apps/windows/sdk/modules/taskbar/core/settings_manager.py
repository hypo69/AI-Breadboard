# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Taskbar - Settings Manager
# =============================================================================
# Description:
#   Управление настройками панели задач через Registry, Shell API и Win32.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.taskbar.core.settings_manager import TaskbarSettingsManager
#
#     mgr = TaskbarSettingsManager()
#     settings = mgr.get_settings()
#
# File: settings_manager.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.taskbar.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 17:30:00
# =============================================================================

from __future__ import annotations
"""Менеджер системных настроек панели задач Windows 10/11."""

import ctypes
import os
import subprocess
import sys
import winreg
from typing import Any, Dict, Optional

from logger import logger
from apps.windows.sdk.modules.taskbar.core.models import TaskbarSettings, TaskbarSettingsUpdate

# Win32 константы
HWND_BROADCAST = 0xFFFF
WM_SETTINGCHANGE = 0x001A
SMTO_ABORTIFHUNG = 0x0002

ABM_GETSTATE = 0x00000004
ABM_SETSTATE = 0x0000000A
ABS_AUTOHIDE = 0x00000001
ABS_ALWAYSONTOP = 0x00000002

_EXPLORER_ADVANCED_KEY = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"
_SEARCH_KEY = r"Software\Microsoft\Windows\CurrentVersion\Search"
_STUCKRECTS3_KEY = r"Software\Microsoft\Windows\CurrentVersion\Explorer\StuckRects3"


class APPBARDATA(ctypes.Structure):
    """Структура Win32 APPBARDATA для работы с SHAppBarMessage."""
    _fields_ = [
        ("cbSize", ctypes.c_uint32),
        ("hWnd", ctypes.c_void_p),
        ("uCallbackMessage", ctypes.c_uint32),
        ("uEdge", ctypes.c_uint32),
        ("rc", ctypes.c_long * 4),
        ("lParam", ctypes.c_int32),
    ]


class TaskbarSettingsManager:
    """Управление системными настройками и отображением панели задач."""

    def __init__(self) -> None:
        """Инициализация менеджера настроек панели задач."""
        self.is_win11 = self._check_is_win11()

    def _check_is_win11(self) -> bool:
        """Определяет, запущена ли система на Windows 11 (сборка 22000+)."""
        try:
            build = sys.getwindowsversion().build
            return build >= 22000
        except Exception:
            return True

    def _read_registry_dword(self, root_key: int, subkey: str, value_name: str, default: int = 0) -> int:
        """Безопасное чтение значения DWORD из реестра Windows."""
        try:
            with winreg.OpenKey(root_key, subkey, 0, winreg.KEY_READ) as key:
                val, _ = winreg.QueryValueEx(key, value_name)
                return int(val)
        except (FileNotFoundError, OSError, ValueError):
            return default

    def _write_registry_dword(self, root_key: int, subkey: str, value_name: str, value: int) -> bool:
        """Безопасная запись значения DWORD в реестр Windows."""
        try:
            with winreg.CreateKey(root_key, subkey) as key:
                winreg.SetValueEx(key, value_name, 0, winreg.REG_DWORD, value)
            return True
        except OSError as exc:
            logger.error(f"[TaskbarSettings] Ошибка записи в реестр {subkey}\\{value_name}: {exc}")
            return False

    def get_auto_hide_state(self) -> bool:
        """Получает статус автоскрытия панели задач через SHAppBarMessage или реестр."""
        try:
            abd = APPBARDATA()
            abd.cbSize = ctypes.sizeof(APPBARDATA)
            state = ctypes.windll.shell32.SHAppBarMessage(ABM_GETSTATE, ctypes.byref(abd))
            return bool(state & ABS_AUTOHIDE)
        except Exception as exc:
            logger.debug(f"[TaskbarSettings] Fallback при чтении APPBARDATA: {exc}")

        # Fallback через StuckRects3
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _STUCKRECTS3_KEY, 0, winreg.KEY_READ) as key:
                val, _ = winreg.QueryValueEx(key, "Settings")
                if isinstance(val, (bytes, bytearray)) and len(val) >= 9:
                    return (val[8] & 0x01) == 0x01
        except Exception:
            pass
        return False

    def set_auto_hide_state(self, enable: bool) -> bool:
        """Устанавливает статус автоскрытия панели задач."""
        success = False
        try:
            abd = APPBARDATA()
            abd.cbSize = ctypes.sizeof(APPBARDATA)
            abd.lParam = ABS_AUTOHIDE if enable else ABS_ALWAYSONTOP
            ctypes.windll.shell32.SHAppBarMessage(ABM_SETSTATE, ctypes.byref(abd))
            success = True
        except Exception as exc:
            logger.error(f"[TaskbarSettings] Ошибка SHAppBarMessage(ABM_SETSTATE): {exc}")

        # Обновление StuckRects3 для персистентности
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _STUCKRECTS3_KEY, 0, winreg.KEY_ALL_ACCESS) as key:
                val, val_type = winreg.QueryValueEx(key, "Settings")
                if isinstance(val, (bytes, bytearray)) and len(val) >= 9:
                    buf = bytearray(val)
                    if enable:
                        buf[8] = (buf[8] & ~0x02) | 0x01
                    else:
                        buf[8] = (buf[8] & ~0x01) | 0x02
                    winreg.SetValueEx(key, "Settings", 0, val_type, bytes(buf))
                    success = True
        except Exception as exc:
            logger.debug(f"[TaskbarSettings] Не удалось обновить StuckRects3: {exc}")

        return success

    def get_settings(self) -> TaskbarSettings:
        """Возвращает текущие конфигурационные параметры панели задач."""
        alignment = self._read_registry_dword(
            winreg.HKEY_CURRENT_USER, _EXPLORER_ADVANCED_KEY, "TaskbarAl", 1 if self.is_win11 else 0
        )
        search_mode = self._read_registry_dword(
            winreg.HKEY_CURRENT_USER, _SEARCH_KEY, "SearchboxTaskbarMode", 1
        )
        widgets_val = self._read_registry_dword(
            winreg.HKEY_CURRENT_USER, _EXPLORER_ADVANCED_KEY, "TaskbarDa", 1
        )
        task_view_val = self._read_registry_dword(
            winreg.HKEY_CURRENT_USER, _EXPLORER_ADVANCED_KEY, "ShowTaskViewButton", 1
        )
        copilot_val = self._read_registry_dword(
            winreg.HKEY_CURRENT_USER, _EXPLORER_ADVANCED_KEY, "ShowCopilotButton", 0
        )
        badges_val = self._read_registry_dword(
            winreg.HKEY_CURRENT_USER, _EXPLORER_ADVANCED_KEY, "TaskbarBadges", 1
        )
        glom_val = self._read_registry_dword(
            winreg.HKEY_CURRENT_USER, _EXPLORER_ADVANCED_KEY, "TaskbarGlomLevel", 0
        )
        small_val = self._read_registry_dword(
            winreg.HKEY_CURRENT_USER, _EXPLORER_ADVANCED_KEY, "TaskbarSmallIcons", 0
        )
        auto_hide = self.get_auto_hide_state()

        return TaskbarSettings(
            alignment=alignment,
            search_mode=search_mode,
            widgets_visible=bool(widgets_val),
            task_view_visible=bool(task_view_val),
            copilot_visible=bool(copilot_val),
            auto_hide=auto_hide,
            badges_enabled=bool(badges_val),
            combine_buttons=glom_val,
            small_icons=bool(small_val),
            location="bottom",
        )

    def update_settings(self, patch: TaskbarSettingsUpdate) -> Dict[str, Any]:
        """Обновляет указанные параметры панели задач и уведомляет Explorer."""
        changed: Dict[str, Any] = {}

        if patch.alignment is not None:
            val = 1 if patch.alignment >= 1 else 0
            if self._write_registry_dword(winreg.HKEY_CURRENT_USER, _EXPLORER_ADVANCED_KEY, "TaskbarAl", val):
                changed["alignment"] = val

        if patch.search_mode is not None:
            val = max(0, min(3, patch.search_mode))
            self._write_registry_dword(winreg.HKEY_CURRENT_USER, _SEARCH_KEY, "SearchboxTaskbarMode", val)
            self._write_registry_dword(winreg.HKEY_CURRENT_USER, _EXPLORER_ADVANCED_KEY, "SearchboxTaskbarMode", val)
            changed["search_mode"] = val

        if patch.widgets_visible is not None:
            val = 1 if patch.widgets_visible else 0
            if self._write_registry_dword(winreg.HKEY_CURRENT_USER, _EXPLORER_ADVANCED_KEY, "TaskbarDa", val):
                changed["widgets_visible"] = bool(val)

        if patch.task_view_visible is not None:
            val = 1 if patch.task_view_visible else 0
            if self._write_registry_dword(winreg.HKEY_CURRENT_USER, _EXPLORER_ADVANCED_KEY, "ShowTaskViewButton", val):
                changed["task_view_visible"] = bool(val)

        if patch.copilot_visible is not None:
            val = 1 if patch.copilot_visible else 0
            if self._write_registry_dword(winreg.HKEY_CURRENT_USER, _EXPLORER_ADVANCED_KEY, "ShowCopilotButton", val):
                changed["copilot_visible"] = bool(val)

        if patch.badges_enabled is not None:
            val = 1 if patch.badges_enabled else 0
            if self._write_registry_dword(winreg.HKEY_CURRENT_USER, _EXPLORER_ADVANCED_KEY, "TaskbarBadges", val):
                changed["badges_enabled"] = bool(val)

        if patch.combine_buttons is not None:
            val = max(0, min(2, patch.combine_buttons))
            if self._write_registry_dword(winreg.HKEY_CURRENT_USER, _EXPLORER_ADVANCED_KEY, "TaskbarGlomLevel", val):
                changed["combine_buttons"] = val

        if patch.auto_hide is not None:
            res = self.set_auto_hide_state(patch.auto_hide)
            changed["auto_hide"] = patch.auto_hide
            changed["auto_hide_applied"] = res

        # Оповещение подсистемы рабочего стола о смене параметров
        self.notify_settings_changed()

        if patch.restart_explorer:
            self.restart_explorer()
            changed["explorer_restarted"] = True

        return {
            "status": "SUCCESS",
            "applied_changes": changed,
            "current_settings": self.get_settings().model_dump(),
        }

    def notify_settings_changed(self) -> None:
        """Отправляет широковещательное сообщение WM_SETTINGCHANGE для обновления GUI."""
        try:
            result = ctypes.c_ulong()
            ctypes.windll.user32.SendMessageTimeoutW(
                HWND_BROADCAST,
                WM_SETTINGCHANGE,
                0,
                "TraySettings",
                SMTO_ABORTIFHUNG,
                1500,
                ctypes.byref(result),
            )
        except Exception as exc:
            logger.debug(f"[TaskbarSettings] Не удалось отправить WM_SETTINGCHANGE: {exc}")

    def restart_explorer(self) -> bool:
        """Перезапускает процесс explorer.exe для гарантированного применения некоторых опций."""
        try:
            subprocess.run(["taskkill", "/f", "/im", "explorer.exe"], check=False, capture_output=True)
            subprocess.Popen(["explorer.exe"])
            return True
        except Exception as exc:
            logger.error(f"[TaskbarSettings] Ошибка перезапуска explorer.exe: {exc}")
            return False
