# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules System_Checkpoints Core - Freshness Auditor
# =============================================================================
# Description:
#   Модуль аудита актуальности образов восстановления и системного дрейфа (System Drift).
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.system_checkpoints.core.freshness_auditor import FreshnessAuditor
#
#     service = FreshnessAuditor()
#
# File: freshness_auditor.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.system_checkpoints.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Модуль аудита актуальности образов восстановления и системного дрейфа (System Drift)."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from logger import logger
from apps.windows.system_checkpoints.models import (
    FreshnessLevel,
    FreshnessReport,
    SystemDriftMetrics,
    SystemImageMetadata,
)


class FreshnessAuditor:
    """Анализатор актуальности образов восстановления и выявления системного дрейфа.

    Оценивает возраст последнего созданного образа восстановления, число накопившихся
    обновлений Windows (KB), вновь установленных программ и обновленных драйверов,
    формируя понятный отчет о готовности системы к восстановлению.
    """

    def __init__(
        self,
        high_max_days: int = 30,
        medium_max_days: int = 90,
        low_max_days: int = 180,
    ) -> None:
        """Инициализация аудитора актуальности.

        Args:
            high_max_days: Максимальный возраст образа в днях для статуса 'Высокая'.
            medium_max_days: Максимальный возраст для статуса 'Средняя'.
            low_max_days: Максимальный возраст для статуса 'Низкая'.
        """
        self.high_max_days = high_max_days
        self.medium_max_days = medium_max_days
        self.low_max_days = low_max_days

    def collect_system_telemetry(self) -> Dict[str, Any]:
        """Сбор текущей системной телеметрии (ПО, драйверы, KB) с безопасным fallback.

        Returns:
            Dict[str, Any]: Словарь со списками и счетчиками установленных компонентов.
        """
        kbs: List[str] = []
        apps: List[str] = []
        drivers_count = 0

        # 1. Сбор обновлений KB
        try:
            from apps.windows.sdk.core.audits.update_collector import UpdateCollector
            collector = UpdateCollector()
            res = collector.collect()
            hotfixes = res.metrics.get("recent_hotfixes", [])
            kbs = [h.get("HotFixID", "") for h in hotfixes if isinstance(h, dict) and h.get("HotFixID")]
            if not kbs:
                total_kb = res.metrics.get("installed_kb_count", 0)
                if total_kb:
                    kbs = [f"KB (всего {total_kb})"]
        except Exception as ex:
            logger.debug(f"Не удалось получить список KB через UpdateCollector: {ex}")

        # 2. Сбор установленного софта
        try:
            from apps.windows.sdk.core.software_audit import SoftwareAuditEngine
            engine = SoftwareAuditEngine()
            installed = engine.get_installed_applications()
            apps = [a.display_name for a in installed[:15] if a.display_name]
        except Exception as ex:
            logger.debug(f"Не удалось получить список ПО через SoftwareAuditEngine: {ex}")

        # 3. Сбор драйверов
        try:
            from apps.windows.sdk.core.audits.driver_collector import DriverCollector
            d_collector = DriverCollector()
            d_res = d_collector.collect()
            drivers_count = len(getattr(d_res, "findings", []))
            if drivers_count == 0:
                drivers_count = d_res.metrics.get("total_drivers_count", 0) if hasattr(d_res, "metrics") else 0
        except Exception as ex:
            logger.debug(f"Не удалось получить список драйверов: {ex}")

        return {
            "recent_kbs": kbs,
            "recent_apps": apps,
            "drivers_count": drivers_count,
            "total_apps_count": len(apps),
            "total_kbs_count": len(kbs),
        }

    def assess_freshness(
        self,
        latest_image: Optional[SystemImageMetadata],
        reference_date_str: Optional[str] = None,
        manual_drift: Optional[SystemDriftMetrics] = None,
    ) -> FreshnessReport:
        """Расчет актуальности образа восстановления на основе возраста и дрейфа.

        Args:
            latest_image: Метаданные последнего WIM-образа (если найден).
            reference_date_str: Кастомная дата снимка (ГГГГ-ММ-ДД HH:MM:SS) при отсутствии WIM.
            manual_drift: Переданные вручную метрики дрейфа (для тестов/моделирования).

        Returns:
            FreshnessReport: Структурированный аналитический отчет актуальности.
        """
        if not latest_image and not reference_date_str:
            return FreshnessReport(
                last_image_name=None,
                last_image_date=None,
                age_days=0,
                drift=SystemDriftMetrics(),
                freshness_level=FreshnessLevel.UNKNOWN,
                freshness_label_ru="Образы восстановления отсутствуют",
                recommendation="Рекомендуется создать базовый эталонный образ чистой системы.",
                can_restore_safely=False,
            )

        target_date_str = latest_image.created_at if latest_image else reference_date_str
        image_name = Path(latest_image.image_path).name if latest_image else "System Checkpoint"

        # Расчет возраста в днях
        age_days = 0
        if target_date_str:
            try:
                # Поддержка форматов 'YYYY-MM-DD HH:MM:SS' и 'YYYY-MM-DD'
                clean_dt = target_date_str[:19].replace("T", " ")
                if len(clean_dt) == 10:
                    dt = datetime.strptime(clean_dt, "%Y-%m-%d")
                else:
                    dt = datetime.strptime(clean_dt[:19], "%Y-%m-%d %H:%M:%S")
                age_days = max(0, (datetime.now() - dt).days)
            except Exception as ex:
                logger.debug(f"Не удалось распарсить дату {target_date_str}: {ex}")

        # Сбор или применение метрик дрейфа
        if manual_drift is not None:
            drift = manual_drift
            drift.days_since_creation = age_days
        else:
            telemetry = self.collect_system_telemetry()
            # Оценочные веса изменений с учетом возраста
            estimated_kb_changes = min(len(telemetry["recent_kbs"]), max(1, age_days // 15)) if age_days > 0 else 0
            estimated_app_changes = min(telemetry["total_apps_count"], max(1, age_days // 7)) if age_days > 0 else 0
            estimated_drv_changes = min(telemetry["drivers_count"], max(1, age_days // 30)) if age_days > 0 else 0

            drift = SystemDriftMetrics(
                days_since_creation=age_days,
                changed_components_count=estimated_kb_changes,
                installed_apps_count=estimated_app_changes,
                updated_drivers_count=estimated_drv_changes,
                recent_kbs=telemetry["recent_kbs"][:5],
                recent_apps=telemetry["recent_apps"][:5],
            )

        total_changes = (
            drift.changed_components_count
            + drift.installed_apps_count
            + drift.updated_drivers_count
        )

        # Вычисление уровня актуальности
        if age_days <= self.high_max_days and total_changes <= 15:
            level = FreshnessLevel.HIGH
            label_ru = "Высокая (образ актуален)"
            rec = "Образ находится в актуальном состоянии. Обновление не требуется."
            safe = True
        elif age_days <= self.medium_max_days and total_changes <= 45:
            level = FreshnessLevel.MEDIUM
            label_ru = "Умеренная (накопились изменения)"
            rec = "В системе накопились обновления и новые программы. Рекомендуется зафиксировать периодическую контрольную точку."
            safe = True
        elif age_days <= self.low_max_days and total_changes <= 80:
            level = FreshnessLevel.LOW
            label_ru = "Низкая (образ устаревает)"
            rec = "Образ существенно устарел. При откате потребуется повторная установка драйверов и обновлений. Запланируйте обновление образа."
            safe = False
        else:
            level = FreshnessLevel.CRITICAL_OUTDATED
            label_ru = "Критически устарел"
            rec = "Образ создан очень давно либо система кардинально изменилась. Рекомендуется создать свежий базовый образ."
            safe = False

        return FreshnessReport(
            last_image_name=image_name,
            last_image_date=target_date_str,
            age_days=age_days,
            drift=drift,
            freshness_level=level,
            freshness_label_ru=label_ru,
            recommendation=rec,
            can_restore_safely=safe,
        )
