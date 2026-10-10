# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Native - Package Root
# =============================================================================
# Description:
#   Единый C-FFI слой (Слой 2) для низкоуровневых Win32 API вызовов.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.native import win32_error_check, WindowsErrorDecoder, PDHManager
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.sdk.native
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 09:36:00
# =============================================================================

from __future__ import annotations
"""Единый слой Win32 C-FFI вызовов к нативным DLL (wevtapi, setupapi, iphlpapi, pdh, scm, ntdll, advapi32, kernel32, psapi)."""

from apps.windows.sdk.native.error import (
    Win32Error,
    win32_error_check,
    WindowsErrorDecoder,
    BUGCHECK_CODES_MAP,
)
from apps.windows.sdk.native.pdh import PDHManager
from apps.windows.sdk.native.wevtapi import WindowsEventLogAPI
from apps.windows.sdk.native.scm import ServiceManagerFFI
from apps.windows.sdk.native.setupapi import SetupAPI
from apps.windows.sdk.native.ntdll import NativeNT
from apps.windows.sdk.native.kernel32 import Kernel32
from apps.windows.sdk.native.advapi32 import Advapi32
from apps.windows.sdk.native.psapi import Psapi
from apps.windows.sdk.native.tasksched import TaskSchedulerFFI

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
