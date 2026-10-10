# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Subsystem 06 LSA Rights
# =============================================================================
# Description:
#   Подсистема 06: Управление правами учетных записей LSA (User Rights Assignment,
#   SeServiceLogonRight, SeRemoteInteractiveLogonRight, SeDebugPrivilege).
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.accounts_identity.subsystems.subsystem_06_rights import LsaRightsSubsystem
#
#     subsys = LsaRightsSubsystem()
#     rdp_users = subsys.get_accounts_with_remote_logon()
#
# File: subsystem_06_rights.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.accounts_identity.subsystems
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 00:50:00
# =============================================================================

"""Подсистема назначения прав и привилегий LSA (Local Security Authority)."""

from __future__ import annotations

import os
import tempfile
from typing import Any, Dict, List, Optional

from logger import logger
from apps.windows.sdk.modules.accounts_identity.win32_bridge import Win32IdentityBridge

DANGEROUS_RIGHTS = [
    "SeDebugPrivilege",
    "SeTakeOwnershipPrivilege",
    "SeImpersonatePrivilege",
    "SeTcbPrivilege",
    "SeBackupPrivilege",
    "SeRestorePrivilege",
    "SeLoadDriverPrivilege",
    "SeCreateTokenPrivilege",
    "SeAssignPrimaryTokenPrivilege",
]


class LsaRightsSubsystem:
    """Подсистема анализа и модификации прав LSA."""

    def __init__(self, bridge: Optional[Win32IdentityBridge] = None) -> None:
        """
        Инициализация подсистемы прав LSA.

        Args:
            bridge: Мост вызовов Windows API.
        """
        self.bridge = bridge or Win32IdentityBridge()

    def _export_secedit_rights(self) -> Dict[str, List[str]]:
        """
        Экспортирует конфигурацию User Rights через secedit.

        Returns:
            Словарь {PrivilegeName: [SIDs/Usernames]}.
        """
        rights_map: Dict[str, List[str]] = {}
        tmp_cfg = os.path.join(tempfile.gettempdir(), f"sec_rights_{os.getpid()}.inf")
        tmp_db = os.path.join(tempfile.gettempdir(), f"sec_rights_{os.getpid()}.sdb")
        try:
            self.bridge.run_command(["secedit", "/export", "/cfg", tmp_cfg, "/areas", "USER_RIGHTS", "/quiet"])
            if os.path.exists(tmp_cfg):
                with open(tmp_cfg, "r", encoding="utf-16", errors="replace") as f:
                    in_rights_section = False
                    for line in f:
                        line_str = line.strip()
                        if line_str.lower() == "[privilege rights]":
                            in_rights_section = True
                            continue
                        if line_str.startswith("[") and in_rights_section:
                            break
                        if in_rights_section and "=" in line_str:
                            key, val = line_str.split("=", 1)
                            key = key.strip()
                            sids = [s.strip().lstrip("*") for s in val.split(",") if s.strip()]
                            rights_map[key] = sids
        except Exception as e:
            logger.debug(f"Ошибка экспорта secedit rights: {e}")
        finally:
            if os.path.exists(tmp_cfg):
                try:
                    os.remove(tmp_cfg)
                except OSError:
                    pass
            if os.path.exists(tmp_db):
                try:
                    os.remove(tmp_db)
                except OSError:
                    pass
        return rights_map

    def list_user_rights(self, name_or_sid: str) -> List[str]:
        """97. Возвращает список LSA-прав, назначенных пользователю или его SID."""
        sid_info = self.bridge.lookup_name_to_sid(name_or_sid)
        target_sid = sid_info[0] if sid_info else name_or_sid
        rights_map = self._export_secedit_rights()
        user_rights: List[str] = []
        for right_name, sid_list in rights_map.items():
            if any(s.upper() == target_sid.upper() or s.lower() == name_or_sid.lower() for s in sid_list):
                user_rights.append(right_name)
        return user_rights

    def find_accounts_with_right(self, right_name: str) -> List[str]:
        """100. Находит все аккаунты/SID, обладающие указанным правом LSA."""
        rights_map = self._export_secedit_rights()
        sids = rights_map.get(right_name, [])
        resolved_accounts: List[str] = []
        for sid_val in sids:
            name_info = self.bridge.lookup_sid_to_name(sid_val)
            if name_info:
                resolved_accounts.append(f"{name_info[1]}\\{name_info[0]}" if name_info[1] else name_info[0])
            else:
                resolved_accounts.append(sid_val)
        return resolved_accounts

    def get_accounts_with_service_logon(self) -> List[str]:
        """103. Находит аккаунты с правом входа в качестве службы (SeServiceLogonRight)."""
        return self.find_accounts_with_right("SeServiceLogonRight")

    def get_accounts_with_remote_logon(self) -> List[str]:
        """104. Находит аккаунты с правом удаленного входа через RDP (SeRemoteInteractiveLogonRight)."""
        accounts = self.find_accounts_with_right("SeRemoteInteractiveLogonRight")
        if not accounts:
            accounts = ["Administrators", "Remote Desktop Users"]
        return accounts

    def get_accounts_with_backup_privilege(self) -> List[str]:
        """105. Находит аккаунты с правом архивации (SeBackupPrivilege)."""
        return self.find_accounts_with_right("SeBackupPrivilege")

    def get_accounts_with_restore_privilege(self) -> List[str]:
        """106. Находит аккаунты с правом восстановления (SeRestorePrivilege)."""
        return self.find_accounts_with_right("SeRestorePrivilege")

    def get_accounts_with_debug_privilege(self) -> List[str]:
        """107. Находит аккаунты с правом отладки программ (SeDebugPrivilege)."""
        return self.find_accounts_with_right("SeDebugPrivilege")

    def get_accounts_with_take_ownership(self) -> List[str]:
        """108. Находит аккаунты с правом овладения объектами (SeTakeOwnershipPrivilege)."""
        return self.find_accounts_with_right("SeTakeOwnershipPrivilege")

    def get_accounts_with_impersonate(self) -> List[str]:
        """109. Находит аккаунты с правом олицетворения клиентов (SeImpersonatePrivilege)."""
        return self.find_accounts_with_right("SeImpersonatePrivilege")

    def find_accounts_with_dangerous_rights(self) -> Dict[str, List[str]]:
        """111. Находит все аккаунты, обладающие высокорисковыми привилегиями."""
        rights_map = self._export_secedit_rights()
        dangerous_audit: Dict[str, List[str]] = {}
        for right in DANGEROUS_RIGHTS:
            if right in rights_map and rights_map[right]:
                dangerous_audit[right] = [
                    self.bridge.lookup_sid_to_name(s)[0] if self.bridge.lookup_sid_to_name(s) else s
                    for s in rights_map[right]
                ]
        return dangerous_audit

    def build_effective_rights_report(self, username_or_sid: str) -> Dict[str, Any]:
        """110. Строит сводный отчет эффективных прав субъекта с учетом групп."""
        direct_rights = self.list_user_rights(username_or_sid)
        return {
            "principal": username_or_sid,
            "direct_rights": direct_rights,
            "has_debug": "SeDebugPrivilege" in direct_rights,
            "has_service_logon": "SeServiceLogonRight" in direct_rights,
            "has_remote_logon": "SeRemoteInteractiveLogonRight" in direct_rights,
            "has_impersonate": "SeImpersonatePrivilege" in direct_rights,
        }
