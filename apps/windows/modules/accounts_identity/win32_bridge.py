# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Accounts & Identity Win32 Bridge
# =============================================================================
# Description:
#   Низкоуровневый мост взаимодействия с Windows API (Advapi32, Netapi32,
#   LSA, Wtsapi32, Userenv, Secur32, Dsrole) и безопасными фоллбэками.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.accounts_identity.win32_bridge import Win32IdentityBridge
#
#     bridge = Win32IdentityBridge()
#     sid_str = bridge.lookup_name_to_sid("Administrator")
#
# File: win32_bridge.py
# Project: ai-breadboard
# Package: apps.windows.modules.accounts_identity
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 00:49:00
# =============================================================================

"""Низкоуровневый Win32/NetAPI/LSA мост для Accounts & Identity."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import json
import os
import platform
import subprocess
from typing import Any, Dict, List, Optional, Tuple

from logger import logger

# Константы WinAPI и SID типов
SID_NAME_USE_MAP = {
    1: "User",
    2: "Group",
    3: "Domain",
    4: "Alias",
    5: "WellKnownGroup",
    6: "DeletedAccount",
    7: "Invalid",
    8: "Unknown",
    9: "Computer",
    10: "Label",
}

# Известные стандартные SID
WELL_KNOWN_SIDS: Dict[str, str] = {
    "S-1-0-0": "Nobody",
    "S-1-1-0": "Everyone",
    "S-1-2-0": "Local",
    "S-1-3-0": "Creator Owner",
    "S-1-3-1": "Creator Group",
    "S-1-5-18": "SYSTEM",
    "S-1-5-19": "LOCAL SERVICE",
    "S-1-5-20": "NETWORK SERVICE",
    "S-1-5-32-544": "Administrators",
    "S-1-5-32-545": "Users",
    "S-1-5-32-546": "Guests",
    "S-1-5-32-555": "Remote Desktop Users",
    "S-1-5-32-558": "Performance Monitor Users",
    "S-1-5-32-559": "Performance Log Users",
    "S-1-5-32-573": "Event Log Readers",
    "S-1-15-2-1": "ALL APPLICATION PACKAGES",
    "S-1-15-2-2": "ALL RESTRICTED APPLICATION PACKAGES",
}


class Win32IdentityBridge:
    """Обертка над системными DLL Windows для операций идентификации."""

    def __init__(self) -> None:
        """Инициализация библиотек и привязка API сигнатур."""
        self._is_windows = platform.system().lower() == "windows"
        self._advapi32: Optional[ctypes.WinDLL] = None
        self._netapi32: Optional[ctypes.WinDLL] = None
        self._wtsapi32: Optional[ctypes.WinDLL] = None
        self._userenv: Optional[ctypes.WinDLL] = None
        self._secur32: Optional[ctypes.WinDLL] = None
        self._dsrole: Optional[ctypes.WinDLL] = None

        if self._is_windows:
            self._load_dlls()

    def _load_dlls(self) -> None:
        """Загрузка системных DLL."""
        try:
            self._advapi32 = ctypes.windll.advapi32
            self._netapi32 = ctypes.windll.netapi32
            self._wtsapi32 = ctypes.windll.wtsapi32
            self._userenv = ctypes.windll.userenv
            self._secur32 = ctypes.windll.secur32
            self._dsrole = ctypes.windll.dsrole
        except Exception as e:
            logger.debug(f"Некоторые системные DLL недоступны: {e}")

    def run_powershell_json(self, script: str) -> Any:
        """
        Выполняет фрагмент PowerShell с преобразованием результата в JSON.

        Args:
            script: Команда или блок команд PowerShell.

        Returns:
            Распарсенный JSON или None при ошибке.
        """
        if not self._is_windows:
            return None
        try:
            full_cmd = f"& {{ {script} }} | ConvertTo-Json -Depth 5 -Compress"
            proc = subprocess.run(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", full_cmd],
                capture_output=True,
                text=True,
                timeout=12,
                encoding="utf-8",
                errors="replace"
            )
            stdout = proc.stdout.strip()
            if stdout:
                return json.loads(stdout)
            return None
        except Exception as e:
            logger.debug(f"Ошибка выполнения PowerShell script: {e}")
            return None

    def run_command(self, cmd_list: List[str]) -> Tuple[int, str, str]:
        """
        Выполняет штатную команду CLI.

        Args:
            cmd_list: Список аргументов команды.

        Returns:
            Кортеж (returncode, stdout, stderr).
        """
        try:
            proc = subprocess.run(
                cmd_list,
                capture_output=True,
                text=True,
                timeout=10,
                encoding="utf-8",
                errors="replace"
            )
            return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
        except Exception as e:
            logger.debug(f"Ошибка выполнения CLI команды {cmd_list}: {e}")
            return -1, "", str(e)

    def lookup_name_to_sid(self, name: str, system_name: Optional[str] = None) -> Optional[Tuple[str, str, str]]:
        """
        Транслирует имя аккаунта в SID, имя домена и тип сущности.

        Args:
            name: Имя учетной записи или группы.
            system_name: Имя хоста или None для локального.

        Returns:
            Кортеж (sid_str, domain_name, sid_type) или None.
        """
        if not self._is_windows or not self._advapi32:
            return None

        try:
            sid_size = wintypes.DWORD(0)
            domain_size = wintypes.DWORD(0)
            sid_type = wintypes.DWORD(0)

            # Первый вызов для определения размеров буферов
            self._advapi32.LookupAccountNameW(
                system_name,
                name,
                None,
                ctypes.byref(sid_size),
                None,
                ctypes.byref(domain_size),
                ctypes.byref(sid_type)
            )

            if sid_size.value == 0:
                # Фоллбэк через PowerShell
                res = self.run_powershell_json(f"(New-Object System.Security.Principal.NTAccount('{name}')).Translate([System.Security.Principal.SecurityIdentifier]).Value")
                if res and isinstance(res, str):
                    return res, "", "User"
                return None

            sid_buf = ctypes.create_string_buffer(sid_size.value)
            domain_buf = ctypes.create_unicode_buffer(domain_size.value)

            if self._advapi32.LookupAccountNameW(
                system_name,
                name,
                sid_buf,
                ctypes.byref(sid_size),
                domain_buf,
                ctypes.byref(domain_size),
                ctypes.byref(sid_type)
            ):
                sid_str_ptr = wintypes.LPWSTR()
                if self._advapi32.ConvertSidToStringSidW(sid_buf, ctypes.byref(sid_str_ptr)):
                    sid_str = sid_str_ptr.value
                    ctypes.windll.kernel32.LocalFree(sid_str_ptr)
                    type_label = SID_NAME_USE_MAP.get(sid_type.value, "Unknown")
                    return sid_str, domain_buf.value, type_label
        except Exception as e:
            logger.debug(f"Исключение при LookupAccountNameW: {e}")

        return None

    def lookup_sid_to_name(self, sid_str: str, system_name: Optional[str] = None) -> Optional[Tuple[str, str, str]]:
        """
        Транслирует строковый SID в имя аккаунта, домен и тип сущности.

        Args:
            sid_str: Строковый SID (S-1-...).
            system_name: Имя хоста.

        Returns:
            Кортеж (name, domain, sid_type) или None.
        """
        if sid_str in WELL_KNOWN_SIDS:
            return WELL_KNOWN_SIDS[sid_str], "NT AUTHORITY", "WellKnownGroup"

        if not self._is_windows or not self._advapi32:
            return None

        try:
            sid_ptr = wintypes.LPVOID()
            if not self._advapi32.ConvertStringSidToSidW(sid_str, ctypes.byref(sid_ptr)):
                return None

            name_size = wintypes.DWORD(0)
            domain_size = wintypes.DWORD(0)
            sid_type = wintypes.DWORD(0)

            self._advapi32.LookupAccountSidW(
                system_name,
                sid_ptr,
                None,
                ctypes.byref(name_size),
                None,
                ctypes.byref(domain_size),
                ctypes.byref(sid_type)
            )

            if name_size.value == 0:
                ctypes.windll.kernel32.LocalFree(sid_ptr)
                return None

            name_buf = ctypes.create_unicode_buffer(name_size.value)
            domain_buf = ctypes.create_unicode_buffer(domain_size.value)

            success = self._advapi32.LookupAccountSidW(
                system_name,
                sid_ptr,
                name_buf,
                ctypes.byref(name_size),
                domain_buf,
                ctypes.byref(domain_size),
                ctypes.byref(sid_type)
            )
            ctypes.windll.kernel32.LocalFree(sid_ptr)

            if success:
                type_label = SID_NAME_USE_MAP.get(sid_type.value, "Unknown")
                return name_buf.value, domain_buf.value, type_label
        except Exception as e:
            logger.debug(f"Исключение при LookupAccountSidW: {e}")

        # Фоллбэк через PowerShell
        res = self.run_powershell_json(f"(New-Object System.Security.Principal.SecurityIdentifier('{sid_str}')).Translate([System.Security.Principal.NTAccount]).Value")
        if res and isinstance(res, str):
            parts = res.split("\\", 1)
            if len(parts) == 2:
                return parts[1], parts[0], "User"
            return res, "", "User"

        return None

    def get_current_user_name_ex(self, format_type: int = 2) -> Optional[str]:
        """
        Получает расширенное имя текущего пользователя через GetUserNameExW.

        Args:
            format_type: 2=NameSamCompatible, 3=NameDisplay, 8=NameUserPrincipal, 1=NameFullyQualifiedDN.

        Returns:
            Строка с именем или None.
        """
        if not self._is_windows or not self._secur32:
            return None
        try:
            buf_size = wintypes.ULONG(256)
            buf = ctypes.create_unicode_buffer(256)
            # 2 = NameSamCompatible
            if self._secur32.GetUserNameExW(format_type, buf, ctypes.byref(buf_size)):
                return buf.value
        except Exception as e:
            logger.debug(f"Ошибка GetUserNameExW ({format_type}): {e}")
        return None

    def check_is_valid_sid(self, sid_str: str) -> bool:
        """
        Проверяет валидность структуры строкового SID.

        Args:
            sid_str: Строка вида S-1-5-...

        Returns:
            True если SID валиден.
        """
        if not sid_str or not sid_str.startswith("S-1-"):
            return False
        if not self._is_windows or not self._advapi32:
            parts = sid_str.split("-")
            return len(parts) >= 3 and parts[0] == "S" and parts[1] == "1"
        try:
            sid_ptr = wintypes.LPVOID()
            if self._advapi32.ConvertStringSidToSidW(sid_str, ctypes.byref(sid_ptr)):
                is_valid = bool(self._advapi32.IsValidSid(sid_ptr))
                ctypes.windll.kernel32.LocalFree(sid_ptr)
                return is_valid
        except Exception:
            pass
        return False

    def is_current_process_admin(self) -> bool:
        """Проверяет запуск текущего процесса с правами Администратора."""
        if not self._is_windows:
            return False
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False
