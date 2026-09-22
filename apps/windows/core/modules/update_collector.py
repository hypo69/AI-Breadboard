# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Update Diagnostic Collector
# =============================================================================
# Description:
#   Инспекция версии ОС, установленных обновлений (KB), статуса центра
#   обновления Windows и выявление сбоев обслуживания (Servicing Stack).
#
# Examples:
#   >>> from apps.windows.core.modules.update_collector import UpdateCollector
#   >>> collector = UpdateCollector()
#   >>> result = collector.collect()
#
# File: update_collector.py
# Project: ai-breadboard
# Package: apps.windows.core.modules
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Коллектор аудита обновлений Windows."""

from __future__ import annotations

import json
import subprocess
import time
import winreg
from typing import Any, Dict, List

from logger import logger
from apps.windows.core.models import AuditFinding, DomainAuditResult, RiskLevel


class UpdateCollector:
    """Коллектор фактов о Центре обновления Windows и KB."""

    def collect(self) -> DomainAuditResult:
        """Сбор данных о версии Windows и обновлениях.

        Returns:
            DomainAuditResult: Результат аудита обновлений.
        """
        start_t = time.perf_counter()
        findings: List[AuditFinding] = []
        os_info = self._get_os_version()
        hotfixes = self._get_hotfixes()

        metrics: Dict[str, Any] = {
            "os_product_name": os_info.get("product_name"),
            "display_version": os_info.get("display_version"),
            "current_build": os_info.get("current_build"),
            "installed_kb_count": len(hotfixes),
            "recent_hotfixes": hotfixes[:5],
        }

        duration_ms = (time.perf_counter() - start_t) * 1000
        return DomainAuditResult(
            domain_name="updates",
            title_ru="Обновления Windows (Windows Update)",
            status="ok",
            findings=findings,
            metrics=metrics,
            scan_duration_ms=round(duration_ms, 2),
        )

    def _get_os_version(self) -> Dict[str, str]:
        """Получение точной версии Windows из реестра."""
        info = {}
        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
            ) as key:
                info["product_name"] = str(winreg.QueryValueEx(key, "ProductName")[0])
                info["display_version"] = str(winreg.QueryValueEx(key, "DisplayVersion")[0])
                info["current_build"] = str(winreg.QueryValueEx(key, "CurrentBuild")[0])
        except OSError:
            pass
        return info

    def _get_hotfixes(self) -> List[Dict[str, str]]:
        """Получение списка установленных исправлений (KB)."""
        cmd = [
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-HotFix | Select-Object HotFixID, Description, InstalledOn | ConvertTo-Json -Compress",
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout.strip())
                if isinstance(data, dict):
                    return [data]
                elif isinstance(data, list):
                    return data
        except Exception as e:
            logger.debug(f"Ошибка при вызове Get-HotFix: {e}")
        return []
