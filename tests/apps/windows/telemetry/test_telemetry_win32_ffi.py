# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Apps Windows Telemetry - Test Telemetry Win32 Ffi
# =============================================================================
# Description:
#   Тесты низкоуровневых оберток Windows API и Win32 FFI.
#
# Usage Examples:
#   Python API:
#     from tests.apps.windows.telemetry.test_telemetry_win32_ffi import TestWin32ErrorDecoder
#
#     service = TestWin32ErrorDecoder()
#
# File: test_telemetry_win32_ffi.py
# Project: ai-breadboard
# Package: tests.apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

"""Тесты низкоуровневых оберток Windows API и Win32 FFI.

Updated: 2026-10-01 11:07:00"""

import os
import pytest

from apps.windows.telemetry.win32_ffi.error_decoder import WindowsErrorDecoder, decode_bugcheck_code, format_system_error
from apps.windows.telemetry.win32_ffi.advapi32 import Advapi32API
from apps.windows.telemetry.win32_ffi.kernel32 import Kernel32API
from apps.windows.telemetry.win32_ffi.nethelper import IPHelperAPI
from apps.windows.telemetry.win32_ffi.ntdll import NtdllAPI
from apps.windows.telemetry.win32_ffi.psapi import PsapiAPI
from apps.windows.telemetry.win32_ffi.scm import ServiceControlManager
from apps.windows.telemetry.win32_ffi.setupapi import SetupAPI
from apps.windows.telemetry.win32_ffi.tasksched import TaskSchedulerAPI
from apps.windows.telemetry.win32_ffi.wevtapi import WevtAPI
from apps.windows.telemetry.win32_ffi.etw import EtwAPI


class TestWin32ErrorDecoder:
    """Тестирование нативного декодера ошибок Win32 и кодов BugCheck."""

    def test_decode_known_bugcheck_code(self):
        result = decode_bugcheck_code(0x0000000A)
        assert isinstance(result, dict)
        assert result['symbol'] == 'IRQL_NOT_LESS_OR_EQUAL'
        assert 'IRQL' in result['description_ru']

    def test_decode_unknown_bugcheck_code(self):
        result = decode_bugcheck_code(0x99999999)
        assert isinstance(result, dict)
        assert result['symbol'] == 'UNKNOWN_BUGCHECK'

    def test_format_system_error(self):
        msg = format_system_error(0)
        assert isinstance(msg, str)
        msg_err = format_system_error(2)  # ERROR_FILE_NOT_FOUND
        assert isinstance(msg_err, str)

    def test_windows_error_decoder_class(self):
        decoder = WindowsErrorDecoder()
        desc = decoder.format_system_error(0)
        assert isinstance(desc, str)


class TestAdvapi32API:
    """Тестирование взаимодействия с advapi32.dll (Реестр)."""

    def test_advapi32_init(self):
        adv = Advapi32API()
        assert adv is not None


class TestKernel32API:
    """Тестирование взаимодействия с kernel32.dll."""

    def test_kernel32_init(self):
        k32 = Kernel32API()
        assert k32 is not None


class TestIPHelperAPI:
    """Тестирование сетевых хелперов и системных таблиц сокетов."""

    def test_iphelper_init(self):
        net = IPHelperAPI()
        assert net is not None


class TestNtdllAPI:
    """Тестирование системного уровня ntdll.dll."""

    def test_ntdll_init(self):
        nt = NtdllAPI()
        assert nt is not None


class TestPsapiAPI:
    """Тестирование получения метрик процессов из psapi.dll."""

    def test_psapi_init(self):
        ps = PsapiAPI()
        assert ps is not None


class TestServiceControlManager:
    """Тестирование диспетчера служб Windows SCM."""

    def test_scm_init(self):
        scm = ServiceControlManager()
        assert scm is not None


class TestSetupAPI:
    """Тестирование уровня PnP устройств setupapi.dll."""

    def test_setupapi_init(self):
        setup = SetupAPI()
        assert setup is not None


class TestTaskSchedulerAPI:
    """Тестирование планировщика задач Windows."""

    def test_tasksched_init(self):
        task_api = TaskSchedulerAPI()
        assert task_api is not None


class TestWevtAPI:
    """Тестирование журналов событий Windows Event Log API."""

    def test_wevtapi_init(self):
        wevt = WevtAPI()
        assert wevt is not None


class TestEtwAPI:
    """Тестирование сессии трассировки событий ETW."""

    def test_etw_api_init(self):
        etw = EtwAPI()
        assert etw is not None
