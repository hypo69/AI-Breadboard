# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry Sqlite - Maintenance
# =============================================================================
# Description:
#   Обслуживание, очистка, агрегация и контроль размера базы данных SQLite.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.sqlite.maintenance import TelemetryMaintenance
#
#     maint = TelemetryMaintenance(connection_manager)
#     stats = maint.get_storage_stats()
#
# File: maintenance.py
# Project: ai-breadboard
# Package: apps.windows.telemetry.sqlite
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 01:59:00
# =============================================================================

from __future__ import annotations

"""Методы обслуживания, очистки старых записей, дефрагментации и агрегации телеметрии в SQLite."""

import sqlite3
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .connection import TelemetryConnectionManager

try:
    from logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class TelemetryMaintenance:
    """Выполняет регламентные операции: очистка, контроль размера, вакуумирование и агрегации."""

    def __init__(
        self,
        connection_manager: TelemetryConnectionManager,
        max_db_size_mb: float = 50.0,
        retention_days: int = 7,
        auto_vacuum_enabled: bool = True,
        buffer_file_path: Optional[Path] = None,
    ) -> None:
        """Инициализирует менеджер обслуживания базы данных.

        Args:
            connection_manager: Менеджер соединений SQLite.
            max_db_size_mb: Максимальный размер файлов БД в МБ.
            retention_days: Срок хранения сырых записей в днях.
            auto_vacuum_enabled: Флаг автоматического запуска VACUUM.
            buffer_file_path: Путь к файлу буфера.
        """
        self._cm = connection_manager
        self.max_db_size_mb = max(1.0, float(max_db_size_mb))
        self.retention_days = max(1, int(retention_days))
        self.auto_vacuum_enabled = bool(auto_vacuum_enabled)
        self.buffer_file_path = buffer_file_path or (self._cm.db_path.parent / 'telemetry_buffer.jsonl')

    def get_db_file_sizes(self) -> Dict[str, int]:
        """Возвращает физические размеры файлов БД на диске (DB, WAL, SHM) в байтах."""
        db_path = self._cm.db_path
        db_bytes = db_path.stat().st_size if db_path.exists() else 0
        wal_path = db_path.with_name(db_path.name + '-wal')
        shm_path = db_path.with_name(db_path.name + '-shm')
        wal_bytes = wal_path.stat().st_size if wal_path.exists() else 0
        shm_bytes = shm_path.stat().st_size if shm_path.exists() else 0
        return {
            'db_bytes': db_bytes,
            'wal_bytes': wal_bytes,
            'shm_bytes': shm_bytes,
            'total_bytes': db_bytes + wal_bytes + shm_bytes,
        }

    def get_total_db_size_mb(self) -> float:
        """Возвращает совокупный физический размер файлов БД в МБ."""
        sizes = self.get_db_file_sizes()
        return round(sizes['total_bytes'] / (1024.0 * 1024.0), 3)

    def checkpoint_wal(self) -> bool:
        """Сбрасывает WAL-журнал в основной файл базы данных."""
        if self._cm.read_only:
            return False
        with self._cm.lock:
            try:
                with self._cm.get_connection() as conn:
                    conn.execute('PRAGMA wal_checkpoint(TRUNCATE);')
                return True
            except Exception as e:
                logger.debug(f'Ошибка сброса WAL-журнала: {e}')
                return False

    def vacuum(self) -> bool:
        """Выполняет сжатие и дефрагментацию базы данных."""
        if self._cm.read_only:
            return False
        with self._cm.lock:
            self.checkpoint_wal()
            try:
                conn = sqlite3.connect(str(self._cm.db_path), timeout=30.0, isolation_level=None)
                try:
                    conn.execute('VACUUM;')
                finally:
                    conn.close()
                logger.info(f'Выполнен VACUUM для базы данных телеметрии ({self._cm.db_path})')
                return True
            except Exception as e:
                logger.warning(f'Ошибка при выполнении VACUUM: {e}')
                return False

    def get_storage_stats(self, buffered_count: int = 0, buffer_mode: str = 'memory', buffer_size: int = 50, flush_interval_seconds: float = 30.0) -> Dict[str, Any]:
        """Возвращает агрегированную статистику таблиц, размера и параметров."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM system_snapshots;')
            snap_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM process_snapshots;')
            proc_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM sensor_polls;')
            sensors_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM telemetry_events;')
            events_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM hardware_audits;')
            audits_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM app_polls;')
            app_polls_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM app_events;')
            app_events_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM app_param_changes;')
            app_params_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM custom_records;')
            custom_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM device_events;')
            device_events_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM device_inventory;')
            device_inventory_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM w64_events;')
            w64_events_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM process_outliers;')
            outliers_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM process_rollups_2min;')
            rollups_2min_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM process_rollups_daily;')
            rollups_daily_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM incidents;')
            incidents_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM telemetry_rollups;')
            rollups_count = cursor.fetchone()[0]

            def _safe_count(table: str) -> int:
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM {table};')
                    return cursor.fetchone()[0]
                except Exception:
                    return 0

            telemetry_hourly_count = _safe_count('telemetry_hourly')
            telemetry_daily_count = _safe_count('telemetry_daily')
            telemetry_weekly_count = _safe_count('telemetry_weekly')
            telemetry_monthly_count = _safe_count('telemetry_monthly')
            telemetry_yearly_count = _safe_count('telemetry_yearly')
            telemetry_spikes_count = _safe_count('telemetry_spikes')
            disk_inventory_count = _safe_count('disk_inventory')
            volume_inventory_count = _safe_count('volume_inventory')
            disk_health_count = _safe_count('disk_health_snapshots')
            disk_perf_count = _safe_count('disk_performance_samples')
            disk_io_count = _safe_count('disk_io_events')
            cpu_inventory_count = _safe_count('cpu_inventory')
            ram_module_inventory_count = _safe_count('ram_module_inventory')
            gpu_inventory_count = _safe_count('gpu_inventory')
            network_adapter_inventory_count = _safe_count('network_adapter_inventory')
            cpu_samples_count = _safe_count('cpu_telemetry_samples')
            ram_samples_count = _safe_count('ram_telemetry_samples')
            gpu_samples_count = _safe_count('gpu_telemetry_samples')
            network_samples_count = _safe_count('network_adapter_samples')

            file_sizes = self.get_db_file_sizes()
            size_mb = round(file_sizes['db_bytes'] / (1024 * 1024), 2)
            wal_size_mb = round(file_sizes['wal_bytes'] / (1024 * 1024), 2)
            total_size_mb = round(file_sizes['total_bytes'] / (1024 * 1024), 2)
            buffer_file_size = self.buffer_file_path.stat().st_size if self.buffer_file_path.exists() else 0

            return {
                'db_path': str(self._cm.db_path),
                'snapshots_count': snap_count,
                'process_snapshots_count': proc_count,
                'process_outliers_count': outliers_count,
                'process_rollups_2min_count': rollups_2min_count,
                'process_rollups_daily_count': rollups_daily_count,
                'incidents_count': incidents_count,
                'telemetry_rollups_count': rollups_count,
                'telemetry_hourly_count': telemetry_hourly_count,
                'telemetry_daily_count': telemetry_daily_count,
                'telemetry_weekly_count': telemetry_weekly_count,
                'telemetry_monthly_count': telemetry_monthly_count,
                'telemetry_yearly_count': telemetry_yearly_count,
                'telemetry_spikes_count': telemetry_spikes_count,
                'disk_inventory_count': disk_inventory_count,
                'volume_inventory_count': volume_inventory_count,
                'disk_health_count': disk_health_count,
                'disk_perf_count': disk_perf_count,
                'disk_io_count': disk_io_count,
                'cpu_inventory_count': cpu_inventory_count,
                'ram_module_inventory_count': ram_module_inventory_count,
                'gpu_inventory_count': gpu_inventory_count,
                'network_adapter_inventory_count': network_adapter_inventory_count,
                'cpu_samples_count': cpu_samples_count,
                'ram_samples_count': ram_samples_count,
                'gpu_samples_count': gpu_samples_count,
                'network_samples_count': network_samples_count,
                'sensor_polls_count': sensors_count,
                'events_count': events_count,
                'hardware_audits_count': audits_count,
                'app_polls_count': app_polls_count,
                'app_events_count': app_events_count,
                'app_param_changes_count': app_params_count,
                'custom_records_count': custom_count,
                'device_events_count': device_events_count,
                'device_inventory_count': device_inventory_count,
                'w64_events_count': w64_events_count,
                'file_size_mb': size_mb,
                'wal_size_mb': wal_size_mb,
                'total_size_mb': total_size_mb,
                'max_db_size_mb': self.max_db_size_mb,
                'retention_days': self.retention_days,
                'size_limit_exceeded': total_size_mb > self.max_db_size_mb,
                'buffer_mode': buffer_mode,
                'buffered_count': buffered_count,
                'buffer_size': buffer_size,
                'flush_interval_seconds': flush_interval_seconds,
                'buffer_file_path': str(self.buffer_file_path),
                'buffer_file_size_bytes': buffer_file_size,
            }

    def cleanup_old_records(self, retention_days: Optional[int] = None, vacuum_after: bool = False) -> int:
        """Удаляет устаревшие записи телеметрии."""
        if self._cm.read_only:
            return 0
        days = retention_days if retention_days is not None else self.retention_days
        threshold_epoch = datetime.now(timezone.utc).timestamp() - (float(days) * 86400.0 if days > 0 else -1.0)
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM system_snapshots WHERE created_at < ?', (threshold_epoch,))
            old_ids = [row[0] for row in cursor.fetchall()]
            if old_ids:
                cursor.execute('DELETE FROM process_snapshots WHERE snapshot_id IN (SELECT id FROM system_snapshots WHERE created_at < ?)', (threshold_epoch,))
                cursor.execute('DELETE FROM system_snapshots WHERE created_at < ?', (threshold_epoch,))
            cursor.execute('DELETE FROM sensor_polls WHERE created_at < ?', (threshold_epoch,))
            cursor.execute('DELETE FROM telemetry_events WHERE created_at < ?', (threshold_epoch,))
            cursor.execute('DELETE FROM app_polls WHERE created_at < ?', (threshold_epoch,))
            cursor.execute('DELETE FROM app_events WHERE created_at < ?', (threshold_epoch,))
            cursor.execute('DELETE FROM app_param_changes WHERE created_at < ?', (threshold_epoch,))
            cursor.execute('DELETE FROM custom_records WHERE created_at < ?', (threshold_epoch,))
            cursor.execute('DELETE FROM w64_events WHERE created_at < ?', (threshold_epoch,))
            cursor.execute('DELETE FROM process_outliers WHERE created_at < ?', (threshold_epoch,))
            cursor.execute('DELETE FROM device_events WHERE created_at < ?', (threshold_epoch,))
            cursor.execute('DELETE FROM system_extended_audits WHERE created_at < ?', (threshold_epoch,))
            cursor.execute('DELETE FROM disk_io_events WHERE created_at < ?', (threshold_epoch,))
            cursor.execute('DELETE FROM disk_performance_samples WHERE created_at < ?', (threshold_epoch,))
            cursor.execute('DELETE FROM disk_health_snapshots WHERE created_at < ?', (threshold_epoch,))
            cursor.execute('DELETE FROM cpu_telemetry_samples WHERE created_at < ?', (threshold_epoch,))
            cursor.execute('DELETE FROM ram_telemetry_samples WHERE created_at < ?', (threshold_epoch,))
            cursor.execute('DELETE FROM gpu_telemetry_samples WHERE created_at < ?', (threshold_epoch,))
            cursor.execute('DELETE FROM network_adapter_samples WHERE created_at < ?', (threshold_epoch,))
            conn.commit()
            deleted_count = len(old_ids)
            logger.info(f'Очищено {deleted_count} устаревших снимков телеметрии (старше {days} дн.)')

        if vacuum_after and self.auto_vacuum_enabled:
            self.vacuum()

        return deleted_count

    def enforce_size_limit(self, max_size_mb: Optional[float] = None, target_ratio: float = 0.85) -> Dict[str, Any]:
        """Ограничивает совокупный размер БД телеметрии."""
        if self._cm.read_only:
            return {'pruned': False, 'read_only': True}
        limit_mb = max_size_mb if max_size_mb is not None else self.max_db_size_mb
        initial_sizes = self.get_db_file_sizes()
        initial_size_mb = round(initial_sizes['total_bytes'] / (1024.0 * 1024.0), 3)

        if initial_size_mb <= limit_mb:
            return {
                'pruned': False,
                'initial_size_mb': initial_size_mb,
                'final_size_mb': initial_size_mb,
                'max_size_mb': limit_mb,
                'deleted_snapshots': 0,
                'deleted_records': 0,
            }

        target_mb = max(0.5, limit_mb * target_ratio)
        logger.warning(f'⚠️ Превышен лимит размера базы данных: {initial_size_mb:.2f} МБ > {limit_mb:.2f} МБ.')

        total_deleted_snaps = self.cleanup_old_records(retention_days=self.retention_days, vacuum_after=False)
        self.checkpoint_wal()

        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            while True:
                cursor.execute('SELECT COUNT(*) FROM system_snapshots;')
                snap_count = cursor.fetchone()[0]
                if not snap_count or snap_count <= 5:
                    break
                batch_size = max(5, int(snap_count * 0.25))
                cursor.execute('SELECT id, created_at FROM system_snapshots ORDER BY created_at ASC LIMIT ?', (batch_size,))
                rows = cursor.fetchall()
                if not rows:
                    break
                ids_to_del = [r[0] for r in rows]
                cutoff_t = rows[-1][1]
                placeholders = ','.join('?' for _ in ids_to_del)
                cursor.execute(f'DELETE FROM process_snapshots WHERE snapshot_id IN ({placeholders})', ids_to_del)
                cursor.execute(f'DELETE FROM system_snapshots WHERE id IN ({placeholders})', ids_to_del)
                cursor.execute('DELETE FROM sensor_polls WHERE created_at <= ?', (cutoff_t,))
                cursor.execute('DELETE FROM w64_events WHERE created_at <= ?', (cutoff_t,))
                cursor.execute('DELETE FROM app_polls WHERE created_at <= ?', (cutoff_t,))
                cursor.execute('DELETE FROM custom_records WHERE created_at <= ?', (cutoff_t,))
                conn.commit()
                total_deleted_snaps += len(ids_to_del)
                if snap_count - len(ids_to_del) <= 5:
                    break

        if self.auto_vacuum_enabled:
            self.vacuum()
        else:
            self.checkpoint_wal()

        final_sizes = self.get_db_file_sizes()
        final_size_mb = round(final_sizes['total_bytes'] / (1024.0 * 1024.0), 3)

        return {
            'pruned': True,
            'initial_size_mb': initial_size_mb,
            'final_size_mb': final_size_mb,
            'max_size_mb': limit_mb,
            'target_size_mb': target_mb,
            'deleted_snapshots': total_deleted_snaps,
        }

    def aggregate_process_metrics_2min(self, cutoff_seconds: int = 120, outlier_cpu_threshold: float = 30.0) -> Dict[str, int]:
        """Обобщает процессы старше двух минут по средним показателям."""
        if self._cm.read_only:
            return {'rollups_created': 0, 'outliers_saved': 0, 'raw_deleted': 0}
        now_epoch = datetime.now(timezone.utc).timestamp()
        cutoff_epoch = now_epoch - cutoff_seconds
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.id, p.snapshot_id, p.timestamp, p.pid, p.name, p.status,
                       p.cpu_percent, p.memory_mb, p.memory_percent, p.num_threads,
                       p.username, s.created_at as snap_epoch
                FROM process_snapshots p
                JOIN system_snapshots s ON p.snapshot_id = s.id
                WHERE s.created_at < ?
                ORDER BY p.name, p.pid, s.created_at ASC
            ''', (cutoff_epoch,))
            raw_rows = cursor.fetchall()
            if not raw_rows:
                return {'rollups_created': 0, 'outliers_saved': 0, 'raw_deleted': 0}

            outlier_rows = []
            for r in raw_rows:
                cpu_val = float(r['cpu_percent'] or 0.0)
                if cpu_val >= outlier_cpu_threshold:
                    outlier_rows.append((
                        r['snapshot_id'], r['timestamp'], r['snap_epoch'], r['pid'], r['name'],
                        r['status'] or 'running', cpu_val, float(r['memory_mb'] or 0.0),
                        float(r['memory_percent'] or 0.0), int(r['num_threads'] or 1),
                        r['username'] or '', f'Outlier: CPU={cpu_val:.1f}%',
                    ))
            outliers_saved = 0
            if outlier_rows:
                cursor.executemany('''
                    INSERT INTO process_outliers (
                        snapshot_id, timestamp, created_at, pid, name, status,
                        cpu_percent, memory_mb, memory_percent, num_threads, username, details
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', outlier_rows)
                outliers_saved = len(outlier_rows)

            grouped = defaultdict(list)
            for r in raw_rows:
                grouped[(r['name'], r['pid'])].append(r)

            rollup_rows = []
            for (p_name, p_pid), procs in grouped.items():
                cnt = len(procs)
                cpus = [float(p['cpu_percent'] or 0.0) for p in procs]
                mems = [float(p['memory_mb'] or 0.0) for p in procs]
                threads = [int(p['num_threads'] or 1) for p in procs]
                proc_outliers = sum(1 for c in cpus if c >= outlier_cpu_threshold)
                rollup_rows.append((
                    procs[0]['timestamp'], procs[-1]['timestamp'], procs[0]['snap_epoch'], procs[-1]['snap_epoch'],
                    p_name, p_pid, procs[-1]['username'] or '', cnt, round(sum(cpus) / cnt, 2),
                    round(max(cpus), 2), round(min(cpus), 2), round(sum(mems) / cnt, 2),
                    round(max(mems), 2), round(min(mems), 2), round(sum(threads) / cnt, 1), proc_outliers,
                ))

            if rollup_rows:
                cursor.executemany('''
                    INSERT INTO process_rollups_2min (
                        period_start, period_end, period_start_epoch, period_end_epoch,
                        name, pid, username, sample_count, avg_cpu_percent, max_cpu_percent,
                        min_cpu_percent, avg_memory_mb, max_memory_mb, min_memory_mb,
                        avg_num_threads, outliers_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', rollup_rows)

            raw_ids = [r['id'] for r in raw_rows]
            cursor.execute(f'''
                DELETE FROM process_snapshots WHERE id IN ({','.join(['?'] * len(raw_ids))})
            ''', raw_ids)
            conn.commit()
            return {'rollups_created': len(rollup_rows), 'outliers_saved': outliers_saved, 'raw_deleted': len(raw_ids)}

    def aggregate_process_metrics_daily(self, cutoff_days: int = 1) -> Dict[str, int]:
        """Обобщает агрегаты процессов в суточную статистику."""
        if self._cm.read_only:
            return {'daily_rollups_created': 0, '2min_rollups_cleaned': 0}
        now_epoch = datetime.now(timezone.utc).timestamp()
        cutoff_epoch = now_epoch - cutoff_days * 86400
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM process_rollups_2min WHERE period_end_epoch < ? ORDER BY name, period_start_epoch ASC', (cutoff_epoch,))
            old_rollups = cursor.fetchall()
            if not old_rollups:
                return {'daily_rollups_created': 0, '2min_rollups_cleaned': 0}

            grouped_daily = defaultdict(list)
            for r in old_rollups:
                d_str = r['period_start'][:10] if len(r['period_start']) >= 10 else 'unknown'
                grouped_daily[(d_str, r['name'])].append(r)

            daily_rows = []
            for (d_str, p_name), items in grouped_daily.items():
                total_samples = sum(int(it['sample_count']) for it in items)
                if total_samples <= 0:
                    continue
                weighted_cpu = sum(float(it['avg_cpu_percent']) * int(it['sample_count']) for it in items) / total_samples
                weighted_mem = sum(float(it['avg_memory_mb']) * int(it['sample_count']) for it in items) / total_samples
                daily_rows.append((
                    d_str, p_name, total_samples, round(weighted_cpu, 2), round(max(float(it['max_cpu_percent']) for it in items), 2),
                    round(weighted_mem, 2), round(max(float(it['max_memory_mb']) for it in items), 2),
                    sum(int(it['outliers_count'] or 0) for it in items), max(it['period_end'] for it in items),
                ))

            if daily_rows:
                cursor.executemany('''
                    INSERT INTO process_rollups_daily (
                        date, name, sample_count, avg_cpu_percent, max_cpu_percent,
                        avg_memory_mb, max_memory_mb, outliers_count, last_seen
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', daily_rows)

            del_ids = [r['id'] for r in old_rollups]
            cursor.execute(f'DELETE FROM process_rollups_2min WHERE id IN ({','.join(['?'] * len(del_ids))})', del_ids)
            conn.commit()
            return {'daily_rollups_created': len(daily_rows), '2min_rollups_cleaned': len(del_ids)}
