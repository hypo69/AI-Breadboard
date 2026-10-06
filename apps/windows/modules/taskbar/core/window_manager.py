# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Taskbar - Window Manager
# =============================================================================
# Description:
#   Управление окнами Windows рабочего стола и панели задач через Win32 API.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.taskbar.core.window_manager import WindowManager
#
#     mgr = WindowManager()
#     windows = mgr.list_windows()
#
# File: window_manager.py
# Project: ai-breadboard
# Package: apps.windows.modules.taskbar.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 17:30:00
# =============================================================================

from __future__ import annotations
"""Управление окнами рабочего стола через Win32 User32 и DWM API."""

import ctypes
from ctypes import wintypes
import os
from typing import Any, Callable, Dict, List, Optional
import psutil

from logger import logger
from apps.windows.modules.taskbar.core.models import (
    WindowBatchActionRequest,
    WindowItem,
    WindowMoveRequest,
    WindowRect,
)

# Win32 константы
SW_HIDE = 0
SW_SHOWNORMAL = 1
SW_SHOWMINIMIZED = 2
SW_MAXIMIZE = 3
SW_SHOW = 5
SW_MINIMIZE = 6
SW_RESTORE = 9

WM_CLOSE = 0x0010

GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_APPWINDOW = 0x00040000

# Callback prototype для EnumWindows
WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)


class RECT(ctypes.Structure):
    """Структура прямоугольника Win32 RECT."""
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


class WindowManager:
    """Управление окнами верхнего уровня операционной системы Windows."""

    def __init__(self) -> None:
        """Инициализация менеджера окон."""
        self._user32 = ctypes.windll.user32
        self._kernel32 = ctypes.windll.kernel32

    def _get_process_name(self, pid: int) -> str:
        """Получение имени процесса по PID."""
        if pid <= 0:
            return ""
        try:
            return psutil.Process(pid).name()
        except Exception:
            return ""

    def _get_window_rect(self, hwnd: int) -> WindowRect:
        """Получение координат и размеров окна по его HWND."""
        r = RECT()
        try:
            if self._user32.GetWindowRect(hwnd, ctypes.byref(r)):
                w = max(0, r.right - r.left)
                h = max(0, r.bottom - r.top)
                return WindowRect(
                    left=r.left,
                    top=r.top,
                    right=r.right,
                    bottom=r.bottom,
                    width=w,
                    height=h,
                )
        except Exception:
            pass
        return WindowRect()

    def get_taskbar_rect(self) -> WindowRect:
        """Возвращает координаты и габариты главной панели задач Windows (Shell_TrayWnd)."""
        try:
            hwnd = self._user32.FindWindowW("Shell_TrayWnd", None)
            if hwnd:
                return self._get_window_rect(hwnd)
        except Exception as exc:
            logger.debug(f"[WindowManager] Ошибка определения габаритов Taskbar: {exc}")
        return WindowRect()

    def get_foreground_window(self) -> Optional[WindowItem]:
        """Возвращает информацию о текущем активном окне переднего плана."""
        try:
            hwnd = self._user32.GetForegroundWindow()
            if hwnd:
                return self.get_window_by_hwnd(hwnd)
        except Exception as exc:
            logger.debug(f"[WindowManager] Ошибка GetForegroundWindow: {exc}")
        return None

    def get_window_by_hwnd(self, hwnd: int) -> Optional[WindowItem]:
        """Получение детальной информации об окне по его HWND."""
        if not self._user32.IsWindow(hwnd):
            return None

        # Заголовок окна
        length = self._user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        self._user32.GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value

        # Имя класса
        class_buf = ctypes.create_unicode_buffer(256)
        self._user32.GetClassNameW(hwnd, class_buf, 256)
        class_name = class_buf.value

        # PID
        pid = wintypes.DWORD()
        self._user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        process_id = pid.value
        process_name = self._get_process_name(process_id)

        # Состояния
        is_visible = bool(self._user32.IsWindowVisible(hwnd))
        is_minimized = bool(self._user32.IsIconic(hwnd))
        is_maximized = bool(self._user32.IsZoomed(hwnd))
        fg_hwnd = self._user32.GetForegroundWindow()
        is_foreground = (hwnd == fg_hwnd)

        rect = self._get_window_rect(hwnd)

        return WindowItem(
            hwnd=hwnd,
            title=title,
            process_id=process_id,
            process_name=process_name,
            class_name=class_name,
            is_visible=is_visible,
            is_minimized=is_minimized,
            is_maximized=is_maximized,
            is_foreground=is_foreground,
            rect=rect,
        )

    def list_windows(
        self,
        only_visible: bool = True,
        only_taskbar: bool = True,
        title_filter: Optional[str] = None,
        process_filter: Optional[str] = None,
    ) -> List[WindowItem]:
        """Перечисляет все окна рабочего стола с опциональной фильтрацией."""
        result: List[WindowItem] = []

        def enum_windows_proc(hwnd: int, lparam: int) -> bool:
            if not self._user32.IsWindow(hwnd):
                return True

            is_vis = bool(self._user32.IsWindowVisible(hwnd))
            if only_visible and not is_vis:
                return True

            length = self._user32.GetWindowTextLengthW(hwnd)
            # Если требуется фильтрация по панели задач, пропускаем безымянные окна
            if only_taskbar and length == 0:
                return True

            # Проверка стилей окна (отсечение tool window без явного app window)
            if only_taskbar:
                ex_style = self._user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                if (ex_style & WS_EX_TOOLWINDOW) and not (ex_style & WS_EX_APPWINDOW):
                    return True

            win_info = self.get_window_by_hwnd(hwnd)
            if win_info:
                # Фильтр по названию
                if title_filter and title_filter.lower() not in win_info.title.lower():
                    return True
                # Фильтр по процессу
                if process_filter and process_filter.lower() not in win_info.process_name.lower():
                    return True
                result.append(win_info)

            return True

        cb = WNDENUMPROC(enum_windows_proc)
        self._user32.EnumWindows(cb, 0)
        return result

    def activate_window(self, hwnd: int) -> bool:
        """Активирует окно, восстанавливает из свернутого состояния и выводит на передний план."""
        if not self._user32.IsWindow(hwnd):
            return False
        try:
            if self._user32.IsIconic(hwnd):
                self._user32.ShowWindow(hwnd, SW_RESTORE)
            else:
                self._user32.ShowWindow(hwnd, SW_SHOW)
            self._user32.BringWindowToTop(hwnd)
            return bool(self._user32.SetForegroundWindow(hwnd))
        except Exception as exc:
            logger.error(f"[WindowManager] Ошибка активации окна HWND {hwnd}: {exc}")
            return False

    def minimize_window(self, hwnd: int) -> bool:
        """Сворачивает окно на панель задач."""
        if not self._user32.IsWindow(hwnd):
            return False
        return bool(self._user32.ShowWindow(hwnd, SW_MINIMIZE))

    def maximize_window(self, hwnd: int) -> bool:
        """Разворачивает окно на весь экран."""
        if not self._user32.IsWindow(hwnd):
            return False
        return bool(self._user32.ShowWindow(hwnd, SW_MAXIMIZE))

    def restore_window(self, hwnd: int) -> bool:
        """Восстанавливает нормальный размер окна."""
        if not self._user32.IsWindow(hwnd):
            return False
        return bool(self._user32.ShowWindow(hwnd, SW_RESTORE))

    def move_window(self, hwnd: int, req: WindowMoveRequest) -> bool:
        """Изменяет положение и размеры окна."""
        if not self._user32.IsWindow(hwnd):
            return False
        return bool(self._user32.MoveWindow(hwnd, req.x, req.y, req.width, req.height, True))

    def close_window(self, hwnd: int) -> bool:
        """Корректно закрывает окно через отправку сообщения WM_CLOSE."""
        if not self._user32.IsWindow(hwnd):
            return False
        return bool(self._user32.PostMessageW(hwnd, WM_CLOSE, 0, 0))

    def batch_action(self, req: WindowBatchActionRequest) -> Dict[str, Any]:
        """Выполняет пакетные действия над окнами рабочего стола."""
        action = req.action.lower()
        windows = self.list_windows(only_visible=True, only_taskbar=True)
        affected = 0

        if action == "minimize_all":
            for w in windows:
                if not w.is_minimized:
                    self.minimize_window(w.hwnd)
                    affected += 1
        elif action == "restore_all":
            for w in windows:
                if w.is_minimized:
                    self.restore_window(w.hwnd)
                    affected += 1
        elif action == "minimize_all_except":
            target = req.target_hwnd
            for w in windows:
                if w.hwnd != target and not w.is_minimized:
                    self.minimize_window(w.hwnd)
                    affected += 1
            if target:
                self.activate_window(target)
        elif action == "close_by_process":
            proc_target = (req.process_name or "").lower()
            for w in windows:
                if proc_target and proc_target in w.process_name.lower():
                    self.close_window(w.hwnd)
                    affected += 1
        else:
            return {"status": "ERROR", "message": f"Неизвестное действие: {req.action}"}

        return {
            "status": "SUCCESS",
            "action": req.action,
            "affected_windows_count": affected,
        }
