# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry_Research - Startup History Manager
# =============================================================================
# Description:
#   Менеджер истории, архивации и детектора изменений автозагрузки Windows.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry_research.startup_history_manager import StartupHistoryManager
#
#     service = StartupHistoryManager()
#
# File: startup_history_manager.py
# Project: ai-breadboard
# Package: apps.windows.telemetry_research
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 13:56:00
# =============================================================================

from __future__ import annotations
"""Менеджер истории, архивации и детектора изменений автозагрузки Windows."""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from logger import logger
from apps.windows.sdk.modules.startup.core.models import (
    AuditReport,
    StartupArchiveEntry,
    StartupChangeItem,
    StartupEntry,
)


class StartupHistoryManager:
    """Менеджер архивных снимков и отслеживания изменений точек автозапуска."""

    def __init__(
        self,
        archive_dir: Optional[Path] = None,
        storage_dir: Optional[Path] = None,
        max_archives: int = 100,
        use_file_index: bool = True,
    ) -> None:
        """Инициализация менеджера истории автозапуска.

        Args:
            archive_dir: Каталог для хранения архивных снимков (по умолчанию data/telemetry/startup_archives).
            storage_dir: Алиас для archive_dir.
            max_archives: Максимальное количество хранимых архивов для ротации.
            use_file_index: Использовать ли индексный файл архивов.
        """
        target_dir = archive_dir if archive_dir is not None else storage_dir
        if target_dir is None:
            base_dir = Path(__file__).resolve().parent.parent.parent.parent
            self.archive_dir = base_dir / 'data' / 'telemetry' / 'startup_archives'
        else:
            self.archive_dir = Path(target_dir)
        self.max_archives = max(10, max_archives)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.archive_dir / 'startup_index.jsonl'
        self._cached_latest_report: Optional[AuditReport] = None
        self.use_file_index = use_file_index

    def detect_changes(
        self,
        current_report: AuditReport,
        baseline_report: Optional[AuditReport] = None,
    ) -> List[StartupChangeItem]:
        """Сравнение двух снимков автозапуска и выявление всех отличий (Diff Engine).

        Args:
            current_report: Текущий срез аудита автозапуска.
            baseline_report: Базовый срез для сравнения (если None, берется последний сохраненный).

        Returns:
            List[StartupChangeItem]: Список зафиксированных изменений.
        """
        base = baseline_report
        if base is None:
            if self._cached_latest_report is not None:
                base = self._cached_latest_report
            else:
                latest_entry = self.get_latest_archive()
                if latest_entry:
                    base = latest_entry.report
        if base is None:
            return []

        changes: List[StartupChangeItem] = []
        now_ts = datetime.now(timezone.utc).isoformat()

        if isinstance(base, dict):
            raw_base_entries = base.get('entries', [])
            base_entries_list = [StartupEntry.model_validate(e) if isinstance(e, dict) else e for e in raw_base_entries]
        elif hasattr(base, 'entries'):
            base_entries_list = [StartupEntry.model_validate(e) if isinstance(e, dict) else e for e in base.entries]
        else:
            return []

        base_entries: Dict[str, StartupEntry] = {e.id: e for e in base_entries_list}

        if isinstance(current_report, dict):
            raw_curr_entries = current_report.get('entries', [])
            curr_entries_list = [StartupEntry.model_validate(e) if isinstance(e, dict) else e for e in raw_curr_entries]
        elif hasattr(current_report, 'entries'):
            curr_entries_list = [StartupEntry.model_validate(e) if isinstance(e, dict) else e for e in current_report.entries]
        else:
            return []

        curr_entries: Dict[str, StartupEntry] = {e.id: e for e in curr_entries_list}

        # 1. Новые записи в автозагрузке
        for entry_id, entry in curr_entries.items():
            if entry_id not in base_entries:
                status_str = 'включен' if entry.is_enabled else 'отключен'
                desc = (
                    f"Добавлен новый элемент автозапуска: «{entry.name}» "
                    f"({entry.location_type.value if hasattr(entry.location_type, 'value') else entry.location_type}, {status_str}). "
                    f"Команда: {entry.command or entry.executable_path}"
                )
                changes.append(
                    StartupChangeItem(
                        change_type='added',
                        entry_id=entry.id,
                        name=entry.name,
                        description=desc,
                        previous_value=None,
                        current_value=entry.model_dump(mode='json'),
                        timestamp=now_ts,
                    )
                )

        # 2. Удаленные записи из автозагрузки
        for entry_id, entry in base_entries.items():
            if entry_id not in curr_entries:
                desc = f"Удален элемент из автозапуска: «{entry.name}» (Расположение: {entry.location_type.value if hasattr(entry.location_type, 'value') else entry.location_type})"
                changes.append(
                    StartupChangeItem(
                        change_type='removed',
                        entry_id=entry.id,
                        name=entry.name,
                        description=desc,
                        previous_value=entry.model_dump(mode='json'),
                        current_value=None,
                        timestamp=now_ts,
                    )
                )

        # 3. Изменения параметров существующих записей
        for entry_id, entry in curr_entries.items():
            if entry_id in base_entries:
                old_entry = base_entries[entry_id]

                # Изменение статуса активности (ВКЛ / ОТКЛ)
                if old_entry.is_enabled != entry.is_enabled:
                    old_st = 'ВКЛЮЧЕН' if old_entry.is_enabled else 'ОТКЛЮЧЕН'
                    new_st = 'ВКЛЮЧЕН' if entry.is_enabled else 'ОТКЛЮЧЕН'
                    desc = f"Изменен статус активности «{entry.name}»: было {old_st} -> стало {new_st}"
                    changes.append(
                        StartupChangeItem(
                            change_type='state_changed',
                            entry_id=entry.id,
                            name=entry.name,
                            description=desc,
                            previous_value={'is_enabled': old_entry.is_enabled},
                            current_value={'is_enabled': entry.is_enabled},
                            timestamp=now_ts,
                        )
                    )

                # Изменение исполняемого пути или команды
                if (old_entry.executable_path != entry.executable_path) or (old_entry.command != entry.command):
                    desc = f"Изменена команда запуска для «{entry.name}»: «{old_entry.command}» -> «{entry.command}»"
                    changes.append(
                        StartupChangeItem(
                            change_type='path_changed',
                            entry_id=entry.id,
                            name=entry.name,
                            description=desc,
                            previous_value={'command': old_entry.command, 'executable_path': old_entry.executable_path},
                            current_value={'command': entry.command, 'executable_path': entry.executable_path},
                            timestamp=now_ts,
                        )
                    )

                # Изменение уровня риска
                old_risk = old_entry.risk_level.value if hasattr(old_entry.risk_level, 'value') else str(old_entry.risk_level)
                new_risk = entry.risk_level.value if hasattr(entry.risk_level, 'value') else str(entry.risk_level)
                if old_risk != new_risk:
                    desc = f"Изменен уровень риска «{entry.name}»: было {old_risk.upper()} -> стало {new_risk.upper()}"
                    changes.append(
                        StartupChangeItem(
                            change_type='risk_changed',
                            entry_id=entry.id,
                            name=entry.name,
                            description=desc,
                            previous_value={'risk_level': old_risk, 'reasons': old_entry.risk_reasons},
                            current_value={'risk_level': new_risk, 'reasons': entry.risk_reasons},
                            timestamp=now_ts,
                        )
                    )

        return changes

    def archive_report(
        self,
        report: AuditReport,
        auto_diff: bool = True,
    ) -> StartupArchiveEntry:
        """Сохранение снимка аудита автозапуска в архив с фиксацией изменений.

        Args:
            report: Отчет аудита автозапуска.
            auto_diff: Выполнять ли автоматическое вычисление изменений.

        Returns:
            StartupArchiveEntry: Созданная запись архива.
        """
        changes: List[StartupChangeItem] = []
        if auto_diff:
            changes = self.detect_changes(report)
            if changes:
                logger.info(f"Зафиксировано {len(changes)} изменений в автозагрузке Windows!")
                for c in changes:
                    logger.info(f" [Автозапуск] {c.change_type.upper()}: {c.description}")

        archive_id = f"startup_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        timestamp = datetime.now(timezone.utc).isoformat()
        entry = StartupArchiveEntry(
            archive_id=archive_id,
            timestamp=timestamp,
            total_entries=len(report.entries),
            health_score=report.summary.health_score if report.summary else 100,
            changes_count=len(changes),
            changes=changes,
            report=report,
        )

        archive_file = self.archive_dir / f'{archive_id}.json'
        try:
            with open(archive_file, 'w', encoding='utf-8') as f:
                json.dump(entry.model_dump(mode='json'), f, ensure_ascii=False, indent=2)
        except Exception as ex:
            logger.error(f'Ошибка сохранения архива автозапуска в файл: {ex}')

        index_entry = {
            'archive_id': archive_id,
            'timestamp': timestamp,
            'total_entries': entry.total_entries,
            'health_score': entry.health_score,
            'changes_count': entry.changes_count,
            'file_name': f'{archive_id}.json',
        }
        if self.use_file_index:
            try:
                with open(self.index_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(index_entry, ensure_ascii=False) + '\n')
            except Exception as ex:
                logger.error(f'Ошибка записи индекса архивов автозапуска: {ex}')

        self._cached_latest_report = report
        self._rotate_archives()
        return entry

    def record_snapshot(
        self,
        report: AuditReport,
        auto_diff: bool = True,
    ) -> tuple[StartupArchiveEntry, List[StartupChangeItem]]:
        """Сохранение снимка автозапуска с возвратом кортежа (архивная запись, список изменений).

        Args:
            report: Отчет аудита автозапуска.
            auto_diff: Выполнять ли вычисление изменений.

        Returns:
            tuple[StartupArchiveEntry, List[StartupChangeItem]]: Кортеж архива и списка изменений.
        """
        archive_entry = self.archive_report(report, auto_diff=auto_diff)
        return archive_entry, archive_entry.changes

    def _rotate_archives(self) -> None:
        """Ротация старых архивных файлов при превышении лимита."""
        try:
            json_files = sorted(self.archive_dir.glob('startup_*.json'), key=os.path.getmtime)
            if len(json_files) > self.max_archives:
                to_delete = json_files[:len(json_files) - self.max_archives]
                for p in to_delete:
                    try:
                        p.unlink()
                    except OSError:
                        pass
        except Exception as ex:
            logger.debug(f'Ошибка при ротации архивов автозапуска: {ex}')

    def get_latest_archive(self) -> Optional[StartupArchiveEntry]:
        """Получение самого свежего архива автозапуска из хранилища.

        Returns:
            Optional[StartupArchiveEntry]: Последний архив или None.
        """
        try:
            json_files = sorted(self.archive_dir.glob('startup_*.json'), key=os.path.getmtime, reverse=True)
            if json_files:
                latest_path = json_files[0]
                with open(latest_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return StartupArchiveEntry.model_validate(data)
        except Exception as ex:
            logger.error(f'Ошибка чтения последнего архива автозапуска: {ex}', exc_info=True)
        return None

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение сводного списка сохраненных архивов автозапуска.

        Args:
            limit: Максимальное количество записей архива.

        Returns:
            List[Dict[str, Any]]: Список метаданных архивов.
        """
        records: List[Dict[str, Any]] = []
        if not self.index_file.exists():
            return records
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            records.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        except Exception as ex:
            logger.debug(f'Ошибка чтения индекса архивов автозапуска: {ex}')
        return list(reversed(records))[:limit]

    def get_archive_by_id(self, archive_id: str) -> Optional[StartupArchiveEntry]:
        """Получение конкретного полного архивного снимка по ID.

        Args:
            archive_id: Идентификатор архива.

        Returns:
            Optional[StartupArchiveEntry]: Найденный архив или None.
        """
        safe_id = Path(archive_id).name
        target = self.archive_dir / f'{safe_id}.json'
        if not target.exists():
            target = self.archive_dir / safe_id
        if target.exists():
            try:
                with open(target, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return StartupArchiveEntry.model_validate(data)
            except Exception as ex:
                logger.debug(f'Ошибка загрузки архива автозапуска {archive_id}: {ex}')
        return None

    def get_change_timeline(self, limit: int = 100) -> List[StartupChangeItem]:
        """Получение сводного списка всех изменений автозапуска из архивов.

        Args:
            limit: Лимит изменений для возврата.

        Returns:
            List[StartupChangeItem]: Хронологический список зафиксированных изменений.
        """
        all_changes: List[StartupChangeItem] = []
        json_files = sorted(self.archive_dir.glob('startup_*.json'), key=os.path.getmtime, reverse=True)
        for p in json_files:
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    entry = StartupArchiveEntry.model_validate(data)
                    if entry.changes:
                        all_changes.extend(entry.changes)
                        if len(all_changes) >= limit:
                            break
            except Exception:
                continue
        return all_changes[:limit]

    # Алиас для удобства
    get_changes = get_change_timeline
