# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Subsystem 01 Identity
# =============================================================================
# Description:
#   Подсистема 01: Текущий субъект, контекст безопасности, UPN, FQDN,
#   маркер доступа, группы, привилегии и Mandatory Integrity Level.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.accounts_identity.subsystems.subsystem_01_identity import IdentitySubsystem
#
#     subsys = IdentitySubsystem()
#     ctx = subsys.get_current_identity_context()
#
# File: subsystem_01_identity.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.accounts_identity.subsystems
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 00:50:00
# =============================================================================

"""Подсистема идентификации текущего пользователя и маркера доступа."""

from __future__ import annotations

import getpass
import os
import subprocess
from typing import Any, Dict, List, Optional

from logger import logger
from apps.windows.sdk.modules.accounts_identity.models import (
    GroupRef,
    IntegrityLevel,
    TokenDetails,
    TokenPrivilege,
    TokenType,
)
from apps.windows.sdk.modules.accounts_identity.win32_bridge import Win32IdentityBridge


class IdentitySubsystem:
    """Подсистема работы с текущим контекстом безопасности Windows."""

    def __init__(self, bridge: Optional[Win32IdentityBridge] = None) -> None:
        """
        Инициализирует подсистему идентификации.

        Args:
            bridge: Экземпляр Win32IdentityBridge для системных вызовов.
        """
        self.bridge = bridge or Win32IdentityBridge()

    def get_current_user(self) -> str:
        """1. Возвращает имя текущего пользователя."""
        return os.environ.get("USERNAME") or getpass.getuser()

    def get_domain_and_user(self) -> str:
        """2. Возвращает строку DOMAIN\\User."""
        name_sam = self.bridge.get_current_user_name_ex(2)
        if name_sam:
            return name_sam
        domain = os.environ.get("USERDOMAIN", "WORKGROUP")
        user = self.get_current_user()
        return f"{domain}\\{user}"

    def get_upn(self) -> Optional[str]:
        """3. Возвращает UPN (User Principal Name) текущего пользователя."""
        upn = self.bridge.get_current_user_name_ex(8)
        if upn:
            return upn
        _, out, _ = self.bridge.run_command(["whoami", "/upn"])
        if out and not out.lower().startswith("error"):
            return out
        return None

    def get_fqdn(self) -> Optional[str]:
        """4. Возвращает FQDN identity текущего пользователя."""
        fqdn = self.bridge.get_current_user_name_ex(1)
        if fqdn:
            return fqdn
        _, out, _ = self.bridge.run_command(["whoami", "/fqdn"])
        if out and not out.lower().startswith("error"):
            return out
        return None

    def get_current_user_sid(self) -> str:
        """5. Возвращает строковый SID текущего пользователя."""
        user_name = self.get_current_user()
        res = self.bridge.lookup_name_to_sid(user_name)
        if res:
            return res[0]
        # Фоллбэк через whoami /user
        _, out, _ = self.bridge.run_command(["whoami", "/user"])
        if out:
            lines = [l.strip() for l in out.splitlines() if l.strip() and "S-1-" in l]
            if lines:
                parts = lines[-1].split()
                if len(parts) >= 2:
                    return parts[-1]
        return "S-1-5-21-0-0-0-1000"

    def get_logon_id(self) -> str:
        """6. Возвращает Logon ID (LUID) сеанса входа."""
        _, out, _ = self.bridge.run_command(["whoami", "/logonid"])
        if out:
            lines = [l.strip() for l in out.splitlines() if "0x" in l]
            if lines:
                return lines[0].split()[-1]
        return "0x0"

    def get_current_user_groups(self) -> List[GroupRef]:
        """7. Возвращает группы из токена текущего пользователя."""
        groups: List[GroupRef] = []
        ps_script = "Get-CimInstance Win32_GroupUser | Where-Object { $_.PartComponent -match ('\"' + $env:USERNAME + '\"') } | ForEach-Object { [regex]::match($_.GroupComponent, 'Name=\"([^\"]+)\"').Groups[1].Value }"
        res = self.bridge.run_powershell_json(ps_script)
        if res:
            names = [res] if isinstance(res, str) else res
            for g_name in names:
                if isinstance(g_name, str) and g_name.strip():
                    is_adm = g_name.lower() in ("administrators", "администраторы")
                    sid_info = self.bridge.lookup_name_to_sid(g_name)
                    sid_val = sid_info[0] if sid_info else ""
                    groups.append(GroupRef(name=g_name, sid=sid_val, is_admin=is_adm, is_local=True))
        if not groups:
            # Парсинг whoami /groups
            _, out, _ = self.bridge.run_command(["whoami", "/groups"])
            for line in out.splitlines():
                if "S-1-" in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        g_name = parts[0]
                        g_sid = parts[1]
                        is_adm = "Admin" in g_name or g_sid.endswith("-544")
                        groups.append(GroupRef(name=g_name, sid=g_sid, is_admin=is_adm, is_local=True))
        return groups

    def get_current_user_privileges(self) -> List[TokenPrivilege]:
        """8. Возвращает привилегии токена текущего пользователя."""
        privileges: List[TokenPrivilege] = []
        _, out, _ = self.bridge.run_command(["whoami", "/priv"])
        sensitive = {
            "SeDebugPrivilege", "SeTakeOwnershipPrivilege", "SeImpersonatePrivilege",
            "SeBackupPrivilege", "SeRestorePrivilege", "SeTcbPrivilege", "SeLoadDriverPrivilege"
        }
        for line in out.splitlines():
            if line.startswith("Se") and "Privilege" in line:
                parts = line.split()
                if len(parts) >= 2:
                    p_name = parts[0]
                    p_state = parts[-1].lower() == "enabled"
                    privileges.append(
                        TokenPrivilege(
                            name=p_name,
                            enabled=p_state,
                            is_sensitive=p_name in sensitive
                        )
                    )
        return privileges

    def get_current_user_claims(self) -> List[Dict[str, Any]]:
        """9. Возвращает security claims токена."""
        _, out, _ = self.bridge.run_command(["whoami", "/claims"])
        claims: List[Dict[str, Any]] = []
        for line in out.splitlines():
            line = line.strip()
            if line and not line.startswith("=") and not line.lower().startswith("claim"):
                claims.append({"claim_raw": line})
        return claims

    def get_integrity_level(self) -> IntegrityLevel:
        """12. Определяет Mandatory Integrity Level текущего процесса."""
        _, out, _ = self.bridge.run_command(["whoami", "/groups"])
        out_lower = out.lower()
        if "high mandatory level" in out_lower:
            return IntegrityLevel.HIGH
        if "system mandatory level" in out_lower:
            return IntegrityLevel.SYSTEM
        if "medium mandatory level" in out_lower:
            return IntegrityLevel.MEDIUM
        if "low mandatory level" in out_lower:
            return IntegrityLevel.LOW
        if "untrusted mandatory level" in out_lower:
            return IntegrityLevel.UNTRUSTED
        # Проверка админских прав
        if self.bridge.is_current_process_admin():
            return IntegrityLevel.HIGH
        return IntegrityLevel.MEDIUM

    def check_token_membership(self, group_name_or_sid: str) -> bool:
        """11. Проверяет членство текущего токена в указанной группе."""
        if group_name_or_sid.lower() in ("administrators", "s-1-5-32-544"):
            return self.bridge.is_current_process_admin()
        groups = self.get_current_user_groups()
        for g in groups:
            if g.name.lower() == group_name_or_sid.lower() or g.sid == group_name_or_sid:
                return True
        return False

    def get_current_identity_context(self) -> TokenDetails:
        """10. Формирует полный контекст маркера доступа текущего процесса."""
        pid = os.getpid()
        user_name = self.get_current_user()
        domain = os.environ.get("USERDOMAIN", "WORKGROUP")
        user_sid = self.get_current_user_sid()
        integrity = self.get_integrity_level()
        is_elevated = self.bridge.is_current_process_admin()
        groups = self.get_current_user_groups()
        privileges = self.get_current_user_privileges()
        logon_sid = self.get_logon_id()

        return TokenDetails(
            pid=pid,
            process_name="python.exe",
            user_name=user_name,
            user_sid=user_sid,
            domain=domain,
            integrity_level=integrity,
            is_elevated=is_elevated,
            token_type=TokenType.PRIMARY,
            session_id=1,
            logon_sid=logon_sid,
            groups=groups,
            privileges=privileges,
        )
