# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry Win32_Ffi -   Init  
# =============================================================================
# Description:
#   Модуль низкоуровневых биндингов Win32 FFI / ctypes.
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.telemetry.win32_ffi
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Модуль низкоуровневых биндингов Win32 FFI / ctypes."""

from .kernel32 import Kernel32API
from .psapi import PsapiAPI
from .advapi32 import Advapi32API
from .ntdll import NtdllAPI
from .etw import EtwAPI
from .wevtapi import WevtAPI, ChannelMetadata, CHANNEL_DESCRIPTIONS
from .scm import ServiceControlManager, ServiceInfo
from .tasksched import TaskSchedulerAPI
from .nethelper import IPHelperAPI, NetworkSocketInfo
from .setupapi import SetupAPI, PnPDeviceInfo
from .error_decoder import WindowsErrorDecoder, format_system_error, decode_bugcheck_code

__all__ = [
    'Kernel32API',
    'PsapiAPI',
    'Advapi32API',
    'NtdllAPI',
    'EtwAPI',
    'WevtAPI',
    'ChannelMetadata',
    'CHANNEL_DESCRIPTIONS',
    'ServiceControlManager',
    'ServiceInfo',
    'TaskSchedulerAPI',
    'IPHelperAPI',
    'NetworkSocketInfo',
    'SetupAPI',
    'PnPDeviceInfo',
    'WindowsErrorDecoder',
    'format_system_error',
    'decode_bugcheck_code',
]
