# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Event Log Audit & Correlation Collector
# =============================================================================
# Description:
#   Сбор критических событий и ошибок из журналов Windows (System, Application),
#   корреляция сбоев оборудования, драйверов и приложений по временной шкале.
#
# Examples:
#   >>> from apps.windows.core.modules.eventlog_collector import EventLogCollector
#   >>> collector = EventLogCollector()
#   >>> result = collector.collect()
#
# File: eventlog_collector.py
# Project: ai-breadboard
# Package: apps.windows.core.modules
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Коллектор аудита и корреляции системных журналов Windows."""

from __future__ import annotations

import json
import subprocess
import time
from typing import Any, Dict, List

from src.logger import logger
from apps.windows.core.models import AuditFinding, DomainAuditResult, RiskLevel


class EventLogCollector:
    """Коллектор фактов из журналов событий Windows."""

    def collect(self, hours: int = 24) -> DomainAuditResult:
        """Сбор недавних критических событий и ошибок.

        Args:
            hours: Глубина выборки событий в часах.

        Returns:
            DomainAuditResult: Результат аудита журналов событий.
        """
        start_t = time.perf_counter()
        findings: List[AuditFinding] = []
        events = self._get_recent_errors(hours=hours)

        metrics: Dict[str, Any] = {
            "time_window_hours": hours,
            "critical_events_count": len([e for e in events if e.get("Level") in (1, "Critical")]),
            "error_events_count": len([e for e in events if e.get("Level") in (2, "Error")]),
            "total_events": len(events),
        }

        # Группировка ошибок по источникам
        sources: Dict[str, int] = {}
        for ev in events:
            src = ev.get("ProviderName", "Unknown")
            sources[src] = sources.get(src, 0) + 1

        for src, count in sources.items():
            if count >= 3:
                findings.append(
                    AuditFinding(
                        domain="eventlog",
                        category="recurring_error",
                        title=f"Повторяющиеся системные ошибки от '{src}'",
                        description=f"Источник '{src}' зафиксировал {count} ошибок за последние {hours} ч.",
                        severity=RiskLevel.CAUTION if count < 10 else RiskLevel.CRITICAL,
                        evidence={"source": src, "error_count": count},
                    )
                )

        duration_ms = (time.perf_counter() - start_t) * 1000
        return DomainAuditResult(
            domain_name="eventlog",
            title_ru="Системные журналы и корреляция ошибок",
            status="warning" if findings else "ok",
            findings=findings[:15],
            metrics=metrics,
            scan_duration_ms=round(duration_ms, 2),
        )

    def _get_recent_errors(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Получение ошибок за последние N часов через Get-WinEvent."""
        cmd = [
            "powershell",
            "-NoProfile",
            "-Command",
            f"Get-WinEvent -FilterHashtable @{{LogName='System','Application'; Level=1,2; StartTime=(Get-Date).AddHours(-{hours})}} -MaxEvents 50 -ErrorAction SilentlyContinue | Select-Object TimeCreated, Id, ProviderName, LevelDisplayName, Message | ConvertTo-Json -Compress",
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout.strip())
                if isinstance(data, dict):
                    return [data]
                elif isinstance(data, list):
                    return data
        except Exception as e:
            logger.debug(f"Ошибка при вызове Get-WinEvent: {e}")
        return []
