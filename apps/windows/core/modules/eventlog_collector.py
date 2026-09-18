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

import time
from typing import Any, Dict, List

from src.logger import logger
from apps.windows.api.wevtapi import WevtAPI
from apps.windows.core.models import AuditFinding, DomainAuditResult, RiskLevel


class EventLogCollector:
    """Коллектор фактов из журналов событий Windows."""

    def __init__(self) -> None:
        """Инициализация коллектора с нативным WevtAPI."""
        self.wevtapi = WevtAPI()

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
            "critical_events_count": len([e for e in events if str(e.get("level", "")).lower() in ("critical", "1")]),
            "error_events_count": len([e for e in events if str(e.get("level", "")).lower() in ("error", "2")]),
            "total_events": len(events),
        }

        # Группировка ошибок по источникам
        sources: Dict[str, int] = {}
        for ev in events:
            src = ev.get("provider", "Unknown") or "Unknown"
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
        """Получение ошибок через нативный WevtAPI без использования PowerShell."""
        events: List[Dict[str, Any]] = []
        try:
            for chan in ("System", "Application"):
                errs = self.wevtapi.read_events(channel=chan, limit=25, level="Error", hours=hours)
                events.extend(errs)
                crits = self.wevtapi.read_events(channel=chan, limit=25, level="Critical", hours=hours)
                events.extend(crits)
        except Exception as e:
            logger.debug(f"Ошибка при сборе системных ошибок через WevtAPI: {e}")
        return events

