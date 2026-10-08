# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Defender Core - Event Correlator
# =============================================================================
# Description:
#   Модуль сбора и корреляции событий журнала Windows Defender Operational.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.defender.core.event_correlator import EventCorrelator
#
#     service = EventCorrelator()
#
# File: event_correlator.py
# Project: ai-breadboard
# Package: apps.windows.modules.defender.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 04:11:30
# =============================================================================

from __future__ import annotations
"""Модуль сбора и корреляции событий журнала Windows Defender Operational."""

import json
import platform
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional
from logger import logger
from apps.windows.modules.defender.core.models import DefenderEventRecord

class EventCorrelator:
    """Сборщик и коррелятор событий Windows Defender."""
    EVENT_ID_CATEGORIES = {
        1000: ('Scan Started', 'Information'),
        1001: ('Scan Completed', 'Information'),
        1002: ('Scan Cancelled', 'Warning'),
        1005: ('Scan Failed', 'Error'),
        1006: ('Malware Detected', 'Warning'),
        1007: ('Malware Remediated', 'Information'),
        1008: ('Remediation Failed', 'Error'),
        1015: ('Suspicious Behavior', 'Warning'),
        1116: ('Malware Detected', 'Warning'),
        1117: ('Action Taken', 'Information'),
        1121: ('Network Protection Block', 'Warning'),
        1122: ('Network Protection Audit', 'Information'),
        1123: ('Controlled Folder Access Block', 'Warning'),
        1124: ('Controlled Folder Access Audit', 'Information'),
        1125: ('Attack Surface Reduction Block', 'Warning'),
        1126: ('Attack Surface Reduction Audit', 'Information'),
        2000: ('Signature Updated', 'Information'),
        2001: ('Signature Update Failed', 'Error'),
        2002: ('Signature Update Cancelled', 'Warning'),
        2003: ('Engine Updated', 'Information'),
        5000: ('Real-time Protection Enabled', 'Information'),
        5001: ('Real-time Protection Disabled', 'Critical'),
        5007: ('Configuration Changed', 'Warning'),
    }

    def get_recent_events(self, max_events: int=50) -> List[DefenderEventRecord]:
        """Получение последних событий из журнала Windows Defender/Operational.

        Args:
            max_events: Количество событий для выборки.

        Returns:
            List[DefenderEventRecord]: Список распарсенных событий безопасности.
        """
        if platform.system() != 'Windows':
            return []
        ps_cmd = f"Get-WinEvent -LogName 'Microsoft-Windows-Windows Defender/Operational' -MaxEvents {max_events} -ErrorAction SilentlyContinue | Select-Object Id, TimeCreated, LevelDisplayName, Message | ConvertTo-Json -Depth 2 -Compress"
        try:
            res = subprocess.run(f'powershell.exe -NoProfile -NonInteractive -Command "{ps_cmd}"', capture_output=True, text=True, timeout=15, shell=True)
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout.strip())
                events_list = data if isinstance(data, list) else [data]
                records: List[DefenderEventRecord] = []
                for ev in events_list:
                    if not isinstance(ev, dict):
                        continue
                    eid = int(ev.get('Id', 0))
                    raw_time = ev.get('TimeCreated', '')
                    time_str = raw_time
                    if isinstance(raw_time, str) and raw_time.startswith('/Date('):
                        try:
                            ts_ms = int(raw_time[6:-2].split('+')[0].split('-')[0])
                            time_str = datetime.fromtimestamp(ts_ms / 1000.0).strftime('%Y-%m-%d %H:%M:%S')
                        except Exception:
                            pass
                    cat, default_lvl = self.EVENT_ID_CATEGORIES.get(eid, ('General', 'Information'))
                    level_name = ev.get('LevelDisplayName') or default_lvl
                    msg = str(ev.get('Message', '')).strip()
                    records.append(DefenderEventRecord(event_id=eid, timestamp=str(time_str), level=level_name, message=msg, category=cat, details={'event_id': eid}))
                return records
        except Exception as e:
            logger.debug(f'Ошибка чтения журнала событий Defender: {e}')
        return []

    def find_latest_event_for_task(self, event_ids: List[int], since_timestamp: Optional[str] = None) -> Optional[DefenderEventRecord]:
        """Поиск последнего события Defender, относящегося к указанным Event ID.

        Args:
            event_ids: Список ожидаемых идентификаторов событий (например, [1001, 1005] или [2000, 2001]).
            since_timestamp: Фильтрация по времени (не ранее этой отметки).

        Returns:
            Optional[DefenderEventRecord]: Найденное событие или None.
        """
        recent = self.get_recent_events(max_events=20)
        target_ids = set(event_ids)
        for ev in recent:
            if ev.event_id in target_ids:
                if since_timestamp and ev.timestamp < since_timestamp:
                    continue
                return ev
        return None