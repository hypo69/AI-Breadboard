# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry Win32_Ffi - Error Decoder
# =============================================================================
# Description:
#   Модуль нативного декодирования системных кодов возврата Win32, HRESULT,
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.win32_ffi.error_decoder import WindowsErrorDecoder
#
#     service = WindowsErrorDecoder()
#
# File: error_decoder.py
# Project: ai-breadboard
# Package: apps.windows.telemetry.win32_ffi
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Модуль нативного декодирования системных кодов возврата Win32, HRESULT,"""

import ctypes
import ctypes.wintypes as wintypes
import os
import sys
from typing import Any, Dict, Optional, Tuple, Union

try:
    from logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# Флаги для FormatMessageW
FORMAT_MESSAGE_ALLOCATE_BUFFER = 0x00000100
FORMAT_MESSAGE_IGNORE_INSERTS = 0x00000200
FORMAT_MESSAGE_FROM_SYSTEM = 0x00001000
FORMAT_MESSAGE_FROM_HMODULE = 0x00000800

# Известные стандартные Stop-коды ядра Windows (BugCheck Codes)
BUGCHECK_CODES_MAP: Dict[int, Tuple[str, str]] = {
    0x0000000A: ('IRQL_NOT_LESS_OR_EQUAL', 'Процесс или драйвер попытался обратиться к адресу памяти при недопустимо высоком уровне IRQL.'),
    0x0000001E: ('KMODE_EXCEPTION_NOT_HANDLED', 'Программа ядра или драйвер сгенерировали исключение, которое не было перехвачено обработчиком.'),
    0x00000024: ('NTFS_FILE_SYSTEM', 'Критический сбой или повреждение в системном драйвере файловой системы ntfs.sys.'),
    0x0000003B: ('SYSTEM_SERVICE_EXCEPTION', 'Исключение при выполнении подпрограммы системной службы Windows.'),
    0x00000050: ('PAGE_FAULT_IN_NONPAGED_AREA', 'Запрос недопустимой системной памяти. Ошибка вызвана некорректным адресом или сбоем RAM.'),
    0x0000007E: ('SYSTEM_THREAD_EXCEPTION_NOT_HANDLED', 'Системный поток сгенерировал неперехваченное исключение (часто связано с несовместимым драйвером).'),
    0x0000007F: ('UNEXPECTED_KERNEL_MODE_TRAP', 'Аппаратная ловушка процессора (деление на ноль, повреждение стека или перегрузка оборудования).'),
    0x0000009F: ('DRIVER_POWER_STATE_FAILURE', 'Драйвер находится в несогласованном или недействительном состоянии управления электропитанием (сна/пробуждения).'),
    0x000000BE: ('ATTEMPTED_WRITE_TO_READONLY_MEMORY', 'Попытка драйвера выполнить запись в сегмент памяти, доступный только для чтения.'),
    0x000000C2: ('BAD_POOL_CALLER', 'Текущий поток выполнил некорректный запрос к пулу системной памяти ядра.'),
    0x000000D1: ('DRIVER_IRQL_NOT_LESS_OR_EQUAL', 'Драйвер попытался обратиться к выгружаемой памяти на повышенном уровне прерываний IRQL.'),
    0x000000EF: ('CRITICAL_PROCESS_DIED', 'Критически важный системный процесс (csrss.exe, wininit.exe и др.) неожиданно завершил свою работу.'),
    0x00000109: ('CRITICAL_STRUCTURE_CORRUPTION', 'Ядро обнаружило повреждение критических структур данных или кода ядра (PatchGuard).'),
    0x00000116: ('VIDEO_TDR_FAILURE', 'Сбой видеодрайвера: попытка сброса зависшего графического драйвера завершилась тайм-аутом.'),
    0x00000117: ('VIDEO_TDR_TIMEOUT_DETECTED', 'Графический драйвер не ответил вовремя в пределах интервала обнаружения тайм-аута TDR.'),
    0x00000124: ('WHEA_UNCORRECTABLE_ERROR', 'Критическая неустранимая аппаратная ошибка архитектуры Windows Hardware Error Architecture (CPU/RAM/PCIe).'),
    0x00000133: ('DPC_WATCHDOG_VIOLATION', 'Сторожевой таймер DPC зафиксировал зависание отложенного вызова процедуры драйвером.'),
    0x00000139: ('KERNEL_SECURITY_CHECK_FAILURE', 'Ядро обнаружило повреждение критической структуры данных безопасности (Buffer Overflow / Stack Cookie).'),
    0x00000154: ('UNEXPECTED_STORE_EXCEPTION', 'Сбой подсистемы хранения страниц памяти ядра (компрессия памяти / повреждение накопителя).'),
    0x00000192: ('KERNEL_AUTO_BOOST_LOCK_ACQUISITION_WITH_RAISED_IRQL', 'Попытка захвата блокировки AutoBoost ядра на повышенном уровне IRQL.'),
    0x000001A7: ('STORE_DATA_STRUCTURE_CORRUPTION', 'Повреждение внутренней структуры данных диспетчера хранилища страниц памяти.'),
    0xC000021A: ('STATUS_SYSTEM_PROCESS_TERMINATED', 'Подсистема пользовательского режима (WinLogon или Csrss) аварийно завершилась с нарушением безопасности.'),
    0xC0000221: ('STATUS_IMAGE_CHECKSUM_MISMATCH', 'Контрольная сумма системного драйвера или DLL не совпадает с заголовком файла.'),
}


class WindowsErrorDecoder:
    """Класс нативного декодирования ошибок Windows через FormatMessageW."""

    def __init__(self) -> None:
        """Инициализация дескрипторов библиотек."""
        self._kernel32 = getattr(ctypes.windll, 'kernel32', None) if os.name == 'nt' else None
        self._ntdll_handle: Optional[int] = None
        if self._kernel32 and os.name == 'nt':
            try:
                self._kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
                self._kernel32.GetModuleHandleW.restype = wintypes.HMODULE
                self._ntdll_handle = self._kernel32.GetModuleHandleW('ntdll.dll')
            except Exception as ex:
                logger.debug(f'Не удалось получить дескриптор ntdll.dll: {ex}')

    def parse_error_code(self, code: Union[int, str]) -> Tuple[int, str]:
        """Преобразовать входной код ошибки (число, hex-строку или отрицательный int) в uint32.

        Args:
            code: Числовое или строковое представление кода ошибки.

        Returns:
            Tuple[int, str]: (нормализованный uint32 код, форматированная hex-строка 0xXXXXXXXX).
        """
        if isinstance(code, str):
            c_str = code.strip()
            try:
                if c_str.lower().startswith('0x'):
                    val = int(c_str, 16)
                else:
                    val = int(c_str, 10)
            except ValueError:
                return 0, '0x00000000'
        else:
            val = int(code)

        # Преобразуем отрицательные 32-битные числа (например из ctypes signed HRESULT) в беззнаковый uint32
        uint_val = val & 0xFFFFFFFF
        return uint_val, f'0x{uint_val:08X}'

    def format_system_error(self, code: Union[int, str], lang_id: int = 0) -> str:
        """Получить локализованное системное описание ошибки из Windows API (Win32 / HRESULT / NTSTATUS).

        Args:
            code: Код ошибки (например, 5, 0x80070005, 0xC0000005, '0x80240020').
            lang_id: Идентификатор языка (0 - язык текущего потока/системы).

        Returns:
            str: Локализованное текстовое описание ошибки или пустая строка, если код не распознан.
        """
        if not self._kernel32 or os.name != 'nt':
            return ''

        uint_code, _ = self.parse_error_code(code)
        if uint_code == 0:
            return 'Операция успешно завершена.'

        # 1. Попытка чтения из системного репозитория (FORMAT_MESSAGE_FROM_SYSTEM для Win32 и HRESULT)
        buf = wintypes.LPWSTR()
        flags = FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS
        chars = self._kernel32.FormatMessageW(
            flags,
            None,
            wintypes.DWORD(uint_code),
            wintypes.DWORD(lang_id),
            ctypes.byref(buf),
            0,
            None,
        )

        if chars > 0 and buf.value:
            msg = buf.value.strip().rstrip('\r\n.')
            if self._kernel32.LocalFree:
                self._kernel32.LocalFree(buf)
            return msg

        # 2. Если код лежит в диапазоне NTSTATUS (0xC0000000..0xDFFFFFFF или 0x40000000..0x7FFFFFFF)
        # запрашиваем системные сообщения из ntdll.dll
        if self._ntdll_handle:
            buf_nt = wintypes.LPWSTR()
            flags_nt = FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_HMODULE | FORMAT_MESSAGE_IGNORE_INSERTS
            chars_nt = self._kernel32.FormatMessageW(
                flags_nt,
                wintypes.HMODULE(self._ntdll_handle),
                wintypes.DWORD(uint_code),
                wintypes.DWORD(lang_id),
                ctypes.byref(buf_nt),
                0,
                None,
            )
            if chars_nt > 0 and buf_nt.value:
                msg_nt = buf_nt.value.strip().rstrip('\r\n.')
                if self._kernel32.LocalFree:
                    self._kernel32.LocalFree(buf_nt)
                return msg_nt

        # 3. Если это HRESULT вида 0x8007XXXX (Win32 Facility 7), пробуем распаковать Win32 код ошибки
        if (uint_code & 0xFFFF0000) == 0x80070000:
            win32_subcode = uint_code & 0xFFFF
            return self.format_system_error(win32_subcode, lang_id=lang_id)

        return ''

    def decode_bugcheck_code(self, code: Union[int, str]) -> Dict[str, str]:
        """Расшифровать Stop-код синего экрана (BSOD BugCheck Code).

        Args:
            code: Числовой или строковый код BugCheck (например, 209, 0xD1, '0x000000D1').

        Returns:
            Dict[str, str]: Словарь с полями 'code_hex', 'symbol', 'description_ru'.
        """
        uint_code, hex_str = self.parse_error_code(code)
        symbol = 'UNKNOWN_BUGCHECK'
        desc = 'Критический сбой ядра Windows.'

        if uint_code in BUGCHECK_CODES_MAP:
            symbol, desc = BUGCHECK_CODES_MAP[uint_code]
        else:
            # Пробуем запросить описание через ntdll
            nt_desc = self.format_system_error(uint_code)
            if nt_desc:
                desc = nt_desc

        return {
            'code_hex': hex_str,
            'code_dec': str(uint_code),
            'symbol': symbol,
            'description_ru': desc,
        }


# Глобальный синглтон декодера
_decoder_instance: Optional[WindowsErrorDecoder] = None


def get_error_decoder() -> WindowsErrorDecoder:
    """Получить глобальный экземпляр WindowsErrorDecoder."""
    global _decoder_instance
    if _decoder_instance is None:
        _decoder_instance = WindowsErrorDecoder()
    return _decoder_instance


def format_system_error(code: Union[int, str], lang_id: int = 0) -> str:
    """Удобный хелпер для форматирования системного кода ошибки."""
    return get_error_decoder().format_system_error(code, lang_id=lang_id)


def decode_bugcheck_code(code: Union[int, str]) -> Dict[str, str]:
    """Удобный хелпер для расшифровки Stop-кода ядра (BugCheck)."""
    return get_error_decoder().decode_bugcheck_code(code)


__all__ = [
    'WindowsErrorDecoder',
    'get_error_decoder',
    'format_system_error',
    'decode_bugcheck_code',
    'BUGCHECK_CODES_MAP',
]
