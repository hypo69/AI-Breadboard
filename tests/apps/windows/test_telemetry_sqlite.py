# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Apps Windows - Test Telemetry Sqlite
# =============================================================================
# Description:
#   Модульные тесты для базы данных телеметрии SQLite.
#
# Usage Examples:
#   Python API:
#     from tests.apps.windows.test_telemetry_sqlite import test_storage
#
#     res = test_storage()
#
# File: test_telemetry_sqlite.py
# Project: ai-breadboard
# Package: tests.apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

from __future__ import annotations
"""Модульные тесты для базы данных телеметрии SQLite."""

# -*- coding: utf-8 -*-
# Updated: 2026-10-01 10:05:00
"""Модульные тесты для базы данных телеметрии SQLite."""
import csv
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
import pytest
from unittest.mock import MagicMock
from apps.windows.telemetry.models import CpuMetrics, DiskIoMetrics, GpuMetrics, HardwareArchiveEntry, HardwareAuditReport, MemoryMetrics, ProcessMetrics, SystemSnapshot
from apps.windows.telemetry.sqlite import TelemetryStorage
from apps.windows.telemetry.service import TelemetryLoggerService
from apps.windows.telemetry.collector import SystemCollector
from apps.windows.telemetry_research.extractor import TelemetryDataExtractor

@pytest.fixture
def test_storage(tmp_path: Path) -> TelemetryStorage:
    """Создает изолированный экземпляр базы данных SQLite для тестов."""
    db_file = tmp_path / 'test_telemetry.db'
    return TelemetryStorage(db_path=db_file)

def _create_sample_snapshot() -> SystemSnapshot:
    """Вспомогательная функция для создания тестового SystemSnapshot."""
    return SystemSnapshot(timestamp=datetime.now(timezone.utc).isoformat(), hostname='TEST-PC', uptime_seconds=3600.0, cpu=CpuMetrics(total_percent=25.5, frequency_mhz=3800.0, per_core_percent=[20.0, 30.0]), memory=MemoryMetrics(total_gb=16.0, used_gb=8.0, percent=50.0, swap_percent=10.0), gpus=[GpuMetrics(name='NVIDIA GeForce RTX 3080', load_percent=45.0, temperature_celsius=62.0)], disk_io=DiskIoMetrics(read_bytes_per_sec=1024 * 1024, write_bytes_per_sec=2 * 1024 * 1024, read_count_per_sec=100, write_count_per_sec=200), top_processes=[ProcessMetrics(pid=1001, name='chrome.exe', status='running', cpu_percent=12.5, memory_mb=450.0, memory_percent=2.8, num_threads=24, username='DOMAIN\\user'), ProcessMetrics(pid=1002, name='python.exe', status='running', cpu_percent=8.0, memory_mb=210.0, memory_percent=1.3, num_threads=8, username='DOMAIN\\user')])

def test_storage_init_and_stats(test_storage: TelemetryStorage) -> None:
    """Тестирование создания базы данных и схемы таблиц."""
    stats = test_storage.get_storage_stats()
    assert stats['snapshots_count'] == 0
    assert stats['process_snapshots_count'] == 0
    assert stats['sensor_polls_count'] == 0
    assert stats['events_count'] == 0
    assert stats['hardware_audits_count'] == 0
    assert Path(stats['db_path']).exists()

def test_save_and_get_snapshots(test_storage: TelemetryStorage) -> None:
    """Тестирование сохранения и извлечения срезов системы и процессов."""
    snapshot = _create_sample_snapshot()
    snapshot_id = test_storage.save_snapshot(snapshot, top_n=10)
    assert snapshot_id > 0
    snapshots = test_storage.get_snapshots(limit=10)
    assert len(snapshots) == 1
    snap_data = snapshots[0]
    assert snap_data['hostname'] == 'TEST-PC'
    assert snap_data['cpu_total_percent'] == 25.5
    assert snap_data['memory_percent'] == 50.0
    assert snap_data['gpu_load_percent'] == 45.0
    assert snap_data['gpu_temp_c'] == 62.0
    procs = test_storage.get_snapshot_processes(snapshot_id)
    assert len(procs) == 2
    assert procs[0]['name'] == 'chrome.exe'
    assert procs[0]['pid'] == 1001
    assert procs[0]['cpu_percent'] == 12.5

def test_get_process_history(test_storage: TelemetryStorage) -> None:
    """Тестирование получения истории процесса по имени или PID."""
    snapshot = _create_sample_snapshot()
    test_storage.save_snapshot(snapshot)
    chrome_history = test_storage.get_process_history(name='chrome')
    assert len(chrome_history) == 1
    assert chrome_history[0]['name'] == 'chrome.exe'
    pid_history = test_storage.get_process_history(pid=1002)
    assert len(pid_history) == 1
    assert pid_history[0]['name'] == 'python.exe'

def test_save_sensor_polls_and_batch(test_storage: TelemetryStorage) -> None:
    """Тестирование сохранения отдельных замеров и пакета сенсоров."""
    sensor1 = {'id': 'cpu_temp_1', 'hardware_name': 'Intel Core i5', 'hardware_type': 'cpu', 'sensor_category': 'Temperatures', 'sensor_name': 'CPU Package', 'unit': '°C', 'value': 55.0}
    s_id = test_storage.save_sensor_poll(sensor1)
    assert s_id > 0
    batch = [{'id': 'fan_1', 'hardware_name': 'Mainboard', 'hardware_type': 'mainboard', 'sensor_category': 'Fans', 'sensor_name': 'Chassis Fan #1', 'unit': 'RPM', 'value': 1200.0}, {'id': 'gpu_temp_1', 'hardware_name': 'NVIDIA GPU', 'hardware_type': 'gpu', 'sensor_category': 'Temperatures', 'sensor_name': 'GPU Core', 'unit': '°C', 'value': 60.0}]
    batch_count = test_storage.save_sensor_polls_batch(batch)
    assert batch_count == 2
    temp_sensors = test_storage.get_sensor_history(category='Temperatures')
    assert len(temp_sensors) == 2
    latest = test_storage.get_latest_sensors()
    assert len(latest) == 3

def test_save_and_get_events(test_storage: TelemetryStorage) -> None:
    """Тестирование сохранения и фильтрации событий телеметрии."""
    ev1_id = test_storage.save_event(event_type='process_start', event_details={'process': 'notepad.exe', 'pid': 4567}, severity='info')
    assert ev1_id > 0
    ev2_id = test_storage.save_event(event_type='hardware_change', event_details={'device': 'USB Mouse', 'action': 'connected'}, severity='warning')
    assert ev2_id > 0
    all_events = test_storage.get_events()
    assert len(all_events) == 2
    hw_events = test_storage.get_events(event_type='hardware_change')
    assert len(hw_events) == 1
    assert hw_events[0]['severity'] == 'warning'

def test_save_hardware_archive(test_storage: TelemetryStorage) -> None:
    """Тестирование сохранения архивных снимков оборудования."""
    entry = HardwareArchiveEntry(archive_id='hw_test_001', timestamp=datetime.now(timezone.utc).isoformat(), devices_count=42, changes_count=1, report=HardwareAuditReport(timestamp=datetime.now(timezone.utc).isoformat(), hostname='TEST-HOST', devices_count=42, problem_devices_count=0, outdated_drivers_count=1))
    aid = test_storage.save_hardware_archive(entry)
    assert aid > 0
    stats = test_storage.get_storage_stats()
    assert stats['hardware_audits_count'] == 1

def test_cleanup_old_records(test_storage: TelemetryStorage) -> None:
    """Тестирование удаления устаревших записей телеметрии."""
    snapshot = _create_sample_snapshot()
    test_storage.save_snapshot(snapshot)
    test_storage.save_event('test_ev', {'msg': 'old'})
    deleted = test_storage.cleanup_old_records(retention_days=0)
    assert deleted >= 1
    stats = test_storage.get_storage_stats()
    assert stats['snapshots_count'] == 0
    assert stats['events_count'] == 0

@pytest.mark.skip(reason="Метод migrate_csv_to_db устарел")
def test_migrate_csv_to_db(tmp_path: Path, test_storage: TelemetryStorage) -> None:
    """Тестирование миграции исторических CSV файлов в SQLite базу данных."""
    csv_dir = tmp_path / 'csv_logs'
    csv_dir.mkdir()
    snap_csv = csv_dir / 'telemetry_20260924.csv'
    with open(snap_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'hostname', 'cpu_percent', 'memory_percent', 'gpu_load', 'disk_io_read', 'disk_io_write', 'network_recv', 'network_sent'])
        writer.writerow(['2026-09-24T12:00:00+03:00', 'TEST-HOST', 35.0, 60.0, 50.0, 1048576, 2097152, 50000, 10000])
    sensor_csv = csv_dir / 'hardware_monitor_polls.csv'
    with open(sensor_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'hardware', 'sensor_name', 'category', 'value', 'unit'])
        writer.writerow(['2026-09-24T12:00:00+03:00', 'CPU', 'Core Temp', 'Temperatures', 65.5, '°C'])
    results = test_storage.migrate_csv_to_db(csv_dir=csv_dir)
    assert results['snapshots'] == 1
    assert results['sensor_polls'] == 1
    stats = test_storage.get_storage_stats()
    assert stats['snapshots_count'] == 1
    assert stats['sensor_polls_count'] == 1
from unittest.mock import MagicMock

def test_service_with_sqlite_storage(test_storage: TelemetryStorage) -> None:
    """Тестирование работы сервиса TelemetryLoggerService с SQLite хранилищем."""
    mock_collector = MagicMock(spec=SystemCollector)
    service = TelemetryLoggerService(interval_sec=0.2, top_processes=5, collector=mock_collector, storage=test_storage)
    assert service.storage == test_storage
    ev_id = service.record_event('service_start', {'mode': 'test'})
    assert ev_id > 0
    events = test_storage.get_events(event_type='service_start')
    assert len(events) == 1
    status = service.get_status()
    assert 'storage_stats' in status
    assert status['storage_stats']['events_count'] == 1

def test_system_collector_db_methods(test_storage: TelemetryStorage) -> None:
    """Тестирование методов сохранения в БД у SystemCollector."""
    collector = SystemCollector(storage=test_storage, auditor=MagicMock(), history_manager=MagicMock())
    snap = _create_sample_snapshot()
    snap_id = collector.save_snapshot_to_db(snapshot=snap, top_n=5)
    assert snap_id > 0
    snapshots = collector.get_snapshots(limit=5)
    assert len(snapshots) == 1
    procs = collector.get_process_history(name='chrome')
    assert len(procs) == 1

def test_extractor_load_from_database(test_storage: TelemetryStorage) -> None:
    """Тестирование извлечения данных из базы SQLite в TelemetryDataExtractor."""
    snapshot = _create_sample_snapshot()
    test_storage.save_snapshot(snapshot)
    test_storage.save_event('custom_event', {'val': 123})
    extractor = TelemetryDataExtractor(storage=test_storage)
    db_records = extractor.load_from_database()
    assert len(db_records) >= 2
    all_recs = extractor.load_all_records(include_database=True)
    assert len(all_recs) >= 2

def test_get_latest_processes(test_storage: TelemetryStorage) -> None:
    """Тестирование извлечения процессов из последнего снимка в SQLite."""
    empty_procs = test_storage.get_latest_processes()
    assert empty_procs == []
    snap1 = _create_sample_snapshot()
    test_storage.save_snapshot(snap1)
    snap2 = _create_sample_snapshot()
    snap2.top_processes = [ProcessMetrics(pid=2001, name='worker.exe', status='running', cpu_percent=45.0, memory_mb=600.0, memory_percent=3.7, num_threads=16, num_handles=500, username='SYSTEM'), ProcessMetrics(pid=2002, name='helper.exe', status='running', cpu_percent=5.0, memory_mb=100.0, memory_percent=0.6, num_threads=4, num_handles=1200, username='SYSTEM')]
    test_storage.save_snapshot(snap2)
    latest_procs = test_storage.get_latest_processes(limit=10, sort_by='cpu')
    assert len(latest_procs) == 2
    assert latest_procs[0]['name'] == 'worker.exe'
    assert latest_procs[0]['cpu_percent'] == 45.0
    assert latest_procs[1]['name'] == 'helper.exe'
    handles_procs = test_storage.get_latest_processes(limit=0, sort_by='handles')
    assert len(handles_procs) == 2
    assert handles_procs[0]['name'] == 'helper.exe'
    assert handles_procs[0]['num_handles'] == 1200

def test_aggregate_process_metrics_2min_with_outliers(test_storage: TelemetryStorage) -> None:
    """Тестирование обобщения записей процессов старше 2 минут с сохранением выбросов."""
    old_time_epoch = datetime.now(timezone.utc).timestamp() - 180
    old_time_iso = datetime.fromtimestamp(old_time_epoch, tz=timezone.utc).isoformat()
    snap_old = _create_sample_snapshot()
    snap_old.timestamp = old_time_iso
    snap_old.top_processes = [ProcessMetrics(pid=3001, name='app.exe', status='running', cpu_percent=10.0, memory_mb=200.0, memory_percent=1.2, num_threads=4, username='USER'), ProcessMetrics(pid=3002, name='spike_task.exe', status='running', cpu_percent=88.5, memory_mb=500.0, memory_percent=3.1, num_threads=12, username='USER')]
    snap_id = test_storage.save_snapshot(snap_old)
    with test_storage._lock, test_storage._get_connection() as conn:
        conn.execute('UPDATE system_snapshots SET created_at = ? WHERE id = ?', (old_time_epoch, snap_id))
        conn.commit()
    snap_fresh = _create_sample_snapshot()
    test_storage.save_snapshot(snap_fresh)
    res = test_storage.aggregate_process_metrics_2min(cutoff_seconds=120, outlier_cpu_threshold=30.0)
    assert res['rollups_created'] >= 2
    assert res['outliers_saved'] >= 1
    assert res['raw_deleted'] >= 2
    stats = test_storage.get_process_stats(name='spike_task.exe')
    assert stats['total_outliers_count'] >= 1
    assert stats['outliers'][0]['cpu_percent'] == 88.5
    assert stats['outliers'][0]['name'] == 'spike_task.exe'
    assert len(stats['rollups_2min']) >= 1
    assert stats['rollups_2min'][0]['avg_cpu_percent'] == 88.5
    assert stats['rollups_2min'][0]['outliers_count'] == 1
    fresh_procs = test_storage.get_latest_processes()
    assert len(fresh_procs) > 0

def test_aggregate_process_metrics_daily(test_storage: TelemetryStorage) -> None:
    """Тестирование обобщения данных старше 1 дня в суточную статистику."""
    old_time_epoch = datetime.now(timezone.utc).timestamp() - 2 * 86400
    old_time_iso = datetime.fromtimestamp(old_time_epoch, tz=timezone.utc).isoformat()
    with test_storage._lock, test_storage._get_connection() as conn:
        conn.execute('\n            INSERT INTO process_rollups_2min (\n                period_start, period_end, period_start_epoch, period_end_epoch,\n                name, pid, username, sample_count, avg_cpu_percent, max_cpu_percent,\n                min_cpu_percent, avg_memory_mb, max_memory_mb, min_memory_mb,\n                avg_num_threads, outliers_count\n            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n        ', (old_time_iso, old_time_iso, old_time_epoch, old_time_epoch, 'daemon.exe', 4001, 'SYSTEM', 10, 15.0, 45.0, 5.0, 300.0, 350.0, 250.0, 8.0, 1))
        conn.commit()
    daily_res = test_storage.aggregate_process_metrics_daily(cutoff_days=1)
    assert daily_res['daily_rollups_created'] >= 1
    assert daily_res['2min_rollups_cleaned'] >= 1
    stats = test_storage.get_process_stats(name='daemon.exe')
    assert len(stats['daily_stats']) >= 1
    assert stats['daily_stats'][0]['name'] == 'daemon.exe'
    assert stats['daily_stats'][0]['sample_count'] == 10
    assert stats['daily_stats'][0]['avg_cpu_percent'] == 15.0
    assert stats['daily_stats'][0]['max_cpu_percent'] == 45.0


def test_memory_buffer_accumulation_and_flush(tmp_path: Path) -> None:
    """Тестирование накопления данных в буфере памяти и их сброса в SQLite."""
    db_file = tmp_path / 'buffered_telemetry.db'
    storage = TelemetryStorage(db_path=db_file, buffer_mode='memory', buffer_size=10, auto_flush=False)

    # Добавляем 2 события и 1 опрос сенсора
    storage.save_event('test_ev_1', {'key': 'val1'})
    storage.save_event('test_ev_2', {'key': 'val2'})
    storage.save_sensor_poll({'id': 'temp_cpu', 'sensor_category': 'Temperatures', 'sensor_name': 'CPU', 'value': 45.0})

    # Проверяем, что записи ожидают в буфере
    assert storage.get_buffered_count() == 3

    # Принудительный сброс
    flushed = storage.flush()
    assert flushed == 3
    assert storage.get_buffered_count() == 0

    # Проверяем наличие записей в базе данных
    events = storage.get_events()
    assert len(events) == 2
    sensors = storage.get_sensor_history(sensor_id='temp_cpu')
    assert len(sensors) == 1
    storage.close()


def test_buffer_auto_flush_on_threshold(tmp_path: Path) -> None:
    """Тестирование автоматического сброса буфера при достижении buffer_size."""
    db_file = tmp_path / 'threshold_telemetry.db'
    storage = TelemetryStorage(db_path=db_file, buffer_mode='memory', buffer_size=3, auto_flush=False)

    storage.save_event('ev1', {'n': 1})
    storage.save_event('ev2', {'n': 2})
    assert storage.get_buffered_count() == 2

    # 3-я запись должна вызвать автосброс
    storage.save_event('ev3', {'n': 3})
    assert storage.get_buffered_count() == 0

    events = storage.get_events()
    assert len(events) == 3
    storage.close()


def test_file_buffer_mode_and_crash_recovery(tmp_path: Path) -> None:
    """Тестирование аварийного режима буферизации в JSONL файл и восстановления после сбоя."""
    db_file = tmp_path / 'crash_telemetry.db'
    buffer_file = tmp_path / 'telemetry_buffer.jsonl'

    storage = TelemetryStorage(
        db_path=db_file,
        buffer_mode='file',
        buffer_size=10,
        buffer_file_path=buffer_file,
        auto_flush=False,
    )

    # Сохраняем снимок и события
    snap = _create_sample_snapshot()
    storage.save_snapshot(snap)
    storage.save_event('crash_event', {'status': 'power_failure_risk'})

    # Проверяем, что буферный файл JSONL существует на диске и содержит записи
    assert buffer_file.exists()
    assert buffer_file.stat().st_size > 0

    with open(buffer_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    assert len(lines) == 2

    # Имитируем падение/перезапуск приложения: создаем новый экземпляр с тем же файлом буфера
    storage_restarted = TelemetryStorage(
        db_path=db_file,
        buffer_mode='file',
        buffer_size=10,
        buffer_file_path=buffer_file,
        auto_flush=False,
    )

    # При инициализации остаточный буфер должен быть автоматически импортирован в SQLite
    snapshots = storage_restarted.get_snapshots()
    assert len(snapshots) == 1
    events = storage_restarted.get_events(event_type='crash_event')
    assert len(events) == 1

    # Файл буфера после сброса должен быть очищен
    assert buffer_file.stat().st_size == 0
    storage.close()
    storage_restarted.close()


def test_set_buffer_mode_dynamic(tmp_path: Path) -> None:
    """Тестирование динамического переключения режимов буферизации."""
    db_file = tmp_path / 'dynamic_mode.db'
    storage = TelemetryStorage(db_path=db_file, buffer_mode='memory', buffer_size=10, auto_flush=False)

    assert storage.get_buffer_mode() == 'memory'
    storage.save_event('mem_event', {'m': 'ram'})
    assert storage.get_buffered_count() == 1

    # Переключаем в режим 'file' -> должен произойти сброс памяти
    storage.set_buffer_mode('file')
    assert storage.get_buffer_mode() == 'file'
    assert storage.get_buffered_count() == 0

    # Проверяем, что mem_event записался в SQLite
    assert len(storage.get_events(event_type='mem_event')) == 1

    # Переключаем в 'direct'
    storage.set_buffer_mode('direct')
    assert storage.get_buffer_mode() == 'direct'
    storage.save_event('direct_event', {'m': 'direct'})

    # Запись сразу попадает в БД без буфера
    assert len(storage.get_events(event_type='direct_event')) == 1

    stats = storage.get_storage_stats()
    assert stats['buffer_mode'] == 'direct'
    assert 'buffer_file_path' in stats
    storage.close()


def test_legacy_process_snapshots_schema_migration(tmp_path: Path) -> None:
    """Тестирование автоматической миграции при запуске на базе данных с устаревшей схемой process_snapshots."""
    db_file = tmp_path / 'legacy_telemetry.db'
    
    # Создаем базу с устаревшей структурой (без integrity_level, elevation, num_handles)
    with sqlite3.connect(db_file) as conn:
        conn.execute('''
            CREATE TABLE system_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                created_at REAL NOT NULL,
                hostname TEXT,
                uptime_seconds REAL,
                cpu_total_percent REAL,
                cpu_frequency_mhz REAL,
                memory_total_gb REAL,
                memory_used_gb REAL,
                memory_percent REAL,
                swap_percent REAL,
                gpu_load_percent REAL,
                gpu_temp_c REAL,
                disk_read_bytes_sec REAL,
                disk_write_bytes_sec REAL,
                disk_read_count_sec REAL,
                disk_write_count_sec REAL,
                network_sent_bytes_sec REAL,
                network_recv_bytes_sec REAL
            )
        ''')
        conn.execute('''
            CREATE TABLE process_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                pid INTEGER NOT NULL,
                name TEXT NOT NULL,
                status TEXT,
                cpu_percent REAL,
                memory_mb REAL,
                memory_percent REAL,
                num_threads INTEGER,
                username TEXT,
                read_bytes_sec REAL,
                write_bytes_sec REAL
            )
        ''')
        conn.commit()

    # Инициализация TelemetryStorage должна выполнить миграцию схемы
    storage = TelemetryStorage(db_path=db_file, buffer_mode='direct')
    
    # Проверяем, что сохранение снимка с новыми полями integrity_level и elevation отрабатывает без ошибок
    snapshot = _create_sample_snapshot()
    snap_id = storage.save_snapshot(snapshot)
    assert snap_id > 0
    
    # Проверяем извлечение процессов
    procs = storage.get_snapshot_processes(snap_id)
    assert len(procs) == 2
    assert procs[0]['name'] == 'chrome.exe'
    
    # Проверяем, что колонки действительно добавлены в таблицу
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(process_snapshots)")
        cols = {row[1] for row in cursor.fetchall()}
        assert 'integrity_level' in cols
        assert 'elevation' in cols
        assert 'num_handles' in cols
        
    storage.close()
