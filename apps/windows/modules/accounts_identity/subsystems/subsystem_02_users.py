# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Subsystem 02 Users
# =============================================================================
# Description:
#   Подсистема 02: Управление локальными и доменными пользователями
#   Windows SAM (CRUD, включение/отключение, атрибуты, парольные флаги).
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.accounts_identity.subsystems.subsystem_02_users import UsersSubsystem
#
#     subsys = UsersSubsystem()
#     users = subsys.list_users()
#
# File: subsystem_02_users.py
# Project: ai-breadboard
# Package: apps.windows.modules.accounts_identity.subsystems
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 00:50:00
# =============================================================================

"""Подсистема управления учетными записями пользователей Windows SAM."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from logger import logger
from apps.windows.modules.accounts_identity.models import AccountDetails
from apps.windows.modules.accounts_identity.win32_bridge import Win32IdentityBridge


class UsersSubsystem:
    """Подсистема операций над учетными записями пользователей."""

    def __init__(self, bridge: Optional[Win32IdentityBridge] = None) -> None:
        """
        Инициализация подсистемы пользователей.

        Args:
            bridge: Мост вызовов Windows API.
        """
        self.bridge = bridge or Win32IdentityBridge()

    def list_users(self) -> List[AccountDetails]:
        """13. Возвращает список всех локальных пользователей."""
        ps_cmd = (
            "Get-LocalUser | Select-Object Name, SID, FullName, Description, Enabled, "
            "AccountExpires, PasswordRequired, PasswordLastSet, PasswordExpires, "
            "UserMayChangePassword, PasswordNeverExpires, LastLogon"
        )
        raw_users = self.bridge.run_powershell_json(ps_cmd)
        results: List[AccountDetails] = []
        if raw_users:
            items = [raw_users] if isinstance(raw_users, dict) else raw_users
            for item in items:
                if not isinstance(item, dict):
                    continue
                sid_val = str(item.get("SID", {}).get("Value", item.get("SID", "")))
                name = item.get("Name", "")
                full_name = item.get("FullName") or ""
                description = item.get("Description") or ""
                enabled = bool(item.get("Enabled", True))
                pwd_req = bool(item.get("PasswordRequired", True))
                pwd_never = bool(item.get("PasswordNeverExpires", False))
                user_may_chg = bool(item.get("UserMayChangePassword", True))

                results.append(
                    AccountDetails(
                        name=name,
                        sid=sid_val,
                        full_name=full_name,
                        description=description,
                        enabled=enabled,
                        password_required=pwd_req,
                        password_never_expires=pwd_never,
                        cannot_change_password=not user_may_chg,
                        account_expires=str(item.get("AccountExpires")) if item.get("AccountExpires") else None,
                        password_last_set=str(item.get("PasswordLastSet")) if item.get("PasswordLastSet") else None,
                        password_expires=str(item.get("PasswordExpires")) if item.get("PasswordExpires") else None,
                        last_logon=str(item.get("LastLogon")) if item.get("LastLogon") else None,
                    )
                )

        if not results:
            # Фоллбэк через штатный net user
            _, out, _ = self.bridge.run_command(["net", "user"])
            for line in out.splitlines():
                if "---" in line or "command completed" in line.lower() or "команда выполнена" in line.lower():
                    continue
                for name in line.split():
                    if name.strip():
                        sid_info = self.bridge.lookup_name_to_sid(name)
                        sid_val = sid_info[0] if sid_info else ""
                        results.append(AccountDetails(name=name, sid=sid_val))
        return results

    def get_user_info(self, name_or_sid: str) -> Optional[AccountDetails]:
        """14, 15. Извлекает исчерпывающую информацию о пользователе."""
        users = self.list_users()
        for u in users:
            if u.name.lower() == name_or_sid.lower() or u.sid == name_or_sid:
                return u
        # Попытка поиска по SID через bridge
        sid_info = self.bridge.lookup_sid_to_name(name_or_sid) if name_or_sid.startswith("S-1-") else None
        if sid_info:
            return AccountDetails(name=sid_info[0], sid=name_or_sid)
        return None

    def get_user_sid(self, username: str) -> Optional[str]:
        """16. Возвращает строковый SID по имени пользователя."""
        info = self.bridge.lookup_name_to_sid(username)
        return info[0] if info else None

    def get_name_by_sid(self, sid_str: str) -> Optional[str]:
        """17. Возвращает имя пользователя по SID."""
        info = self.bridge.lookup_sid_to_name(sid_str)
        return info[0] if info else None

    def create_user(self, name: str, password: Optional[str] = None, full_name: str = "", description: str = "") -> bool:
        """18. Создает нового локального пользователя."""
        cmd = f"New-LocalUser -Name '{name}' -FullName '{full_name}' -Description '{description}'"
        if password:
            cmd = f"$pwd = ConvertTo-SecureString '{password}' -AsPlainText -Force; New-LocalUser -Name '{name}' -Password $pwd -FullName '{full_name}' -Description '{description}'"
        else:
            cmd += " -NoPassword"
        ret, _, _ = self.bridge.run_command(["powershell.exe", "-NoProfile", "-Command", cmd])
        return ret == 0

    def delete_user(self, name: str) -> bool:
        """19. Удаляет локального пользователя."""
        ret, _, _ = self.bridge.run_command(["powershell.exe", "-NoProfile", "-Command", f"Remove-LocalUser -Name '{name}'"])
        return ret == 0

    def enable_user(self, name: str) -> bool:
        """22. Включает учетную запись."""
        ret, _, _ = self.bridge.run_command(["powershell.exe", "-NoProfile", "-Command", f"Enable-LocalUser -Name '{name}'"])
        return ret == 0

    def disable_user(self, name: str) -> bool:
        """23. Отключает учетную запись."""
        ret, _, _ = self.bridge.run_command(["powershell.exe", "-NoProfile", "-Command", f"Disable-LocalUser -Name '{name}'"])
        return ret == 0

    def rename_user(self, old_name: str, new_name: str) -> bool:
        """21. Переименовывает учетную запись пользователя."""
        ret, _, _ = self.bridge.run_command(["powershell.exe", "-NoProfile", "-Command", f"Rename-LocalUser -Name '{old_name}' -NewName '{new_name}'"])
        return ret == 0

    def set_full_name(self, name: str, full_name: str) -> bool:
        """24. Устанавливает полное имя пользователя."""
        ret, _, _ = self.bridge.run_command(["powershell.exe", "-NoProfile", "-Command", f"Set-LocalUser -Name '{name}' -FullName '{full_name}'"])
        return ret == 0

    def set_description(self, name: str, description: str) -> bool:
        """25. Устанавливает описание учетной записи."""
        ret, _, _ = self.bridge.run_command(["powershell.exe", "-NoProfile", "-Command", f"Set-LocalUser -Name '{name}' -Description '{description}'"])
        return ret == 0

    def set_account_expiration(self, name: str, expires: Optional[str]) -> bool:
        """26. Устанавливает дату истечения учетной записи."""
        if expires:
            cmd = f"Set-LocalUser -Name '{name}' -AccountExpires (Get-Date '{expires}')"
        else:
            cmd = f"Set-LocalUser -Name '{name}' -AccountNeverExpires"
        ret, _, _ = self.bridge.run_command(["powershell.exe", "-NoProfile", "-Command", cmd])
        return ret == 0

    def set_cannot_change_password(self, name: str, cannot_change: bool) -> bool:
        """28. Запрещает или разрешает пользователю менять пароль."""
        val = "$false" if cannot_change else "$true"
        ret, _, _ = self.bridge.run_command(["powershell.exe", "-NoProfile", "-Command", f"Set-LocalUser -Name '{name}' -UserMayChangePassword {val}"])
        return ret == 0

    def set_password_never_expires(self, name: str, never_expires: bool) -> bool:
        """29. Управляет бессрочным действием пароля."""
        val = "$true" if never_expires else "$false"
        ret, _, _ = self.bridge.run_command(["powershell.exe", "-NoProfile", "-Command", f"Set-LocalUser -Name '{name}' -PasswordNeverExpires {val}"])
        return ret == 0
