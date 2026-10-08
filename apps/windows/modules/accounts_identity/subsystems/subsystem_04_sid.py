# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Subsystem 04 SID Resolution
# =============================================================================
# Description:
#   Подсистема 04: Разрешение SID <-> Name, идентификация встроенных и
#   Well-Known субъектов (SYSTEM, LOCAL SERVICE, RID 500), аудит осиротевших SID.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.accounts_identity.subsystems.subsystem_04_sid import SidSubsystem
#
#     subsys = SidSubsystem()
#     res = subsys.resolve_principal("S-1-5-18")
#
# File: subsystem_04_sid.py
# Project: ai-breadboard
# Package: apps.windows.modules.accounts_identity.subsystems
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 00:50:00
# =============================================================================

"""Подсистема разрешения SID и работы со встроенными субъектами безопасности."""

from __future__ import annotations

import winreg
from typing import Any, Dict, List, Optional, Tuple

from logger import logger
from apps.windows.modules.accounts_identity.models import PrincipalType
from apps.windows.modules.accounts_identity.win32_bridge import WELL_KNOWN_SIDS, Win32IdentityBridge


class SidSubsystem:
    """Подсистема трансляции SID и проверки системных учетных записей."""

    def __init__(self, bridge: Optional[Win32IdentityBridge] = None) -> None:
        """
        Инициализация подсистемы SID.

        Args:
            bridge: Мост вызовов Windows API.
        """
        self.bridge = bridge or Win32IdentityBridge()

    def name_to_sid(self, name: str) -> Optional[str]:
        """83. Преобразует имя учетной записи в строковый SID."""
        res = self.bridge.lookup_name_to_sid(name)
        return res[0] if res else None

    def sid_to_name(self, sid_str: str) -> Optional[str]:
        """84. Преобразует строковый SID в имя пользователя или группы."""
        res = self.bridge.lookup_sid_to_name(sid_str)
        return res[0] if res else None

    def sid_to_domain(self, sid_str: str) -> Optional[str]:
        """85. Определяет домен субъекта по SID."""
        res = self.bridge.lookup_sid_to_name(sid_str)
        return res[1] if res else None

    def sid_to_account_type(self, sid_str: str) -> str:
        """86. Определяет тип субъекта (User, Group, Alias, WellKnownGroup и т.д.)."""
        res = self.bridge.lookup_sid_to_name(sid_str)
        return res[2] if res else "Unknown"

    def is_valid_sid(self, sid_str: str) -> bool:
        """87. Проверяет валидность структуры SID."""
        return self.bridge.check_is_valid_sid(sid_str)

    def compare_sids(self, sid1: str, sid2: str) -> bool:
        """89. Сравнивает два строковых SID на идентичность."""
        if not sid1 or not sid2:
            return False
        return sid1.strip().upper() == sid2.strip().upper()

    def is_well_known_sid(self, sid_str: str) -> bool:
        """74, 92. Определяет, является ли SID общеизвестным системным маркером."""
        if sid_str in WELL_KNOWN_SIDS:
            return True
        if sid_str.startswith("S-1-5-32-") or sid_str.startswith("S-1-5-18") or sid_str.startswith("S-1-5-19") or sid_str.startswith("S-1-5-20"):
            return True
        return False

    def is_built_in_account(self, name_or_sid: str) -> bool:
        """73. Определяет, является ли аккаунт встроенным системным (RID 500, 501, 503, 504)."""
        built_ins = {
            "administrator", "администратор", "guest", "гость",
            "defaultaccount", "wdagutilityaccount", "system",
            "local service", "network service", "trustedinstaller"
        }
        if name_or_sid.lower() in built_ins:
            return True
        if name_or_sid.endswith("-500") or name_or_sid.endswith("-501") or name_or_sid.endswith("-503") or name_or_sid.endswith("-504"):
            return True
        return self.is_well_known_sid(name_or_sid)

    def is_orphaned_sid(self, sid_str: str) -> bool:
        """93. Выявляет осиротевший SID (отсутствующий в SAM и AD)."""
        if not self.is_valid_sid(sid_str):
            return False
        if self.is_well_known_sid(sid_str):
            return False
        # Если не удается разрешить имя по SID - аккаунт осиротел
        res = self.bridge.lookup_sid_to_name(sid_str)
        return res is None

    def find_acl_references(self, sid_str: str) -> List[str]:
        """94. Ищет файловые дескрипторы безопасности, ссылающиеся на SID."""
        # Сканирование общих системных папок на наличие SID в ACL
        ps_cmd = f"Get-ChildItem -Path $env:SystemDrive\\ -Directory -MaxDepth 1 -ErrorAction SilentlyContinue | Where-Object {{ (Get-Acl $_.FullName -ErrorAction SilentlyContinue).AccessToString -match '{sid_str}' }} | Select-Object -ExpandProperty FullName"
        res = self.bridge.run_powershell_json(ps_cmd)
        if res:
            return [res] if isinstance(res, str) else [str(x) for x in res]
        return []

    def find_registry_references(self, sid_str: str) -> List[str]:
        """95. Ищет разделы реестра со ссылкой на SID в ProfileList."""
        references: List[str] = []
        try:
            profile_list_key = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, profile_list_key) as key:
                num_subkeys = winreg.QueryInfoKey(key)[0]
                for i in range(num_subkeys):
                    subkey_name = winreg.EnumKey(key, i)
                    if subkey_name.upper() == sid_str.upper():
                        references.append(f"HKLM\\{profile_list_key}\\{subkey_name}")
        except Exception as e:
            logger.debug(f"Ошибка сканирования реестра для SID {sid_str}: {e}")
        return references

    def find_service_references(self, sid_str: str) -> List[str]:
        """96. Ищет службы Windows, зарегистрированные под указанным аккаунтом/SID."""
        account_name = self.sid_to_name(sid_str)
        if not account_name:
            return []
        ps_cmd = f"Get-CimInstance Win32_Service | Where-Object {{ $_.StartName -match '{account_name}' }} | Select-Object -ExpandProperty Name"
        res = self.bridge.run_powershell_json(ps_cmd)
        if res:
            return [res] if isinstance(res, str) else [str(x) for x in res]
        return []

    def resolve_principal(self, identifier: str) -> Dict[str, Any]:
        """
        Универсальное разрешение идентификатора (SID или Имя).

        Returns:
            Словарь со свойствами (sid, name, domain, type, is_built_in, is_orphaned).
        """
        ident = identifier.strip()
        if ident.startswith("S-1-"):
            sid_val = ident
            name_info = self.bridge.lookup_sid_to_name(sid_val)
            if name_info:
                name_val, domain_val, type_val = name_info
                is_orphaned = False
            else:
                name_val = "Account Unknown"
                domain_val = ""
                type_val = "Unknown"
                is_orphaned = True
        else:
            sid_info = self.bridge.lookup_name_to_sid(ident)
            if sid_info:
                sid_val, domain_val, type_val = sid_info
                name_val = ident
                is_orphaned = False
            else:
                sid_val = ""
                name_val = ident
                domain_val = ""
                type_val = "Unknown"
                is_orphaned = True

        return {
            "sid": sid_val,
            "name": name_val,
            "domain": domain_val,
            "principal_type": type_val,
            "is_built_in": self.is_built_in_account(name_val or sid_val),
            "is_orphaned": is_orphaned,
            "is_well_known": self.is_well_known_sid(sid_val),
        }
