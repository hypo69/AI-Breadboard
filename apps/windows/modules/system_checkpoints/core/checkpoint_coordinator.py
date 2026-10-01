# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules System_Checkpoints Core - Checkpoint Coordinator
# =============================================================================
# Description:
#   Главный координатор системы контрольных точек и трех механизмов восстановления Windows.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.system_checkpoints.core.checkpoint_coordinator import CheckpointCoordinator
#
#     service = CheckpointCoordinator()
#
# File: checkpoint_coordinator.py
# Project: ai-breadboard
# Package: apps.windows.modules.system_checkpoints.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Главный координатор системы контрольных точек и трех механизмов восстановления Windows."""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from logger import logger
from apps.windows.system_checkpoints.models import (
    CheckpointCreateRequest,
    CheckpointType,
    FreshnessReport,
    RecoveryMechanism,
    SystemCheckpointRecord,
    WinREStatus,
)
from apps.windows.system_checkpoints.core.image_manager import SystemImageManager
from apps.windows.system_checkpoints.core.winre_manager import WinREManager
from apps.windows.system_checkpoints.core.freshness_auditor import FreshnessAuditor


class CheckpointCoordinator:
    """Единый диспетчер и координатор контрольных точек системы.

    Связывает воедино три независимых механизма восстановления:
    1. System Image (WIM-образы DISM);
    2. Recovery Environment (WinRE);
    3. Restore Point (System Restore / VSS).
    """

    def __init__(
        self,
        catalog_path: str = "data/system_checkpoints/catalog.json",
        image_manager: Optional[SystemImageManager] = None,
        winre_manager: Optional[WinREManager] = None,
        freshness_auditor: Optional[FreshnessAuditor] = None,
    ) -> None:
        """Инициализация координатора контрольных точек.

        Args:
            catalog_path: Путь к файлу каталога контрольных точек.
            image_manager: Экземпляр SystemImageManager (DI).
            winre_manager: Экземпляр WinREManager (DI).
            freshness_auditor: Экземпляр FreshnessAuditor (DI).
        """
        self.catalog_path = Path(catalog_path)
        self.image_manager = image_manager or SystemImageManager()
        self.winre_manager = winre_manager or WinREManager()
        self.freshness_auditor = freshness_auditor or FreshnessAuditor()

    def _get_restore_manager(self):
        """Ленивая инициализация нативного WindowsSystemRestoreManager."""
        try:
            from apps.windows.core.system_restore import WindowsSystemRestoreManager
            return WindowsSystemRestoreManager()
        except Exception as ex:
            logger.debug(f"Не удалось инициализировать WindowsSystemRestoreManager: {ex}")
            return None

    def load_catalog(self) -> List[SystemCheckpointRecord]:
        """Загрузка каталога всех зарегистрированных контрольных точек.

        Returns:
            List[SystemCheckpointRecord]: Список записей контрольных точек.
        """
        if not self.catalog_path.exists():
            return []
        try:
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            if not isinstance(raw_data, list):
                return []
            records: List[SystemCheckpointRecord] = []
            for item in raw_data:
                try:
                    c_type = CheckpointType(item.get("checkpoint_type", CheckpointType.PERIODIC.value))
                    mechs = [RecoveryMechanism(m) for m in item.get("mechanisms", []) if m in RecoveryMechanism._value2member_map_]
                    record = SystemCheckpointRecord(
                        checkpoint_id=item["checkpoint_id"],
                        checkpoint_type=c_type,
                        mechanisms=mechs,
                        created_at=item.get("created_at", ""),
                        title=item.get("title", ""),
                        description=item.get("description", ""),
                        image_path=item.get("image_path"),
                        restore_point_seq=item.get("restore_point_seq"),
                        drift_at_creation=item.get("drift_at_creation"),
                    )
                    records.append(record)
                except Exception as ex:
                    logger.debug(f"Ошибка парсинга записи контрольной точки: {ex}")
            # Сортировка от свежих к старым
            records.sort(key=lambda x: x.created_at, reverse=True)
            return records
        except Exception as ex:
            logger.error(f"Не удалось прочитать каталог контрольных точек {self.catalog_path}: {ex}")
            return []

    def save_catalog(self, records: List[SystemCheckpointRecord]) -> bool:
        """Сохранение обновленного списка контрольных точек в каталог.

        Args:
            records: Список контрольных точек для сохранения.

        Returns:
            bool: Успешность операции.
        """
        try:
            self.catalog_path.parent.mkdir(parents=True, exist_ok=True)
            payload = [r.to_dict() for r in records]
            with open(self.catalog_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            return True
        except Exception as ex:
            logger.error(f"Ошибка записи каталога {self.catalog_path}: {ex}")
            return False

    def get_comprehensive_health(self) -> Dict[str, Any]:
        """Сводная оценка готовности всех трех механизмов восстановления.

        Returns:
            Dict[str, Any]: Статус WIM-образов, WinRE и System Restore.
        """
        # 1. System Images
        images = self.image_manager.scan_recovery_images()
        latest_img = images[0] if images else None

        # 2. WinRE
        winre_stat = self.winre_manager.get_status()

        # 3. System Restore
        sr_mgr = self._get_restore_manager()
        sr_points = sr_mgr.list_restore_points() if sr_mgr else []
        sr_prot = sr_mgr.check_protection_status() if sr_mgr else {"system_protection_enabled": False}

        # 4. Freshness
        freshness = self.freshness_auditor.assess_freshness(latest_image=latest_img)

        # Вычисление общего индекса готовности (0-100)
        score = 0
        if winre_stat.enabled:
            score += 30
        if sr_prot.get("system_protection_enabled", False):
            score += 25
        if len(sr_points) > 0:
            score += 15
        if latest_img:
            score += 30 if freshness.can_restore_safely else 15

        return {
            "health_score": min(100, score),
            "winre": winre_stat.to_dict(),
            "system_restore": {
                "protection_enabled": sr_prot.get("system_protection_enabled", False),
                "restore_points_count": len(sr_points),
                "recent_points": sr_points[:3],
            },
            "system_images": {
                "total_images_found": len(images),
                "latest_image": latest_img.to_dict() if latest_img else None,
            },
            "freshness": freshness.to_dict(),
            "timestamp": datetime.now().isoformat(),
        }

    def get_freshness_report(self) -> FreshnessReport:
        """Получение детального отчета актуальности последнего образа.

        Returns:
            FreshnessReport: Отчет актуальности с метриками дрейфа и рекомендациями.
        """
        images = self.image_manager.scan_recovery_images()
        latest_img = images[0] if images else None
        catalog = self.load_catalog()
        ref_date = catalog[0].created_at if catalog and not latest_img else None
        return self.freshness_auditor.assess_freshness(latest_image=latest_img, reference_date_str=ref_date)

    def create_checkpoint(self, req: CheckpointCreateRequest) -> Dict[str, Any]:
        """Создание новой контрольной точки с координацией механизмов.

        Args:
            req: Параметры запроса создания контрольной точки.

        Returns:
            Dict[str, Any]: Результат создания со статусом каждого задействованного механизма.
        """
        now_dt = datetime.now()
        chk_id = f"chk_{now_dt.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"
        active_mechanisms: List[RecoveryMechanism] = []
        restore_point_result = None
        image_result = None
        image_file_path = None
        restore_seq = None

        # Префикс названия по типу контрольной точки
        type_labels = {
            CheckpointType.BASELINE: "🟢 [Базовая]",
            CheckpointType.POST_CONFIG: "🔵 [После настройки]",
            CheckpointType.PRE_UPDATE: "🟡 [Перед обновлением]",
            CheckpointType.PRE_EXPERIMENT: "🟠 [Перед экспериментом]",
            CheckpointType.PERIODIC: "🔴 [Периодическая]",
            CheckpointType.CUSTOM: "⚪ [Контрольная точка]",
        }
        full_title = f"{type_labels.get(req.checkpoint_type, '')} {req.title}".strip()

        # 1. Создание нативной точки восстановления Windows (VSS)
        if req.create_restore_point:
            sr_mgr = self._get_restore_manager()
            if sr_mgr:
                r_type = "MODIFY_SETTINGS"
                if req.checkpoint_type == CheckpointType.PRE_UPDATE:
                    r_type = "WINDOWS_UPDATE"
                elif req.checkpoint_type == CheckpointType.PRE_EXPERIMENT:
                    r_type = "APPLICATION_INSTALL"

                restore_point_result = sr_mgr.create_restore_point(
                    description=full_title,
                    restore_point_type=r_type,
                )
                if restore_point_result.get("success", False):
                    active_mechanisms.append(RecoveryMechanism.RESTORE_POINT)
                    points = sr_mgr.list_restore_points()
                    if points:
                        restore_seq = points[-1].get("sequence_number")
            else:
                restore_point_result = {"success": False, "error": "SystemRestoreManager недоступен"}

        # 2. Создание WIM-образа (DISM)
        if req.create_wim_image:
            if req.checkpoint_type == CheckpointType.BASELINE:
                image_result = self.image_manager.create_baseline_image(
                    source_drive=req.target_drive,
                    destination_dir=req.destination_dir,
                    description=req.description or full_title,
                )
            else:
                image_result = self.image_manager.create_periodic_checkpoint(
                    source_drive=req.target_drive,
                    destination_dir=req.destination_dir,
                    description=req.description or full_title,
                    append_if_exists=False,
                )
            if image_result.get("success", False):
                active_mechanisms.append(RecoveryMechanism.SYSTEM_IMAGE)
                image_file_path = image_result.get("target_file")

        # 3. Фиксация дрейфа на момент создания
        telemetry = self.freshness_auditor.collect_system_telemetry()
        drift_snapshot = {
            "captured_at": now_dt.isoformat(),
            "kbs_count": telemetry.get("total_kbs_count", 0),
            "apps_count": telemetry.get("total_apps_count", 0),
            "drivers_count": telemetry.get("drivers_count", 0),
        }

        # 4. Сохранение записи в каталоге
        record = SystemCheckpointRecord(
            checkpoint_id=chk_id,
            checkpoint_type=req.checkpoint_type,
            mechanisms=active_mechanisms if active_mechanisms else [RecoveryMechanism.RESTORE_POINT],
            created_at=now_dt.strftime("%Y-%m-%d %H:%M:%S"),
            title=full_title,
            description=req.description,
            image_path=image_file_path,
            restore_point_seq=restore_seq,
            drift_at_creation=drift_snapshot,
        )

        catalog = self.load_catalog()
        catalog.insert(0, record)
        self.save_catalog(catalog)

        return {
            "success": True,
            "checkpoint_id": chk_id,
            "record": record.to_dict(),
            "restore_point_result": restore_point_result,
            "image_result": image_result,
            "message": f"Контрольная точка '{full_title}' успешно зарегистрирована.",
        }

    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Удаление контрольной точки из каталога.

        Args:
            checkpoint_id: Идентификатор контрольной точки.

        Returns:
            bool: True если удалено, False если не найдено.
        """
        catalog = self.load_catalog()
        filtered = [r for r in catalog if r.checkpoint_id != checkpoint_id]
        if len(filtered) != len(catalog):
            self.save_catalog(filtered)
            return True
        return False
