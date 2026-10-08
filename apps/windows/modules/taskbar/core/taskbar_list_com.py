# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Taskbar - ITaskbarList3 COM
# =============================================================================
# Description:
#   Обертка COM интерфейса ITaskbarList3 для управления индикатором прогресса и оверлеями.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.taskbar.core.taskbar_list_com import TaskbarList3Wrapper
#
#     tb = TaskbarList3Wrapper()
#     tb.set_progress_value(hwnd, 50, 100)
#
# File: taskbar_list_com.py
# Project: ai-breadboard
# Package: apps.windows.modules.taskbar.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 04:20:00
# =============================================================================

from __future__ import annotations
"""COM интерфейс ITaskbarList3 для управления прогрессом, оверлеями и миниатюрами."""

import ctypes
from ctypes import wintypes
from enum import IntEnum
from typing import Any, Dict, Optional

from logger import logger

# Константы флагов состояния прогресса (TBPFLAG)
class TaskbarProgressFlag(IntEnum):
    """Флаги состояния индикатора выполнения ITaskbarList3."""
    TBPF_NOPROGRESS = 0x0
    TBPF_INDETERMINATE = 0x1
    TBPF_NORMAL = 0x2
    TBPF_ERROR = 0x4
    TBPF_PAUSED = 0x8


class TaskbarList3Wrapper:
    """Управление расширенными возможностями панели задач через ITaskbarList3 COM API."""

    CLSID_TaskbarList = "{56FDF344-FD6D-11d0-958A-006097C9A090}"
    IID_ITaskbarList3 = "{EA1AFB91-9E28-4B86-90E9-9E9F8A5EEFAF}"

    def __init__(self) -> None:
        """Инициализирует интерфейс COM ITaskbarList3."""
        self._initialized = False
        self._com_instance = None
        self._init_com()

    def _init_com(self) -> None:
        """Инициализация COM библиотеки и создание экземпляра ITaskbarList3."""
        try:
            import comtypes.client
            self._com_instance = comtypes.client.CreateObject(
                self.CLSID_TaskbarList,
                interface=comtypes.client.lazybind.IUnknown
            )
            # Вызов HrInit
            if hasattr(self._com_instance, "HrInit"):
                self._com_instance.HrInit()
            self._initialized = True
        except Exception as exc:
            logger.error(f"[TaskbarList3] Не удалось инициализировать comtypes ITaskbarList3: {exc}")
            self._initialized = False

    def set_progress_state(self, hwnd: int, state: TaskbarProgressFlag) -> bool:
        """Устанавливает состояние индикатора прогресса на кнопке окна."""
        if not hwnd or not ctypes.windll.user32.IsWindow(hwnd):
            return False

        if self._initialized and self._com_instance and hasattr(self._com_instance, "SetProgressState"):
            try:
                self._com_instance.SetProgressState(hwnd, int(state))
                return True
            except Exception as exc:
                logger.error(f"[TaskbarList3] Ошибка SetProgressState COM: {exc}")

        return False

    def set_progress_value(self, hwnd: int, completed: int, total: int) -> bool:
        """Устанавливает численное значение индикатора прогресса."""
        if not hwnd or not ctypes.windll.user32.IsWindow(hwnd):
            return False

        if self._initialized and self._com_instance and hasattr(self._com_instance, "SetProgressValue"):
            try:
                self._com_instance.SetProgressValue(hwnd, completed, total)
                return True
            except Exception as exc:
                logger.error(f"[TaskbarList3] Ошибка SetProgressValue COM: {exc}")

        return False

    def set_overlay_icon(self, hwnd: int, hicon: Optional[int], description: str = "") -> bool:
        """Устанавливает иконку оверлея (значок уведомления) на кнопку окна."""
        if not hwnd or not ctypes.windll.user32.IsWindow(hwnd):
            return False

        if self._initialized and self._com_instance and hasattr(self._com_instance, "SetOverlayIcon"):
            try:
                self._com_instance.SetOverlayIcon(hwnd, hicon or 0, description)
                return True
            except Exception as exc:
                logger.error(f"[TaskbarList3] Ошибка SetOverlayIcon COM: {exc}")

        return False
