# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Native - Package Root
# =============================================================================
# Description:
#   Единый C-FFI слой (Слой 2) для низкоуровневых Win32 API вызовов.
#
# Usage Examples:
#   Python API:
#     from apps.windows.native import win32_error_check, WindowsErrorDecoder, PDHManager
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.native
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 09:36:00
# =============================================================================

from __future__ import annotations
"""Единый слой Win32 C-FFI вызовов к нативным DLL (wevtapi, setupapi, iphlpapi, pdh, scm, ntdll, advapi32, kernel32, psapi)."""

from apps.windows.native.error import (
    Win32Error,
    win32_error_check,
    WindowsErrorDecoder,
    BUGCHECK_CODES_MAP,
)
from apps.windows.native.pdh import PDHManager
from apps.windows.native.wevtapi import WindowsEventLogAPI
from apps.windows.native.scm import ServiceManagerFFI
from apps.windows.native.setupapi import SetupAPI
from apps.windows.native.ntdll import NativeNT
from apps.windows.native.kernel32 import Kernel32
from apps.windows.native.advapi32 import Advapi32
from apps.windows.native.psapi import Psapi
from apps.windows.native.tasksched import TaskSchedulerFFI

__all__ = [
    "Win32Error",
    "win32_error_check",
    "WindowsErrorDecoder",
    "BUGCHECK_CODES_MAP",
    "PDHManager",
    "WindowsEventLogAPI",
    "ServiceManagerFFI",
    "SetupAPI",
    "NativeNT",
    "Kernel32",
    "Advapi32",
    "Psapi",
    "TaskSchedulerFFI",
]
