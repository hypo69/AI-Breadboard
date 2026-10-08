# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Subsystem 10 Audit Events
# =============================================================================
# Description:
#   Подсистема 10: Аудит событий безопасности Windows (Security Event Log:
#   создание/удаление пользователей 4720/4726, сброс паролей 4724, блокировка 4740,
#   изменение групп 4732/4733, успешные и неудачные входы 4624/4625).
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.accounts_identity.subsystems.subsystem_10_audit import AuditSubsystem
#
#     subsys = AuditSubsystem()
#     events = subsys.get_recent_identity_events(limit=20)
#
# File: subsystem_10_audit.py
# Project: ai-breadboard
# Package: apps.windows.modules.accounts_identity.subsystems
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 01:57:30
# =============================================================================

"""Подсистема чтения и корреляции журнала событий безопасности Windows (Security Events)."""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

from logger import logger
from apps.windows.modules.accounts_identity.models import AuditEventItem
from apps.windows.modules.accounts_identity.win32_bridge import Win32IdentityBridge

EVENT_NAME_MAP = {
    4720: "User Created",
    4722: "User Enabled",
    4723: "Password Change Attempt",
    4724: "Password Reset",
    4725: "User Disabled",
    4726: "User Deleted",
    4731: "Local Group Created",
    4732: "Member Added to Local Group",
    4733: "Member Removed from Local Group",
    4734: "Local Group Deleted",
    4735: "Local Group Changed",
    4738: "User Changed",
    4740: "Account Locked Out",
    4624: "Successful Logon",
    4625: "Failed Logon",
}


class AuditSubsystem:
    """Подсистема извлечения аудиторских следов учетных записей."""

    def __init__(self, bridge: Optional[Win32IdentityBridge] = None, wevtapi: Optional[Any] = None) -> None:
        """
        Инициализация подсистемы аудита.

        Args:
            bridge: Мост вызовов Windows API.
            wevtapi: Экземпляр WevtAPI для нативного и быстрого чтения журналов.
        """
        self.bridge = bridge or Win32IdentityBridge()
        if wevtapi is not None:
            self._wevtapi = wevtapi
        else:
            try:
                from apps.windows.telemetry.win32_ffi.wevtapi import WevtAPI
                self._wevtapi = WevtAPI()
            except Exception:
                self._wevtapi = None

    def get_recent_identity_events(self, limit: int = 50, event_id: Optional[int] = None) -> List[AuditEventItem]:
        """
        167-181. Извлекает последние события управления учетными записями и входов.

        Args:
            limit: Максимальное количество записей.
            event_id: Опциональный фильтр по ID события.

        Returns:
            Список объектов AuditEventItem.
        """
        events: List[AuditEventItem] = []

        # 1. Быстрый нативный сбор через Win32 EvtQuery (WevtAPI)
        if self._wevtapi and getattr(self._wevtapi, "is_available", lambda: False)():
            try:
                target_eids = [event_id] if event_id else [4720, 4722, 4724, 4725, 4726, 4732, 4733, 4740, 4624, 4625]
                raw_events = self._wevtapi.read_events(
                    channel="Security",
                    limit=limit,
                    event_id=target_eids,
                    format_message=False,
                )
                if raw_events:
                    for ev in raw_events:
                        eid = int(ev.get("event_id", 0))
                        ename = EVENT_NAME_MAP.get(eid, f"Security Event {eid}")
                        t_str = str(ev.get("timestamp") or datetime.datetime.now().isoformat())
                        edata = ev.get("event_data", {})

                        target_user = (
                            edata.get("TargetUserName")
                            or edata.get("SamAccountName")
                            or edata.get("MemberName")
                            or edata.get("TargetAccountName")
                            or ""
                        )
                        caller_user = (
                            edata.get("SubjectUserName")
                            or edata.get("AccountName")
                            or edata.get("SubjectAccountName")
                            or ""
                        )
                        if target_user.startswith("CN="):
                            target_user = target_user.split(",")[0].replace("CN=", "")

                        desc = ev.get("message") or f"{ename} (ID {eid}) - Target: {target_user or '-'}, Caller: {caller_user or '-'}"

                        events.append(
                            AuditEventItem(
                                event_id=eid,
                                event_name=ename,
                                timestamp=t_str,
                                target_account=target_user,
                                caller_account=caller_user,
                                description=desc[:150],
                            )
                        )
                    return events
            except Exception as ex:
                logger.debug(f"Исключение при чтении Security Event Log через WevtAPI: {ex}")

        # 2. Оптимизированный PowerShell fallback с разбором XML без тяжеловесного Message resolution
        ids_filter = f"Id={event_id}" if event_id else "Id=4720,4722,4724,4725,4726,4732,4733,4740,4624,4625"
        ps_cmd = f"""
        $startTime = (Get-Date).AddDays(-14)
        $events = Get-WinEvent -FilterHashtable @{{LogName='Security'; {ids_filter}; StartTime=$startTime}} -MaxEvents {limit} -ErrorAction SilentlyContinue
        if (-not $events) {{
            $events = Get-WinEvent -FilterHashtable @{{LogName='Security'; {ids_filter}}} -MaxEvents {min(limit, 30)} -ErrorAction SilentlyContinue
        }}
        if (-not $events) {{ "[]"; exit 0 }}
        $out = @()
        foreach ($e in $events) {{
            $xml = [xml]$e.ToXml()
            $data = @{{}}
            foreach ($d in $xml.Event.EventData.Data) {{ $data[$d.Name] = $d.'#text' }}
            $out += @{{
                Id = $e.Id
                TimeCreated = $e.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss')
                TargetUser = if ($data['TargetUserName']) {{ $data['TargetUserName'] }} else {{ $data['SamAccountName'] }}
                CallerUser = if ($data['SubjectUserName']) {{ $data['SubjectUserName'] }} else {{ $data['AccountName'] }}
                Message = "$($e.Id)"
            }}
        }}
        $out | ConvertTo-Json -Depth 3 -Compress
        """
        raw = self.bridge.run_powershell_json(ps_cmd)
        if raw:
            items = [raw] if isinstance(raw, dict) else raw
            for item in items:
                if not isinstance(item, dict):
                    continue
                eid = int(item.get("Id", 0))
                ename = EVENT_NAME_MAP.get(eid, f"Security Event {eid}")
                t_str = str(item.get("TimeCreated", datetime.datetime.now().isoformat()))
                target_user = str(item.get("TargetUser") or "")
                caller_user = str(item.get("CallerUser") or "")
                desc = f"{ename} (ID {eid}) - Target: {target_user or '-'}, Caller: {caller_user or '-'}"

                events.append(
                    AuditEventItem(
                        event_id=eid,
                        event_name=ename,
                        timestamp=t_str,
                        target_account=target_user,
                        caller_account=caller_user,
                        description=desc[:150],
                    )
                )

        return events

    def get_events_for_user(self, username: str, limit: int = 20) -> List[AuditEventItem]:
        """Фильтрует события аудита для конкретного пользователя."""
        all_events = self.get_recent_identity_events(limit=limit * 3)
        u_lower = username.lower()
        return [
            e for e in all_events
            if u_lower in e.target_account.lower() or u_lower in e.caller_account.lower()
        ][:limit]
