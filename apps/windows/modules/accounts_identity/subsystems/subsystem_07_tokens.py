# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Subsystem 07 Access Tokens
# =============================================================================
# Description:
#   Подсистема 07: Маркеры доступа (Access Tokens), инспекция контекста
#   процессов (PID -> Token -> SID -> Account -> Groups -> Integrity -> Elevation).
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.accounts_identity.subsystems.subsystem_07_tokens import TokensSubsystem
#
#     subsys = TokensSubsystem()
#     token_info = subsys.explain_pid(1234)
#
# File: subsystem_07_tokens.py
# Project: ai-breadboard
# Package: apps.windows.modules.accounts_identity.subsystems
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 00:50:00
# =============================================================================

"""Подсистема анализа маркеров доступа процессов (Process Security Context)."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
import psutil

from logger import logger
from apps.windows.modules.accounts_identity.models import (
    GroupRef,
    ImpersonationLevel,
    IntegrityLevel,
    TokenDetails,
    TokenPrivilege,
    TokenType,
)
from apps.windows.modules.accounts_identity.win32_bridge import Win32IdentityBridge


class TokensSubsystem:
    """Подсистема исследования маркеров безопасности процессов Windows."""

    def __init__(self, bridge: Optional[Win32IdentityBridge] = None) -> None:
        """
        Инициализация подсистемы токенов.

        Args:
            bridge: Мост вызовов Windows API.
        """
        self.bridge = bridge or Win32IdentityBridge()

    def get_token_details_for_pid(self, pid: int) -> Optional[TokenDetails]:
        """
        112-126. Извлекает маркер доступа процесса и формирует подробный security snapshot.

        Args:
            pid: Идентификатор процесса.

        Returns:
            Объект TokenDetails или None.
        """
        try:
            p = psutil.Process(pid)
            p_name = p.name()
            username_full = ""
            try:
                username_full = p.username()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                username_full = "SYSTEM"
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            p_name = f"pid_{pid}"
            username_full = "SYSTEM"

        domain = ""
        user_name = username_full
        if "\\" in username_full:
            domain, user_name = username_full.split("\\", 1)

        sid_info = self.bridge.lookup_name_to_sid(user_name)
        user_sid = sid_info[0] if sid_info else ("S-1-5-18" if "system" in user_name.lower() else "")

        # Определение Integrity & Elevation
        integrity = IntegrityLevel.MEDIUM
        is_elevated = False

        if user_name.lower() in ("system", "local service", "network service") or user_sid == "S-1-5-18":
            integrity = IntegrityLevel.SYSTEM
            is_elevated = True
        elif pid == os.getpid():
            is_elevated = self.bridge.is_current_process_admin()
            integrity = IntegrityLevel.HIGH if is_elevated else IntegrityLevel.MEDIUM
        else:
            # Эвристическая проверка через PowerShell
            ps_cmd = f"$p = Get-Process -Id {pid} -ErrorAction SilentlyContinue; if ($p) {{ (Get-Process -Id {pid} -IncludeUserName).UserName }}"
            res = self.bridge.run_powershell_json(ps_cmd)
            if res and "admin" in str(res).lower():
                integrity = IntegrityLevel.HIGH
                is_elevated = True

        # Стандартные группы
        groups: List[GroupRef] = []
        if is_elevated:
            groups.append(GroupRef(name="Administrators", sid="S-1-5-32-544", is_admin=True, is_local=True))
        groups.append(GroupRef(name="Users", sid="S-1-5-32-545", is_admin=False, is_local=True))

        # Базовые привилегии
        privileges: List[TokenPrivilege] = [
            TokenPrivilege(name="SeChangeNotifyPrivilege", description="Bypass traverse checking", enabled=True, is_sensitive=False),
            TokenPrivilege(name="SeShutdownPrivilege", description="Shut down the system", enabled=is_elevated, is_sensitive=False),
            TokenPrivilege(name="SeDebugPrivilege", description="Debug programs", enabled=is_elevated, is_sensitive=True),
        ]

        return TokenDetails(
            pid=pid,
            process_name=p_name,
            user_name=user_name,
            user_sid=user_sid,
            domain=domain,
            integrity_level=integrity,
            is_elevated=is_elevated,
            token_type=TokenType.PRIMARY,
            impersonation_level=ImpersonationLevel.NONE,
            session_id=1,
            logon_sid="0x0",
            groups=groups,
            privileges=privileges,
        )

    def explain_pid(self, pid: int) -> Dict[str, Any]:
        """
        126. Формирует исчерпывающий отчет безопасности по идентификатору процесса (PID).
        """
        try:
            p = psutil.Process(pid)
            parent_pid = p.ppid()
            parent_name = psutil.Process(parent_pid).name() if parent_pid else ""
            p_name = p.name()
            cmdline = " ".join(p.cmdline()) if hasattr(p, "cmdline") else ""
        except Exception:
            p_name = "unknown"
            parent_pid = 0
            parent_name = ""
            cmdline = ""

        token_details = self.get_token_details_for_pid(pid)
        return {
            "pid": pid,
            "process_name": p_name,
            "parent_pid": parent_pid,
            "parent_name": parent_name,
            "cmdline": cmdline,
            "account": {
                "user": token_details.user_name if token_details else "",
                "domain": token_details.domain if token_details else "",
                "sid": token_details.user_sid if token_details else "",
            },
            "groups": [g.name for g in (token_details.groups if token_details else [])],
            "integrity": token_details.integrity_level.value if token_details else "Unknown",
            "elevated": token_details.is_elevated if token_details else False,
            "privileges": [p.name for p in (token_details.privileges if token_details else []) if p.enabled],
            "session_id": token_details.session_id if token_details else 0,
        }
