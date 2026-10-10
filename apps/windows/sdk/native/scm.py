# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry Win32_Ffi - Scm
# =============================================================================
# Description:
#   Низкоуровневый интерфейс к Service Control Manager (advapi32.dll) Windows.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.win32_ffi.scm import SERVICE_STATUS_PROCESS
#
#     service = SERVICE_STATUS_PROCESS()
#
# File: scm.py
# Project: ai-breadboard
# Package: apps.windows.telemetry.win32_ffi
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Низкоуровневый интерфейс к Service Control Manager (advapi32.dll) Windows."""

import ctypes
import ctypes.wintypes as wintypes
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from logger import logger
SC_MANAGER_CONNECT = 1
SC_MANAGER_CREATE_SERVICE = 2
SC_MANAGER_ENUMERATE_SERVICE = 4
SC_MANAGER_LOCK = 8
SC_MANAGER_QUERY_LOCK_STATUS = 16
SC_MANAGER_MODIFY_BOOT_CONFIG = 32
SC_MANAGER_ALL_ACCESS = 983103
SERVICE_WIN32_OWN_PROCESS = 16
SERVICE_WIN32_SHARE_PROCESS = 32
SERVICE_DRIVER = 11
SERVICE_TYPE_ALL = SERVICE_WIN32_OWN_PROCESS | SERVICE_WIN32_SHARE_PROCESS | SERVICE_DRIVER
SERVICE_ACTIVE = 1
SERVICE_INACTIVE = 2
SERVICE_STATE_ALL = SERVICE_ACTIVE | SERVICE_INACTIVE
SERVICE_STOPPED = 1
SERVICE_START_PENDING = 2
SERVICE_STOP_PENDING = 3
SERVICE_RUNNING = 4
SERVICE_CONTINUE_PENDING = 5
SERVICE_PAUSE_PENDING = 6
SERVICE_PAUSED = 7
SERVICE_QUERY_CONFIG = 1
SERVICE_CHANGE_CONFIG = 2
SERVICE_QUERY_STATUS = 4
SERVICE_ENUMERATE_DEPENDENTS = 8
SERVICE_START = 16
SERVICE_STOP = 32
SERVICE_PAUSE_CONTINUE = 64
SERVICE_INTERROGATE = 128
SERVICE_USER_DEFINED_CONTROL = 256
SERVICE_ALL_ACCESS = 983551
SC_ENUM_PROCESS_INFO = 0
ERROR_MORE_DATA = 234

class SERVICE_STATUS_PROCESS(ctypes.Structure):
    """Структура статуса и процесса службы."""
    _fields_ = [('dwServiceType', wintypes.DWORD), ('dwCurrentState', wintypes.DWORD), ('dwControlsAccepted', wintypes.DWORD), ('dwWin32ExitCode', wintypes.DWORD), ('dwServiceSpecificExitCode', wintypes.DWORD), ('dwCheckPoint', wintypes.DWORD), ('dwWaitHint', wintypes.DWORD), ('dwProcessId', wintypes.DWORD), ('dwServiceFlags', wintypes.DWORD)]

class ENUM_SERVICE_STATUS_PROCESSW(ctypes.Structure):
    """Структура элемента перечисления служб с PID."""
    _fields_ = [('lpServiceName', wintypes.LPWSTR), ('lpDisplayName', wintypes.LPWSTR), ('ServiceStatusProcess', SERVICE_STATUS_PROCESS)]

class QUERY_SERVICE_CONFIGW(ctypes.Structure):
    """Структура детальной конфигурации службы."""
    _fields_ = [('dwServiceType', wintypes.DWORD), ('dwStartType', wintypes.DWORD), ('dwErrorControl', wintypes.DWORD), ('lpBinaryPathName', wintypes.LPWSTR), ('lpLoadOrderGroup', wintypes.LPWSTR), ('dwTagId', wintypes.DWORD), ('lpDependencies', wintypes.LPWSTR), ('lpServiceStartName', wintypes.LPWSTR), ('lpDisplayName', wintypes.LPWSTR)]

@dataclass
class ServiceInfo:
    """Нормализованные данные о службе Windows."""
    name: str
    display_name: str
    state: str
    state_code: int
    pid: int
    service_type: int
    binary_path: str = ''
    start_type: str = ''
    account: str = ''

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь."""
        return {'name': self.name, 'display_name': self.display_name, 'state': self.state, 'state_code': self.state_code, 'pid': self.pid, 'service_type': self.service_type, 'binary_path': self.binary_path, 'start_type': self.start_type, 'account': self.account}

class ServiceControlManager:
    """Низкоуровневый клиент к Service Control Manager (advapi32.dll)."""
    STATE_MAP = {SERVICE_STOPPED: 'STOPPED', SERVICE_START_PENDING: 'START_PENDING', SERVICE_STOP_PENDING: 'STOP_PENDING', SERVICE_RUNNING: 'RUNNING', SERVICE_CONTINUE_PENDING: 'CONTINUE_PENDING', SERVICE_PAUSE_PENDING: 'PAUSE_PENDING', SERVICE_PAUSED: 'PAUSED'}
    START_TYPE_MAP = {0: 'BOOT', 1: 'SYSTEM', 2: 'AUTO_START', 3: 'DEMAND_START', 4: 'DISABLED'}

    def __init__(self) -> None:
        """Инициализация функций advapi32.dll."""
        self._advapi32 = ctypes.windll.advapi32
        self._OpenSCManagerW = self._advapi32.OpenSCManagerW
        self._OpenSCManagerW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD]
        self._OpenSCManagerW.restype = wintypes.SC_HANDLE
        self._EnumServicesStatusExW = self._advapi32.EnumServicesStatusExW
        self._EnumServicesStatusExW.argtypes = [wintypes.SC_HANDLE, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, wintypes.LPBYTE, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.DWORD), wintypes.LPCWSTR]
        self._EnumServicesStatusExW.restype = wintypes.BOOL
        self._OpenServiceW = self._advapi32.OpenServiceW
        self._OpenServiceW.argtypes = [wintypes.SC_HANDLE, wintypes.LPCWSTR, wintypes.DWORD]
        self._OpenServiceW.restype = wintypes.SC_HANDLE
        self._QueryServiceConfigW = self._advapi32.QueryServiceConfigW
        self._QueryServiceConfigW.argtypes = [wintypes.SC_HANDLE, wintypes.LPBYTE, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
        self._QueryServiceConfigW.restype = wintypes.BOOL
        self._CloseServiceHandle = self._advapi32.CloseServiceHandle
        self._CloseServiceHandle.argtypes = [wintypes.SC_HANDLE]
        self._CloseServiceHandle.restype = wintypes.BOOL

    def enum_services(self, service_type: int=SERVICE_WIN32_OWN_PROCESS | SERVICE_WIN32_SHARE_PROCESS) -> List[ServiceInfo]:
        """Быстрое пакетное перечисление всех служб через EnumServicesStatusExW.

        Args:
            service_type: Маска типов служб (Win32, Driver, etc.).

        Returns:
            List[ServiceInfo]: Список обнаруженных служб с PID и статусом.
        """
        h_scm = self._OpenSCManagerW(None, None, SC_MANAGER_ENUMERATE_SERVICE | SC_MANAGER_CONNECT)
        if not h_scm:
            logger.debug('Не удалось открыть SCManager через WinAPI')
            return []
        services: List[ServiceInfo] = []
        try:
            bytes_needed = wintypes.DWORD(0)
            services_returned = wintypes.DWORD(0)
            resume_handle = wintypes.DWORD(0)
            self._EnumServicesStatusExW(h_scm, SC_ENUM_PROCESS_INFO, service_type, SERVICE_STATE_ALL, None, 0, ctypes.byref(bytes_needed), ctypes.byref(services_returned), ctypes.byref(resume_handle), None)
            if bytes_needed.value == 0:
                return []
            buf = (ctypes.c_byte * bytes_needed.value)()
            success = self._EnumServicesStatusExW(h_scm, SC_ENUM_PROCESS_INFO, service_type, SERVICE_STATE_ALL, ctypes.cast(buf, wintypes.LPBYTE), bytes_needed.value, ctypes.byref(bytes_needed), ctypes.byref(services_returned), ctypes.byref(resume_handle), None)
            if not success and ctypes.GetLastError() != ERROR_MORE_DATA:
                return []
            entry_ptr = ctypes.cast(buf, ctypes.POINTER(ENUM_SERVICE_STATUS_PROCESSW))
            for i in range(services_returned.value):
                entry = entry_ptr[i]
                state_code = entry.ServiceStatusProcess.dwCurrentState
                state_str = self.STATE_MAP.get(state_code, 'UNKNOWN')
                pid = entry.ServiceStatusProcess.dwProcessId
                svc = ServiceInfo(name=entry.lpServiceName or '', display_name=entry.lpDisplayName or entry.lpServiceName or '', state=state_str, state_code=state_code, pid=pid, service_type=entry.ServiceStatusProcess.dwServiceType)
                services.append(svc)
        except Exception as ex:
            logger.debug(f'Исключение при нативном перечислении служб SCM: {ex}')
        finally:
            self._CloseServiceHandle(h_scm)
        return services

    def get_service_config(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Получение подробной конфигурации службы через QueryServiceConfigW.

        Args:
            service_name: Системное имя службы.

        Returns:
            Optional[Dict[str, Any]]: Данные конфигурации или None при ошибке.
        """
        h_scm = self._OpenSCManagerW(None, None, SC_MANAGER_CONNECT)
        if not h_scm:
            return None
        try:
            h_svc = self._OpenServiceW(h_scm, service_name, SERVICE_QUERY_CONFIG)
            if not h_svc:
                return None
            try:
                bytes_needed = wintypes.DWORD(0)
                self._QueryServiceConfigW(h_svc, None, 0, ctypes.byref(bytes_needed))
                if bytes_needed.value == 0:
                    return None
                buf = (ctypes.c_byte * bytes_needed.value)()
                if not self._QueryServiceConfigW(h_svc, ctypes.cast(buf, wintypes.LPBYTE), bytes_needed.value, ctypes.byref(bytes_needed)):
                    return None
                cfg = ctypes.cast(buf, ctypes.POINTER(QUERY_SERVICE_CONFIGW)).contents
                return {'binary_path': cfg.lpBinaryPathName or '', 'start_type': self.START_TYPE_MAP.get(cfg.dwStartType, str(cfg.dwStartType)), 'start_type_code': cfg.dwStartType, 'account': cfg.lpServiceStartName or '', 'display_name': cfg.lpDisplayName or service_name, 'dependencies': cfg.lpDependencies or ''}
            finally:
                self._CloseServiceHandle(h_svc)
        except Exception as ex:
            logger.debug(f"Ошибка чтения конфигурации службы '{service_name}': {ex}")
            return None
        finally:
            self._CloseServiceHandle(h_scm)


ServiceManagerFFI = ServiceControlManager

__all__ = [
    "ServiceControlManager",
    "ServiceManagerFFI",
    "ServiceInfo",
    "SERVICE_STATUS_PROCESS",
    "QUERY_SERVICE_CONFIGW",
]