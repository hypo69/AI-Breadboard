# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry - Process Token Collector
# =============================================================================
# Description:
#   Коллектор токенов процессов, уровней целостности, прав UAC, SID и Session ID.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.process_token_collector import ProcessTokenCollector
#
#     collector = ProcessTokenCollector()
#     tokens = collector.collect()
#
# File: process_token_collector.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 01:45:00
# =============================================================================

"""Коллектор токенов процессов, уровней целостности, прав UAC, SID и Session ID."""

from __future__ import annotations

import ctypes
import ctypes.wintypes as wtypes
import os
from typing import Dict, List, Optional
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False

from .models import ProcessTokenInfo

TOKEN_QUERY = 8
TokenUser = 1
TokenGroups = 2
TokenPrivileges = 3
TokenElevation = 20
TokenIntegrityLevel = 25


class TOKEN_ELEVATION(ctypes.Structure):
    _fields_ = [('TokenIsElevated', wtypes.DWORD)]


class LUID(ctypes.Structure):
    _fields_ = [('LowPart', wtypes.DWORD), ('HighPart', wtypes.LONG)]


class LUID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_ = [('Luid', LUID), ('Attributes', wtypes.DWORD)]


class TOKEN_MANDATORY_LABEL(ctypes.Structure):
    _fields_ = [('Label', LUID_AND_ATTRIBUTES)]


class SID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_ = [('Sid', ctypes.c_void_p), ('Attributes', wtypes.DWORD)]


class TOKEN_USER(ctypes.Structure):
    _fields_ = [('User', SID_AND_ATTRIBUTES)]


def _get_process_token(handle: Any) -> wtypes.HANDLE:
    """Получить дескриптор токена процесса."""
    token = wtypes.HANDLE()
    if not ctypes.windll.advapi32.OpenProcessToken(handle, TOKEN_QUERY, ctypes.byref(token)):
        raise ctypes.WinError()
    return token


def _get_token_elevation(token: Any) -> bool:
    """Определить статус повышения прав UAC."""
    elevation = TOKEN_ELEVATION()
    size = wtypes.DWORD(ctypes.sizeof(elevation))
    ret = ctypes.windll.advapi32.GetTokenInformation(
        token, TokenElevation, ctypes.byref(elevation), size, ctypes.byref(size)
    )
    if not ret:
        raise ctypes.WinError()
    return bool(elevation.TokenIsElevated)


def _get_integrity_level(token: Any) -> str:
    """Получить уровень целостности процесса (Untrusted, Low, Medium, High, System)."""
    size = wtypes.DWORD(0)
    ctypes.windll.advapi32.GetTokenInformation(token, TokenIntegrityLevel, None, 0, ctypes.byref(size))
    if size.value == 0:
        return 'Medium'
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


def _get_token_sid(token: Any) -> Optional[str]:
    """Извлечь строковый SID пользователя из токена процесса."""
    try:
        size = wtypes.DWORD(0)
        ctypes.windll.advapi32.GetTokenInformation(token, TokenUser, None, 0, ctypes.byref(size))
        if size.value == 0:
            return None
        buf = ctypes.create_string_buffer(size.value)
        if not ctypes.windll.advapi32.GetTokenInformation(token, TokenUser, buf, size, ctypes.byref(size)):
            return None
        user_struct = ctypes.cast(buf, ctypes.POINTER(TOKEN_USER)).contents
        sid_ptr = user_struct.User.Sid
        if not sid_ptr:
            return None
        str_sid = wtypes.LPWSTR()
        if ctypes.windll.advapi32.ConvertSidToStringSidW(sid_ptr, ctypes.byref(str_sid)):
            sid_val = str_sid.value
            ctypes.windll.kernel32.LocalFree(str_sid)
            return sid_val
    except Exception:
        pass
    return None


def get_process_session_id(pid: int) -> Optional[int]:
    """Получить Session ID процесса (Session 0=Службы, Session 1+=Интерактивный пользователь)."""
    if os.name != 'nt':
        return None
    try:
        session_id = wtypes.DWORD(0)
        if ctypes.windll.kernel32.ProcessIdToSessionId(pid, ctypes.byref(session_id)):
            return int(session_id.value)
    except Exception:
        pass
    return None


class ProcessTokenCollector:
    """Коллектор сведений о безопасности токенов, правах UAC, SID и сессиях процессов Windows."""

    def get_process_token_info(self, pid: int, name: str = '') -> Optional[ProcessTokenInfo]:
        """Собрать информацию о токене для конкретного PID.

        Args:
            pid: Идентификатор процесса.
            name: Имя процесса (опционально).

        Returns:
            Optional[ProcessTokenInfo]: Данные токена или None при отсутствии доступа.
        """
        if os.name != 'nt':
            return ProcessTokenInfo(pid=pid, name=name, elevation=False, integrity_level='Medium', sid=None, session_id=1)

        session_id = get_process_session_id(pid)
        handle = ctypes.windll.kernel32.OpenProcess(1024, False, pid)
        if not handle:
            return ProcessTokenInfo(
                pid=pid,
                name=name,
                elevation=None,
                integrity_level=None,
                privileges=[],
                sid=None,
                session_id=session_id,
            )
        try:
            token = _get_process_token(handle)
            elevated = _get_token_elevation(token)
            integrity = _get_integrity_level(token)
            sid = _get_token_sid(token)
            privileges: List[str] = []
            return ProcessTokenInfo(
                pid=pid,
                name=name,
                elevation=bool(elevated),
                integrity_level=integrity,
                privileges=privileges,
                sid=sid,
                session_id=session_id,
            )
        except Exception:
            return ProcessTokenInfo(
                pid=pid,
                name=name,
                elevation=None,
                integrity_level=None,
                privileges=[],
                sid=None,
                session_id=session_id,
            )
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)

    def collect(self) -> List[ProcessTokenInfo]:
        """Собрать сведения о токенах для всех активных процессов в системе.

        Returns:
            List[ProcessTokenInfo]: Список токенов процессов.
        """
        results: List[ProcessTokenInfo] = []
        if not PSUTIL_AVAILABLE:
            current_pid = os.getpid()
            info = self.get_process_token_info(current_pid, 'python.exe')
            if info:
                results.append(info)
            return results

        for proc in psutil.process_iter(attrs=['pid', 'name']):
            try:
                pid = proc.info['pid']
                name = proc.info['name'] or 'unknown'
                info = self.get_process_token_info(pid, name)
                if info:
                    results.append(info)
            except Exception:
                continue
        return results