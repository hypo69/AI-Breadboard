# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Taskbar - ITaskbarList3 COM
# =============================================================================
# Description:
#   Обертка COM интерфейса ITaskbarList3 для управления индикатором прогресса и оверлеями
#   с использованием встроенного модуля ctypes (без внешних зависимостей).
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
# Updated: 2026-10-08 04:35:00
# =============================================================================

from __future__ import annotations
"""COM интерфейс ITaskbarList3 для управления прогрессом, оверлеями и миниатюрами."""

import ctypes
from ctypes import wintypes
from enum import IntEnum
import sys
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


class _GUID(ctypes.Structure):
    """Структура Win32 GUID для COM интерфейсов."""
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", wintypes.BYTE * 8),
    ]

    def __init__(self, guid_str: str) -> None:
        """Парсит строковое представление GUID в бинарную структуру."""
        super().__init__()
        if sys.platform == "win32":
            ctypes.windll.ole32.CLSIDFromString(ctypes.c_wchar_p(guid_str), ctypes.byref(self))


class TaskbarList3Wrapper:
    """Управление расширенными возможностями панели задач через ITaskbarList3 COM API."""

    CLSID_TaskbarList = "{56FDF344-FD6D-11d0-958A-006097C9A090}"
    IID_ITaskbarList3 = "{EA1AFB91-9E28-4B86-90E9-9E9F8A5EEFAF}"

    def __init__(self) -> None:
        """Инициализирует интерфейс COM ITaskbarList3."""
        self._initialized = False
        self._ptr: Optional[ctypes.c_void_p] = None
        self._fn_hr_init = None
        self._fn_set_progress_state = None
        self._fn_set_progress_value = None
        self._fn_set_overlay_icon = None
        self._fn_release = None
        self._init_com()

    def _init_com(self) -> None:
        """Инициализация COM библиотеки и создание экземпляра ITaskbarList3 через ctypes."""
        if sys.platform != "win32":
            return

        try:
            # Инициализация COM для вызывающего потока
            ctypes.windll.ole32.CoInitialize(None)
            clsid = _GUID(self.CLSID_TaskbarList)
            iid = _GUID(self.IID_ITaskbarList3)
            p_tbl = ctypes.c_void_p()

            # CLSCTX_INPROC_SERVER (0x1) | CLSCTX_LOCAL_SERVER (0x4)
            hr = ctypes.windll.ole32.CoCreateInstance(
                ctypes.byref(clsid),
                None,
                0x1 | 0x4,
                ctypes.byref(iid),
                ctypes.byref(p_tbl),
            )
            if hr != 0 or not p_tbl.value:
                logger.warning(f"[TaskbarList3] Не удалось создать экземпляр COM ITaskbarList3 (HRESULT: {hr:#x})")
                return

            self._ptr = p_tbl
            vtable = ctypes.cast(p_tbl, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)))

            # Привязка методов vtable ITaskbarList3:
            # 2: Release
            # 3: HrInit
            # 9: SetProgressValue(HWND, ULONGLONG, ULONGLONG)
            # 10: SetProgressState(HWND, TBPFLAG)
            # 18: SetOverlayIcon(HWND, HICON, LPCWSTR)
            self._fn_release = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)(vtable.contents[2])
            self._fn_hr_init = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p)(vtable.contents[3])
            self._fn_set_progress_value = ctypes.WINFUNCTYPE(
                ctypes.c_long, ctypes.c_void_p, wintypes.HWND, ctypes.c_ulonglong, ctypes.c_ulonglong
            )(vtable.contents[9])
            self._fn_set_progress_state = ctypes.WINFUNCTYPE(
                ctypes.c_long, ctypes.c_void_p, wintypes.HWND, ctypes.c_int
            )(vtable.contents[10])
            self._fn_set_overlay_icon = ctypes.WINFUNCTYPE(
                ctypes.c_long, ctypes.c_void_p, wintypes.HWND, wintypes.HICON, wintypes.LPCWSTR
            )(vtable.contents[18])

            try:
                self._fn_hr_init(self._ptr)
            except Exception:
                pass

            self._initialized = True
        except Exception as exc:
            logger.error(f"[TaskbarList3] Ошибка инициализации ITaskbarList3 COM: {exc}")
            self._initialized = False

    def set_progress_state(self, hwnd: int, state: TaskbarProgressFlag) -> bool:
        """Устанавливает состояние индикатора прогресса на кнопке окна."""
        if not hwnd or not self._initialized or not self._ptr or not self._fn_set_progress_state:
            return False
        if not ctypes.windll.user32.IsWindow(hwnd):
            return False

        try:
            hr = self._fn_set_progress_state(self._ptr, hwnd, int(state))
            return hr == 0
        except Exception as exc:
            logger.error(f"[TaskbarList3] Ошибка SetProgressState COM: {exc}")
            return False

    def set_progress_value(self, hwnd: int, completed: int, total: int) -> bool:
        """Устанавливает численное значение индикатора прогресса."""
        if not hwnd or not self._initialized or not self._ptr or not self._fn_set_progress_value:
            return False
        if not ctypes.windll.user32.IsWindow(hwnd):
            return False

        try:
            hr = self._fn_set_progress_value(self._ptr, hwnd, completed, total)
            return hr == 0
        except Exception as exc:
            logger.error(f"[TaskbarList3] Ошибка SetProgressValue COM: {exc}")
            return False

    def set_overlay_icon(self, hwnd: int, hicon: Optional[int], description: str = "") -> bool:
        """Устанавливает иконку оверлея (значок уведомления) на кнопку окна."""
        if not hwnd or not self._initialized or not self._ptr or not self._fn_set_overlay_icon:
            return False
        if not ctypes.windll.user32.IsWindow(hwnd):
            return False

        try:
            hr = self._fn_set_overlay_icon(self._ptr, hwnd, hicon or 0, description)
            return hr == 0
        except Exception as exc:
            logger.error(f"[TaskbarList3] Ошибка SetOverlayIcon COM: {exc}")
            return False

    def __del__(self) -> None:
        """Освобождает COM интерфейс ITaskbarList3 при сборке мусора."""
        ptr = self._ptr
        fn_release = self._fn_release
        self._ptr = None
        self._fn_release = None
        if ptr and fn_release:
            try:
                fn_release(ptr)
            except (OSError, Exception):
                pass

