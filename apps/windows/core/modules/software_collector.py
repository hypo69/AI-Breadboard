# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Software Component Intelligence Collector
# =============================================================================
# Description:
#   Инвентаризация установленных программ, сопоставление со службами,
#   задачами планировщика, автозагрузкой и выявление осиротевших компонентов.
#
# Examples:
#   >>> from apps.windows.core.modules.software_collector import SoftwareCollector
#   >>> collector = SoftwareCollector()
#   >>> result = collector.collect()
#
# File: software_collector.py
# Project: ai-breadboard
# Package: apps.windows.core.modules
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Коллектор аудита установленных программ и компонентов."""

from __future__ import annotations

import time
import winreg
from typing import Any, Dict, List

from src.logger import logger
from apps.windows.core.models import AuditFinding, DomainAuditResult, RiskLevel


class SoftwareCollector:
    """Коллектор инвентаря установленного ПО и связанных системных сущностей."""

    def collect(self) -> DomainAuditResult:
        """Сбор данных об установленных приложениях.

        Returns:
            DomainAuditResult: Результат аудита программного обеспечения.
        """
        start_t = time.perf_counter()
        findings: List[AuditFinding] = []
        apps = self._get_installed_apps()

        metrics: Dict[str, Any] = {
            "total_apps_count": len(apps),
            "microsoft_apps_count": sum(1 for a in apps if "microsoft" in (a.get("publisher") or "").lower()),
            "third_party_apps_count": sum(1 for a in apps if "microsoft" not in (a.get("publisher") or "").lower()),
        }

        # Анализ устаревших или потенциально нежелательных приложений
        for app in apps:
            name = app.get("display_name", "")
            publisher = app.get("publisher", "")
            if not publisher:
                findings.append(
                    AuditFinding(
                        domain="software",
                        category="unknown_publisher",
                        title=f"Приложение без указания издателя: {name}",
                        description=f"Приложение '{name}' установлено в системе, но не указывает издателя.",
                        severity=RiskLevel.INFO,
                        evidence=app,
                    )
                )

        duration_ms = (time.perf_counter() - start_t) * 1000
        return DomainAuditResult(
            domain_name="software",
            title_ru="Установленные программы",
            status="ok" if not findings else "warning",
            findings=findings[:20],
            metrics=metrics,
            scan_duration_ms=round(duration_ms, 2),
        )

    def _get_installed_apps(self) -> List[Dict[str, Any]]:
        """Чтение установленных программ из веток Uninstall реестра."""
        apps: List[Dict[str, Any]] = []
        reg_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]

        seen_names = set()
        for hive, subkey in reg_paths:
            try:
                with winreg.OpenKey(hive, subkey) as root_key:
                    num_subkeys, _, _ = winreg.QueryInfoKey(root_key)
                    for i in range(num_subkeys):
                        try:
                            subkey_name = winreg.EnumKey(root_key, i)
                            with winreg.OpenKey(root_key, subkey_name) as app_key:
                                display_name = self._get_reg_val(app_key, "DisplayName")
                                if display_name and display_name not in seen_names:
                                    seen_names.add(display_name)
                                    apps.append({
                                        "display_name": display_name,
                                        "version": self._get_reg_val(app_key, "DisplayVersion") or "",
                                        "publisher": self._get_reg_val(app_key, "Publisher") or "",
                                        "install_date": self._get_reg_val(app_key, "InstallDate") or "",
                                        "install_location": self._get_reg_val(app_key, "InstallLocation") or "",
                                        "uninstall_string": self._get_reg_val(app_key, "UninstallString") or "",
                                    })
                        except (OSError, PermissionError):
                            continue
            except (OSError, PermissionError):
                continue

        return apps

    def _get_reg_val(self, key: Any, val_name: str) -> str:
        """Безопасное чтение строкового значения из реестра."""
        try:
            val, _ = winreg.QueryValueEx(key, val_name)
            return str(val)
        except OSError:
            return ""
