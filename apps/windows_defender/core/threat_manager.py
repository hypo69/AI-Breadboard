# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Defender Threat Manager
# =============================================================================
# Description:
#   Управление журналом обнаружения угроз Microsoft Defender:
#   активные инциденты, объекты в карантине, история нейтрализации
#   вредоносного ПО (Trojan, Ransomware, PUA, Adware).
#
# File: threat_manager.py
# Project: ai-breadboard
# Package: apps.windows_defender.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модуль управления журналом угроз и инцидентов Microsoft Defender."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.logger import logger
from apps.windows_defender.core.defender_service import DefenderService
from apps.windows_defender.core.models import ThreatRecord, ThreatSeverity


class ThreatManager:
    """Менеджер обнаруженных угроз и журнала инцидентов Defender."""

    SEVERITY_MAP = {
        1: ThreatSeverity.LOW,
        2: ThreatSeverity.MEDIUM,
        4: ThreatSeverity.HIGH,
        5: ThreatSeverity.SEVERE,
    }

    def __init__(self, defender_service: Optional[DefenderService] = None) -> None:
        """Инициализация менеджера угроз."""
        self._service = defender_service or DefenderService()

    def get_threats_history(self, limit: int = 50) -> List[ThreatRecord]:
        """Получение истории обнаруженных угроз.

        Args:
            limit: Максимальное количество записей.

        Returns:
            List[ThreatRecord]: Список записей об угрозах.
        """
        raw_threats = self._service._run_powershell_json(f"Get-MpThreatDetection | Select-Object -First {limit}")
        results: List[ThreatRecord] = []

        if raw_threats:
            items = raw_threats if isinstance(raw_threats, list) else [raw_threats]
            for item in items:
                if not isinstance(item, dict):
                    continue

                sev_val = item.get("SeverityID", 0)
                sev = self.SEVERITY_MAP.get(sev_val, ThreatSeverity.UNKNOWN)

                resources = item.get("Resources") or []
                if isinstance(resources, str):
                    resources = [resources]

                results.append(
                    ThreatRecord(
                        threat_id=str(item.get("ThreatID", "N/A")),
                        threat_name=str(item.get("ThreatName", "Неизвестная угроза")),
                        severity=sev,
                        category=str(item.get("CategoryID", "Malware")),
                        initial_detection_time=str(item.get("InitialDetectionTime", "")),
                        last_detection_time=str(item.get("LastThreatStatusChangeTime", "")),
                        status=str(item.get("RemediationStatus", "Cleaned")),
                        resources=resources,
                        remediation_path=str(item.get("RemediationPath", "")),
                    )
                )

        return results
