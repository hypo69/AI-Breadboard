# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows API Wrappers Package
# =============================================================================
# Description:
#   Модульный слой низкоуровневых оберток Windows API:
#   - kernel32: Снимки процессов, дескрипторы, память
#   - psapi: Анализ рабочей памяти процессов и модулей
#   - advapi32: Реестр, токены и безопасность
#   - scm: Service Control Manager (OpenSCManagerW, EnumServicesStatusExW)
#   - tasksched: Task Scheduler 2.0 COM API (Schedule.Service)
#   - nethelper: IP Helper API (GetExtendedTcpTable, GetExtendedUdpTable)
#   - setupapi: SetupAPI и Configuration Manager PnP (CM_Get_DevNode_Status)
#   - ntdll: Native NT API функции
#   - etw: Event Tracing for Windows
#   - wevtapi: Windows Event Log API (wevtapi.dll)
#
# File: __init__.py
# Project: AI-Breadboard
# Package: apps.windows.api
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Экспорт низкоуровневых оберток Windows Native и COM API."""

from .kernel32 import Kernel32API
from .psapi import PsapiAPI
from .advapi32 import Advapi32API
from .ntdll import NtdllAPI
from .etw import EtwAPI
from .wevtapi import WevtAPI
from .scm import ServiceControlManager, ServiceInfo
from .tasksched import TaskSchedulerAPI
from .nethelper import IPHelperAPI, NetworkSocketInfo
from .setupapi import SetupAPI, PnPDeviceInfo

__all__ = [
    'Kernel32API',
    'PsapiAPI',
    'Advapi32API',
    'NtdllAPI',
    'EtwAPI',
    'WevtAPI',
    'ServiceControlManager',
    'ServiceInfo',
    'TaskSchedulerAPI',
    'IPHelperAPI',
    'NetworkSocketInfo',
    'SetupAPI',
    'PnPDeviceInfo',
]
