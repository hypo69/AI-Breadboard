# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: System Integrity Audit Collector
# =============================================================================
# Description:
#   Проверка целостности системных файлов Windows, хранилища компонентов
#   WinSxS (DISM/SFC), состояния CBS и флагов ожидающей перезагрузки (Pending Reboot).
#
# Examples:
#   >>> from apps.windows.core.modules.integrity_collector import IntegrityCollector
#   >>> collector = IntegrityCollector()
#   >>> result = collector.collect()
#
# File: integrity_collector.py
# Project: ai-breadboard
# Package: apps.windows.core.modules
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Коллектор аудита целостности системных компонентов Windows."""

from __future__ import annotations

import os
import time
import winreg
from typing import Any, Dict, List

from src.logger import logger
from apps.windows.core.models import ActionType, AuditFinding, DomainAuditResult, RemediationAction, RiskLevel


class IntegrityCollector:
    """Коллектор фактов целостности системных файлов и обслуживания Windows."""

    def collect(self) -> DomainAuditResult:
        """Сбор данных о целостности и ожидающих перезагрузках.

        Returns:
            DomainAuditResult: Результат аудита целостности.
        """
        start_t = time.perf_counter()
        findings: List[AuditFinding] = []
        
        # 1. Проверка флагов ожидающей перезагрузки (Pending Reboot)
        pending_reboot = self._check_pending_reboot()
        metrics: Dict[str, Any] = {
            "pending_reboot": pending_reboot,
            "cbs_log_present": os.path.exists(r"C:\Windows\Logs\CBS\CBS.log"),
        }

        if pending_reboot:
            findings.append(
                AuditFinding(
                    domain="integrity",
                    category="pending_reboot",
                    title="Требуется перезагрузка системы",
                    description="В реестре обнаружены отложенные операции установки обновлений/компонентов, требующие перезагрузки.",
                    severity=RiskLevel.CAUTION,
                    evidence={"pending_reboot": True},
                    actions=[
                        RemediationAction(
                            action_id="restart_computer",
                            action_type=ActionType.CUSTOM_COMMAND,
                            title="Перезагрузить компьютер",
                            description="Плановая перезагрузка для завершения установки системных компонентов",
                            target="localhost",
                            risk=RiskLevel.CAUTION,
                            requires_reboot=True,
                            execution_command="Restart-Computer -Force",
                        )
                    ]
                )
            )

        # 2. Предложение выполнения DISM / SFC при необходимости
        repair_action = RemediationAction(
            action_id="dism_sfc_repair",
            action_type=ActionType.REPAIR_INTEGRITY,
            title="Восстановление хранилища компонентов DISM и SFC",
            description="Запуск восстановления поврежденных системных файлов через DISM RestoreHealth и SFC ScanNow",
            target="WinSxS",
            risk=RiskLevel.CRITICAL,
            execution_command="DISM.exe /Online /Cleanup-Image /RestoreHealth; sfc /scannow",
        )
        findings.append(
            AuditFinding(
                domain="integrity",
                category="system_servicing",
                title="Интерфейс восстановления целостности компонентов готов",
                description="Доступна автоматическая процедура проверки и восстановления системных файлов (SFC/DISM).",
                severity=RiskLevel.INFO,
                actions=[repair_action],
            )
        )

        duration_ms = (time.perf_counter() - start_t) * 1000
        return DomainAuditResult(
            domain_name="integrity",
            title_ru="Целостность системы (SFC / DISM)",
            status="warning" if pending_reboot else "ok",
            findings=findings,
            metrics=metrics,
            scan_duration_ms=round(duration_ms, 2),
        )

    def _check_pending_reboot(self) -> bool:
        """Проверка системных ключей реестра на ожидание перезагрузки."""
        keys_to_check = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired"),
        ]
        for hive, subkey in keys_to_check:
            try:
                with winreg.OpenKey(hive, subkey):
                    return True
            except OSError:
                pass
        return False
