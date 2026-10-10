# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Native - Performance Data Helper (PDH)
# =============================================================================
# Description:
#   Win32 C-FFI вызовы к pdh.dll для сбора счетчиков производительности Windows.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.native.pdh import PDHManager
#
# File: pdh.py
# Project: ai-breadboard
# Package: apps.windows.sdk.native
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 09:36:00
# =============================================================================

from __future__ import annotations
"""Win32 Performance Data Helper (pdh.dll) C-FFI обертка."""

import ctypes
import ctypes.wintypes as wintypes
import os
from typing import Any, Dict, Optional

from logger import logger

# Константы PDH
PDH_FMT_DOUBLE = 0x00000200
PDH_FMT_LONG = 0x00000100
PDH_FMT_LARGE = 0x00000400
PDH_FMT_NOSCALE = 0x00001000
PDH_FMT_1000 = 0x00002000
PDH_FMT_NODATA = 0x00004000

ERROR_SUCCESS = 0


class PDH_FMT_COUNTERVALUE_DOUBLE(ctypes.Structure):
    _fields_ = [
        ("CStatus", wintypes.DWORD),
        ("dummy", wintypes.DWORD),
        ("doubleValue", ctypes.c_double),
    ]


class PDHManager:
    """Менеджер счетчиков производительности Windows (PDH C-FFI)."""

    def __init__(self) -> None:
        self._pdh = getattr(ctypes.windll, "pdh", None) if os.name == "nt" else None
        self._query_handle: Optional[ctypes.c_void_p] = None
        self._counters: Dict[str, ctypes.c_void_p] = {}

    @property
    def is_available(self) -> bool:
        """Доступна ли библиотека pdh.dll в текущей системе."""
        return self._pdh is not None

    def open_query(self) -> bool:
        """Инициализирует сессию запроса PDH."""
        if not self._pdh:
            return False
        h_query = ctypes.c_void_p()
        status = self._pdh.PdhOpenQueryW(None, 0, ctypes.byref(h_query))
        if status == ERROR_SUCCESS:
            self._query_handle = h_query
            return True
        logger.debug(f"[PDH] Ошибка PdhOpenQueryW: {hex(status & 0xFFFFFFFF)}")
        return False

    def add_counter(self, name: str, counter_path: str) -> bool:
        """Добавляет счетчик производительности в текущий запрос."""
        if not self._pdh or not self._query_handle:
            return False
        h_counter = ctypes.c_void_p()
        status = self._pdh.PdhAddEnglishCounterW(
            self._query_handle, counter_path, 0, ctypes.byref(h_counter)
        )
        if status == ERROR_SUCCESS:
            self._counters[name] = h_counter
            return True
        logger.debug(f"[PDH] Не удалось добавить счетчик {counter_path}: {hex(status & 0xFFFFFFFF)}")
        return False

    def collect(self) -> bool:
        """Собрать данные по всем зарегистрированным счетчикам."""
        if not self._pdh or not self._query_handle:
            return False
        status = self._pdh.PdhCollectQueryData(self._query_handle)
        return status == ERROR_SUCCESS

    def get_value(self, name: str) -> Optional[float]:
        """Получить значение счетчика в формате double."""
        if not self._pdh or name not in self._counters:
            return None
        h_counter = self._counters[name]
        val = PDH_FMT_COUNTERVALUE_DOUBLE()
        status = self._pdh.PdhGetFormattedCounterValue(
            h_counter, PDH_FMT_DOUBLE | PDH_FMT_NOSCALE, None, ctypes.byref(val)
        )
        if status == ERROR_SUCCESS and val.CStatus == ERROR_SUCCESS:
            return val.doubleValue
        return None

    def close(self) -> None:
        """Закрыть дескриптор запроса PDH."""
        if self._pdh and self._query_handle:
            try:
                self._pdh.PdhCloseQuery(self._query_handle)
            except Exception:
                pass
            self._query_handle = None
            self._counters.clear()

    def __del__(self) -> None:
        self.close()
