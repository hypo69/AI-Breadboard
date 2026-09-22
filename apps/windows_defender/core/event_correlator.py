# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Defender Event Correlator
# =============================================================================
# Description:
#   Сбор и анализ журналов событий Microsoft-Windows-Windows Defender/Operational.
#   Парсинг событий обнаружения (1116/1117), блокировок ASR (1125/1126),
#   Controlled Folder Access (1123/1124), сетевой защиты (1121/1122),
#   отключения защиты (5001) и обновлений сигнатур (2000).
#
# File: event_correlator.py
# Project: ai-breadboard
# Package: apps.windows_defender.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модуль сбора и корреляции событий журнала Windows Defender Operational."""

from __future__ import annotations

import json
import platform
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional

from logger import logger
from apps.windows_defender.core.models import DefenderEventRecord


class EventCorrelator:
    """Сборщик и коррелятор событий Windows Defender."""

    EVENT_ID_CATEGORIES = {
        1006: ("Malware Detected", "Warning"),
        1007: ("Malware Remediated", "Information"),
        1008: ("Remediation Failed", "Error"),
        1015: ("Suspicious Behavior", "Warning"),
        1116: ("Malware Detected", "Warning"),
        1117: ("Action Taken", "Information"),
        1121: ("Network Protection Block", "Warning"),
        1122: ("Network Protection Audit", "Information"),
        1123: ("Controlled Folder Access Block", "Warning"),
        1124: ("Controlled Folder Access Audit", "Information"),
        1125: ("Attack Surface Reduction Block", "Warning"),
        1126: ("Attack Surface Reduction Audit", "Information"),
        2000: ("Signature Updated", "Information"),
        2001: ("Signature Update Failed", "Error"),
        5000: ("Real-time Protection Enabled", "Information"),
        5001: ("Real-time Protection Disabled", "Critical"),
        5007: ("Configuration Changed", "Warning"),
    }

    def get_recent_events(self, max_events: int = 50) -> List[DefenderEventRecord]:
        """Получение последних событий из журнала Windows Defender/Operational.

        Args:
            max_events: Количество событий для выборки.

        Returns:
            List[DefenderEventRecord]: Список распарсенных событий безопасности.
        """
        if platform.system() != "Windows":
            return []

        ps_cmd = (
            f"Get-WinEvent -LogName 'Microsoft-Windows-Windows Defender/Operational' -MaxEvents {max_events} "
            "-ErrorAction SilentlyContinue | Select-Object Id, TimeCreated, LevelDisplayName, Message | "
            "ConvertTo-Json -Depth 2 -Compress"
        )

        try:
            res = subprocess.run(
                f"powershell.exe -NoProfile -NonInteractive -Command \"{ps_cmd}\"",
                capture_output=True,
                text=True,
                timeout=15,
                shell=True,
            )
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout.strip())
                events_list = data if isinstance(data, list) else [data]
                records: List[DefenderEventRecord] = []

                for ev in events_list:
                    if not isinstance(ev, dict):
                        continue
                    eid = int(ev.get("Id", 0))
                    raw_time = ev.get("TimeCreated", "")
                    
                    time_str = raw_time
                    if isinstance(raw_time, str) and raw_time.startswith("/Date("):
                        try:
                            ts_ms = int(raw_time[6:-2].split("+")[0].split("-")[0])
                            time_str = datetime.fromtimestamp(ts_ms / 1000.0).strftime("%Y-%m-%d %H:%M:%S")
                        except Exception:
                            pass

                    cat, default_lvl = self.EVENT_ID_CATEGORIES.get(eid, ("General", "Information"))
                    level_name = ev.get("LevelDisplayName") or default_lvl
                    msg = str(ev.get("Message", "")).strip()

                    records.append(
                        DefenderEventRecord(
                            event_id=eid,
                            timestamp=str(time_str),
                            level=level_name,
                            message=msg,
                            category=cat,
                            details={"event_id": eid},
                        )
                    )
                return records
        except Exception as e:
            logger.debug(f"Ошибка чтения журнала событий Defender: {e}")

        return []
