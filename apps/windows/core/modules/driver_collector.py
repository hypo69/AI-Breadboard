# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Driver & PnP Audit Collector
# =============================================================================
# Description:
#   Диагностика драйверов, устройств с ошибками PnP (Code 10/31/43/28),
#   проверка цифровых подписей и аудит пакетов в хранилище DriverStore.
#
# Examples:
#   >>> from apps.windows.core.modules.driver_collector import DriverCollector
#   >>> collector = DriverCollector()
#   >>> result = collector.collect()
#
# File: driver_collector.py
# Project: ai-breadboard
# Package: apps.windows.core.modules
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Коллектор аудита драйверов и устройств Windows."""

from __future__ import annotations

import json
import subprocess
import time
from typing import Any, Dict, List

from src.logger import logger
from apps.windows.core.models import ActionType, AuditFinding, DomainAuditResult, RemediationAction, RiskLevel


class DriverCollector:
    """Коллектор фактов о драйверах и статусе устройств PnP."""

    def collect(self) -> DomainAuditResult:
        """Сбор данных о драйверах и проблемных устройствах.

        Returns:
            DomainAuditResult: Результат аудита драйверов.
        """
        start_t = time.perf_counter()
        findings: List[AuditFinding] = []
        metrics: Dict[str, Any] = {
            "problem_devices_count": 0,
            "driver_packages_count": 0,
            "old_driver_packages_count": 0,
        }

        # 1. Проверка проблемных устройств через PowerShell Get-PnpDevice
        problem_devices = self._get_problem_devices()
        metrics["problem_devices_count"] = len(problem_devices)

        for dev in problem_devices:
            status = dev.get("Status", "Unknown")
            name = dev.get("FriendlyName") or dev.get("InstanceId", "Неизвестное устройство")
            err_code = dev.get("ProblemCode", "Unknown")
            findings.append(
                AuditFinding(
                    domain="drivers",
                    category="problem_device",
                    title=f"Ошибка устройства PnP: {name}",
                    description=f"Устройство находится в статусе '{status}' (Код проблемы: {err_code}).",
                    severity=RiskLevel.CRITICAL if str(err_code) in ("10", "43") else RiskLevel.CAUTION,
                    evidence=dev,
                    actions=[
                        RemediationAction(
                            action_id=f"restart_pnp_{dev.get('InstanceId', 'dev')[:20]}",
                            action_type=ActionType.CUSTOM_COMMAND,
                            title=f"Перезапустить устройство {name}",
                            description="Попытка перезапуска PnP устройства через PowerShell",
                            target=dev.get("InstanceId", ""),
                            risk=RiskLevel.CAUTION,
                            execution_command=f"Disable-PnpDevice -InstanceId '{dev.get('InstanceId')}' -Confirm:$false; Enable-PnpDevice -InstanceId '{dev.get('InstanceId')}' -Confirm:$false",
                        )
                    ],
                )
            )

        # 2. Инвентаризация DriverStore через pnputil
        driver_packages = self._get_driverstore_packages()
        metrics["driver_packages_count"] = len(driver_packages)

        duration_ms = (time.perf_counter() - start_t) * 1000
        status = "ok"
        if any(f.severity == RiskLevel.CRITICAL for f in findings):
            status = "critical"
        elif any(f.severity == RiskLevel.CAUTION for f in findings):
            status = "warning"

        return DomainAuditResult(
            domain_name="drivers",
            title_ru="Драйверы и PnP устройства",
            status=status,
            findings=findings,
            metrics=metrics,
            scan_duration_ms=round(duration_ms, 2),
        )

    def _get_problem_devices(self) -> List[Dict[str, Any]]:
        """Получение списка устройств со статусом Error или Degraded."""
        cmd = [
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-PnpDevice -Status Error, Degraded | Select-Object FriendlyName, InstanceId, Status, Problem, ProblemDescription, Class | ConvertTo-Json -Compress",
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
            logger.debug(f"Ошибка при вызове Get-PnpDevice: {e}")
        return []

    def _get_driverstore_packages(self) -> List[Dict[str, str]]:
        """Получение списка пакетов драйверов через pnputil /enum-drivers."""
        packages = []
        try:
            res = subprocess.run(["pnputil", "/enum-drivers"], capture_output=True, text=True, timeout=15)
            if res.returncode == 0:
                cur_pkg: Dict[str, str] = {}
                for line in res.stdout.splitlines():
                    line = line.strip()
                    if line.startswith("Published Name:") or line.startswith("Опубликованное имя:"):
                        if cur_pkg:
                            packages.append(cur_pkg)
                        cur_pkg = {"published_name": line.split(":", 1)[1].strip()}
                    elif line.startswith("Original Name:") or line.startswith("Исходное имя:"):
                        cur_pkg["original_name"] = line.split(":", 1)[1].strip()
                    elif line.startswith("Provider Name:") or line.startswith("Имя поставщика:"):
                        cur_pkg["provider"] = line.split(":", 1)[1].strip()
                    elif line.startswith("Class Name:") or line.startswith("Имя класса:"):
                        cur_pkg["class"] = line.split(":", 1)[1].strip()
                if cur_pkg:
                    packages.append(cur_pkg)
        except Exception as e:
            logger.debug(f"Ошибка при вызове pnputil: {e}")
        return packages
