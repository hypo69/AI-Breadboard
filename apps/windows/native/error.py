# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Native - Error Handling & Decoder
# =============================================================================
# Description:
#   Win32/NTSTATUS/HRESULT обработка ошибок, декоратор win32_error_check и декодер кодов.
#
# Usage Examples:
#   Python API:
#     from apps.windows.native.error import win32_error_check, WindowsErrorDecoder, Win32Error
#
# File: error.py
# Project: ai-breadboard
# Package: apps.windows.native
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 09:36:00
# =============================================================================

from __future__ import annotations
"""Единая подсистема обработки ошибок Win32 C-FFI вызовов."""

import ctypes
import ctypes.wintypes as wintypes
import functools
import os
import sys
from typing import Any, Callable, Dict, Optional, Tuple, TypeVar, Union

from logger import logger

# Экспортируем WindowsErrorDecoder из error_decoder для обратной совместимости и централизации
from apps.windows.native.error_decoder import WindowsErrorDecoder, BUGCHECK_CODES_MAP

F = TypeVar("F", bound=Callable[..., Any])


class Win32Error(Exception):
    """Исключение для ошибок вызовов Win32 C-FFI."""

    def __init__(self, code: int, message: str = "", win32_func: str = ""):
        self.code = code
        self.win32_func = win32_func
        self.raw_message = message
        decoder = WindowsErrorDecoder()
        _, hex_code, desc = decoder.decode(code)
        self.hex_code = hex_code
        self.description = desc or message
        super().__init__(f"Win32 Error {self.hex_code} in {win32_func or 'Native API'}: {self.description}")


def win32_error_check(func_name: Optional[str] = None) -> Callable[[F], F]:
    """Декоратор для автоматической проверки GetLastError() и Win32 кодов возврата."""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                result = func(*args, **kwargs)
                # Если функция возвращает 0/False/NULL и это критический сбой Win32:
                if result is False or result == 0:
                    if os.name == "nt" and hasattr(ctypes, "windll"):
                        err_code = ctypes.windll.kernel32.GetLastError()
                        if err_code != 0:
                            decoder = WindowsErrorDecoder()
                            _, hex_code, desc = decoder.decode(err_code)
                            logger.debug(f"[Win32 C-FFI] {func_name or func.__name__} вернул {result}, GetLastError={hex_code}: {desc}")
                return result
            except Win32Error:
                raise
            except Exception as ex:
                logger.error(f"[Win32 C-FFI] Исключение в {func_name or func.__name__}: {ex}")
                raise
        return wrapper  # type: ignore
    return decorator


__all__ = [
    "Win32Error",
    "win32_error_check",
    "WindowsErrorDecoder",
    "BUGCHECK_CODES_MAP",
]
