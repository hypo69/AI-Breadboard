# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry Sqlite - Storage
# =============================================================================
# Description:
#   Главный фасад TelemetryStorage базы данных SQLite телеметрии.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.sqlite import TelemetryStorage
#
#     storage = TelemetryStorage.get_instance(read_only=True)
#     snapshots = storage.get_snapshots(limit=10)
#
# File: storage.py
# Project: ai-breadboard
# Package: apps.windows.telemetry.sqlite
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 05:41:00
# =============================================================================

from __future__ import annotations

"""Главный класс TelemetryStorage, объединяющий подсистемы чтения, записи, буферизации и обслуживания."""

import atexit
import os
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .aggregator import AggregationLevel, TelemetrySqlAggregator
from .buffer import TelemetryBuffer
from .connection import TelemetryConnectionManager
from .maintenance import TelemetryMaintenance
from .reader import TelemetryReader
from .schema import init_database_schema
from .writer import TelemetryWriter
from ..models import (
    HardwareArchiveEntry,
    ProcessLifecycleEvent,
    ProcessProvenanceInfo,
    StartupArchiveEntry,
    SystemMetricRollup,
    SystemSnapshot,
    TelemetryIncident,
)
from ..telemetry_config import TelemetryConfigManager

try:
    from logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class TelemetryStorage:
    """Универсальный фасад персистентного хранения и выборки телеметрии в SQLite."""

    _instance: Optional[TelemetryStorage] = None
    _ro_instance: Optional[TelemetryStorage] = None
    _lock = threading.RLock()

    def __init__(
        self,
        db_path: Optional[Union[str, Path]] = None,
        buffer_mode: Optional[str] = None,
        buffer_size: Optional[int] = None,
        flush_interval_seconds: Optional[float] = None,
        buffer_file_path: Optional[Union[str, Path]] = None,
        auto_flush: bool = True,
        max_db_size_mb: Optional[float] = None,
        retention_days: Optional[int] = None,
        auto_vacuum: Optional[bool] = None,
        read_only: bool = False,
    ) -> None:
        """Инициализирует подключение к SQLite базе данных телеметрии."""
        self.read_only = bool(read_only)

        # 1. Определение путей базы данных
        if db_path is None:
            programdata = os.environ.get('ProgramData') or os.environ.get('ALLUSERSPROFILE')
            if programdata and os.path.exists(programdata):
                base_dir = Path(programdata)
            else:
                appdata = os.environ.get('APPDATA') or os.environ.get('LOCALAPPDATA')
                base_dir = Path(appdata) if appdata and os.path.exists(appdata) else (Path.home() / '.config')

            ai_tel_dir = base_dir / 'AITelemetry' / 'data'
            if (ai_tel_dir / 'telemetry.db').is_file() or ai_tel_dir.is_dir():
                target_dir = ai_tel_dir
            else:
                target_dir = base_dir / 'AI-Breadboard' / 'apps' / 'windows' / 'telemetry' / 'logs'

            if not self.read_only:
                target_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = target_dir / 'telemetry.db'
        else:
            self.db_path = Path(db_path)
            if not self.read_only:
                self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 2. Конфигурация
        cfg_manager = None
        try:
            cfg_manager = TelemetryConfigManager()
        except Exception:
            cfg_manager = None

        raw_mode = buffer_mode or (cfg_manager.get_buffer_mode() if cfg_manager else 'memory')
        b_mode = raw_mode.lower() if raw_mode in ('memory', 'file', 'direct') else 'memory'
        b_size = int(buffer_size if buffer_size is not None else (cfg_manager.get_buffer_size() if cfg_manager else 50))
        f_interval = float(flush_interval_seconds if flush_interval_seconds is not None else (cfg_manager.get_flush_interval_seconds() if cfg_manager else 30.0))
        m_size = float(max_db_size_mb if max_db_size_mb is not None else (cfg_manager.get_max_db_size_mb() if cfg_manager else 50.0))
        r_days = int(retention_days if retention_days is not None else (cfg_manager.get_retention_days() if cfg_manager else 7))
        a_vacuum = bool(auto_vacuum if auto_vacuum is not None else (cfg_manager.is_auto_vacuum_enabled() if cfg_manager else True))

        # 3. Инициализация менеджера подключений
        self._cm = TelemetryConnectionManager(db_path=self.db_path, read_only=self.read_only, lock=self._lock)

        # 4. Инициализация схемы (только в режиме записи)
        if not self.read_only:
            try:
                with self._cm.lock, self._cm.get_connection() as conn:
                    init_database_schema(conn)
            except Exception as schema_err:
                logger.warning(f'Ошибка инициализации схемы базы данных: {schema_err}')

        # 5. Инициализация подсистем
        self._reader = TelemetryReader(self._cm)
        self._writer = TelemetryWriter(self._cm)
        self._buffer = TelemetryBuffer(
            connection_manager=self._cm,
            writer=self._writer,
            buffer_mode=b_mode,
            buffer_size=b_size,
            flush_interval_seconds=f_interval,
            buffer_file_path=buffer_file_path,
            auto_flush=auto_flush,
        )
        self._maintenance = TelemetryMaintenance(
            connection_manager=self._cm,
            max_db_size_mb=m_size,
            retention_days=r_days,
            auto_vacuum_enabled=a_vacuum,
            buffer_file_path=self._buffer.buffer_file_path,
        )
        self._aggregator = TelemetrySqlAggregator(self._cm)

        if not self.read_only:
            try:
                atexit.register(self.close)
            except Exception:
                pass

    @classmethod
    def get_instance(
        cls,
        db_path: Optional[Union[str, Path]] = None,
        read_only: bool = False,
    ) -> TelemetryStorage:
        """Возвращает синглтон-экземпляр хранилища телеметрии (для записи или только для чтения)."""
        with cls._lock:
            if read_only:
                if cls._ro_instance is None or (db_path is not None and cls._ro_instance.db_path != Path(db_path)):
                    cls._ro_instance = TelemetryStorage(db_path=db_path, read_only=True, auto_flush=False)
                return cls._ro_instance
            else:
                if cls._instance is None or (db_path is not None and cls._instance.db_path != Path(db_path)):
                    cls._instance = TelemetryStorage(db_path=db_path, read_only=False)
                return cls._instance

    def _get_connection(self) -> sqlite3.Connection:
        """Создает и настраивает соединение с базой данных SQLite."""
        return self._cm.get_connection()

    def get_connection(self) -> sqlite3.Connection:
        """Возвращает активное подключение к SQLite базе данных."""
        return self._cm.get_connection()

    @property
    def connection(self) -> sqlite3.Connection:
        """Свойство прямого доступа к подключению SQLite."""
        return self._cm.get_connection()

    @property
    def reader(self) -> TelemetryReader:
        """Подсистема чтения данных."""
        return self._reader

    @property
    def writer(self) -> TelemetryWriter:
        """Подсистема записи данных."""
        return self._writer

    @property
    def buffer(self) -> TelemetryBuffer:
        """Подсистема буферизации."""
        return self._buffer

    @property
    def maintenance(self) -> TelemetryMaintenance:
        """Подсистема регламентного обслуживания."""
        return self._maintenance

    @property
    def aggregator(self) -> TelemetrySqlAggregator:
        """Подсистема многоуровневой SQL-агрегации."""
        return self._aggregator

    # -------------------------------------------------------------------------
    # Делегирование методов буфера
    # -------------------------------------------------------------------------

    def set_buffer_mode(self, mode: str) -> None:
        self._buffer.set_buffer_mode(mode)

    def get_buffer_mode(self) -> str:
        return self._buffer.buffer_mode

    def set_flush_interval_seconds(self, interval: float) -> None:
        """Обновляет интервал таймера сброса буфера в SQLite."""
        self._buffer.set_flush_interval_seconds(interval)

    def get_buffered_count(self) -> int:
        return self._buffer.get_buffered_count()

    def flush(self) -> int:
        return self._buffer.flush()

    def close(self) -> None:
        self._aggregator.stop_background_scheduler()
        self._buffer.close()

    # -------------------------------------------------------------------------
    # Делегирование методов сохранения (Writer / Buffer)
    # -------------------------------------------------------------------------

    def save_snapshot(self, snapshot: SystemSnapshot, top_n: int = 20) -> int:
        if self._buffer.buffer_mode == 'direct':
            with self._cm.lock, self._cm.get_connection() as conn:
                snap_id = self._writer.insert_snapshot_row(conn.cursor(), {'data': snapshot, 'top_n': top_n})
                conn.commit()
                return snap_id
        snap_dict = snapshot if isinstance(snapshot, dict) else (snapshot.model_dump() if hasattr(snapshot, 'model_dump') else (vars(snapshot) if hasattr(snapshot, '__dict__') else snapshot))
        self._buffer.enqueue({'type': 'snapshot', 'data': snap_dict, 'top_n': top_n})
        return 1

    def save_sensor_poll(self, sensor_item: Dict[str, Any], timestamp: Optional[str] = None) -> int:
        if self._buffer.buffer_mode == 'direct':
            with self._cm.lock, self._cm.get_connection() as conn:
                row = self._writer.prepare_sensor_poll_row(sensor_item, timestamp)
                conn.cursor().execute('''
                    INSERT INTO sensor_polls (
                        sensor_id, timestamp, created_at, hardware_name, hardware_type,
                        sensor_category, sensor_name, unit, value, provider, provider_priority, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(sensor_id, timestamp) DO UPDATE SET
                        created_at = excluded.created_at, hardware_name = excluded.hardware_name,
                        hardware_type = excluded.hardware_type, sensor_category = excluded.sensor_category,
                        sensor_name = excluded.sensor_name, unit = excluded.unit, value = excluded.value,
                        provider = excluded.provider, provider_priority = excluded.provider_priority,
                        raw_json = excluded.raw_json
                ''', row)
                conn.commit()
                return 1
        self._buffer.enqueue({'type': 'sensor_poll', 'data': sensor_item, 'timestamp': timestamp})
        return 1

    def save_sensor_polls_batch(self, items: List[Dict[str, Any]], timestamp: Optional[str] = None, deduplicate: bool = True) -> int:
        if not items:
            return 0
        if deduplicate:
            from ..sensor_registry import SensorDeduplicator, SensorProvider
            deduplicator = SensorDeduplicator()
            for item in items:
                sensor_id = str(item.get('id', ''))
                value = item.get('value', 0.0)
                provider_raw = item.get('_provider', SensorProvider.SENSOR_COLLECTOR)
                if isinstance(provider_raw, str):
                    try:
                        provider = SensorProvider[provider_raw.upper()]
                    except KeyError:
                        provider = SensorProvider.SENSOR_COLLECTOR
                elif isinstance(provider_raw, SensorProvider):
                    provider = provider_raw
                else:
                    provider = SensorProvider.SENSOR_COLLECTOR
                deduplicator.add(sensor_id, provider, value)
            unique_providers = deduplicator.get_unique()
            items = [it for it in items if str(it.get('id', '')) in unique_providers]

        if not items:
            return 0
        if self._buffer.buffer_mode == 'direct':
            return self._writer.batch_insert_records([{'type': 'sensor_polls_batch', 'data': items, 'timestamp': timestamp}])
        self._buffer.enqueue({'type': 'sensor_polls_batch', 'data': items, 'timestamp': timestamp})
        return len(items)

    save_sensor_polls = save_sensor_polls_batch

    def save_sensor_aggregates_batch(self, aggregates: List[Dict[str, Any]]) -> int:
        if not aggregates:
            return 0
        if self._buffer.buffer_mode == 'direct':
            return self._writer.batch_insert_records([{'type': 'sensor_aggregates_batch', 'data': aggregates}])
        self._buffer.enqueue({'type': 'sensor_aggregates_batch', 'data': aggregates})
        return len(aggregates)

    def save_event(self, event_type: str, event_details: Dict[str, Any], severity: str = 'info', timestamp: Optional[str] = None) -> int:
        rec = {'type': 'event', 'event_type': event_type, 'details': event_details, 'severity': severity, 'timestamp': timestamp}
        if self._buffer.buffer_mode == 'direct':
            return self._writer.batch_insert_records([rec])
        self._buffer.enqueue(rec)
        return 1

    def save_hardware_archive(self, archive_entry: HardwareArchiveEntry) -> int:
        entry_dict = archive_entry if isinstance(archive_entry, dict) else (archive_entry.model_dump() if hasattr(archive_entry, 'model_dump') else (vars(archive_entry) if hasattr(archive_entry, '__dict__') else archive_entry))
        if self._buffer.buffer_mode == 'direct':
            return self._writer.batch_insert_records([{'type': 'hardware_archive', 'data': entry_dict}])
        self._buffer.enqueue({'type': 'hardware_archive', 'data': entry_dict})
        return 1

    def save_startup_archive(self, archive_entry: StartupArchiveEntry) -> int:
        """Сохраняет снимок аудита автозапуска и зафиксированные изменения в БД."""
        entry_dict = archive_entry if isinstance(archive_entry, dict) else (archive_entry.model_dump() if hasattr(archive_entry, 'model_dump') else (vars(archive_entry) if hasattr(archive_entry, '__dict__') else archive_entry))
        if self._buffer.buffer_mode == 'direct':
            return self._writer.batch_insert_records([{'type': 'startup_archive', 'data': entry_dict}])
        self._buffer.enqueue({'type': 'startup_archive', 'data': entry_dict})
        return 1

    def save_app_poll(self, app: str, poll_type: str, metric_name: str, value: Any, unit: str = '', status: str = 'OK', details: Any = '', timestamp: Optional[str] = None) -> int:
        rec = {'type': 'app_poll', 'app': app, 'poll_type': poll_type, 'metric_name': metric_name, 'value': value, 'unit': unit, 'status': status, 'details': details, 'timestamp': timestamp}
        if self._buffer.buffer_mode == 'direct':
            return self._writer.batch_insert_records([rec])
        self._buffer.enqueue(rec)
        return 1

    def save_app_event(self, app: str, event_type: str, status: str = 'OK', details: Any = '', timestamp: Optional[str] = None) -> int:
        rec = {'type': 'app_event', 'app': app, 'event_type': event_type, 'status': status, 'details': details, 'timestamp': timestamp}
        if self._buffer.buffer_mode == 'direct':
            return self._writer.batch_insert_records([rec])
        self._buffer.enqueue(rec)
        return 1

    def save_app_param_change(self, app: str, param_name: str, old_value: Any, new_value: Any, status: str = 'SUCCESS', user: str = 'system', details: Any = '', timestamp: Optional[str] = None) -> int:
        rec = {'type': 'app_param_change', 'app': app, 'param_name': param_name, 'old_value': old_value, 'new_value': new_value, 'status': status, 'user': user, 'details': details, 'timestamp': timestamp}
        if self._buffer.buffer_mode == 'direct':
            return self._writer.batch_insert_records([rec])
        self._buffer.enqueue(rec)
        return 1

    def save_app_polls_batch(self, polls: List[Dict[str, Any]]) -> int:
        if not polls:
            return 0
        if self._buffer.buffer_mode == 'direct':
            return self._writer.batch_insert_records([{'type': 'app_polls_batch', 'data': polls}])
        self._buffer.enqueue({'type': 'app_polls_batch', 'data': polls})
        return len(polls)

    def save_app_events_batch(self, events: List[Dict[str, Any]]) -> int:
        if not events:
            return 0
        if self._buffer.buffer_mode == 'direct':
            return self._writer.batch_insert_records([{'type': 'app_events_batch', 'data': events}])
        self._buffer.enqueue({'type': 'app_events_batch', 'data': events})
        return len(events)

    def save_app_param_changes_batch(self, param_changes: List[Dict[str, Any]]) -> int:
        if not param_changes:
            return 0
        if self._buffer.buffer_mode == 'direct':
            return self._writer.batch_insert_records([{'type': 'app_param_changes_batch', 'data': param_changes}])
        self._buffer.enqueue({'type': 'app_param_changes_batch', 'data': param_changes})
        return len(param_changes)

    def save_custom_record(self, source_file: str, payload: Dict[str, Any], timestamp: Optional[str] = None) -> int:
        rec = {'type': 'custom_record', 'source_file': source_file, 'payload': payload, 'timestamp': timestamp}
        if self._buffer.buffer_mode == 'direct':
            return self._writer.batch_insert_records([rec])
        self._buffer.enqueue(rec)
        return 1

    def save_device_event(self, event: Dict[str, Any], timestamp: Optional[str] = None) -> int:
        rec = {'type': 'device_event', 'data': event, 'timestamp': timestamp}
        if self._buffer.buffer_mode == 'direct':
            return self._writer.batch_insert_records([rec])
        self._buffer.enqueue(rec)
        return 1

    def save_w64_event(self, event_data: Dict[str, Any], provider: str = 'w64_collector') -> int:
        rec = {'type': 'w64_event', 'data': event_data, 'provider': provider}
        if self._buffer.buffer_mode == 'direct':
            return self._writer.batch_insert_records([rec])
        self._buffer.enqueue(rec)
        return 1

    def save_process_provenance_event(self, event: Union[ProcessLifecycleEvent, ProcessProvenanceInfo, Dict[str, Any]]) -> bool:
        ev_dict = event if isinstance(event, dict) else (event.model_dump() if hasattr(event, 'model_dump') else (vars(event) if hasattr(event, '__dict__') else event))
        if self._buffer.buffer_mode == 'direct':
            return self._writer.batch_insert_records([{'type': 'process_provenance_event', 'data': ev_dict}]) > 0
        self._buffer.enqueue({'type': 'process_provenance_event', 'data': ev_dict})
        return True

    def save_process_provenance_batch(self, events: List[Union[ProcessLifecycleEvent, ProcessProvenanceInfo, Dict[str, Any]]]) -> int:
        if not events:
            return 0
        ev_dicts = [e if isinstance(e, dict) else (e.model_dump() if hasattr(e, 'model_dump') else (vars(e) if hasattr(e, '__dict__') else e)) for e in events]
        if self._buffer.buffer_mode == 'direct':
            return self._writer.batch_insert_records([{'type': 'process_provenance_events_batch', 'data': ev_dicts}])
        self._buffer.enqueue({'type': 'process_provenance_events_batch', 'data': ev_dicts})
        return len(events)

    def save_incident(self, incident: TelemetryIncident) -> bool:
        return self._writer.batch_insert_records([{
            'type': 'incident',
            'data': incident if isinstance(incident, dict) else (incident.model_dump() if hasattr(incident, 'model_dump') else (vars(incident) if hasattr(incident, '__dict__') else incident))
        }]) > 0 or True

    def save_system_rollup(self, rollup: SystemMetricRollup) -> bool:
        return self._writer.batch_insert_records([{
            'type': 'system_rollup',
            'data': rollup if isinstance(rollup, dict) else (rollup.model_dump() if hasattr(rollup, 'model_dump') else (vars(rollup) if hasattr(rollup, '__dict__') else rollup))
        }]) > 0 or True

    def save_reboot_session(self, session: Any) -> int:
        return self._writer.batch_insert_records([{
            'type': 'reboot_session',
            'data': session if isinstance(session, dict) else (session.model_dump() if hasattr(session, 'model_dump') else (vars(session) if hasattr(session, '__dict__') else session))
        }]) or 1

    def save_extended_audit(self, audit: Any, timestamp: Optional[str] = None) -> int:
        return self._writer.batch_insert_records([{
            'type': 'extended_audit',
            'data': audit if isinstance(audit, dict) else (audit.model_dump() if hasattr(audit, 'model_dump') else (vars(audit) if hasattr(audit, '__dict__') else audit)),
            'timestamp': timestamp,
        }]) or 1

    # -------------------------------------------------------------------------
    # Делегирование методов чтения (Reader)
    # -------------------------------------------------------------------------

    def get_snapshots(self, limit: int = 60, since_epoch: Optional[float] = None) -> List[Dict[str, Any]]:
        return self._reader.get_snapshots(limit=limit, since_epoch=since_epoch)

    def get_latest_snapshot_full(self) -> Optional[Dict[str, Any]]:
        """Извлекает и десериализует последний системный снимок со всеми метаданными и процессами."""
        return self._reader.get_latest_snapshot_full()

    def get_latest_cpu(self) -> Optional[Dict[str, Any]]:
        return self._reader.get_latest_cpu()

    def get_cpu_history(self, limit: int = 60, since_epoch: Optional[float] = None) -> List[Dict[str, Any]]:
        return self._reader.get_cpu_history(limit=limit, since_epoch=since_epoch)

    def get_latest_storage_data(self) -> Dict[str, Any]:
        return self._reader.get_latest_storage_data()

    def get_snapshot_processes(self, snapshot_id: int) -> List[Dict[str, Any]]:
        return self._reader.get_snapshot_processes(snapshot_id=snapshot_id)

    def get_process_history(self, name: Optional[str] = None, pid: Optional[int] = None, limit: int = 100) -> List[Dict[str, Any]]:
        return self._reader.get_process_history(name=name, pid=pid, limit=limit)

    def get_process_provenance_history(self, **kwargs: Any) -> List[Dict[str, Any]]:
        return self._reader.get_process_provenance_history(**kwargs)

    def get_process_lineage(self, guid_or_pid: Union[str, int]) -> List[Dict[str, Any]]:
        return self._reader.get_process_lineage(guid_or_pid=guid_or_pid)

    def get_latest_processes(self, limit: int = 50, sort_by: str = 'cpu') -> List[Dict[str, Any]]:
        return self._reader.get_latest_processes(limit=limit, sort_by=sort_by)

    def get_process_stats(self, name: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        return self._reader.get_process_stats(name=name, limit=limit)

    def get_events(self, event_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        return self._reader.get_events(event_type=event_type, limit=limit)

    def get_sensor_history(self, sensor_id: Optional[str] = None, category: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        return self._reader.get_sensor_history(sensor_id=sensor_id, category=category, limit=limit)

    def get_latest_sensors(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        return self._reader.get_latest_sensors(limit=limit)

    def get_cpu_hierarchy_metrics(self) -> Dict[str, Any]:
        """Извлекает иерархические метрики процессора, ядер, потоков и сенсоров из базы телеметрии."""
        return self._reader.get_cpu_hierarchy_metrics()

    def get_app_polls(self, app: Optional[str] = None, metric_name: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        return self._reader.get_app_polls(app=app, metric_name=metric_name, limit=limit)

    def get_app_events(self, app: Optional[str] = None, event_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        return self._reader.get_app_events(app=app, event_type=event_type, limit=limit)

    def get_app_param_changes(self, app: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        return self._reader.get_app_param_changes(app=app, limit=limit)

    def export_app_polls_to_csv(self, app: Optional[str] = None, output_path: Optional[Union[str, Path]] = None, limit: int = 50000) -> Path:
        return self._reader.export_app_polls_to_csv(app=app, output_path=output_path, limit=limit)

    def export_app_events_to_csv(self, app: Optional[str] = None, output_path: Optional[Union[str, Path]] = None, limit: int = 50000) -> Path:
        return self._reader.export_app_events_to_csv(app=app, output_path=output_path, limit=limit)

    def export_app_param_changes_to_csv(self, app: Optional[str] = None, output_path: Optional[Union[str, Path]] = None, limit: int = 50000) -> Path:
        return self._reader.export_app_param_changes_to_csv(app=app, output_path=output_path, limit=limit)

    def get_custom_records(self, source_file: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        return self._reader.get_custom_records(source_file=source_file, limit=limit)

    def get_device_events(self, event_type: Optional[str] = None, device_instance_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        return self._reader.get_device_events(event_type=event_type, device_instance_id=device_instance_id, limit=limit)

    def get_device_install_date(self, device_instance_id: str) -> Optional[str]:
        return self._reader.get_device_install_date(device_instance_id=device_instance_id)

    def get_or_create_device_install_date(
        self,
        device_instance_id: str,
        friendly_name: Optional[str] = None,
        device_class: Optional[str] = None,
        default_date: Optional[str] = None,
    ) -> str:
        """Возвращает существующую дату установки устройства или сохраняет новую."""
        existing = self._reader.get_device_install_date(device_instance_id)
        if existing:
            return existing
        date_to_save = default_date or datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M')
        if not self.read_only:
            try:
                with self._cm.lock, self._cm.get_connection() as conn:
                    cursor = conn.cursor()
                    self._writer.upsert_device_inventory(
                        cursor=cursor,
                        device_instance_id=device_instance_id,
                        friendly_name=friendly_name,
                        device_class=device_class,
                        install_date=date_to_save,
                    )
                    conn.commit()
            except Exception as ex:
                logger.debug(f'Ошибка сохранения инвентаря устройства: {ex}')
        return date_to_save

    def get_w64_events(self, event_type: Optional[str] = None, provider: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        return self._reader.get_w64_events(event_type=event_type, provider=provider, limit=limit)

    def get_incidents(self, limit: int = 50, trigger_type: Optional[str] = None, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        return self._reader.get_incidents(limit=limit, trigger_type=trigger_type, severity=severity)

    def get_system_rollups(self, tier: str = '1m', start_epoch: Optional[float] = None, end_epoch: Optional[float] = None, limit: int = 100) -> List[Dict[str, Any]]:
        return self._reader.get_system_rollups(tier=tier, start_epoch=start_epoch, end_epoch=end_epoch, limit=limit)

    def get_reboot_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._reader.get_reboot_history(limit=limit)

    def get_latest_reboot_session(self) -> Optional[Dict[str, Any]]:
        return self._reader.get_latest_reboot_session()

    def get_extended_audits(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._reader.get_extended_audits(limit=limit)

    def get_latest_extended_audit(self) -> Optional[Dict[str, Any]]:
        return self._reader.get_latest_extended_audit()

    def get_hardware_audits(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._reader.get_hardware_audits(limit=limit)

    def get_latest_hardware_audit(self) -> Optional[Dict[str, Any]]:
        return self._reader.get_latest_hardware_audit()

    def get_startup_archives(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._reader.get_startup_archives(limit=limit)

    def get_latest_startup_archive(self) -> Optional[Dict[str, Any]]:
        return self._reader.get_latest_startup_archive()

    def get_startup_changes(self, limit: int = 100, archive_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return self._reader.get_startup_changes(limit=limit, archive_id=archive_id)

    def get_telemetry_rollups(self, level: str = 'hourly', sensor_id: Optional[str] = None, start_epoch: Optional[float] = None, end_epoch: Optional[float] = None, limit: int = 100) -> List[Dict[str, Any]]:
        return self._reader.get_telemetry_rollups(level=level, sensor_id=sensor_id, start_epoch=start_epoch, end_epoch=end_epoch, limit=limit)

    def get_telemetry_spikes(self, sensor_id: Optional[str] = None, start_epoch: Optional[float] = None, limit: int = 100) -> List[Dict[str, Any]]:
        return self._reader.get_telemetry_spikes(sensor_id=sensor_id, start_epoch=start_epoch, limit=limit)

    def get_telemetry_time_ranges(self) -> Dict[str, Any]:
        """Возвращает временные диапазоны и доступные интервалы из БД телеметрии."""
        return self._reader.get_telemetry_time_ranges()

    def get_history_by_interval(self, interval: str = 'seconds', metric: str = 'all', limit: int = 120) -> List[Dict[str, Any]]:
        """Возвращает исторические срезы снимков под указанный интервал."""
        return self._reader.get_history_by_interval(interval=interval, metric=metric, limit=limit)

    # -------------------------------------------------------------------------
    # Делегирование методов хранилища накопителей (Storage Subsystem)
    # -------------------------------------------------------------------------

    def save_disk_inventory(self, disk_data: Any) -> None:
        """Сохранить или обновить паспорт физического накопителя."""
        rec = {'type': 'disk_inventory', 'data': disk_data}
        if self._buffer.buffer_mode == 'direct':
            self._writer.batch_insert_records([rec])
            return
        self._buffer.enqueue(rec)

    def save_volume_inventory(self, volume_data: Any) -> None:
        """Сохранить или обновить паспорт логического тома."""
        rec = {'type': 'volume_inventory', 'data': volume_data}
        if self._buffer.buffer_mode == 'direct':
            self._writer.batch_insert_records([rec])
            return
        self._buffer.enqueue(rec)

    def save_disk_health_snapshot(self, health_data: Any) -> None:
        """Сохранить снимок здоровья / SMART / TBW накопителя."""
        rec = {'type': 'disk_health', 'data': health_data}
        if self._buffer.buffer_mode == 'direct':
            self._writer.batch_insert_records([rec])
            return
        self._buffer.enqueue(rec)

    def save_disk_performance_sample(self, perf_data: Any) -> None:
        """Сохранить сэмпл производительности диска."""
        rec = {'type': 'disk_performance', 'data': perf_data}
        if self._buffer.buffer_mode == 'direct':
            self._writer.batch_insert_records([rec])
            return
        self._buffer.enqueue(rec)

    def save_disk_io_event(self, io_event_data: Any) -> None:
        """Сохранить событие прямого ввода-вывода."""
        rec = {'type': 'disk_io_event', 'data': io_event_data}
        if self._buffer.buffer_mode == 'direct':
            self._writer.batch_insert_records([rec])
            return
        self._buffer.enqueue(rec)

    def get_disk_inventory(self, disk_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Извлечь паспортные данные физических дисков."""
        return self._reader.get_disk_inventory(disk_id=disk_id)

    def get_volume_inventory(self) -> List[Dict[str, Any]]:
        """Извлечь паспортные данные логических томов."""
        return self._reader.get_volume_inventory()

    def get_disk_health_history(
        self,
        disk_id: Optional[int] = None,
        serial_number: Optional[str] = None,
        limit: int = 100,
        since_epoch: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Извлечь историю здоровья и SMART/TBW накопителей."""
        return self._reader.get_disk_health_history(disk_id=disk_id, serial_number=serial_number, limit=limit, since_epoch=since_epoch)

    def get_disk_performance_samples(
        self,
        disk_name: Optional[str] = None,
        limit: int = 100,
        since_epoch: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Извлечь сэмплы производительности дисков."""
        return self._reader.get_disk_performance_samples(disk_name=disk_name, limit=limit, since_epoch=since_epoch)

    def get_disk_io_events(
        self,
        pid: Optional[int] = None,
        disk_id: Optional[int] = None,
        limit: int = 100,
        since_epoch: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Извлечь события ввода-вывода процессов."""
        return self._reader.get_disk_io_events(pid=pid, disk_id=disk_id, limit=limit, since_epoch=since_epoch)

    # -------------------------------------------------------------------------
    # Делегирование методов хранилища процессоров (CPU Subsystem)
    # -------------------------------------------------------------------------

    def save_cpu_inventory(self, cpu_data: Any) -> None:
        """Сохранить или обновить паспорт процессора."""
        rec = {'type': 'cpu_inventory', 'data': cpu_data}
        if self._buffer.buffer_mode == 'direct':
            self._writer.batch_insert_records([rec])
            return
        self._buffer.enqueue(rec)

    def save_cpu_telemetry_sample(self, sample_data: Any) -> None:
        """Сохранить снимок телеметрии процессора."""
        rec = {'type': 'cpu_telemetry', 'data': sample_data}
        if self._buffer.buffer_mode == 'direct':
            self._writer.batch_insert_records([rec])
            return
        self._buffer.enqueue(rec)

    def get_cpu_inventory(self, processor_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Извлечь паспортные данные процессоров."""
        return self._reader.get_cpu_inventory(processor_id=processor_id)

    def get_cpu_telemetry_samples(
        self,
        processor_id: Optional[int] = None,
        limit: int = 100,
        since_epoch: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Извлечь историю метрик процессора."""
        return self._reader.get_cpu_telemetry_samples(processor_id=processor_id, limit=limit, since_epoch=since_epoch)

    # -------------------------------------------------------------------------
    # Делегирование методов хранилища памяти (RAM Module / SPD Subsystem)
    # -------------------------------------------------------------------------

    def save_ram_module_inventory(self, module_data: Any) -> None:
        """Сохранить или обновить паспорт планки оперативной памяти."""
        rec = {'type': 'ram_module_inventory', 'data': module_data}
        if self._buffer.buffer_mode == 'direct':
            self._writer.batch_insert_records([rec])
            return
        self._buffer.enqueue(rec)

    def save_ram_telemetry_sample(self, sample_data: Any) -> None:
        """Сохранить снимок телеметрии оперативной памяти."""
        rec = {'type': 'ram_telemetry', 'data': sample_data}
        if self._buffer.buffer_mode == 'direct':
            self._writer.batch_insert_records([rec])
            return
        self._buffer.enqueue(rec)

    def get_ram_module_inventory(self) -> List[Dict[str, Any]]:
        """Извлечь паспортные данные физических планок оперативной памяти."""
        return self._reader.get_ram_module_inventory()

    def get_ram_telemetry_samples(
        self,
        limit: int = 100,
        since_epoch: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Извлечь историю метрик оперативной памяти."""
        return self._reader.get_ram_telemetry_samples(limit=limit, since_epoch=since_epoch)

    # -------------------------------------------------------------------------
    # Делегирование методов хранилища графики (GPU Subsystem)
    # -------------------------------------------------------------------------

    def save_gpu_inventory(self, gpu_data: Any) -> None:
        """Сохранить или обновить паспорт графического ускорителя."""
        rec = {'type': 'gpu_inventory', 'data': gpu_data}
        if self._buffer.buffer_mode == 'direct':
            self._writer.batch_insert_records([rec])
            return
        self._buffer.enqueue(rec)

    def save_gpu_telemetry_sample(self, sample_data: Any) -> None:
        """Сохранить снимок телеметрии графического ускорителя."""
        rec = {'type': 'gpu_telemetry', 'data': sample_data}
        if self._buffer.buffer_mode == 'direct':
            self._writer.batch_insert_records([rec])
            return
        self._buffer.enqueue(rec)

    def get_gpu_inventory(self, gpu_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Извлечь паспортные данные GPU."""
        return self._reader.get_gpu_inventory(gpu_id=gpu_id)

    def get_gpu_telemetry_samples(
        self,
        gpu_id: Optional[int] = None,
        name: Optional[str] = None,
        limit: int = 100,
        since_epoch: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Извлечь историю метрик GPU."""
        return self._reader.get_gpu_telemetry_samples(gpu_id=gpu_id, name=name, limit=limit, since_epoch=since_epoch)

    # -------------------------------------------------------------------------
    # Делегирование методов хранилища сети (Network Adapter Subsystem)
    # -------------------------------------------------------------------------

    def save_network_adapter_inventory(self, adapter_data: Any) -> None:
        """Сохранить или обновить паспорт сетевого адаптера."""
        rec = {'type': 'network_adapter_inventory', 'data': adapter_data}
        if self._buffer.buffer_mode == 'direct':
            self._writer.batch_insert_records([rec])
            return
        self._buffer.enqueue(rec)

    def save_network_adapter_sample(self, sample_data: Any) -> None:
        """Сохранить сэмпл показателей сетевого адаптера."""
        rec = {'type': 'network_adapter_sample', 'data': sample_data}
        if self._buffer.buffer_mode == 'direct':
            self._writer.batch_insert_records([rec])
            return
        self._buffer.enqueue(rec)

    def get_network_adapter_inventory(self) -> List[Dict[str, Any]]:
        """Извлечь паспортные данные сетевых адаптеров."""
        return self._reader.get_network_adapter_inventory()

    def get_network_adapter_samples(
        self,
        adapter_name: Optional[str] = None,
        limit: int = 100,
        since_epoch: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Извлечь сэмплы показателей сетевых адаптеров."""
        return self._reader.get_network_adapter_samples(adapter_name=adapter_name, limit=limit, since_epoch=since_epoch)


    # -------------------------------------------------------------------------
    # Делегирование методов обслуживания (Maintenance)
    # -------------------------------------------------------------------------

    def get_db_file_sizes(self) -> Dict[str, int]:
        return self._maintenance.get_db_file_sizes()

    def get_total_db_size_mb(self) -> float:
        return self._maintenance.get_total_db_size_mb()

    def checkpoint_wal(self) -> bool:
        return self._maintenance.checkpoint_wal()

    def vacuum(self) -> bool:
        return self._maintenance.vacuum()

    def get_storage_stats(self) -> Dict[str, Any]:
        return self._maintenance.get_storage_stats(
            buffered_count=self.get_buffered_count(),
            buffer_mode=self.get_buffer_mode(),
            buffer_size=self._buffer.buffer_size,
            flush_interval_seconds=self._buffer.flush_interval_seconds,
        )

    get_stats = get_storage_stats

    def cleanup_old_records(self, retention_days: Optional[int] = None, vacuum_after: bool = False) -> int:
        return self._maintenance.cleanup_old_records(retention_days=retention_days, vacuum_after=vacuum_after)

    def enforce_size_limit(self, max_size_mb: Optional[float] = None, target_ratio: float = 0.85) -> Dict[str, Any]:
        return self._maintenance.enforce_size_limit(max_size_mb=max_size_mb, target_ratio=target_ratio)

    def prune_to_size(self, target_size_mb: float) -> Dict[str, Any]:
        return self.enforce_size_limit(max_size_mb=target_size_mb, target_ratio=0.95)

    def aggregate_process_metrics_2min(self, cutoff_seconds: int = 120, outlier_cpu_threshold: float = 30.0) -> Dict[str, int]:
        return self._maintenance.aggregate_process_metrics_2min(cutoff_seconds=cutoff_seconds, outlier_cpu_threshold=outlier_cpu_threshold)

    def aggregate_process_metrics_daily(self, cutoff_days: int = 1) -> Dict[str, int]:
        return self._maintenance.aggregate_process_metrics_daily(cutoff_days=cutoff_days)

    # -------------------------------------------------------------------------
    # Делегирование методов SQL-агрегации сенсоров (Aggregator)
    # -------------------------------------------------------------------------

    def aggregate_sensors(self, level: Union[AggregationLevel, str], start_epoch: Optional[float] = None, end_epoch: Optional[float] = None, detect_spikes: bool = True) -> Dict[str, Any]:
        return self._aggregator.aggregate(level=level, start_epoch=start_epoch, end_epoch=end_epoch, detect_spikes=detect_spikes)

    def aggregate_hourly(self, start_epoch: Optional[float] = None, end_epoch: Optional[float] = None, detect_spikes: bool = True) -> Dict[str, Any]:
        return self._aggregator.aggregate_hourly(start_epoch=start_epoch, end_epoch=end_epoch, detect_spikes=detect_spikes)

    def aggregate_daily(self, start_epoch: Optional[float] = None, end_epoch: Optional[float] = None) -> Dict[str, Any]:
        return self._aggregator.aggregate_daily(start_epoch=start_epoch, end_epoch=end_epoch)

    def aggregate_weekly(self, start_epoch: Optional[float] = None, end_epoch: Optional[float] = None) -> Dict[str, Any]:
        return self._aggregator.aggregate_weekly(start_epoch=start_epoch, end_epoch=end_epoch)

    def aggregate_monthly(self, start_epoch: Optional[float] = None, end_epoch: Optional[float] = None) -> Dict[str, Any]:
        return self._aggregator.aggregate_monthly(start_epoch=start_epoch, end_epoch=end_epoch)

    def aggregate_yearly(self, start_epoch: Optional[float] = None, end_epoch: Optional[float] = None) -> Dict[str, Any]:
        return self._aggregator.aggregate_yearly(start_epoch=start_epoch, end_epoch=end_epoch)

    def run_aggregation_pipeline(self, start_epoch: Optional[float] = None, end_epoch: Optional[float] = None, detect_spikes: bool = True) -> Dict[str, Any]:
        return self._aggregator.run_pipeline(start_epoch=start_epoch, end_epoch=end_epoch, detect_spikes=detect_spikes)

    def start_background_aggregator(self, interval_seconds: float = 300.0) -> None:
        """Запускает фоновый регламентный планировщик агрегации."""
        self._aggregator.start_background_scheduler(interval_seconds=interval_seconds)

    def stop_background_aggregator(self) -> None:
        """Останавливает фоновый регламентный планировщик агрегации."""
        self._aggregator.stop_background_scheduler()

    # -------------------------------------------------------------------------
    # Делегирование методов подсистем рефакторинга: Data-First SQLite
    # -------------------------------------------------------------------------

    # 1. Windows Event Logs
    def save_event_log_snapshot(self, snapshot_id: str, channels: List[Any], entries: List[Any], intelligence_profiles: Optional[List[Any]] = None) -> int:
        return self._writer.save_event_log_snapshot(snapshot_id, channels, entries, intelligence_profiles)

    def get_latest_event_log_channels(self) -> List[Dict[str, Any]]:
        return self._reader.get_latest_event_log_channels()

    def get_event_log_entries(self, channel: str = 'System', level: str = '', limit: int = 50, hours: int = 24) -> List[Dict[str, Any]]:
        return self._reader.get_event_log_entries(channel=channel, level=level, limit=limit, hours=hours)

    def get_latest_event_log_intelligence_profile(self, channel: str = 'System') -> Optional[Dict[str, Any]]:
        return self._reader.get_latest_event_log_intelligence_profile(channel=channel)

    def get_latest_event_log_report(self) -> Optional[Dict[str, Any]]:
        return self._reader.get_latest_event_log_report()

    # 2. Windows Firewall
    def save_firewall_snapshot(self, snapshot_id: str, profiles: Any, rules: List[Any]) -> int:
        return self._writer.save_firewall_snapshot(snapshot_id, profiles, rules)

    def update_firewall_rule_state(self, rule_name: str, enabled: bool) -> bool:
        return self._writer.update_firewall_rule_state(rule_name, enabled)

    def get_latest_firewall_profiles(self) -> Optional[Dict[str, Any]]:
        return self._reader.get_latest_firewall_profiles()

    def get_latest_firewall_rules(self, direction: Optional[str] = None, limit: int = 200) -> List[Dict[str, Any]]:
        return self._reader.get_latest_firewall_rules(direction=direction, limit=limit)

    # 3. Windows Services
    def save_services_snapshot(self, snapshot_id: str, services: List[Any]) -> int:
        return self._writer.save_services_snapshot(snapshot_id, services)

    def record_service_change(self, service_name: str, display_name: str, action: str, old_state: Optional[str] = None, new_state: Optional[str] = None, performed_by: str = 'SYSTEM', details: Optional[Dict[str, Any]] = None) -> int:
        return self._writer.record_service_change(service_name, display_name, action, old_state, new_state, performed_by, details)

    def get_latest_services_list(self, status: Optional[str] = None, limit: int = 500) -> List[Dict[str, Any]]:
        return self._reader.get_latest_services_list(status=status, limit=limit)

    def get_latest_services_report(self) -> Optional[Dict[str, Any]]:
        return self._reader.get_latest_services_report()

    def get_service_change_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self._reader.get_service_change_events(limit=limit)

    # 4. Throttling & Power
    def save_throttling_snapshot(self, snapshot_id: str, throttling_data: Any, thermal_zones: Optional[List[Any]] = None) -> int:
        return self._writer.save_throttling_snapshot(snapshot_id, throttling_data, thermal_zones)

    def get_latest_throttling_snapshot(self) -> Optional[Dict[str, Any]]:
        return self._reader.get_latest_throttling_snapshot()

    # 5. Forensics
    def save_forensics_snapshot(self, snapshot_id: str, forensics_data: Any) -> int:
        return self._writer.save_forensics_snapshot(snapshot_id, forensics_data)

    def get_latest_forensics_snapshot(self) -> Optional[Dict[str, Any]]:
        return self._reader.get_latest_forensics_snapshot()

    # 6. Process Leaks
    def save_process_leak_snapshot(self, snapshot_id: str, total_processes: Any, suspicious_count: int = 0, leak_items: Optional[List[Any]] = None) -> int:
        return self._writer.save_process_leak_snapshot(snapshot_id, total_processes, suspicious_count, leak_items)

    def get_latest_process_leak_report(self, limit: int = 20) -> Optional[Dict[str, Any]]:
        return self._reader.get_latest_process_leak_report(limit=limit)

    # 7. Defender
    def save_defender_snapshot(self, snapshot_id: str, defender_status: Any, exclusions: Optional[List[Any]] = None, asr_rules: Optional[List[Any]] = None, threats: Optional[List[Any]] = None) -> int:
        return self._writer.save_defender_snapshot(snapshot_id, defender_status, exclusions, asr_rules, threats)

    def get_latest_defender_status(self) -> Optional[Dict[str, Any]]:
        return self._reader.get_latest_defender_status()

    def get_latest_defender_exclusions(self, limit: int = 200) -> List[Dict[str, Any]]:
        return self._reader.get_latest_defender_exclusions(limit=limit)

    def get_latest_defender_asr_rules(self) -> List[Dict[str, Any]]:
        return self._reader.get_latest_defender_asr_rules()

    def get_latest_defender_threats(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._reader.get_latest_defender_threats(limit=limit)

    def get_latest_defender_diagnostics(self) -> Dict[str, Any]:
        return self._reader.get_latest_defender_diagnostics()

    # 8. Process Network & Process Manager
    def save_process_network_snapshot(self, snapshot_id: str, network_items: List[Any]) -> int:
        return self._writer.save_process_network_snapshot(snapshot_id, network_items)

    def get_latest_process_network_activity(self, limit: int = 100, only_internet: bool = True) -> List[Dict[str, Any]]:
        return self._reader.get_latest_process_network_activity(limit=limit, only_internet=only_internet)

    # 9. Software Transparency
    def save_software_inventory(self, apps: List[Any], storage_locations: Optional[List[Any]] = None, config_files: Optional[List[Any]] = None, ai_research: Optional[List[Any]] = None) -> int:
        return self._writer.save_software_inventory(apps, storage_locations, config_files, ai_research)

    def save_software_network_snapshots(self, snapshot_id: str, net_items: List[Any]) -> int:
        return self._writer.save_software_network_snapshots(snapshot_id, net_items)

    def get_software_inventory_from_db(self, limit: int = 200, offset: int = 0) -> List[Dict[str, Any]]:
        return self._reader.get_software_inventory_from_db(limit=limit, offset=offset)

    def get_software_app_details_from_db(self, app_id: str) -> Optional[Dict[str, Any]]:
        return self._reader.get_software_app_details_from_db(app_id=app_id)

    # 10. Security Events & Audit
    def save_security_events(
        self,
        events: List[Any],
        save_raw: bool = False,
        raw_events: Optional[List[Any]] = None,
    ) -> int:
        """Сохраняет события безопасности Windows в SQLite."""
        return self._writer.save_security_events(events, save_raw=save_raw, raw_events=raw_events)

    def save_security_bookmark(
        self,
        channel: str,
        last_record_id: int,
        bookmark_xml: Optional[str] = None,
        last_timestamp: str = '',
    ) -> None:
        """Сохраняет состояние закладки сбора событий в SQLite."""
        self._writer.save_security_bookmark(
            channel=channel,
            last_record_id=last_record_id,
            bookmark_xml=bookmark_xml,
            last_timestamp=last_timestamp,
        )

    def get_security_events(
        self,
        event_id: Optional[int] = None,
        user: Optional[str] = None,
        process_name: Optional[str] = None,
        pid: Optional[int] = None,
        channel: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        since_epoch: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Выборка нормализованных событий безопасности Windows."""
        return self._reader.get_security_events(
            event_id=event_id,
            user=user,
            process_name=process_name,
            pid=pid,
            channel=channel,
            limit=limit,
            offset=offset,
            since_epoch=since_epoch,
        )

    def get_security_failed_logons(self, limit: int = 50, hours: int = 24) -> List[Dict[str, Any]]:
        """Выборка неудачных попыток входа (Event 4625, 4771)."""
        return self._reader.get_security_failed_logons(limit=limit, hours=hours)

    def get_security_process_creations(
        self,
        process_name: Optional[str] = None,
        user: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Выборка запусков процессов (Event 4688) с командной строкой."""
        return self._reader.get_security_process_creations(
            process_name=process_name,
            user=user,
            limit=limit,
        )

    def get_security_bookmark(self, channel: str = 'Security') -> Optional[Dict[str, Any]]:
        """Получить сохраненную закладку канала."""
        return self._reader.get_security_bookmark(channel=channel)

    def get_security_stats(self) -> Dict[str, Any]:
        """Получить сводную статистику по событиям безопасности."""
        return self._reader.get_security_stats()

    def save_power_events(self, events: List[Any]) -> int:
        """Сохраняет события питания в SQLite."""
        return self._writer.save_power_events(events)

    def save_power_sessions(self, sessions: List[Any]) -> int:
        """Сохраняет реконструированные сессии питания в SQLite."""
        return self._writer.save_power_sessions(sessions)

    def get_power_sessions(
        self,
        limit: int = 50,
        offset: int = 0,
        shutdown_type: Optional[str] = None,
        unexpected_only: bool = False,
        clean_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """Извлечь список сессий питания операционной системы."""
        return self._reader.get_power_sessions(
            limit=limit,
            offset=offset,
            shutdown_type=shutdown_type,
            unexpected_only=unexpected_only,
            clean_only=clean_only,
        )

    def get_power_session_by_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Извлечь детальную информацию по конкретной сессии питания."""
        return self._reader.get_power_session_by_id(session_id=session_id)

    def get_power_events(
        self,
        limit: int = 100,
        offset: int = 0,
        event_id: Optional[Union[int, List[int]]] = None,
        event_type: Optional[str] = None,
        hours: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Извлечь события питания и жизненного цикла."""
        return self._reader.get_power_events(
            limit=limit,
            offset=offset,
            event_id=event_id,
            event_type=event_type,
            hours=hours,
        )

    def get_power_summary(self) -> Dict[str, Any]:
        """Получить сводную статистику по сессиям и событиям питания."""
        return self._reader.get_power_summary()

    def get_process_pid_snapshot(self, pid: int) -> Optional[Dict[str, Any]]:
        """Получить последний снимок метрик процесса по PID (< 5 мс)."""
        return self._reader.get_process_pid_snapshot(pid=pid)

    def get_process_file_events(
        self,
        pid: Optional[int] = None,
        directory: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Получить события файловой активности процесса."""
        return self._reader.get_process_file_events(pid=pid, directory=directory, limit=limit)

    def insert_process_pid_snapshots(self, snapshots: List[Union[Dict[str, Any], Any]]) -> int:
        """Сохранить снимки метрик процессов по PID."""
        return self._writer.insert_process_pid_snapshots(snapshots=snapshots)

    def insert_process_file_events(self, events: List[Union[Dict[str, Any], Any]]) -> int:
        """Сохранить события файловой активности."""
        return self._writer.insert_process_file_events(events=events)





