# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Subsystem Domain & Directory
# =============================================================================
# Description:
#   Подсистема доменной и облачной идентификации: Active Directory, Entra ID (AAD),
#   DsRole, членство в домене или рабочей группе, роль машины.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.accounts_identity.subsystems.subsystem_domain import DomainSubsystem
#
#     subsys = DomainSubsystem()
#     info = subsys.get_domain_info()
#
# File: subsystem_domain.py
# Project: ai-breadboard
# Package: apps.windows.modules.accounts_identity.subsystems
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 00:50:00
# =============================================================================

"""Подсистема информации о домене, Active Directory и Entra ID."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from logger import logger
from apps.windows.modules.accounts_identity.models import DomainInfo, MachineRole
from apps.windows.modules.accounts_identity.win32_bridge import Win32IdentityBridge


class DomainSubsystem:
    """Подсистема получения информации о доменном контексте рабочей станции/сервера."""

    def __init__(self, bridge: Optional[Win32IdentityBridge] = None) -> None:
        """
        Инициализация подсистемы домена.

        Args:
            bridge: Мост вызовов Windows API.
        """
        self.bridge = bridge or Win32IdentityBridge()

    def get_domain_info(self) -> DomainInfo:
        """155-166. Считывает исчерпывающую информацию о доменном и Entra ID статусе."""
        ps_cmd = "Get-CimInstance Win32_ComputerSystem | Select-Object Name, Domain, PartOfDomain, DomainRole, Workgroup"
        res = self.bridge.run_powershell_json(ps_cmd)
        computer_name = os.environ.get("COMPUTERNAME", "LOCALHOST")
        domain_name = ""
        workgroup = "WORKGROUP"
        part_of_domain = False
        machine_role = MachineRole.STANDALONE_WORKSTATION

        if res and isinstance(res, dict):
            computer_name = str(res.get("Name") or computer_name)
            domain_name = str(res.get("Domain") or "")
            workgroup = str(res.get("Workgroup") or "WORKGROUP")
            part_of_domain = bool(res.get("PartOfDomain", False))
            role_id = res.get("DomainRole", 0)
            role_map = {
                0: MachineRole.STANDALONE_WORKSTATION,
                1: MachineRole.MEMBER_WORKSTATION,
                2: MachineRole.STANDALONE_SERVER,
                3: MachineRole.MEMBER_SERVER,
                4: MachineRole.BACKUP_DOMAIN_CONTROLLER,
                5: MachineRole.PRIMARY_DOMAIN_CONTROLLER,
            }
            machine_role = role_map.get(role_id, MachineRole.STANDALONE_WORKSTATION)

        # Проверка Entra ID (dsregcmd /status)
        is_entra = self._check_entra_joined()

        return DomainInfo(
            domain_name=domain_name,
            dns_domain=domain_name if part_of_domain else "",
            forest_name=domain_name if part_of_domain else "",
            domain_guid="",
            machine_role=machine_role,
            workgroup=workgroup if not part_of_domain else "",
            is_domain_joined=part_of_domain,
            is_entra_joined=is_entra,
            computer_name=computer_name,
        )

    def _check_entra_joined(self) -> bool:
        """165. Проверяет регистрацию в Azure Active Directory / Microsoft Entra."""
        _, out, _ = self.bridge.run_command(["dsregcmd", "/status"])
        for line in out.splitlines():
            line_str = line.strip()
            if "AzureAdJoined" in line_str and "YES" in line_str.upper():
                return True
            if "EnterpriseJoined" in line_str and "YES" in line_str.upper():
                return True
        return False
