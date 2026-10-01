# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry - Process Token Collector
# =============================================================================
# Description:
#   Process token collector module.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.process_token_collector import TOKEN_ELEVATION
#
#     service = TOKEN_ELEVATION()
#
# File: process_token_collector.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Process token collector module."""

import ctypes
import ctypes.wintypes as wtypes
import psutil
from typing import List
from .models import ProcessTokenInfo
TOKEN_QUERY = 8
TokenElevation = 20
TokenIntegrityLevel = 25
TokenPrivileges = 3

class TOKEN_ELEVATION(ctypes.Structure):
    _fields_ = [('TokenIsElevated', wtypes.DWORD)]

class LUID(ctypes.Structure):
    _fields_ = [('LowPart', wtypes.DWORD), ('HighPart', wtypes.LONG)]

class LUID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_ = [('Luid', LUID), ('Attributes', wtypes.DWORD)]

class TOKEN_MANDATORY_LABEL(ctypes.Structure):
    _fields_ = [('Label', LUID_AND_ATTRIBUTES)]

def _get_process_token(handle):
    token = wtypes.HANDLE()
    if not ctypes.windll.advapi32.OpenProcessToken(handle, TOKEN_QUERY, ctypes.byref(token)):
        raise ctypes.WinError()
    return token

def _get_token_elevation(token):
    elevation = TOKEN_ELEVATION()
    size = wtypes.DWORD(ctypes.sizeof(elevation))
    ret = ctypes.windll.advapi32.GetTokenInformation(token, TokenElevation, ctypes.byref(elevation), size, ctypes.byref(size))
    if not ret:
        raise ctypes.WinError()
    return bool(elevation.TokenIsElevated)

def _get_integrity_level(token):
    size = wtypes.DWORD(0)
    ctypes.windll.advapi32.GetTokenInformation(token, TokenIntegrityLevel, None, 0, ctypes.byref(size))
    buf = ctypes.create_string_buffer(size.value)
    if not ctypes.windll.advapi32.GetTokenInformation(token, TokenIntegrityLevel, buf, size, ctypes.byref(size)):
        raise ctypes.WinError()
    label = ctypes.cast(buf, ctypes.POINTER(TOKEN_MANDATORY_LABEL)).contents
    integrity = label.Label.Luid.LowPart
    if integrity < 4096:
        return 'Untrusted'
    elif integrity < 8192:
        return 'Low'
    elif integrity < 12288:
        return 'Medium'
    elif integrity < 16384:
        return 'High'
    else:
        return 'System'

class ProcessTokenCollector:
    """Collect token information for all accessible processes.

    Возвращает список объектов :class:`ProcessTokenInfo`.
    """

    def collect(self) -> List[ProcessTokenInfo]:
        results: List[ProcessTokenInfo] = []
        for proc in psutil.process_iter(attrs=['pid', 'name']):
            try:
                pid = proc.info['pid']
                name = proc.info['name']
                handle = ctypes.windll.kernel32.OpenProcess(1024, False, pid)
                if not handle:
                    continue
                try:
                    token = _get_process_token(handle)
                    elevated = _get_token_elevation(token)
                    integrity = _get_integrity_level(token)
                    privileges = []
                finally:
                    ctypes.windll.kernel32.CloseHandle(handle)
                results.append(ProcessTokenInfo(pid=pid, name=name, elevation=bool(elevated), integrity_level=integrity, privileges=privileges))
            except Exception:
                continue
        return results