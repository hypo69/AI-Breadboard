# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Tests - Test Error Decoder
# =============================================================================
# Description:
#   Тестирование нативного декодера системных ошибок Windows (Win32, HRESULT,
#
# Usage Examples:
#   Python API:
#     from apps.windows.tests.test_error_decoder import test_error_code_parsing
#
#     res = test_error_code_parsing()
#
# File: test_error_decoder.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Тестирование нативного декодера системных ошибок Windows (Win32, HRESULT,"""

import os
import pytest
from apps.windows.telemetry.win32_ffi.error_decoder import (
    WindowsErrorDecoder,
    decode_bugcheck_code,
    format_system_error,
    get_error_decoder,
)
from apps.windows.telemetry.win32_ffi.wevtapi import WevtAPI


def test_error_code_parsing() -> None:
    """Проверка нормализации числовых и строковых кодов ошибок в uint32."""
    decoder = WindowsErrorDecoder()

    # Десятичное число
    u_val, hex_str = decoder.parse_error_code(5)
    assert u_val == 5
    assert hex_str == '0x00000005'

    # Hex строка с префиксом 0x
    u_val, hex_str = decoder.parse_error_code('0x80070005')
    assert u_val == 0x80070005
    assert hex_str == '0x80070005'

    # Отрицательное целое (например, signed HRESULT -2147024891 == 0x80070005)
    u_val, hex_str = decoder.parse_error_code(-2147024891)
    assert u_val == 0x80070005
    assert hex_str == '0x80070005'

    # Невалидная строка
    u_val, hex_str = decoder.parse_error_code('not_a_code')
    assert u_val == 0
    assert hex_str == '0x00000000'


def test_decode_bugcheck_code() -> None:
    """Проверка расшифровки стандартных Stop-кодов BSOD (BugCheck)."""
    # DRIVER_IRQL_NOT_LESS_OR_EQUAL (0xD1 / 209)
    res_d1 = decode_bugcheck_code(0xD1)
    assert res_d1['symbol'] == 'DRIVER_IRQL_NOT_LESS_OR_EQUAL'
    assert 'IRQL' in res_d1['description_ru']
    assert res_d1['code_hex'] == '0x000000D1'

    # PAGE_FAULT_IN_NONPAGED_AREA (0x50)
    res_50 = decode_bugcheck_code('0x00000050')
    assert res_50['symbol'] == 'PAGE_FAULT_IN_NONPAGED_AREA'
    assert 'памяти' in res_50['description_ru']

    # DPC_WATCHDOG_VIOLATION (0x133)
    res_133 = decode_bugcheck_code(0x133)
    assert res_133['symbol'] == 'DPC_WATCHDOG_VIOLATION'

    # Неизвестный BugCheck код
    res_unk = decode_bugcheck_code(0xDEADBEEF)
    assert res_unk['code_hex'] == '0xDEADBEEF'
    assert 'symbol' in res_unk


@pytest.mark.skipif(os.name != 'nt', reason='Нативное системное форматирование доступно только на Windows')
def test_format_system_error_win32() -> None:
    """Проверка нативного декодирования стандартных Win32 кодов ошибок через FormatMessageW."""
    # Код 5: ERROR_ACCESS_DENIED (Отказано в доступе / Access is denied)
    msg_5 = format_system_error(5)
    assert msg_5 != ''
    assert any(k in msg_5.lower() for k in ('доступ', 'access', 'denied', 'отказано'))

    # Код 2: ERROR_FILE_NOT_FOUND (Не удается найти указанный файл / The system cannot find the file specified)
    msg_2 = format_system_error(2)
    assert msg_2 != ''
    assert any(k in msg_2.lower() for k in ('файл', 'file', 'find', 'найти'))

    # Код 0: Успех
    msg_0 = format_system_error(0)
    assert 'успешно' in msg_0.lower() or 'success' in msg_0.lower()


@pytest.mark.skipif(os.name != 'nt', reason='Нативное системное форматирование доступно только на Windows')
def test_format_system_error_hresult_and_ntstatus() -> None:
    """Проверка декодирования HRESULT (0x80070005) и NTSTATUS (0xC0000005)."""
    # HRESULT 0x80070005 (E_ACCESSDENIED)
    msg_hr = format_system_error('0x80070005')
    assert msg_hr != ''
    assert any(k in msg_hr.lower() for k in ('доступ', 'access', 'denied', 'отказано'))

    # NTSTATUS 0xC0000005 (STATUS_ACCESS_VIOLATION)
    msg_nt = format_system_error('0xC0000005')
    assert msg_nt != ''
    assert len(msg_nt) > 3


def test_wevtapi_publisher_formatting_methods() -> None:
    """Проверка наличия методов и корректности API в классе WevtAPI."""
    wevt = WevtAPI()
    assert hasattr(wevt, 'format_event_message')
    assert hasattr(wevt, '_get_publisher_metadata')
    assert hasattr(wevt, 'close')
    assert hasattr(wevt, '_publisher_cache')

    # Безопасный вызов на пустых данных
    assert wevt.format_event_message(None, '') is None
    wevt.close()
    assert len(wevt._publisher_cache) == 0
