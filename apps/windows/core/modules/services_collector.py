# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Services Matrix Audit Collector
# =============================================================================
# Description:
#   Аудит системных служб Windows, инвентаризация типов запуска, аккаунтов
#   и выявление осиротевших служб (ссылающихся на удаленные исполняемые файлы).
#
# Examples:
#   >>> from apps.windows.core.modules.services_collector import ServicesCollector
#   >>> collector = ServicesCollector()
#   >>> result = collector.collect()
#
# File: services_collector.py
# Project: ai-breadboard
# Package: apps.windows.core.modules
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Коллектор аудита служб Windows."""

from __future__ import annotations

import os
import time
import winreg
from typing import Any, Dict, List

import psutil

from src.logger import logger
from apps.windows.core.models import ActionType, AuditFinding, DomainAuditResult, RemediationAction, RiskLevel


class ServicesCollector:
    """Коллектор фактов о службах Windows."""

    def collect(self) -> DomainAuditResult:
        """Сбор данных о службах и выявление осиротевших записей.

        Returns:
            DomainAuditResult: Результат аудита служб.
        """
        start_t = time.perf_counter()
        findings: List[AuditFinding] = []
        services = []
        running_count = 0
        orphaned_count = 0

        # Чтение служб через реестр HKLM\SYSTEM\CurrentControlSet\Services
        reg_path = r"SYSTEM\CurrentControlSet\Services"
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as root_key:
                num_subkeys, _, _ = winreg.QueryInfoKey(root_key)
                for i in range(min(num_subkeys, 300)):
                    try:
                        svc_name = winreg.EnumKey(root_key, i)
                        with winreg.OpenKey(root_key, svc_name) as svc_key:
                            image_path = self._get_reg_val(svc_key, "ImagePath")
                            display_name = self._get_reg_val(svc_key, "DisplayName") or svc_name
                            start_type = self._get_reg_val(svc_key, "Start")
                            
                            clean_path = image_path.replace('"', '').strip()
                            if "%SystemRoot%" in clean_path:
                                clean_path = clean_path.replace("%SystemRoot%", os.environ.get("SystemRoot", "C:\\Windows"))
                            if clean_path.startswith(r"\??\\"):
                                clean_path = clean_path[4:]

                            # Проверка на отсутствующий исполняемый файл для автозапускаемых служб
                            if clean_path and start_type in ("2", 2) and not os.path.exists(clean_path.split()[0]):
                                orphaned_count += 1
                                action = RemediationAction(
                                    action_id=f"disable_orphaned_svc_{svc_name}",
                                    action_type=ActionType.DISABLE_SERVICE,
                                    title=f"Отключить несуществующую службу {svc_name}",
                                    description=f"Служба ссылается на отсутствующий файл: {clean_path}",
                                    target=svc_name,
                                    risk=RiskLevel.CAUTION,
                                    execution_command=f"Set-Service -Name '{svc_name}' -StartupType Disabled",
                                )
                                findings.append(
                                    AuditFinding(
                                        domain="services",
                                        category="orphaned_service",
                                        title=f"Осиротевшая служба: {display_name}",
                                        description=f"Служба '{svc_name}' настроена на автозапуск, но исполняемый файл отсутствует ({clean_path}).",
                                        severity=RiskLevel.CAUTION,
                                        evidence={"service": svc_name, "path": clean_path},
                                        actions=[action],
                                    )
                                )

                            services.append({
                                "name": svc_name,
                                "display_name": display_name,
                                "image_path": image_path,
                            })
                    except (OSError, PermissionError):
                        continue
        except Exception as e:
            logger.debug(f"Ошибка при инвентаризации служб: {e}")

        # Подсчет запущенных через psutil
        try:
            for s in psutil.win_service_iter():
                if s.status() == psutil.STATUS_RUNNING:
                    running_count += 1
        except Exception:
            pass

        metrics: Dict[str, Any] = {
            "total_services_count": len(services),
            "running_services_count": running_count,
            "orphaned_services_count": orphaned_count,
        }

        duration_ms = (time.perf_counter() - start_t) * 1000
        return DomainAuditResult(
            domain_name="services",
            title_ru="Службы Windows",
            status="warning" if findings else "ok",
            findings=findings,
            metrics=metrics,
            scan_duration_ms=round(duration_ms, 2),
        )

    def _get_reg_val(self, key: Any, val_name: str) -> Any:
        try:
            val, _ = winreg.QueryValueEx(key, val_name)
            return val
        except OSError:
            return ""
