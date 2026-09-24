# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Hardware History and Archive Manager
# =============================================================================
# Description:
#   Управляет архивами аппаратного обеспечения, отслеживает историю изменений
#   железа во времени (Diff Engine) и сохраняет снимки аудита на диск.
#
# Examples:
#   >>> from apps.windows.telemetry.history_manager import HardwareHistoryManager
#   >>> manager = HardwareHistoryManager()
#   >>> changes = manager.detect_changes(current_report, previous_report)
#   >>> entry = manager.archive_report(current_report)
#
# File: history_manager.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Менеджер истории, архивации и детектора изменений аппаратного обеспечения."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from logger import logger
from apps.windows.telemetry.models import (
    HardwareArchiveEntry,
    HardwareAuditReport,
    HardwareChangeItem,
    HardwareDeviceAudit,
)


class HardwareHistoryManager:
    """Менеджер архивов и отслеживания аппаратных изменений."""

    def __init__(self, archive_dir: Optional[Path] = None, max_archives: int = 100) -> None:
        """Инициализация менеджера истории оборудования.

        Args:
            archive_dir: Каталог для хранения архивных снимков (по умолчанию data/telemetry/hardware_archives).
            max_archives: Максимальное количество хранимых архивов для ротации.
        """
        if archive_dir is None:
            # Корневой каталог проекта
            base_dir = Path(__file__).resolve().parent.parent.parent.parent
            self.archive_dir = base_dir / "data" / "telemetry" / "hardware_archives"
        else:
            self.archive_dir = Path(archive_dir)

        self.max_archives = max(10, max_archives)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.archive_dir / "archives_index.jsonl"
        self._cached_latest_report: Optional[HardwareAuditReport] = None

    def detect_changes(
        self,
        current_report: HardwareAuditReport,
        baseline_report: Optional[HardwareAuditReport] = None,
    ) -> List[HardwareChangeItem]:
        """Сравнение двух снимков оборудования и выявление всех изменений (Diff Engine).

        Args:
            current_report: Текущий срез аудита оборудования.
            baseline_report: Базовый срез для сравнения (если None, берется последний сохраненный).

        Returns:
            List[HardwareChangeItem]: Список зафиксированных изменений.
        """
        base = baseline_report
        if base is None:
            latest_entry = self.get_latest_archive()
            if latest_entry:
                base = latest_entry.report

        if base is None:
            return []

        changes: List[HardwareChangeItem] = []
        now_ts = datetime.now(timezone.utc).isoformat()

        base_devs: Dict[str, HardwareDeviceAudit] = {d.device_id.upper(): d for d in base.devices}
        curr_devs: Dict[str, HardwareDeviceAudit] = {d.device_id.upper(): d for d in current_report.devices}

        # 1. Поиск новых подключенных устройств (added)
        for dev_id, dev in curr_devs.items():
            if dev_id not in base_devs:
                changes.append(
                    HardwareChangeItem(
                        change_type="added",
                        device_id=dev.device_id,
                        device_name=dev.name,
                        description=f"Подключено новое устройство: {dev.name} (Класс: {dev.device_class}, Производитель: {dev.manufacturer})",
                        previous_value=None,
                        current_value=dev.model_dump(),
                        timestamp=now_ts,
                    )
                )

        # 2. Поиск отключенных / удаленных устройств (removed)
        for dev_id, dev in base_devs.items():
            if dev_id not in curr_devs:
                changes.append(
                    HardwareChangeItem(
                        change_type="removed",
                        device_id=dev.device_id,
                        device_name=dev.name,
                        description=f"Отключено или удалено устройство: {dev.name} (Класс: {dev.device_class})",
                        previous_value=dev.model_dump(),
                        current_value=None,
                        timestamp=now_ts,
                    )
                )

        # 3. Анализ изменений драйверов и статусов (driver_updated / status_changed)
        for dev_id, dev in curr_devs.items():
            if dev_id in base_devs:
                old_dev = base_devs[dev_id]

                # Проверка драйверов
                old_drv = old_dev.driver
                new_drv = dev.driver
                if old_drv and new_drv:
                    if old_drv.driver_version != new_drv.driver_version or old_drv.driver_date != new_drv.driver_date:
                        desc = (
                            f"Обновлен драйвер для '{dev.name}': "
                            f"версия с '{old_drv.driver_version}' (от {old_drv.driver_date or 'N/A'}) "
                            f"на '{new_drv.driver_version}' (от {new_drv.driver_date or 'N/A'})"
                        )
                        changes.append(
                            HardwareChangeItem(
                                change_type="driver_updated",
                                device_id=dev.device_id,
                                device_name=dev.name,
                                description=desc,
                                previous_value=old_drv.model_dump(),
                                current_value=new_drv.model_dump(),
                                timestamp=now_ts,
                            )
                        )
                elif not old_drv and new_drv:
                    changes.append(
                        HardwareChangeItem(
                            change_type="driver_updated",
                            device_id=dev.device_id,
                            device_name=dev.name,
                            description=f"Установлен драйвер для '{dev.name}': {new_drv.driver_version} ({new_drv.provider})",
                            previous_value=None,
                            current_value=new_drv.model_dump(),
                            timestamp=now_ts,
                        )
                    )

                # Проверка статуса и ошибок PnP
                if old_dev.status != dev.status or old_dev.problem_code != dev.problem_code:
                    desc = (
                        f"Изменен статус устройства '{dev.name}': "
                        f"было '{old_dev.status}' (код {old_dev.problem_code}) -> "
                        f"стало '{dev.status}' (код {dev.problem_code})"
                    )
                    changes.append(
                        HardwareChangeItem(
                            change_type="status_changed",
                            device_id=dev.device_id,
                            device_name=dev.name,
                            description=desc,
                            previous_value={"status": old_dev.status, "problem_code": old_dev.problem_code},
                            current_value={"status": dev.status, "problem_code": dev.problem_code},
                            timestamp=now_ts,
                        )
                    )

        return changes

    def archive_report(
        self,
        report: HardwareAuditReport,
        auto_diff: bool = True,
    ) -> HardwareArchiveEntry:
        """Сохранение снимка аудита оборудования в архив с фиксацией изменений.

        Args:
            report: Отчет аудита оборудования.
            auto_diff: Выполнять ли автоматическое вычисление изменений.

        Returns:
            HardwareArchiveEntry: Созданная запись архива.
        """
        if auto_diff:
            changes = self.detect_changes(report)
            report.changes_since_last_archive = changes
            if changes:
                logger.info(f"Зафиксировано {len(changes)} изменений в аппаратной конфигурации Windows!")
                for c in changes:
                    logger.info(f" [Железо] {c.change_type.upper()}: {c.description}")

        archive_id = f"hw_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        timestamp = datetime.now(timezone.utc).isoformat()

        entry = HardwareArchiveEntry(
            archive_id=archive_id,
            timestamp=timestamp,
            devices_count=report.devices_count,
            changes_count=len(report.changes_since_last_archive),
            report=report,
        )

        # 1. Сохранение полного JSON-файла архива
        archive_file = self.archive_dir / f"{archive_id}.json"
        try:
            with open(archive_file, "w", encoding="utf-8") as f:
                json.dump(entry.model_dump(), f, ensure_ascii=False, indent=2)
        except Exception as ex:
            logger.error(f"Ошибка сохранения архива оборудования в файл: {ex}")

        # 2. Добавление записи в индексный JSONL-файл
        index_entry = {
            "archive_id": archive_id,
            "timestamp": timestamp,
            "devices_count": report.devices_count,
            "problem_devices_count": report.problem_devices_count,
            "outdated_drivers_count": report.outdated_drivers_count,
            "changes_count": len(report.changes_since_last_archive),
            "file_name": f"{archive_id}.json",
        }
        try:
            with open(self.index_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(index_entry, ensure_ascii=False) + "\n")
        except Exception as ex:
            logger.error(f"Ошибка записи индекса архивов оборудования: {ex}")

        self._cached_latest_report = report
        self._rotate_archives()
        return entry

    def _rotate_archives(self) -> None:
        """Ротация старых архивных файлов при превышении лимита."""
        try:
            json_files = sorted(self.archive_dir.glob("hw_*.json"), key=os.path.getmtime)
            if len(json_files) > self.max_archives:
                to_delete = json_files[: len(json_files) - self.max_archives]
                for p in to_delete:
                    try:
                        p.unlink()
                    except OSError:
                        pass
        except Exception as ex:
            logger.debug(f"Ошибка при ротации архивов оборудования: {ex}")

    def get_latest_archive(self) -> Optional[HardwareArchiveEntry]:
        """Получение самого свежего архива оборудования из хранилища.

        Returns:
            Optional[HardwareArchiveEntry]: Последний архив или None.
        """
        try:
            json_files = sorted(self.archive_dir.glob("hw_*.json"), key=os.path.getmtime, reverse=True)
            if json_files:
                latest_path = json_files[0]
                with open(latest_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return HardwareArchiveEntry.model_validate(data)
        except Exception as ex:
            logger.debug(f"Ошибка чтения последнего архива оборудования: {ex}")
        return None

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение сводного списка сохраненных архивов оборудования.

        Args:
            limit: Максимальное количество записей архива.

        Returns:
            List[Dict[str, Any]]: Список метаданных архивов.
        """
        records: List[Dict[str, Any]] = []
        if not self.index_file.exists():
            return records

        try:
            with open(self.index_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            records.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        except Exception as ex:
            logger.debug(f"Ошибка чтения индекса архивов: {ex}")

        # Возвращаем последние limit записей в обратном хронологическом порядке
        return list(reversed(records))[:limit]

    def get_archive_by_id(self, archive_id: str) -> Optional[HardwareArchiveEntry]:
        """Получение конкретного полного архивного снимка по ID.

        Args:
            archive_id: Идентификатор архива.

        Returns:
            Optional[HardwareArchiveEntry]: Найденный архив или None.
        """
        safe_id = Path(archive_id).name
        target = self.archive_dir / f"{safe_id}.json"
        if not target.exists():
            target = self.archive_dir / safe_id

        if target.exists():
            try:
                with open(target, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return HardwareArchiveEntry.model_validate(data)
            except Exception as ex:
                logger.debug(f"Ошибка загрузки архива {archive_id}: {ex}")
        return None

    def get_change_timeline(self, limit: int = 100) -> List[HardwareChangeItem]:
        """Получение сводного таймлайна всех изменений оборудования из архивов.

        Args:
            limit: Лимит изменений для возврата.

        Returns:
            List[HardwareChangeItem]: Хронологический список зафиксированных изменений.
        """
        all_changes: List[HardwareChangeItem] = []
        json_files = sorted(self.archive_dir.glob("hw_*.json"), key=os.path.getmtime, reverse=True)

        for p in json_files:
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    entry = HardwareArchiveEntry.model_validate(data)
                    if entry.report and entry.report.changes_since_last_archive:
                        all_changes.extend(entry.report.changes_since_last_archive)
                        if len(all_changes) >= limit:
                            break
            except Exception:
                continue

        return all_changes[:limit]
