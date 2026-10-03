# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry - Sqlite
# =============================================================================
# Description:
#   Модуль персистентного хранения системной телеметрии в SQLite с поддержкой буферизации.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.sqlite import TelemetryStorage
#
#     instance = TelemetryStorage.get_instance()
#
# File: sqlite.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 00:16:00
# =============================================================================

from __future__ import annotations
"""Модуль персистентного хранения системной телеметрии в SQLite с поддержкой буферизации."""

import atexit
import json
import os
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
try:
    from logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from .models import HardwareArchiveEntry, SystemMetricRollup, SystemSnapshot, TelemetryIncident
from .telemetry_config import TelemetryConfigManager


class TelemetryStorage:
    """Менеджер базы данных SQLite для персистентного хранения телеметрии с буферизацией."""
    _instance: Optional[TelemetryStorage] = None
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
    ) -> None:
        """Инициализирует подключение к базе данных телеметрии и буфер сброса.

        Args:
            db_path: Путь к файлу SQLite базы данных (по умолчанию: logs/telemetry.db).
            buffer_mode: Режим буферизации ('memory', 'file', 'direct').
            buffer_size: Максимальное число записей в буфере перед сбросом.
            flush_interval_seconds: Интервал таймера сброса в секундах.
            buffer_file_path: Путь к файлу JSONL буфера при аварийном режиме сбоев.
            auto_flush: Флаг запуска фонового таймера автоматического сброса.
            max_db_size_mb: Максимальный размер файла базы данных в МБ (по умолчанию из config.json).
            retention_days: Срок хранения сырых записей в днях (по умолчанию 7).
            auto_vacuum: Флаг автоматического выполнения VACUUM при усечении.
        """
        # 1. Определение путей базы данных и логов
        if db_path is None:
            appdata = os.environ.get('APPDATA') or os.environ.get('LOCALAPPDATA')
            if appdata and os.path.exists(appdata):
                base_dir = Path(appdata)
            else:
                base_dir = Path.home() / '.config'
            target_dir = base_dir / 'AI-Breadboard' / 'apps' / 'windows' / 'telemetry' / 'logs'
            target_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = target_dir / 'telemetry.db'
            old_db_path = target_dir.parent / 'telemetry.db'
            if old_db_path.exists() and not self.db_path.exists():
                try:
                    import shutil
                    shutil.copy2(old_db_path, self.db_path)
                    logger.info(f'Существующая база данных скопирована из {old_db_path} в {self.db_path}')
                except Exception as ex:
                    logger.warning(f'Не удалось скопировать старую базу данных: {ex}')
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 2. Загрузка конфигурации буферизации и лимитов размера
        cfg_manager = None
        try:
            cfg_manager = TelemetryConfigManager()
        except Exception:
            cfg_manager = None

        raw_mode = buffer_mode or (cfg_manager.get_buffer_mode() if cfg_manager else 'memory')
        self._buffer_mode = raw_mode.lower() if raw_mode in ('memory', 'file', 'direct') else 'memory'

        raw_size = buffer_size if buffer_size is not None else (cfg_manager.get_buffer_size() if cfg_manager else 50)
        self._buffer_size = max(1, int(raw_size))

        raw_interval = flush_interval_seconds if flush_interval_seconds is not None else (
            cfg_manager.get_flush_interval_seconds() if cfg_manager else 30.0
        )
        self._flush_interval_seconds = max(0.5, float(raw_interval))

        raw_max_size = max_db_size_mb if max_db_size_mb is not None else (
            cfg_manager.get_max_db_size_mb() if cfg_manager else 50.0
        )
        self._max_db_size_mb = max(1.0, float(raw_max_size))

        raw_retention = retention_days if retention_days is not None else (
            cfg_manager.get_retention_days() if cfg_manager else 7
        )
        self._retention_days = max(1, int(raw_retention))

        if auto_vacuum is not None:
            self._auto_vacuum_enabled = bool(auto_vacuum)
        elif cfg_manager:
            self._auto_vacuum_enabled = cfg_manager.is_auto_vacuum_enabled()
        else:
            self._auto_vacuum_enabled = True

        if buffer_file_path is not None:
            self._buffer_file_path = Path(buffer_file_path)
        elif cfg_manager and cfg_manager.get_buffer_file():
            self._buffer_file_path = self.db_path.parent / cfg_manager.get_buffer_file()
        else:
            self._buffer_file_path = self.db_path.parent / 'telemetry_buffer.jsonl'
        self._buffer_file_path.parent.mkdir(parents=True, exist_ok=True)

        # 3. Инициализация буфера памяти и состояния таймера
        self._buffer: List[Dict[str, Any]] = []
        self._file_buffer_count: int = 0
        self._is_running = True
        self._flush_timer: Optional[threading.Timer] = None
        self._auto_flush = auto_flush

        self._init_db()

        # 4. Восстановление данных из аварийного JSON-буфера при запуске
        self._recover_file_buffer()

        # 5. Запуск таймера автосброса и регистрация atexit
        if self._auto_flush and self._buffer_mode != 'direct':
            self._start_flush_timer()

        try:
            atexit.register(self.close)
        except Exception:
            pass

    @classmethod
    def get_instance(cls, db_path: Optional[Union[str, Path]] = None) -> TelemetryStorage:
        """Возвращает синглтон-экземпляр хранилища телеметрии.

        Args:
            db_path: Путь к базе данных (при первой инициализации).

        Returns:
            TelemetryStorage: Экземпляр хранилища.
        """
        with cls._lock:
            if cls._instance is None or (db_path is not None and cls._instance.db_path != Path(db_path)):
                cls._instance = TelemetryStorage(db_path=db_path)
            return cls._instance

    def _get_connection(self) -> sqlite3.Connection:
        """Создает и настраивает соединение с базой данных SQLite.

        Returns:
            sqlite3.Connection: Активное соединение SQLite.
        """
        conn = sqlite3.connect(str(self.db_path), timeout=15.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA journal_mode = WAL;')
        conn.execute('PRAGMA synchronous = NORMAL;')
        conn.execute('PRAGMA foreign_keys = ON;')
        return conn

    def _init_db(self) -> None:
        """Инициализирует оптимизированную структуру таблиц и индексов в базе данных."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            
            # =========================================================================
            # ОСНОВНЫЕ ТАБЛИЦЫ ТЕЛЕМЕТРИИ
            # =========================================================================
            
            # 1. Системные снимки (основная таблица метрик)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    hostname TEXT,
                    uptime_seconds REAL,
                    os_name TEXT,
                    os_build TEXT,
                    os_install_date TEXT,
                    disks_json TEXT,
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
                );
            ''')
            
            # 2. Сенсоры (аппаратные датчики) с защитой от дублей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sensor_polls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sensor_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    hardware_name TEXT,
                    hardware_type TEXT,
                    sensor_category TEXT,
                    sensor_name TEXT,
                    unit TEXT,
                    value REAL,
                    provider TEXT,
                    provider_priority INTEGER DEFAULT 30,
                    raw_json TEXT,
                    UNIQUE(sensor_id, timestamp)
                );
            ''')
            
            # 3. Процессы (снимки процессов)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS process_snapshots (
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
                    num_handles INTEGER DEFAULT 0,
                    username TEXT,
                    read_bytes_sec REAL,
                    write_bytes_sec REAL,
                    integrity_level TEXT,
                    elevation INTEGER DEFAULT 0,
                    FOREIGN KEY (snapshot_id) REFERENCES system_snapshots(id) ON DELETE CASCADE
                );
            ''')
            
            # =========================================================================
            # АГРЕГИРОВАННЫЕ ДАННЫЕ
            # =========================================================================
            
            # 4. Почасовые агрегаты сенсоров
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sensor_aggregates_hourly (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sensor_id TEXT NOT NULL,
                    period_start TEXT NOT NULL,
                    period_end TEXT NOT NULL,
                    avg_value REAL,
                    min_value REAL,
                    max_value REAL,
                    count INTEGER
                );
            ''')
            
            # 5. Двухминутные агрегаты процессов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS process_rollups_2min (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    period_start TEXT NOT NULL,
                    period_end TEXT NOT NULL,
                    period_start_epoch REAL,
                    period_end_epoch REAL,
                    name TEXT NOT NULL,
                    pid INTEGER,
                    username TEXT,
                    sample_count INTEGER NOT NULL,
                    avg_cpu_percent REAL NOT NULL,
                    max_cpu_percent REAL NOT NULL,
                    min_cpu_percent REAL,
                    avg_memory_mb REAL NOT NULL,
                    max_memory_mb REAL NOT NULL,
                    min_memory_mb REAL,
                    avg_num_threads REAL,
                    outliers_count INTEGER DEFAULT 0
                );
            ''')

            # 6. Суточные агрегаты процессов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS process_rollups_daily (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    name TEXT NOT NULL,
                    sample_count INTEGER NOT NULL,
                    avg_cpu_percent REAL NOT NULL,
                    max_cpu_percent REAL NOT NULL,
                    avg_memory_mb REAL NOT NULL,
                    max_memory_mb REAL NOT NULL,
                    outliers_count INTEGER DEFAULT 0,
                    last_seen TEXT
                );
            ''')

            # 7. Бакеты сжатия временных рядов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS telemetry_rollups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    period_start TEXT NOT NULL,
                    period_end TEXT NOT NULL,
                    period_start_epoch REAL NOT NULL,
                    period_end_epoch REAL NOT NULL,
                    duration_seconds REAL NOT NULL,
                    sample_count INTEGER NOT NULL,
                    tier TEXT NOT NULL,
                    cpu_avg REAL,
                    cpu_min REAL,
                    cpu_max REAL,
                    cpu_p95 REAL,
                    ram_avg_gb REAL,
                    ram_min_gb REAL,
                    ram_max_gb REAL,
                    ram_percent_avg REAL,
                    ram_percent_max REAL,
                    disk_read_avg_mbs REAL,
                    disk_read_max_mbs REAL,
                    disk_read_total_mb REAL,
                    disk_write_avg_mbs REAL,
                    disk_write_max_mbs REAL,
                    disk_write_total_mb REAL,
                    network_rx_avg_mbs REAL,
                    network_rx_max_mbs REAL,
                    network_rx_total_mb REAL,
                    network_tx_avg_mbs REAL,
                    network_tx_max_mbs REAL,
                    network_tx_total_mb REAL,
                    raw_json TEXT
                );
            ''')
            
            # =========================================================================
            # СПЕЦИАЛИЗИРОВАННЫЕ ТАБЛИЦЫ
            # =========================================================================
            
            # 8. Аудит оборудования
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS hardware_audits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    archive_id TEXT UNIQUE NOT NULL,
                    timestamp TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    devices_count INTEGER DEFAULT 0,
                    problem_devices_count INTEGER DEFAULT 0,
                    outdated_drivers_count INTEGER DEFAULT 0,
                    changes_count INTEGER DEFAULT 0,
                    raw_json TEXT
                );
            ''')
            
            # 9. История перезагрузок
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reboot_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    boot_id TEXT UNIQUE NOT NULL,
                    boot_time TEXT NOT NULL,
                    previous_boot_time TEXT,
                    uptime_seconds REAL,
                    uptime_human TEXT,
                    shutdown_type TEXT NOT NULL,
                    likely_class TEXT,
                    conclusion TEXT,
                    created_at REAL NOT NULL
                );
            ''')
            
            # 10. Инциденты (обнаруженные аномалии)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    incident_id TEXT UNIQUE NOT NULL,
                    timestamp TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    trigger_type TEXT NOT NULL,
                    severity TEXT DEFAULT 'warning',
                    title TEXT NOT NULL,
                    description TEXT,
                    trigger_metrics_json TEXT,
                    suspect_processes_json TEXT,
                    related_events_json TEXT,
                    metrics_summary_json TEXT,
                    raw_window_json TEXT
                );
            ''')

            # 11. Произвольные события телеметрии
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS telemetry_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    event_type TEXT NOT NULL,
                    severity TEXT DEFAULT 'info',
                    event_details TEXT,
                    raw_json TEXT
                );
            ''')

            # 12. Опросы приложений
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_polls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    app TEXT NOT NULL,
                    poll_type TEXT,
                    metric_name TEXT,
                    value REAL,
                    unit TEXT,
                    status TEXT,
                    details TEXT,
                    raw_json TEXT
                );
            ''')

            # 13. События приложений
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    app TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    status TEXT,
                    message TEXT,
                    details TEXT,
                    raw_json TEXT
                );
            ''')

            # 14. Изменения параметров приложений
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_param_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    app TEXT NOT NULL,
                    param_name TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    status TEXT,
                    user TEXT,
                    details TEXT,
                    raw_json TEXT
                );
            ''')

            # 15. Произвольные пользовательские записи
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS custom_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    source_file TEXT,
                    payload_json TEXT
                );
            ''')

            # 16. События устройств (PnP / Device Events)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS device_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    event_type TEXT NOT NULL,
                    device_instance_id TEXT,
                    friendly_name TEXT,
                    device_class TEXT,
                    category TEXT,
                    has_problem INTEGER DEFAULT 0,
                    problem_code INTEGER DEFAULT 0,
                    status_code INTEGER DEFAULT 0,
                    manufacturer TEXT,
                    flapping_count INTEGER DEFAULT 0,
                    uptime_seconds REAL DEFAULT 0.0,
                    raw_json TEXT
                );
            ''')

            # 17. Системные события W64/ETW
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS w64_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER,
                    timestamp TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    event_type TEXT,
                    path TEXT,
                    pid INTEGER,
                    name TEXT,
                    provider TEXT,
                    raw_json TEXT
                );
            ''')

            # 18. Аномальные процессы (Process Outliers)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS process_outliers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_id INTEGER,
                    timestamp TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    pid INTEGER,
                    name TEXT,
                    status TEXT,
                    cpu_percent REAL,
                    memory_mb REAL,
                    memory_percent REAL,
                    num_threads INTEGER,
                    username TEXT,
                    details TEXT
                );
            ''')

            # 19. Расширенный системный аудит (Defender, Startup, VSS, Users)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_extended_audits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    hostname TEXT,
                    defender_cfa_enabled INTEGER DEFAULT 0,
                    defender_asr_count INTEGER DEFAULT 0,
                    defender_exclusions_count INTEGER DEFAULT 0,
                    defender_threats_count INTEGER DEFAULT 0,
                    startup_entries_count INTEGER DEFAULT 0,
                    vss_snapshots_count INTEGER DEFAULT 0,
                    users_total_count INTEGER DEFAULT 0,
                    users_admin_count INTEGER DEFAULT 0,
                    raw_json TEXT
                );
            ''')
            
            # =========================================================================
            # ИНДЕКСЫ ДЛЯ БЫСТРОГО ПОИСКА
            # =========================================================================
            
            # Системные снимки
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshots_created_at ON system_snapshots(created_at);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON system_snapshots(timestamp);')
            
            # Сенсоры
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sensor_polls_sensor_time ON sensor_polls(sensor_id, created_at);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sensor_polls_category ON sensor_polls(sensor_category, created_at);')
            
            # Процессы
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_processes_snapshot_id ON process_snapshots(snapshot_id);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_processes_name_pid ON process_snapshots(name, pid);')
            
            # Агрегаты
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_aggregates_sensor_time ON sensor_aggregates_hourly(sensor_id, period_start);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_rollups_daily_date ON process_rollups_daily(date, name);')
            
            # Аудит и инциденты
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_hardware_audits_archive_id ON hardware_audits(archive_id);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_reboot_history_boot_time ON reboot_history(boot_time);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_incidents_created_at ON incidents(created_at);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_incidents_trigger ON incidents(trigger_type);')

            # Устройства, W64, Аномалии и Аудит
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_device_events_created_at ON device_events(created_at);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_w64_events_created_at ON w64_events(created_at);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_process_outliers_created_at ON process_outliers(created_at);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_extended_audits_created_at ON system_extended_audits(created_at);')
            
            # =========================================================================
            # МИГРАЦИИ ДЛЯ СУЩЕСТВУЮЩИХ ТАБЛИЦ
            # =========================================================================
            
            # Миграция: добавляем provider_priority и UNIQUE constraint для sensor_polls
            try:
                # Проверяем наличие колонки provider_priority
                cursor.execute("PRAGMA table_info(sensor_polls)")
                columns = [row[1] for row in cursor.fetchall()]
                
                if 'provider_priority' not in columns:
                    logger.info('Миграция: добавление provider_priority в sensor_polls')
                    cursor.execute('ALTER TABLE sensor_polls ADD COLUMN provider_priority INTEGER DEFAULT 30')
                
                # Проверяем наличие UNIQUE constraint на (sensor_id, timestamp)
                cursor.execute("PRAGMA index_list(sensor_polls)")
                indexes = cursor.fetchall()
                has_unique = any(
                    'sensor_id' in str(idx) and 'timestamp' in str(idx) 
                    for idx in indexes
                )
                
                if not has_unique:
                    # SQLite не позволяет добавить UNIQUE к существующей таблице напрямую
                    # Создаём новую таблицу и копируем данные
                    logger.info('Миграция: добавление UNIQUE(sensor_id, timestamp) в sensor_polls')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS sensor_polls_new (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            sensor_id TEXT NOT NULL,
                            timestamp TEXT NOT NULL,
                            created_at REAL NOT NULL,
                            hardware_name TEXT,
                            hardware_type TEXT,
                            sensor_category TEXT,
                            sensor_name TEXT,
                            unit TEXT,
                            value REAL,
                            provider TEXT,
                            provider_priority INTEGER DEFAULT 30,
                            UNIQUE(sensor_id, timestamp)
                        )
                    ''')
                    cursor.execute('''
                        INSERT OR IGNORE INTO sensor_polls_new 
                        SELECT id, sensor_id, timestamp, created_at, hardware_name, hardware_type,
                               sensor_category, sensor_name, unit, value, provider, 
                               COALESCE(provider_priority, 30)
                        FROM sensor_polls
                    ''')
                    cursor.execute('DROP TABLE sensor_polls')
                    cursor.execute('ALTER TABLE sensor_polls_new RENAME TO sensor_polls')
                    # Восстанавливаем индексы
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sensor_polls_sensor_time ON sensor_polls(sensor_id, created_at)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sensor_polls_category ON sensor_polls(sensor_category, created_at)')
                    
            except Exception as migration_err:
                logger.warning(f'Миграция sensor_polls: {migration_err} (возможно, таблица уже обновлена)')

            # Миграция: добавляем severity, event_details, raw_json в telemetry_events
            try:
                cursor.execute("PRAGMA table_info(telemetry_events)")
                columns = [row[1] for row in cursor.fetchall()]
                if 'severity' not in columns:
                    cursor.execute("ALTER TABLE telemetry_events ADD COLUMN severity TEXT DEFAULT 'info'")
                if 'event_details' not in columns:
                    cursor.execute("ALTER TABLE telemetry_events ADD COLUMN event_details TEXT")
                if 'raw_json' not in columns:
                    cursor.execute("ALTER TABLE telemetry_events ADD COLUMN raw_json TEXT")
            except Exception as migration_err:
                logger.warning(f'Миграция telemetry_events: {migration_err}')

            # Миграция: добавляем os_name, os_build, os_install_date, disks_json в system_snapshots
            try:
                cursor.execute("PRAGMA table_info(system_snapshots)")
                columns = [row[1] for row in cursor.fetchall()]
                if 'os_name' not in columns:
                    cursor.execute("ALTER TABLE system_snapshots ADD COLUMN os_name TEXT")
                if 'os_build' not in columns:
                    cursor.execute("ALTER TABLE system_snapshots ADD COLUMN os_build TEXT")
                if 'os_install_date' not in columns:
                    cursor.execute("ALTER TABLE system_snapshots ADD COLUMN os_install_date TEXT")
                if 'hardware_audit' not in columns:
                    cursor.execute("ALTER TABLE system_snapshots ADD COLUMN hardware_audit TEXT")
            except Exception as migration_err:
                logger.warning(f'Миграция system_snapshots: {migration_err}')

            # Миграция: добавляем недостающие колонки в process_snapshots
            try:
                cursor.execute("PRAGMA table_info(process_snapshots)")
                proc_cols = {row[1] for row in cursor.fetchall()}
                if proc_cols:
                    if 'num_handles' not in proc_cols:
                        logger.info('Миграция: добавление num_handles в process_snapshots')
                        cursor.execute("ALTER TABLE process_snapshots ADD COLUMN num_handles INTEGER DEFAULT 0")
                    if 'read_bytes_sec' not in proc_cols:
                        logger.info('Миграция: добавление read_bytes_sec в process_snapshots')
                        cursor.execute("ALTER TABLE process_snapshots ADD COLUMN read_bytes_sec REAL")
                    if 'write_bytes_sec' not in proc_cols:
                        logger.info('Миграция: добавление write_bytes_sec в process_snapshots')
                        cursor.execute("ALTER TABLE process_snapshots ADD COLUMN write_bytes_sec REAL")
                    if 'integrity_level' not in proc_cols:
                        logger.info('Миграция: добавление integrity_level в process_snapshots')
                        cursor.execute("ALTER TABLE process_snapshots ADD COLUMN integrity_level TEXT")
                    if 'elevation' not in proc_cols:
                        logger.info('Миграция: добавление elevation в process_snapshots')
                        cursor.execute("ALTER TABLE process_snapshots ADD COLUMN elevation INTEGER DEFAULT 0")
            except Exception as migration_err:
                logger.warning(f'Миграция process_snapshots: {migration_err}')

            # Миграция: добавляем недостающие колонки в system_snapshots
            try:
                cursor.execute("PRAGMA table_info(system_snapshots)")
                snap_cols = {row[1] for row in cursor.fetchall()}
                if snap_cols:
                    expected_snap_cols = {
                        'os_install_date': 'TEXT',
                        'uptime_seconds': 'REAL',
                        'cpu_frequency_mhz': 'REAL',
                        'swap_percent': 'REAL',
                        'gpu_load_percent': 'REAL',
                        'gpu_temp_c': 'REAL',
                        'disk_read_bytes_sec': 'REAL',
                        'disk_write_bytes_sec': 'REAL',
                        'disk_read_count_sec': 'REAL',
                        'disk_write_count_sec': 'REAL',
                        'network_sent_bytes_sec': 'REAL',
                        'network_recv_bytes_sec': 'REAL',
                    }
                    for col_name, col_type in expected_snap_cols.items():
                        if col_name not in snap_cols:
                            logger.info(f'Миграция: добавление {col_name} в system_snapshots')
                            cursor.execute(f"ALTER TABLE system_snapshots ADD COLUMN {col_name} {col_type}")
            except Exception as migration_err:
                logger.warning(f'Миграция system_snapshots: {migration_err}')

            # Миграция: добавляем raw_json в sensor_polls
            try:
                cursor.execute("PRAGMA table_info(sensor_polls)")
                sensor_cols = {row[1] for row in cursor.fetchall()}
                if sensor_cols and 'raw_json' not in sensor_cols:
                    logger.info('Миграция: добавление raw_json в sensor_polls')
                    cursor.execute("ALTER TABLE sensor_polls ADD COLUMN raw_json TEXT")
            except Exception as migration_err:
                logger.warning(f'Миграция sensor_polls (raw_json): {migration_err}')
            
            conn.commit()

    # -------------------------------------------------------------------------
    # Управление буферизацией и таймером
    # -------------------------------------------------------------------------

    def set_buffer_mode(self, mode: str) -> None:
        """Переключает режим буферизации телеметрии.

        Args:
            mode: Новый режим ('memory', 'file', 'direct').
        """
        valid_mode = mode.lower() if mode.lower() in ('memory', 'file', 'direct') else 'memory'
        with self._lock:
            if self._buffer_mode != valid_mode:
                self.flush()
                self._buffer_mode = valid_mode
                if self._buffer_mode == 'direct':
                    self._stop_flush_timer()
                elif self._auto_flush and self._flush_timer is None:
                    self._start_flush_timer()
                logger.info(f'Режим буферизации телеметрии изменен на: {self._buffer_mode}')

    def get_buffer_mode(self) -> str:
        """Возвращает текущий режим буферизации ('memory', 'file', 'direct')."""
        return self._buffer_mode

    def get_buffered_count(self) -> int:
        """Возвращает текущее количество записей, ожидающих сброса в БД."""
        with self._lock:
            count = len(self._buffer)
            if self._buffer_file_path.exists():
                count += self._file_buffer_count
            return count

    def _start_flush_timer(self) -> None:
        """Запускает фоновый таймер периодического сброса буфера."""
        if not self._is_running:
            return
        self._stop_flush_timer()
        self._flush_timer = threading.Timer(self._flush_interval_seconds, self._on_flush_timer)
        self._flush_timer.daemon = True
        self._flush_timer.start()

    def _stop_flush_timer(self) -> None:
        """Останавливает активный таймер сброса буфера."""
        if self._flush_timer:
            try:
                self._flush_timer.cancel()
            except Exception:
                pass
            self._flush_timer = None

    def _on_flush_timer(self) -> None:
        """Обработчик срабатывания таймера сброса буфера."""
        try:
            self.flush()
        except Exception as ex:
            logger.error(f'Ошибка при автоматическом сбросе буфера телеметрии: {ex}')
        finally:
            if self._is_running and self._auto_flush and self._buffer_mode != 'direct':
                self._start_flush_timer()

    def _recover_file_buffer(self) -> None:
        """Восстанавливает и сбрасывает данные из аварийного JSON-файла при старте."""
        if self._buffer_file_path.exists() and self._buffer_file_path.stat().st_size > 0:
            logger.info(f'Обнаружен остаточный файл буфера телеметрии {self._buffer_file_path}, сброс в SQLite...')
            self.flush()

    def _enqueue_record(self, record: Dict[str, Any]) -> None:
        """Помещает запись в буфер памяти или JSON-файл аварийного режима.

        Args:
            record: Словарь записи с типом и полезной нагрузкой.
        """
        with self._lock:
            if self._buffer_mode == 'file':
                try:
                    line = json.dumps(record, ensure_ascii=False, default=str)
                    with open(self._buffer_file_path, 'a', encoding='utf-8') as f:
                        f.write(line + '\n')
                        f.flush()
                        os.fsync(f.fileno())
                    self._file_buffer_count += 1
                except Exception as ex:
                    logger.error(f'Ошибка записи в файл буфера телеметрии {self._buffer_file_path}: {ex}')
                    self._buffer.append(record)

                if self._file_buffer_count >= self._buffer_size:
                    self.flush()
            else:
                self._buffer.append(record)
                if len(self._buffer) >= self._buffer_size:
                    self.flush()

    def flush(self) -> int:
        """Принудительно сбрасывает все накопленные в памяти и в JSON-файле записи в базу данных SQLite.

        Returns:
            int: Количество успешно сброшенных и зафиксированных записей.
        """
        with self._lock:
            records_to_save: List[Dict[str, Any]] = []

            # 1. Извлечение записей из JSON-файла буфера (если есть)
            if self._buffer_file_path.exists() and self._buffer_file_path.stat().st_size > 0:
                try:
                    with open(self._buffer_file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            stripped = line.strip()
                            if stripped:
                                try:
                                    records_to_save.append(json.loads(stripped))
                                except Exception as parse_err:
                                    logger.warning(f'Не удалось распарсить строку из буфера телеметрии: {parse_err}')
                except Exception as read_err:
                    logger.error(f'Ошибка чтения файла буфера телеметрии: {read_err}')

            # 2. Извлечение записей из буфера памяти
            if self._buffer:
                records_to_save.extend(self._buffer)
                self._buffer = []

            if not records_to_save:
                return 0

            # 3. Пакетная вставка всех записей в единой SQLite транзакции
            inserted_count = self._batch_insert_records(records_to_save)

            # 4. Очистка файла буфера после успешного коммита
            if self._buffer_file_path.exists():
                try:
                    with open(self._buffer_file_path, 'w', encoding='utf-8') as f:
                        f.truncate(0)
                    self._file_buffer_count = 0
                except Exception as trunc_err:
                    logger.warning(f'Ошибка усечения файла буфера телеметрии: {trunc_err}')

            return inserted_count

    def close(self) -> None:
        """Останавливает таймер и выполняет финальный сброс буфера перед завершением."""
        self._is_running = False
        self._stop_flush_timer()
        try:
            self.flush()
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # Пакетная вставка в SQLite при сбросе (Flush)
    # -------------------------------------------------------------------------

    def _batch_insert_records(self, records: List[Dict[str, Any]]) -> int:
        """Выполняет пакетную вставку разнородных записей в SQLite в единой транзакции.

        Args:
            records: Список словарей записей.

        Returns:
            int: Общее число сохраненных записей.
        """
        if not records:
            return 0

        saved_total = 0
        with self._get_connection() as conn:
            cursor = conn.cursor()

            sensor_poll_rows: List[tuple] = []
            sensor_agg_rows: List[tuple] = []

            for item in records:
                rec_type = item.get('type')

                if rec_type == 'snapshot':
                    self._insert_snapshot_row(cursor, item)
                    saved_total += 1

                elif rec_type == 'sensor_poll':
                    row = self._prepare_sensor_poll_row(item.get('data', {}), item.get('timestamp'))
                    sensor_poll_rows.append(row)

                elif rec_type == 'sensor_polls_batch':
                    ts = item.get('timestamp')
                    for s in item.get('data', []):
                        sensor_poll_rows.append(self._prepare_sensor_poll_row(s, ts))

                elif rec_type == 'sensor_aggregates_batch':
                    for a in item.get('data', []):
                        sensor_agg_rows.append((
                            a.get('sensor_id', ''),
                            a.get('period_start', ''),
                            a.get('period_end', ''),
                            a.get('avg', None),
                            a.get('min', None),
                            a.get('max', None),
                            a.get('count', 0),
                        ))

                elif rec_type == 'hardware_archive':
                    self._insert_hardware_archive_row(cursor, item.get('data', {}))
                    saved_total += 1

                elif rec_type == 'event':
                    ts_str = item.get('timestamp') or datetime.now(timezone.utc).isoformat()
                    try:
                        now_epoch = datetime.fromisoformat(ts_str).timestamp()
                    except Exception:
                        now_epoch = datetime.now(timezone.utc).timestamp()
                    details_str = json.dumps(item.get('details', {}), ensure_ascii=False, default=str)
                    cursor.execute('''
                        INSERT INTO telemetry_events (
                            timestamp, created_at, event_type, severity, event_details, raw_json
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (ts_str, now_epoch, item.get('event_type', ''), item.get('severity', 'info'), details_str, details_str))
                    saved_total += 1

                elif rec_type == 'app_poll':
                    row = self._prepare_app_poll_row(item.get('data') or item)
                    cursor.execute('''
                        INSERT INTO app_polls (
                            timestamp, created_at, app, poll_type, metric_name, value, unit, status, details, raw_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', row)
                    saved_total += 1

                elif rec_type == 'app_polls_batch':
                    rows = [self._prepare_app_poll_row(p) for p in item.get('data', [])]
                    if rows:
                        cursor.executemany('''
                            INSERT INTO app_polls (
                                timestamp, created_at, app, poll_type, metric_name, value, unit, status, details, raw_json
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', rows)
                        saved_total += len(rows)

                elif rec_type == 'app_event':
                    row = self._prepare_app_event_row(item.get('data') or item)
                    cursor.execute('''
                        INSERT INTO app_events (
                            timestamp, created_at, app, event_type, status, details, raw_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', row)
                    saved_total += 1

                elif rec_type == 'app_events_batch':
                    rows = [self._prepare_app_event_row(ev) for ev in item.get('data', [])]
                    if rows:
                        cursor.executemany('''
                            INSERT INTO app_events (
                                timestamp, created_at, app, event_type, status, details, raw_json
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', rows)
                        saved_total += len(rows)

                elif rec_type == 'app_param_change':
                    row = self._prepare_app_param_row(item.get('data') or item)
                    cursor.execute('''
                        INSERT INTO app_param_changes (
                            timestamp, created_at, app, param_name, old_value, new_value, status, user, details, raw_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', row)
                    saved_total += 1

                elif rec_type == 'app_param_changes_batch':
                    rows = [self._prepare_app_param_row(pc) for pc in item.get('data', [])]
                    if rows:
                        cursor.executemany('''
                            INSERT INTO app_param_changes (
                                timestamp, created_at, app, param_name, old_value, new_value, status, user, details, raw_json
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', rows)
                        saved_total += len(rows)

                elif rec_type == 'custom_record':
                    ts_str = item.get('timestamp') or datetime.now(timezone.utc).isoformat()
                    try:
                        now_epoch = datetime.fromisoformat(ts_str).timestamp()
                    except Exception:
                        now_epoch = datetime.now(timezone.utc).timestamp()
                    payload_str = json.dumps(item.get('payload', {}), ensure_ascii=False, default=str)
                    cursor.execute('''
                        INSERT INTO custom_records (timestamp, created_at, source_file, payload_json)
                        VALUES (?, ?, ?, ?)
                    ''', (ts_str, now_epoch, item.get('source_file', ''), payload_str))
                    saved_total += 1

                elif rec_type == 'device_event':
                    row = self._prepare_device_event_row(item.get('data', {}), item.get('timestamp'))
                    cursor.execute('''
                        INSERT INTO device_events (
                            timestamp, created_at, event_type, device_instance_id,
                            friendly_name, device_class, category, has_problem,
                            problem_code, status_code, manufacturer,
                            flapping_count, uptime_seconds, raw_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', row)
                    saved_total += 1

                elif rec_type == 'w64_event':
                    row = self._prepare_w64_event_row(item.get('data', {}), item.get('provider', 'w64_collector'))
                    cursor.execute('''
                        INSERT INTO w64_events (
                            event_id, timestamp, created_at, event_type, path, pid, name, provider, raw_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', row)
                    saved_total += 1

            # Выполнение групповых вставок с UPSERT для защиты от дублей
            if sensor_poll_rows:
                # UPSERT: при конфликте (sensor_id, timestamp) обновляем только если новый провайдер имеет выше приоритет
                cursor.executemany('''
                    INSERT INTO sensor_polls (
                        sensor_id, timestamp, created_at, hardware_name, hardware_type,
                        sensor_category, sensor_name, unit, value, provider, provider_priority
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(sensor_id, timestamp) DO UPDATE SET
                        created_at = CASE WHEN excluded.provider_priority > provider_priority 
                                      THEN excluded.created_at ELSE created_at END,
                        hardware_name = CASE WHEN excluded.provider_priority > provider_priority 
                                       THEN excluded.hardware_name ELSE hardware_name END,
                        hardware_type = CASE WHEN excluded.provider_priority > provider_priority 
                                       THEN excluded.hardware_type ELSE hardware_type END,
                        sensor_category = CASE WHEN excluded.provider_priority > provider_priority 
                                          THEN excluded.sensor_category ELSE sensor_category END,
                        sensor_name = CASE WHEN excluded.provider_priority > provider_priority 
                                       THEN excluded.sensor_name ELSE sensor_name END,
                        unit = CASE WHEN excluded.provider_priority > provider_priority 
                                THEN excluded.unit ELSE unit END,
                        value = CASE WHEN excluded.provider_priority > provider_priority 
                              THEN excluded.value ELSE value END,
                        provider = CASE WHEN excluded.provider_priority > provider_priority 
                                  THEN excluded.provider ELSE provider END,
                        provider_priority = CASE WHEN excluded.provider_priority > provider_priority 
                                           THEN excluded.provider_priority ELSE provider_priority END
                ''', sensor_poll_rows)
                saved_total += len(sensor_poll_rows)

            if sensor_agg_rows:
                cursor.executemany('''
                    INSERT INTO sensor_aggregates_hourly (
                        sensor_id, period_start, period_end, avg_value, min_value, max_value, count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', sensor_agg_rows)
                saved_total += len(sensor_agg_rows)

            conn.commit()

        return saved_total

    def _prepare_sensor_poll_row(self, s: Dict[str, Any], timestamp: Optional[str] = None) -> tuple:
        """Подготавливает кортеж для вставки в sensor_polls с приоритетом провайдера.
        
        Returns:
            tuple: (sensor_id, timestamp, created_at, hardware_name, hardware_type,
                    sensor_category, sensor_name, unit, value, provider, provider_priority)
        """
        now_dt = datetime.now(timezone.utc)
        ts_str = timestamp or s.get('timestamp') or now_dt.isoformat()
        try:
            now_epoch = datetime.fromisoformat(ts_str).timestamp()
        except Exception:
            now_epoch = now_dt.timestamp()
        sid = str(s.get('id') or '')
        hw_name = s.get('hardware_name', 'System')
        hw_type = s.get('hardware_type', 'cpu')
        cat = s.get('sensor_category', 'General')
        s_name = s.get('sensor_name', 'Unknown')
        unit = s.get('unit', '')
        raw_val = s.get('value', s.get('value_num', 0.0))
        try:
            val_float = round(float(raw_val), 2)
        except (ValueError, TypeError):
            val_float = 0.0
        
        # Extract provider and priority for UPSERT deduplication
        provider_raw = s.get('_provider', 'sensor_collector')
        if hasattr(provider_raw, 'name'):
            provider_str = provider_raw.name
            provider_priority = provider_raw.value
        elif isinstance(provider_raw, str):
            provider_str = provider_raw.upper()
            # Get priority from SensorProvider enum
            try:
                from .sensor_registry import SensorProvider
                provider_priority = SensorProvider[provider_raw.upper()].value
            except (KeyError, ImportError):
                provider_priority = 30  # Default SENSOR_COLLECTOR priority
        else:
            provider_str = 'SENSOR_COLLECTOR'
            provider_priority = 30
        
        return (sid, ts_str, now_epoch, hw_name, hw_type, cat, s_name, unit, val_float, provider_str, provider_priority)

    def _prepare_app_poll_row(self, p: Dict[str, Any]) -> tuple:
        now_dt = datetime.now(timezone.utc)
        ts_str = p.get('timestamp') or now_dt.isoformat()
        try:
            now_epoch = datetime.fromisoformat(ts_str).timestamp()
        except Exception:
            now_epoch = now_dt.timestamp()
        app = p.get('app', 'unknown')
        poll_type = p.get('poll_type', 'poll')
        metric_name = p.get('metric_name', 'metric')
        val = p.get('value')
        try:
            val_num = float(val) if val is not None and not isinstance(val, (dict, list)) else None
        except (ValueError, TypeError):
            val_num = None
        unit = p.get('unit', '')
        status = p.get('status', 'OK')
        details = p.get('details', '')
        details_str = json.dumps(details, ensure_ascii=False) if isinstance(details, (dict, list)) else str(details or '')
        raw_json = json.dumps({'app': app, 'poll_type': poll_type, 'metric_name': metric_name, 'value': val, 'unit': unit, 'status': status, 'details': details}, ensure_ascii=False)
        return (ts_str, now_epoch, app, poll_type, metric_name, val_num, unit, status, details_str, raw_json)

    def _prepare_app_event_row(self, ev: Dict[str, Any]) -> tuple:
        now_dt = datetime.now(timezone.utc)
        ts_str = ev.get('timestamp') or now_dt.isoformat()
        try:
            now_epoch = datetime.fromisoformat(ts_str).timestamp()
        except Exception:
            now_epoch = now_dt.timestamp()
        app = ev.get('app', 'unknown')
        event_type = ev.get('event_type', 'event')
        status = ev.get('status', 'OK')
        details = ev.get('details', '')
        details_str = json.dumps(details, ensure_ascii=False) if isinstance(details, (dict, list)) else str(details or '')
        raw_json = json.dumps({'app': app, 'event_type': event_type, 'status': status, 'details': details}, ensure_ascii=False)
        return (ts_str, now_epoch, app, event_type, status, details_str, raw_json)

    def _prepare_app_param_row(self, pc: Dict[str, Any]) -> tuple:
        now_dt = datetime.now(timezone.utc)
        ts_str = pc.get('timestamp') or now_dt.isoformat()
        try:
            now_epoch = datetime.fromisoformat(ts_str).timestamp()
        except Exception:
            now_epoch = now_dt.timestamp()
        app = pc.get('app', 'unknown')
        param_name = pc.get('param_name', 'param')
        old_val = pc.get('old_value')
        new_val = pc.get('new_value')
        old_str = json.dumps(old_val, ensure_ascii=False) if isinstance(old_val, (dict, list)) else str(old_val or '')
        new_str = json.dumps(new_val, ensure_ascii=False) if isinstance(new_val, (dict, list)) else str(new_val or '')
        status = pc.get('status', 'SUCCESS')
        user = pc.get('user', 'system')
        details = pc.get('details', '')
        details_str = json.dumps(details, ensure_ascii=False) if isinstance(details, (dict, list)) else str(details or '')
        raw_json = json.dumps({'app': app, 'param_name': param_name, 'old_value': old_val, 'new_value': new_val, 'status': status, 'user': user, 'details': details}, ensure_ascii=False)
        return (ts_str, now_epoch, app, param_name, old_str, new_str, status, user, details_str, raw_json)

    def _prepare_device_event_row(self, event: Dict[str, Any], timestamp: Optional[str] = None) -> tuple:
        now_dt = datetime.now(timezone.utc)
        ts_str = timestamp or event.get('timestamp') or now_dt.isoformat()
        try:
            now_epoch = datetime.fromisoformat(ts_str).timestamp()
        except Exception:
            now_epoch = now_dt.timestamp()
        raw_json = json.dumps(event, ensure_ascii=False, default=str)
        return (
            ts_str,
            now_epoch,
            event.get('event_type', ''),
            event.get('device_instance_id', ''),
            event.get('friendly_name', ''),
            event.get('device_class', ''),
            event.get('category', ''),
            int(bool(event.get('has_problem', False))),
            event.get('problem_code', 0),
            event.get('status_code', 0),
            event.get('manufacturer', ''),
            event.get('flapping_count_in_window', 0),
            event.get('uptime_seconds', 0.0),
            raw_json,
        )

    def _prepare_w64_event_row(self, event_data: Dict[str, Any], provider: str = 'w64_collector') -> tuple:
        now_dt = datetime.now(timezone.utc)
        ts_str = event_data.get('timestamp') or now_dt.isoformat()
        try:
            now_epoch = datetime.fromisoformat(ts_str).timestamp()
        except Exception:
            now_epoch = now_dt.timestamp()
        event_id = str(event_data.get('event_id') or f'evt_{int(now_epoch)}')
        event_type = str(event_data.get('event_type', 'unknown'))
        path_val = event_data.get('path')
        pid_val = event_data.get('pid')
        if pid_val is not None:
            try:
                pid_val = int(pid_val)
            except (ValueError, TypeError):
                pid_val = None
        name_val = event_data.get('name')
        raw_json = json.dumps(event_data, ensure_ascii=False, default=str)
        return (event_id, ts_str, now_epoch, event_type, path_val, pid_val, name_val, provider, raw_json)

    def _insert_snapshot_row(self, cursor: sqlite3.Cursor, item: Dict[str, Any]) -> int:
        snap_data = item.get('data', {})
        top_n = item.get('top_n', 20)

        if isinstance(snap_data, SystemSnapshot):
            snapshot = snap_data
            hostname = snapshot.hostname
            uptime = snapshot.uptime_seconds
            cpu_pct = snapshot.cpu.total_percent if snapshot.cpu else 0.0
            cpu_freq = snapshot.cpu.frequency_mhz if snapshot.cpu else 0.0
            mem_tot = snapshot.memory.total_gb if snapshot.memory else 0.0
            mem_used = snapshot.memory.used_gb if snapshot.memory else 0.0
            mem_pct = snapshot.memory.percent if snapshot.memory else 0.0
            swap_pct = snapshot.memory.swap_percent if snapshot.memory else 0.0
            disk_rb = snapshot.disk_io.read_bytes_per_sec if snapshot.disk_io else 0.0
            disk_wb = snapshot.disk_io.write_bytes_per_sec if snapshot.disk_io else 0.0
            disk_rc = snapshot.disk_io.read_count_per_sec if snapshot.disk_io else 0.0
            disk_wc = snapshot.disk_io.write_count_per_sec if snapshot.disk_io else 0.0
            net_sent = sum(getattr(i, 'bytes_sent_sec', 0.0) or 0.0 for i in (snapshot.network or []))
            net_recv = sum(getattr(i, 'bytes_recv_sec', 0.0) or 0.0 for i in (snapshot.network or []))
            gpu_load = 0.0
            gpu_temp = 0.0
            if snapshot.gpus:
                gpu = snapshot.gpus[0]
                gpu_load = (getattr(gpu, 'load_percent', None) if getattr(gpu, 'load_percent', None) is not None else getattr(gpu, 'utilization_gpu_pct', 0.0)) or 0.0
                gpu_temp = (getattr(gpu, 'temperature_celsius', None) if getattr(gpu, 'temperature_celsius', None) is not None else getattr(gpu, 'temperature_gpu_c', 0.0)) or 0.0
            raw_procs = snapshot.top_processes or []
            os_name = snapshot.os_name or 'Windows'
            os_build = str(snapshot.os_build or '')
            os_install_date = str(snapshot.os_install_date or '')
            disks_list = [d.model_dump() if hasattr(d, 'model_dump') else (vars(d) if not isinstance(d, dict) else d) for d in (snapshot.disks or [])]
            disks_json = json.dumps(disks_list, ensure_ascii=False, default=str) if disks_list else None
            ts_str = snapshot.timestamp
        else:
            hostname = snap_data.get('hostname')
            uptime = snap_data.get('uptime_seconds')
            os_name = snap_data.get('os_name') or 'Windows'
            os_build = str(snap_data.get('os_build') or '')
            os_install_date = str(snap_data.get('os_install_date') or '')
            disks_val = snap_data.get('disks', [])
            disks_list = [d.model_dump() if hasattr(d, 'model_dump') else (vars(d) if not isinstance(d, dict) else d) for d in disks_val] if isinstance(disks_val, list) else []
            disks_json = json.dumps(disks_list, ensure_ascii=False, default=str) if disks_list else None
            cpu_obj = snap_data.get('cpu', {})
            cpu_pct = cpu_obj.get('total_percent', 0.0) if isinstance(cpu_obj, dict) else getattr(cpu_obj, 'total_percent', 0.0)
            cpu_freq = cpu_obj.get('frequency_mhz', 0.0) if isinstance(cpu_obj, dict) else getattr(cpu_obj, 'frequency_mhz', 0.0)
            mem_obj = snap_data.get('memory', {})
            mem_tot = mem_obj.get('total_gb', 0.0) if isinstance(mem_obj, dict) else getattr(mem_obj, 'total_gb', 0.0)
            mem_used = mem_obj.get('used_gb', 0.0) if isinstance(mem_obj, dict) else getattr(mem_obj, 'used_gb', 0.0)
            mem_pct = mem_obj.get('percent', 0.0) if isinstance(mem_obj, dict) else getattr(mem_obj, 'percent', 0.0)
            swap_pct = mem_obj.get('swap_percent', 0.0) if isinstance(mem_obj, dict) else getattr(mem_obj, 'swap_percent', 0.0)
            disk_obj = snap_data.get('disk_io', {})
            disk_rb = disk_obj.get('read_bytes_per_sec', 0.0) if isinstance(disk_obj, dict) else getattr(disk_obj, 'read_bytes_per_sec', 0.0)
            disk_wb = disk_obj.get('write_bytes_per_sec', 0.0) if isinstance(disk_obj, dict) else getattr(disk_obj, 'write_bytes_per_sec', 0.0)
            disk_rc = disk_obj.get('read_count_per_sec', 0.0) if isinstance(disk_obj, dict) else getattr(disk_obj, 'read_count_per_sec', 0.0)
            disk_wc = disk_obj.get('write_count_per_sec', 0.0) if isinstance(disk_obj, dict) else getattr(disk_obj, 'write_count_per_sec', 0.0)
            net_list = snap_data.get('network', [])
            net_sent = sum((n.get('bytes_sent_sec', 0.0) if isinstance(n, dict) else getattr(n, 'bytes_sent_sec', 0.0)) or 0.0 for n in net_list)
            net_recv = sum((n.get('bytes_recv_sec', 0.0) if isinstance(n, dict) else getattr(n, 'bytes_recv_sec', 0.0)) or 0.0 for n in net_list)
            gpus = snap_data.get('gpus', [])
            gpu_load = 0.0
            gpu_temp = 0.0
            if gpus:
                g0 = gpus[0]
                gpu_load = (g0.get('load_percent', 0.0) if isinstance(g0, dict) else getattr(g0, 'load_percent', 0.0)) or 0.0
                gpu_temp = (g0.get('temperature_celsius', 0.0) if isinstance(g0, dict) else getattr(g0, 'temperature_celsius', 0.0)) or 0.0
            raw_procs = snap_data.get('top_processes', [])
            ts_str = snap_data.get('timestamp')

        now_dt = datetime.now(timezone.utc)
        ts_str = ts_str or now_dt.isoformat()
        try:
            now_epoch = datetime.fromisoformat(ts_str).timestamp()
        except Exception:
            now_epoch = now_dt.timestamp()

        cursor.execute('''
            INSERT INTO system_snapshots (
                timestamp, created_at, hostname, uptime_seconds, os_name, os_build, os_install_date, disks_json,
                cpu_total_percent, cpu_frequency_mhz, memory_total_gb, memory_used_gb,
                memory_percent, swap_percent, gpu_load_percent, gpu_temp_c,
                disk_read_bytes_sec, disk_write_bytes_sec, disk_read_count_sec,
                disk_write_count_sec, network_sent_bytes_sec, network_recv_bytes_sec
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ts_str, now_epoch, hostname, uptime, os_name, os_build, os_install_date, disks_json,
            cpu_pct, cpu_freq, mem_tot, mem_used,
            mem_pct, swap_pct, gpu_load, gpu_temp,
            disk_rb, disk_wb, disk_rc,
            disk_wc, net_sent, net_recv,
        ))
        snapshot_id = cursor.lastrowid or 0

        processes = raw_procs if top_n is None or top_n <= 0 else raw_procs[:top_n]
        proc_rows = []
        for p in processes:
            p_dict = p if isinstance(p, dict) else (p.model_dump() if hasattr(p, 'model_dump') else vars(p))
            proc_rows.append((
                snapshot_id,
                ts_str,
                p_dict.get('pid', 0),
                p_dict.get('name', 'unknown'),
                p_dict.get('status', ''),
                float(p_dict.get('cpu_percent', 0.0) or 0.0),
                float(p_dict.get('memory_mb', 0.0) or 0.0),
                float(p_dict.get('memory_percent', 0.0) or 0.0),
                int(p_dict.get('num_threads', 0) or 0),
                int(p_dict.get('num_handles', 0) or 0),
                str(p_dict.get('username', '') or ''),
                float(p_dict.get('read_bytes_sec', 0.0) or 0.0),
                float(p_dict.get('write_bytes_sec', 0.0) or 0.0),
                p_dict.get('integrity_level', None),
                int(bool(p_dict.get('elevation', False))),
            ))
        if proc_rows:
            cursor.executemany('''
                INSERT INTO process_snapshots (
                    snapshot_id, timestamp, pid, name, status, cpu_percent,
                    memory_mb, memory_percent, num_threads, num_handles,
                    username, read_bytes_sec, write_bytes_sec, integrity_level, elevation
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', proc_rows)

        return snapshot_id

    def _insert_hardware_archive_row(self, cursor: sqlite3.Cursor, data: Any) -> int:
        now_dt = datetime.now(timezone.utc)
        if isinstance(data, HardwareArchiveEntry):
            raw_json = data.model_dump_json()
            report = data.report
            prob_count = report.problem_devices_count if report else 0
            outdated_count = report.outdated_drivers_count if report else 0
            archive_id = data.archive_id
            timestamp = data.timestamp
            devices_count = data.devices_count
            changes_count = data.changes_count
        else:
            raw_json = json.dumps(data, ensure_ascii=False, default=str)
            report = data.get('report', {})
            prob_count = report.get('problem_devices_count', 0) if isinstance(report, dict) else getattr(report, 'problem_devices_count', 0)
            outdated_count = report.get('outdated_drivers_count', 0) if isinstance(report, dict) else getattr(report, 'outdated_drivers_count', 0)
            archive_id = data.get('archive_id', f'arch_{int(now_dt.timestamp())}')
            timestamp = data.get('timestamp', now_dt.isoformat())
            devices_count = data.get('devices_count', 0)
            changes_count = data.get('changes_count', 0)

        try:
            now_epoch = datetime.fromisoformat(timestamp).timestamp()
        except Exception:
            now_epoch = now_dt.timestamp()

        cursor.execute('''
            INSERT OR REPLACE INTO hardware_audits (
                archive_id, timestamp, created_at, devices_count,
                problem_devices_count, outdated_drivers_count, changes_count, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (archive_id, timestamp, now_epoch, devices_count, prob_count, outdated_count, changes_count, raw_json))
        return cursor.lastrowid or 0

    # -------------------------------------------------------------------------
    # Публичные методы сохранения телеметрии (с поддержкой буферизации)
    # -------------------------------------------------------------------------

    def save_snapshot(self, snapshot: SystemSnapshot, top_n: int = 20) -> int:
        """Сохраняет срез системной телеметрии и Top-N активных процессов.

        Args:
            snapshot: Снимок телеметрии SystemSnapshot.
            top_n: Количество сохраняемых процессов из топа.

        Returns:
            int: ID созданного снимка или статус буферизации (>0).
        """
        if self._buffer_mode == 'direct':
            with self._lock, self._get_connection() as conn:
                cursor = conn.cursor()
                snap_id = self._insert_snapshot_row(cursor, {'data': snapshot, 'top_n': top_n})
                conn.commit()
                return snap_id

        # Сериализуем модель для надежности буфера
        snap_dict = snapshot.model_dump() if hasattr(snapshot, 'model_dump') else vars(snapshot)
        self._enqueue_record({'type': 'snapshot', 'data': snap_dict, 'top_n': top_n})
        return 1

    def save_sensor_poll(self, sensor_item: Dict[str, Any], timestamp: Optional[str] = None) -> int:
        """Сохраняет единичное измерение аппаратного датчика в буфер/БД.

        Args:
            sensor_item: Словарь с данными датчика (id, hardware_name, value и др.).
            timestamp: Временная метка ISO (если None, генерируется текущая).

        Returns:
            int: ID добавленной записи или статус буферизации (>0).
        """
        if self._buffer_mode == 'direct':
            with self._lock, self._get_connection() as conn:
                cursor = conn.cursor()
                row = self._prepare_sensor_poll_row(sensor_item, timestamp)
                cursor.execute('''
                    INSERT INTO sensor_polls (
                        sensor_id, timestamp, created_at, hardware_name, hardware_type,
                        sensor_category, sensor_name, unit, value, provider, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', row)
                conn.commit()
                return cursor.lastrowid or 0

        self._enqueue_record({'type': 'sensor_poll', 'data': sensor_item, 'timestamp': timestamp})
        return 1

    def save_sensor_polls_batch(self, items: List[Dict[str, Any]], timestamp: Optional[str] = None, deduplicate: bool = True) -> int:
        """Сохраняет пакет измерений сенсоров в буфер/БД с дедупликацией по provider priority.

        Args:
            items: Список показаний датчиков с полями id, value, _provider.
            timestamp: Общая временная метка пакета.
            deduplicate: Если True, выполняет дедупликацию по sensor_id с учетом приоритетов провайдеров.

        Returns:
            int: Количество сохраненных записей.
        """
        if not items:
            return 0
        
        # Дедупликация: оставляем только уникальные sensor_id с учетом приоритетов провайдеров
        if deduplicate:
            from .sensor_registry import SensorDeduplicator, SensorProvider
            
            deduplicator = SensorDeduplicator()
            
            for item in items:
                sensor_id = str(item.get('id', ''))
                value = item.get('value', 0.0)
                provider_raw = item.get('_provider', SensorProvider.SENSOR_COLLECTOR)
                
                # Convert provider to SensorProvider enum if needed
                if isinstance(provider_raw, str):
                    try:
                        provider = SensorProvider[provider_raw.upper()]
                    except KeyError:
                        provider = SensorProvider.SENSOR_COLLECTOR
                elif isinstance(provider_raw, SensorProvider):
                    provider = provider_raw
                else:
                    provider = SensorProvider.SENSOR_COLLECTOR
                
                # Use deduplicator to track best provider
                deduplicator.add(sensor_id, provider, value)
            
            # Get the final unique sensors (winners by provider priority)
            unique_providers = deduplicator.get_unique()
            
            # Filter items to keep only winners
            items = [item for item in items 
                     if str(item.get('id', '')) in unique_providers and
                     self._get_provider_value(item) == unique_providers[str(item.get('id', ''))][0].value]
        
        if not items:
            return 0
        
        if self._buffer_mode == 'direct':
            with self._lock, self._get_connection() as conn:
                cursor = conn.cursor()
                rows = [self._prepare_sensor_poll_row(s, timestamp) for s in items]
                cursor.executemany('''
                    INSERT INTO sensor_polls (
                        sensor_id, timestamp, created_at, hardware_name, hardware_type,
                        sensor_category, sensor_name, unit, value, provider, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', rows)
                conn.commit()
                return len(rows)

        self._enqueue_record({'type': 'sensor_polls_batch', 'data': items, 'timestamp': timestamp})
        return len(items)
    
    def _get_provider_value(self, item: Dict[str, Any]) -> int:
        """Returns the priority value of the provider for comparison."""
        from .sensor_registry import SensorProvider
        provider_raw = item.get('_provider', SensorProvider.SENSOR_COLLECTOR)
        if isinstance(provider_raw, str):
            try:
                return SensorProvider[provider_raw.upper()].value
            except KeyError:
                return SensorProvider.SENSOR_COLLECTOR.value
        elif isinstance(provider_raw, SensorProvider):
            return provider_raw.value
        return SensorProvider.SENSOR_COLLECTOR.value

    save_sensor_polls = save_sensor_polls_batch

    def save_sensor_aggregates_batch(self, aggregates: List[Dict[str, Any]]) -> int:
        """Сохраняет агрегированные показания сенсоров за час.

        Args:
            aggregates: Список словарей с полями:
                sensor_id, period_start, period_end, avg, min, max, count.
        Returns:
            int: Количество записей, сохранённых в буфер/БД.
        """
        if not aggregates:
            return 0
        if self._buffer_mode == 'direct':
            with self._lock, self._get_connection() as conn:
                cursor = conn.cursor()
                rows = []
                for a in aggregates:
                    rows.append((
                        a.get('sensor_id', ''),
                        a.get('period_start', ''),
                        a.get('period_end', ''),
                        a.get('avg', None),
                        a.get('min', None),
                        a.get('max', None),
                        a.get('count', 0),
                        json.dumps(a, ensure_ascii=False, default=str),
                    ))
                cursor.executemany('''
                    INSERT INTO sensor_aggregates_hourly (
                        sensor_id, period_start, period_end, avg_value, min_value, max_value, count, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', rows)
                conn.commit()
                return len(rows)

        self._enqueue_record({'type': 'sensor_aggregates_batch', 'data': aggregates})
        return len(aggregates)

    def save_event(
        self,
        event_type: str,
        event_details: Dict[str, Any],
        severity: str = 'info',
        timestamp: Optional[str] = None,
    ) -> int:
        """Сохраняет событие телеметрии или обнаруженную аномалию.

        Args:
            event_type: Тип события (process_start, file_event, hardware_change и т.д.).
            event_details: Детализированный словарь параметров события.
            severity: Уровень важности (info, warning, error, critical).
            timestamp: Временная метка события.

        Returns:
            int: ID созданной записи или статус буферизации (>0).
        """
        if self._buffer_mode == 'direct':
            now_dt = datetime.now(timezone.utc)
            ts_str = timestamp or now_dt.isoformat()
            try:
                now_epoch = datetime.fromisoformat(ts_str).timestamp()
            except Exception:
                now_epoch = now_dt.timestamp()
            details_str = json.dumps(event_details, ensure_ascii=False, default=str)
            with self._lock, self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO telemetry_events (
                        timestamp, created_at, event_type, severity, event_details, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (ts_str, now_epoch, event_type, severity, details_str, details_str))
                conn.commit()
                return cursor.lastrowid or 0

        self._enqueue_record({
            'type': 'event',
            'event_type': event_type,
            'details': event_details,
            'severity': severity,
            'timestamp': timestamp,
        })
        return 1

    def save_hardware_archive(self, archive_entry: HardwareArchiveEntry) -> int:
        """Сохраняет срез аудита оборудования в таблицу hardware_audits.

        Args:
            archive_entry: Запись архива аудита оборудования.

        Returns:
            int: ID добавленной записи или статус буферизации (>0).
        """
        if self._buffer_mode == 'direct':
            with self._lock, self._get_connection() as conn:
                cursor = conn.cursor()
                aid = self._insert_hardware_archive_row(cursor, archive_entry)
                conn.commit()
                return aid

        entry_dict = archive_entry.model_dump() if hasattr(archive_entry, 'model_dump') else vars(archive_entry)
        self._enqueue_record({'type': 'hardware_archive', 'data': entry_dict})
        return 1

    def save_app_poll(
        self,
        app: str,
        poll_type: str,
        metric_name: str,
        value: Any,
        unit: str = '',
        status: str = 'OK',
        details: Any = '',
        timestamp: Optional[str] = None,
    ) -> int:
        """Сохраняет запись периодического опроса метрики приложения.

        Args:
            app: Имя приложения.
            poll_type: Категория опроса.
            metric_name: Название метрики.
            value: Численное или строковое значение.
            unit: Единица измерения.
            status: Статус проверки.
            details: Дополнительные детали.
            timestamp: ISO временная метка.

        Returns:
            int: ID созданной записи или статус буферизации (>0).
        """
        rec = {
            'type': 'app_poll',
            'app': app,
            'poll_type': poll_type,
            'metric_name': metric_name,
            'value': value,
            'unit': unit,
            'status': status,
            'details': details,
            'timestamp': timestamp,
        }
        if self._buffer_mode == 'direct':
            with self._lock, self._get_connection() as conn:
                cursor = conn.cursor()
                row = self._prepare_app_poll_row(rec)
                cursor.execute('''
                    INSERT INTO app_polls (
                        timestamp, created_at, app, poll_type, metric_name, value, unit, status, details, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', row)
                conn.commit()
                return int(cursor.lastrowid or 0)

        self._enqueue_record(rec)
        return 1

    def save_app_event(
        self,
        app: str,
        event_type: str,
        status: str = 'OK',
        details: Any = '',
        timestamp: Optional[str] = None,
    ) -> int:
        """Сохраняет событие приложения.

        Args:
            app: Имя приложения.
            event_type: Тип события.
            status: Статус выполнения.
            details: Дополнительные метаданные или описание.
            timestamp: ISO временная метка.

        Returns:
            int: ID созданной записи или статус буферизации (>0).
        """
        rec = {
            'type': 'app_event',
            'app': app,
            'event_type': event_type,
            'status': status,
            'details': details,
            'timestamp': timestamp,
        }
        if self._buffer_mode == 'direct':
            with self._lock, self._get_connection() as conn:
                cursor = conn.cursor()
                row = self._prepare_app_event_row(rec)
                cursor.execute('''
                    INSERT INTO app_events (
                        timestamp, created_at, app, event_type, status, details, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', row)
                conn.commit()
                return int(cursor.lastrowid or 0)

        self._enqueue_record(rec)
        return 1

    def save_app_param_change(
        self,
        app: str,
        param_name: str,
        old_value: Any,
        new_value: Any,
        status: str = 'SUCCESS',
        user: str = 'system',
        details: Any = '',
        timestamp: Optional[str] = None,
    ) -> int:
        """Сохраняет факт изменения параметра конфигурации приложения.

        Args:
            app: Имя приложения.
            param_name: Имя параметра.
            old_value: Предыдущее значение.
            new_value: Новое значение.
            status: Статус операции.
            user: Пользователь или подсистема.
            details: Дополнительные детали.
            timestamp: ISO временная метка.

        Returns:
            int: ID созданной записи или статус буферизации (>0).
        """
        rec = {
            'type': 'app_param_change',
            'app': app,
            'param_name': param_name,
            'old_value': old_value,
            'new_value': new_value,
            'status': status,
            'user': user,
            'details': details,
            'timestamp': timestamp,
        }
        if self._buffer_mode == 'direct':
            with self._lock, self._get_connection() as conn:
                cursor = conn.cursor()
                row = self._prepare_app_param_row(rec)
                cursor.execute('''
                    INSERT INTO app_param_changes (
                        timestamp, created_at, app, param_name, old_value, new_value, status, user, details, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', row)
                conn.commit()
                return int(cursor.lastrowid or 0)

        self._enqueue_record(rec)
        return 1

    def save_app_polls_batch(self, polls: List[Dict[str, Any]]) -> int:
        """Сохраняет пачку опросов приложений.

        Args:
            polls: Список словарей параметров опросов.

        Returns:
            int: Количество сохраненных записей.
        """
        if not polls:
            return 0
        if self._buffer_mode == 'direct':
            with self._lock, self._get_connection() as conn:
                cursor = conn.cursor()
                rows = [self._prepare_app_poll_row(p) for p in polls]
                cursor.executemany('''
                    INSERT INTO app_polls (
                        timestamp, created_at, app, poll_type, metric_name, value, unit, status, details, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', rows)
                conn.commit()
                return len(rows)

        self._enqueue_record({'type': 'app_polls_batch', 'data': polls})
        return len(polls)

    def save_app_events_batch(self, events: List[Dict[str, Any]]) -> int:
        """Сохраняет пачку событий приложений.

        Args:
            events: Список словарей событий.

        Returns:
            int: Количество сохраненных записей.
        """
        if not events:
            return 0
        if self._buffer_mode == 'direct':
            with self._lock, self._get_connection() as conn:
                cursor = conn.cursor()
                rows = [self._prepare_app_event_row(ev) for ev in events]
                cursor.executemany('''
                    INSERT INTO app_events (
                        timestamp, created_at, app, event_type, status, details, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', rows)
                conn.commit()
                return len(rows)

        self._enqueue_record({'type': 'app_events_batch', 'data': events})
        return len(events)

    def save_app_param_changes_batch(self, param_changes: List[Dict[str, Any]]) -> int:
        """Сохраняет пачку изменений параметров приложений.

        Args:
            param_changes: Список словарей изменений параметров.

        Returns:
            int: Количество сохраненных записей.
        """
        if not param_changes:
            return 0
        if self._buffer_mode == 'direct':
            with self._lock, self._get_connection() as conn:
                cursor = conn.cursor()
                rows = [self._prepare_app_param_row(pc) for pc in param_changes]
                cursor.executemany('''
                    INSERT INTO app_param_changes (
                        timestamp, created_at, app, param_name, old_value, new_value, status, user, details, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', rows)
                conn.commit()
                return len(rows)

        self._enqueue_record({'type': 'app_param_changes_batch', 'data': param_changes})
        return len(param_changes)

    def save_custom_record(self, source_file: str, payload: Dict[str, Any], timestamp: Optional[str] = None) -> int:
        """Сохраняет произвольную запись лога в SQLite.

        Args:
            source_file: Имя исходного журнала.
            payload: Данные строки в виде словаря.
            timestamp: ISO временная метка.

        Returns:
            int: ID созданной записи или статус буферизации (>0).
        """
        if self._buffer_mode == 'direct':
            now_dt = datetime.now(timezone.utc)
            ts_str = timestamp or payload.get('timestamp') or payload.get('time') or now_dt.isoformat()
            try:
                now_epoch = datetime.fromisoformat(ts_str).timestamp()
            except Exception:
                now_epoch = now_dt.timestamp()
            payload_str = json.dumps(payload, ensure_ascii=False)
            with self._lock, self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO custom_records (
                        timestamp, created_at, source_file, payload_json
                    ) VALUES (?, ?, ?, ?)
                ''', (ts_str, now_epoch, source_file, payload_str))
                conn.commit()
                return int(cursor.lastrowid or 0)

        self._enqueue_record({
            'type': 'custom_record',
            'source_file': source_file,
            'payload': payload,
            'timestamp': timestamp,
        })
        return 1

    def save_device_event(self, event: Dict[str, Any], timestamp: Optional[str] = None) -> int:
        """Сохраняет событие устройства (подключение/отключение/дребезг/ошибка PnP) в БД.

        Args:
            event: Словарь с полями DeviceTransitionEvent.
            timestamp: ISO временная метка.

        Returns:
            int: ID созданной записи или статус буферизации (>0).
        """
        if self._buffer_mode == 'direct':
            with self._lock, self._get_connection() as conn:
                cursor = conn.cursor()
                row = self._prepare_device_event_row(event, timestamp)
                cursor.execute('''
                    INSERT INTO device_events (
                        timestamp, created_at, event_type, device_instance_id,
                        friendly_name, device_class, category, has_problem,
                        problem_code, status_code, manufacturer,
                        flapping_count, uptime_seconds, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', row)
                conn.commit()
                return cursor.lastrowid or 0

        self._enqueue_record({'type': 'device_event', 'data': event, 'timestamp': timestamp})
        return 1

    def save_w64_event(self, event_data: Dict[str, Any], provider: str = 'w64_collector') -> int:
        """Сохраняет системное событие W64/ETW в базу данных SQLite.

        Args:
            event_data: Словарь с полями события.
            provider: Имя провайдера/сенсора.

        Returns:
            int: ID добавленной записи или статус буферизации (>0).
        """
        if self._buffer_mode == 'direct':
            with self._lock, self._get_connection() as conn:
                cursor = conn.cursor()
                row = self._prepare_w64_event_row(event_data, provider)
                cursor.execute('''
                    INSERT INTO w64_events (
                        event_id, timestamp, created_at, event_type, path, pid, name, provider, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', row)
                conn.commit()
                return cursor.lastrowid or 0

        self._enqueue_record({'type': 'w64_event', 'data': event_data, 'provider': provider})
        return 1

    # -------------------------------------------------------------------------
    # Методы чтения данных (с авто-сбросом для консистентности)
    # -------------------------------------------------------------------------

    def get_snapshots(self, limit: int = 60, since_epoch: Optional[float] = None) -> List[Dict[str, Any]]:
        """Извлекает исторические срезы системной телеметрии."""
        self.flush()
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            if since_epoch is not None:
                cursor.execute('''
                    SELECT * FROM system_snapshots
                    WHERE created_at >= ?
                    ORDER BY id DESC
                    LIMIT ?
                ''', (since_epoch, limit))
            else:
                cursor.execute('''
                    SELECT * FROM system_snapshots
                    ORDER BY id DESC
                    LIMIT ?
                ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_latest_cpu(self) -> Optional[Dict[str, Any]]:
        """Извлекает последние метрики процессора из таблицы system_snapshots в SQLite.

        Returns:
            Optional[Dict[str, Any]]: Словарь с полями cpu_total_percent, cpu_frequency_mhz, timestamp или None.
        """
        self.flush()
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, timestamp, created_at, hostname, cpu_total_percent, cpu_frequency_mhz
                FROM system_snapshots
                ORDER BY id DESC
                LIMIT 1;
            ''')
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_cpu_history(self, limit: int = 60, since_epoch: Optional[float] = None) -> List[Dict[str, Any]]:
        """Извлекает историю нагрузки процессора из таблицы system_snapshots в SQLite.

        Args:
            limit: Максимальное количество записей (по умолчанию 60).
            since_epoch: Начальная временная метка UNIX epoch.

        Returns:
            List[Dict[str, Any]]: Список исторических срезов нагрузки CPU.
        """
        self.flush()
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            if since_epoch is not None:
                cursor.execute('''
                    SELECT id, timestamp, created_at, cpu_total_percent, cpu_frequency_mhz
                    FROM system_snapshots
                    WHERE created_at >= ?
                    ORDER BY id DESC
                    LIMIT ?;
                ''', (since_epoch, limit))
            else:
                cursor.execute('''
                    SELECT id, timestamp, created_at, cpu_total_percent, cpu_frequency_mhz
                    FROM system_snapshots
                    ORDER BY id DESC
                    LIMIT ?;
                ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_snapshot_processes(self, snapshot_id: int) -> List[Dict[str, Any]]:
        """Извлекает список процессов, зафиксированных в конкретном снимке."""
        self.flush()
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM process_snapshots
                WHERE snapshot_id = ?
                ORDER BY cpu_percent DESC, memory_mb DESC
            ''', (snapshot_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_process_history(
        self,
        name: Optional[str] = None,
        pid: Optional[int] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Извлекает историю поведения конкретного процесса по имени или PID."""
        self.flush()
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            if pid is not None and name is not None:
                cursor.execute('''
                    SELECT * FROM process_snapshots
                    WHERE pid = ? AND name LIKE ?
                    ORDER BY id DESC LIMIT ?
                ''', (pid, f'%{name}%', limit))
            elif pid is not None:
                cursor.execute('''
                    SELECT * FROM process_snapshots
                    WHERE pid = ?
                    ORDER BY id DESC LIMIT ?
                ''', (pid, limit))
            elif name is not None:
                cursor.execute('''
                    SELECT * FROM process_snapshots
                    WHERE name LIKE ?
                    ORDER BY id DESC LIMIT ?
                ''', (f'%{name}%', limit))
            else:
                cursor.execute('''
                    SELECT * FROM process_snapshots
                    ORDER BY id DESC LIMIT ?
                ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_latest_processes(self, limit: int = 50, sort_by: str = 'cpu') -> List[Dict[str, Any]]:
        """Извлекает процессы из самого последнего зафиксированного снимка в базе данных SQLite."""
        self.flush()
        sort_key = (sort_by or 'cpu').lower()
        if sort_key in ('handles', 'descriptors'):
            order_col = 'num_handles DESC, cpu_percent DESC'
        elif sort_key in ('memory', 'ram'):
            order_col = 'memory_mb DESC, cpu_percent DESC'
        else:
            order_col = 'cpu_percent DESC, memory_mb DESC'
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT MAX(id) FROM system_snapshots;')
            row = cursor.fetchone()
            last_snap_id = row[0] if row and row[0] is not None else None
            if last_snap_id is None:
                cursor.execute('SELECT MAX(snapshot_id) FROM process_snapshots;')
                row = cursor.fetchone()
                last_snap_id = row[0] if row and row[0] is not None else None
            if last_snap_id is None:
                return []
            if limit is not None and limit > 0:
                cursor.execute(f'''
                    SELECT pid, name, status, cpu_percent, memory_mb, memory_percent,
                           num_threads, num_handles, username, read_bytes_sec, write_bytes_sec, timestamp
                    FROM process_snapshots
                    WHERE snapshot_id = ?
                    ORDER BY {order_col}
                    LIMIT ?
                ''', (last_snap_id, limit))
            else:
                cursor.execute(f'''
                    SELECT pid, name, status, cpu_percent, memory_mb, memory_percent,
                           num_threads, num_handles, username, read_bytes_sec, write_bytes_sec, timestamp
                    FROM process_snapshots
                    WHERE snapshot_id = ?
                    ORDER BY {order_col}
                ''', (last_snap_id,))
            return [dict(r) for r in cursor.fetchall()]

    def aggregate_process_metrics_2min(
        self,
        cutoff_seconds: int = 120,
        outlier_cpu_threshold: float = 30.0,
    ) -> Dict[str, int]:
        """Обобщает записи процессов старше двух минут по средним показателям с сохранением выбросов."""
        self.flush()
        now_epoch = datetime.now(timezone.utc).timestamp()
        cutoff_epoch = now_epoch - cutoff_seconds
        with self._lock, self._get_connection() as conn:
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
                        r['snapshot_id'],
                        r['timestamp'],
                        r['snap_epoch'],
                        r['pid'],
                        r['name'],
                        r['status'] or 'running',
                        cpu_val,
                        float(r['memory_mb'] or 0.0),
                        float(r['memory_percent'] or 0.0),
                        int(r['num_threads'] or 1),
                        r['username'] or '',
                        f'Outlier detected: CPU={cpu_val:.1f}% >= {outlier_cpu_threshold}%',
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
            from collections import defaultdict
            grouped = defaultdict(list)
            for r in raw_rows:
                key = (r['name'], r['pid'])
                grouped[key].append(r)
            rollup_rows = []
            for (p_name, p_pid), procs in grouped.items():
                sample_count = len(procs)
                p_start = procs[0]['timestamp']
                p_end = procs[-1]['timestamp']
                p_start_epoch = procs[0]['snap_epoch']
                p_end_epoch = procs[-1]['snap_epoch']
                p_user = procs[-1]['username'] or ''
                cpus = [float(p['cpu_percent'] or 0.0) for p in procs]
                mems = [float(p['memory_mb'] or 0.0) for p in procs]
                threads = [int(p['num_threads'] or 1) for p in procs]
                avg_cpu = round(sum(cpus) / sample_count, 2)
                max_cpu = round(max(cpus), 2)
                min_cpu = round(min(cpus), 2)
                avg_mem = round(sum(mems) / sample_count, 2)
                max_mem = round(max(mems), 2)
                min_mem = round(min(mems), 2)
                avg_threads = round(sum(threads) / sample_count, 1)
                proc_outliers = sum(1 for c in cpus if c >= outlier_cpu_threshold)
                rollup_rows.append((
                    p_start, p_end, p_start_epoch, p_end_epoch, p_name, p_pid, p_user,
                    sample_count, avg_cpu, max_cpu, min_cpu, avg_mem, max_mem, min_mem,
                    avg_threads, proc_outliers,
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
                DELETE FROM process_snapshots
                WHERE id IN ({','.join(['?'] * len(raw_ids))})
            ''', raw_ids)
            conn.commit()
            logger.info(f'Обобщение процессов (> {cutoff_seconds}с) выполнено: агрегатов={len(rollup_rows)}, выбросов={outliers_saved}, удалено_сырых={len(raw_ids)}')
            return {'rollups_created': len(rollup_rows), 'outliers_saved': outliers_saved, 'raw_deleted': len(raw_ids)}

    def aggregate_process_metrics_daily(self, cutoff_days: int = 1) -> Dict[str, int]:
        """Обобщает агрегаты процессов старше одного дня в суточную статистику."""
        self.flush()
        now_epoch = datetime.now(timezone.utc).timestamp()
        cutoff_epoch = now_epoch - cutoff_days * 86400
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, period_start, period_end, period_end_epoch, name,
                       sample_count, avg_cpu_percent, max_cpu_percent,
                       avg_memory_mb, max_memory_mb, outliers_count
                FROM process_rollups_2min
                WHERE period_end_epoch < ?
                ORDER BY name, period_start_epoch ASC
            ''', (cutoff_epoch,))
            old_rollups = cursor.fetchall()
            if not old_rollups:
                return {'daily_rollups_created': 0, '2min_rollups_cleaned': 0}
            from collections import defaultdict
            grouped_daily = defaultdict(list)
            for r in old_rollups:
                d_str = r['period_start'][:10] if len(r['period_start']) >= 10 else 'unknown'
                key = (d_str, r['name'])
                grouped_daily[key].append(r)
            daily_rows = []
            for (d_str, p_name), items in grouped_daily.items():
                total_samples = sum(int(it['sample_count']) for it in items)
                if total_samples <= 0:
                    continue
                weighted_cpu = sum(float(it['avg_cpu_percent']) * int(it['sample_count']) for it in items) / total_samples
                max_cpu = max(float(it['max_cpu_percent']) for it in items)
                weighted_mem = sum(float(it['avg_memory_mb']) * int(it['sample_count']) for it in items) / total_samples
                max_mem = max(float(it['max_memory_mb']) for it in items)
                total_outliers = sum(int(it['outliers_count'] or 0) for it in items)
                last_seen = max(it['period_end'] for it in items)
                daily_rows.append((
                    d_str, p_name, total_samples, round(weighted_cpu, 2), round(max_cpu, 2),
                    round(weighted_mem, 2), round(max_mem, 2), total_outliers, last_seen,
                ))
            if daily_rows:
                cursor.executemany('''
                    INSERT INTO process_rollups_daily (
                        date, name, sample_count, avg_cpu_percent, max_cpu_percent,
                        avg_memory_mb, max_memory_mb, outliers_count, last_seen
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', daily_rows)
            del_ids = [r['id'] for r in old_rollups]
            cursor.execute(f'''
                DELETE FROM process_rollups_2min
                WHERE id IN ({','.join(['?'] * len(del_ids))})
            ''', del_ids)
            conn.commit()
            logger.info(f'Суточное обобщение процессов (> {cutoff_days} дн.) выполнено: суточных_записей={len(daily_rows)}, очищено_2min_агрегатов={len(del_ids)}')
            return {'daily_rollups_created': len(daily_rows), '2min_rollups_cleaned': len(del_ids)}

    def get_process_stats(self, name: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """Возвращает историческую статистику процессов, включая агрегаты и выбросы."""
        self.flush()
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            if name:
                cursor.execute('''
                    SELECT * FROM process_rollups_2min
                    WHERE name LIKE ?
                    ORDER BY id DESC LIMIT ?
                ''', (f'%{name}%', limit))
            else:
                cursor.execute('''
                    SELECT * FROM process_rollups_2min
                    ORDER BY id DESC LIMIT ?
                ''', (limit,))
            rollups_2min = [dict(r) for r in cursor.fetchall()]
            if name:
                cursor.execute('''
                    SELECT * FROM process_rollups_daily
                    WHERE name LIKE ?
                    ORDER BY date DESC LIMIT ?
                ''', (f'%{name}%', limit))
            else:
                cursor.execute('''
                    SELECT * FROM process_rollups_daily
                    ORDER BY date DESC LIMIT ?
                ''', (limit,))
            daily_stats = [dict(r) for r in cursor.fetchall()]
            if name:
                cursor.execute('''
                    SELECT * FROM process_outliers
                    WHERE name LIKE ?
                    ORDER BY id DESC LIMIT ?
                ''', (f'%{name}%', limit))
            else:
                cursor.execute('''
                    SELECT * FROM process_outliers
                    ORDER BY id DESC LIMIT ?
                ''', (limit,))
            outliers = [dict(r) for r in cursor.fetchall()]
            return {
                'name_filter': name,
                'rollups_2min': rollups_2min,
                'daily_stats': daily_stats,
                'outliers': outliers,
                'total_rollups_count': len(rollups_2min),
                'total_outliers_count': len(outliers),
            }

    def get_events(self, event_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Извлекает список зафиксированных событий телеметрии."""
        self.flush()
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            if event_type:
                cursor.execute('''
                    SELECT * FROM telemetry_events
                    WHERE event_type = ?
                    ORDER BY id DESC LIMIT ?
                ''', (event_type, limit))
            else:
                cursor.execute('''
                    SELECT * FROM telemetry_events
                    ORDER BY id DESC LIMIT ?
                ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_sensor_history(
        self,
        sensor_id: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Извлекает историю показаний сенсоров."""
        self.flush()
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            if sensor_id and category:
                cursor.execute('''
                    SELECT * FROM sensor_polls
                    WHERE sensor_id = ? AND sensor_category = ?
                    ORDER BY id DESC LIMIT ?
                ''', (sensor_id, category, limit))
            elif sensor_id:
                cursor.execute('''
                    SELECT * FROM sensor_polls
                    WHERE sensor_id = ?
                    ORDER BY id DESC LIMIT ?
                ''', (sensor_id, limit))
            elif category:
                cursor.execute('''
                    SELECT * FROM sensor_polls
                    WHERE sensor_category = ?
                    ORDER BY id DESC LIMIT ?
                ''', (category, limit))
            else:
                cursor.execute('''
                    SELECT * FROM sensor_polls
                    ORDER BY id DESC LIMIT ?
                ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_latest_sensors(self) -> List[Dict[str, Any]]:
        """Извлекает последнее актуальное значение для каждого сенсора."""
        self.flush()
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT s1.* FROM sensor_polls s1
                INNER JOIN (
                    SELECT sensor_id, MAX(id) as max_id
                    FROM sensor_polls
                    GROUP BY sensor_id
                ) s2 ON s1.id = s2.max_id
                ORDER BY s1.sensor_category, s1.sensor_name;
            ''')
            return [dict(row) for row in cursor.fetchall()]

    def get_app_polls(
        self,
        app: Optional[str] = None,
        metric_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Извлекает историю опросов приложений из SQLite."""
        self.flush()
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            if app and metric_name:
                cursor.execute('''
                    SELECT * FROM app_polls WHERE app = ? AND metric_name = ?
                    ORDER BY id DESC LIMIT ?
                ''', (app, metric_name, limit))
            elif app:
                cursor.execute('''
                    SELECT * FROM app_polls WHERE app = ?
                    ORDER BY id DESC LIMIT ?
                ''', (app, limit))
            else:
                cursor.execute('SELECT * FROM app_polls ORDER BY id DESC LIMIT ?', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_app_events(
        self,
        app: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Извлекает события приложений из SQLite."""
        self.flush()
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            if app and event_type:
                cursor.execute('''
                    SELECT * FROM app_events WHERE app = ? AND event_type = ?
                    ORDER BY id DESC LIMIT ?
                ''', (app, event_type, limit))
            elif app:
                cursor.execute('''
                    SELECT * FROM app_events WHERE app = ?
                    ORDER BY id DESC LIMIT ?
                ''', (app, limit))
            else:
                cursor.execute('SELECT * FROM app_events ORDER BY id DESC LIMIT ?', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_app_param_changes(self, app: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Извлекает историю изменения настроек и параметров приложений."""
        self.flush()
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            if app:
                cursor.execute('''
                    SELECT * FROM app_param_changes WHERE app = ?
                    ORDER BY id DESC LIMIT ?
                ''', (app, limit))
            else:
                cursor.execute('SELECT * FROM app_param_changes ORDER BY id DESC LIMIT ?', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def export_app_polls_to_csv(
        self,
        app: Optional[str] = None,
        output_path: Optional[Union[str, Path]] = None,
        limit: int = 50000,
    ) -> Path:
        """Экспортирует историю опросов приложений из SQLite в CSV-файл."""
        import csv
        self.flush()
        polls = self.get_app_polls(app=app, limit=limit)
        target = Path(output_path) if output_path else Path('app_polls.csv')
        target.parent.mkdir(parents=True, exist_ok=True)
        headers = ['timestamp', 'app', 'poll_type', 'metric_name', 'value', 'unit', 'status', 'details']
        with open(target, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for p in polls:
                writer.writerow([
                    p.get('timestamp', ''),
                    p.get('app', ''),
                    p.get('poll_type', ''),
                    p.get('metric_name', ''),
                    p.get('value', ''),
                    p.get('unit', ''),
                    p.get('status', ''),
                    p.get('details', ''),
                ])
        return target

    def export_app_events_to_csv(
        self,
        app: Optional[str] = None,
        output_path: Optional[Union[str, Path]] = None,
        limit: int = 50000,
    ) -> Path:
        """Экспортирует историю событий приложений из SQLite в CSV-файл."""
        import csv
        self.flush()
        events = self.get_app_events(app=app, limit=limit)
        target = Path(output_path) if output_path else Path('app_events.csv')
        target.parent.mkdir(parents=True, exist_ok=True)
        headers = ['timestamp', 'app', 'event_type', 'status', 'user', 'details']
        with open(target, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for e in events:
                writer.writerow([
                    e.get('timestamp', ''),
                    e.get('app', ''),
                    e.get('event_type', ''),
                    e.get('status', ''),
                    e.get('user', ''),
                    e.get('details', ''),
                ])
        return target

    def export_app_param_changes_to_csv(
        self,
        app: Optional[str] = None,
        output_path: Optional[Union[str, Path]] = None,
        limit: int = 50000,
    ) -> Path:
        """Экспортирует историю изменения параметров приложений из SQLite в CSV-файл."""
        import csv
        self.flush()
        params = self.get_app_param_changes(app=app, limit=limit)
        target = Path(output_path) if output_path else Path('app_param_changes.csv')
        target.parent.mkdir(parents=True, exist_ok=True)
        headers = ['timestamp', 'app', 'param_name', 'old_value', 'new_value', 'status', 'user', 'details']
        with open(target, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for p in params:
                writer.writerow([
                    p.get('timestamp', ''),
                    p.get('app', ''),
                    p.get('param_name', ''),
                    p.get('old_value', ''),
                    p.get('new_value', ''),
                    p.get('status', ''),
                    p.get('user', ''),
                    p.get('details', ''),
                ])
        return target

    def get_custom_records(self, source_file: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Извлекает кастомные записи логов из SQLite."""
        self.flush()
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            if source_file:
                cursor.execute('''
                    SELECT * FROM custom_records WHERE source_file = ?
                    ORDER BY id DESC LIMIT ?
                ''', (source_file, limit))
            else:
                cursor.execute('SELECT * FROM custom_records ORDER BY id DESC LIMIT ?', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_device_events(
        self,
        event_type: Optional[str] = None,
        device_instance_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Извлекает события устройств из БД."""
        self.flush()
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            if event_type and device_instance_id:
                cursor.execute('''
                    SELECT * FROM device_events
                    WHERE event_type = ? AND device_instance_id = ?
                    ORDER BY id DESC LIMIT ?
                ''', (event_type, device_instance_id, limit))
            elif event_type:
                cursor.execute('''
                    SELECT * FROM device_events
                    WHERE event_type = ?
                    ORDER BY id DESC LIMIT ?
                ''', (event_type, limit))
            elif device_instance_id:
                cursor.execute('''
                    SELECT * FROM device_events
                    WHERE device_instance_id = ?
                    ORDER BY id DESC LIMIT ?
                ''', (device_instance_id, limit))
            else:
                cursor.execute('SELECT * FROM device_events ORDER BY id DESC LIMIT ?', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_w64_events(
        self,
        event_type: Optional[str] = None,
        provider: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Извлекает последние события W64/ETW из SQLite хранилища."""
        self.flush()
        query = 'SELECT raw_json FROM w64_events WHERE 1=1'
        params: List[Any] = []
        if event_type:
            query += ' AND event_type = ?'
            params.append(event_type)
        if provider:
            query += ' AND provider = ?'
            params.append(provider)
        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(max(1, limit))

        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = []
            for row in cursor.fetchall():
                try:
                    results.append(json.loads(row[0]))
                except Exception:
                    continue
            return results

    def get_db_file_sizes(self) -> Dict[str, int]:
        """Возвращает размеры файлов базы данных SQLite (основной файл, WAL и SHM) в байтах.

        Returns:
            Dict[str, int]: Словарь с размерами в байтах (db_bytes, wal_bytes, shm_bytes, total_bytes).
        """
        db_bytes = self.db_path.stat().st_size if self.db_path.exists() else 0
        wal_path = self.db_path.with_name(self.db_path.name + '-wal')
        shm_path = self.db_path.with_name(self.db_path.name + '-shm')
        wal_bytes = wal_path.stat().st_size if wal_path.exists() else 0
        shm_bytes = shm_path.stat().st_size if shm_path.exists() else 0
        return {
            'db_bytes': db_bytes,
            'wal_bytes': wal_bytes,
            'shm_bytes': shm_bytes,
            'total_bytes': db_bytes + wal_bytes + shm_bytes,
        }

    def get_total_db_size_mb(self) -> float:
        """Возвращает совокупный физический размер файлов базы данных на диске в МБ.

        Returns:
            float: Суммарный размер в мегабайтах (db + wal + shm).
        """
        sizes = self.get_db_file_sizes()
        return round(sizes['total_bytes'] / (1024.0 * 1024.0), 3)

    def checkpoint_wal(self) -> bool:
        """Сбрасывает WAL-журнал в основной файл базы данных и усекает его до нуля.

        Returns:
            bool: True при успешном сбросе.
        """
        with self._lock:
            try:
                with self._get_connection() as conn:
                    conn.execute('PRAGMA wal_checkpoint(TRUNCATE);')
                return True
            except Exception as e:
                logger.debug(f'Ошибка сброса WAL-журнала: {e}')
                return False

    def vacuum(self) -> bool:
        """Выполняет дефрагментацию и сжатие SQLite базы данных с усечением журнала WAL.

        Returns:
            bool: True при успешной дефрагментации.
        """
        with self._lock:
            self.checkpoint_wal()
            try:
                conn = sqlite3.connect(str(self.db_path), timeout=30.0, isolation_level=None)
                try:
                    conn.execute('VACUUM;')
                finally:
                    conn.close()
                logger.info(f'Выполнен VACUUM для базы данных телеметрии ({self.db_path})')
                return True
            except Exception as e:
                logger.warning(f'Ошибка при выполнении VACUUM для {self.db_path}: {e}')
                return False

    def get_storage_stats(self) -> Dict[str, Any]:
        """Возвращает агрегированную статистику базы данных телеметрии и буфера.

        Returns:
            Dict[str, Any]: Статистика таблиц, параметров буферизации и размера БД.
        """
        self.flush()
        with self._lock, self._get_connection() as conn:
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
            
            file_sizes = self.get_db_file_sizes()
            size_mb = round(file_sizes['db_bytes'] / (1024 * 1024), 2)
            wal_size_mb = round(file_sizes['wal_bytes'] / (1024 * 1024), 2)
            total_size_mb = round(file_sizes['total_bytes'] / (1024 * 1024), 2)
            buffer_file_size = self._buffer_file_path.stat().st_size if self._buffer_file_path.exists() else 0

            return {
                'db_path': str(self.db_path),
                'snapshots_count': snap_count,
                'process_snapshots_count': proc_count,
                'process_outliers_count': outliers_count,
                'process_rollups_2min_count': rollups_2min_count,
                'process_rollups_daily_count': rollups_daily_count,
                'incidents_count': incidents_count,
                'telemetry_rollups_count': rollups_count,
                'sensor_polls_count': sensors_count,
                'events_count': events_count,
                'hardware_audits_count': audits_count,
                'app_polls_count': app_polls_count,
                'app_events_count': app_events_count,
                'app_param_changes_count': app_params_count,
                'custom_records_count': custom_count,
                'device_events_count': device_events_count,
                'w64_events_count': w64_events_count,
                'file_size_mb': size_mb,
                'wal_size_mb': wal_size_mb,
                'total_size_mb': total_size_mb,
                'max_db_size_mb': self._max_db_size_mb,
                'retention_days': self._retention_days,
                'size_limit_exceeded': total_size_mb > self._max_db_size_mb,
                'buffer_mode': self._buffer_mode,
                'buffered_count': self.get_buffered_count(),
                'buffer_size': self._buffer_size,
                'flush_interval_seconds': self._flush_interval_seconds,
                'buffer_file_path': str(self._buffer_file_path),
                'buffer_file_size_bytes': buffer_file_size,
            }

    get_stats = get_storage_stats

    def cleanup_old_records(self, retention_days: Optional[int] = None, vacuum_after: bool = False) -> int:
        """Удаляет устаревшие записи телеметрии старше указанного количества дней.

        Args:
            retention_days: Срок хранения данных в днях (по умолчанию из конфигурации).
            vacuum_after: Флаг выполнения сжатия базы данных после очистки.

        Returns:
            int: Количество удаленных основных снимков.
        """
        self.flush()
        days = retention_days if retention_days is not None else self._retention_days
        if days <= 0:
            threshold_epoch = datetime.now(timezone.utc).timestamp() + 1.0
        else:
            threshold_epoch = datetime.now(timezone.utc).timestamp() - float(days) * 86400.0
        with self._lock, self._get_connection() as conn:
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
            conn.commit()
            deleted_count = len(old_ids)
            logger.info(f'Очищено {deleted_count} устаревших снимков телеметрии (старше {days} дн.)')

        if vacuum_after and self._auto_vacuum_enabled:
            self.vacuum()

        return deleted_count

    def enforce_size_limit(
        self,
        max_size_mb: Optional[float] = None,
        target_ratio: float = 0.85,
    ) -> Dict[str, Any]:
        """Контролирует и ограничивает совокупный размер базы данных telemetry.db.

        При превышении лимита ступенчато удаляет устаревшие сырые снимки и события,
        а затем выполняет WAL checkpoint и VACUUM для физического уменьшения размера на диске.

        Args:
            max_size_mb: Максимальный размер БД в МБ (по умолчанию из конфигурации).
            target_ratio: Коэффициент целевого размера при усечении (по умолчанию 0.85).

        Returns:
            Dict[str, Any]: Отчет о результатах проверки и очистки.
        """
        self.flush()
        limit_mb = max_size_mb if max_size_mb is not None else self._max_db_size_mb
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
        logger.warning(
            f'⚠️ Превышен лимит размера базы данных telemetry.db: {initial_size_mb:.2f} МБ > {limit_mb:.2f} МБ. '
            f'Запуск усечения до целевого размера {target_mb:.2f} МБ.'
        )

        total_deleted_snaps = 0
        total_deleted_records = 0

        # Шаг 1: Очистка записей старше retention_days
        snaps_cleaned = self.cleanup_old_records(retention_days=self._retention_days, vacuum_after=False)
        total_deleted_snaps += snaps_cleaned

        self.checkpoint_wal()

        # Шаг 2: Удаление старейших сырых снимков FIFO батчами
        with self._lock, self._get_connection() as conn:
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
                total_deleted_records += len(ids_to_del)

                if snap_count - len(ids_to_del) <= 5:
                    break

            # Шаг 3: Очистка старых промежуточных таблиц
            cursor.execute('SELECT COUNT(*) FROM process_rollups_2min;')
            r2_count = cursor.fetchone()[0]
            if r2_count > 200:
                cursor.execute('DELETE FROM process_rollups_2min WHERE id IN (SELECT id FROM process_rollups_2min ORDER BY period_end_epoch ASC LIMIT ?)', (r2_count - 200,))
                conn.commit()

        # Шаг 4: Физическое сжатие файла на диске через VACUUM
        if self._auto_vacuum_enabled:
            self.vacuum()
        else:
            self.checkpoint_wal()

        final_sizes = self.get_db_file_sizes()
        final_size_mb = round(final_sizes['total_bytes'] / (1024.0 * 1024.0), 3)
        logger.info(
            f'✅ Усечение базы данных telemetry.db завершено: {initial_size_mb:.2f} МБ -> {final_size_mb:.2f} МБ '
            f'(удалено снимков: {total_deleted_snaps})'
        )

        return {
            'pruned': True,
            'initial_size_mb': initial_size_mb,
            'final_size_mb': final_size_mb,
            'max_size_mb': limit_mb,
            'target_size_mb': target_mb,
            'deleted_snapshots': total_deleted_snaps,
            'deleted_records': total_deleted_records,
        }

    def prune_to_size(self, target_size_mb: float) -> Dict[str, Any]:
        """Принудительно усекает базу данных до указанного целевого размера в МБ.

        Args:
            target_size_mb: Желаемый максимальный размер в МБ.

        Returns:
            Dict[str, Any]: Отчет о результатах усечения.
        """
        return self.enforce_size_limit(max_size_mb=target_size_mb, target_ratio=0.95)

    # -------------------------------------------------------------------------
    # Инциденты и сжатые бакеты (Rollups)
    # -------------------------------------------------------------------------

    def save_incident(self, incident: TelemetryIncident) -> bool:
        """Сохраняет инцидент аномалии и связанный срез кольцевого буфера в базу данных.

        Args:
            incident: Объект TelemetryIncident.

        Returns:
            bool: True при успешном сохранении.
        """
        created_at = datetime.now(timezone.utc).timestamp()
        try:
            with self._lock, self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    INSERT OR REPLACE INTO incidents (
                        incident_id, timestamp, created_at, trigger_type, severity, title, description,
                        trigger_metrics_json, suspect_processes_json, related_events_json, metrics_summary_json, raw_window_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (
                        incident.incident_id,
                        incident.timestamp,
                        created_at,
                        incident.trigger_type,
                        incident.severity,
                        incident.title,
                        incident.description,
                        json.dumps(incident.trigger_metrics, ensure_ascii=False),
                        json.dumps(incident.suspect_processes, ensure_ascii=False),
                        json.dumps(incident.related_events, ensure_ascii=False),
                        json.dumps(incident.metrics_summary, ensure_ascii=False),
                        json.dumps(incident.raw_window, ensure_ascii=False),
                    ),
                )
                conn.commit()
                logger.info(f'Инцидент {incident.incident_id} успешно сохранен в базе данных.')
                return True
        except Exception as ex:
            logger.error(f'Ошибка при сохранении инцидента {incident.incident_id}: {ex}')
            return False

    def get_incidents(
        self,
        limit: int = 50,
        trigger_type: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Возвращает список зафиксированных инцидентов из базы данных.

        Args:
            limit: Максимальное количество возвращаемых инцидентов.
            trigger_type: Фильтр по типу триггера.
            severity: Фильтр по критичности (warning, critical).

        Returns:
            List[Dict[str, Any]]: Список инцидентов с десериализованными полями.
        """
        query = 'SELECT * FROM incidents WHERE 1=1'
        params: List[Any] = []
        if trigger_type:
            query += ' AND trigger_type = ?'
            params.append(trigger_type)
        if severity:
            query += ' AND severity = ?'
            params.append(severity)
        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)

        results: List[Dict[str, Any]] = []
        try:
            with self._lock, self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                for row in cursor.fetchall():
                    item = dict(row)
                    for json_field in ('trigger_metrics_json', 'suspect_processes_json', 'related_events_json', 'metrics_summary_json', 'raw_window_json'):
                        if item.get(json_field):
                            try:
                                item[json_field.replace('_json', '')] = json.loads(item[json_field])
                            except Exception:
                                item[json_field.replace('_json', '')] = []
                    results.append(item)
        except Exception as ex:
            logger.error(f'Ошибка при получении инцидентов: {ex}')
        return results

    def save_system_rollup(self, rollup: SystemMetricRollup) -> bool:
        """Сохраняет сжатый бакет метрик в таблицу telemetry_rollups.

        Args:
            rollup: Сжатый бакет SystemMetricRollup.

        Returns:
            bool: True при успешном сохранении.
        """
        try:
            p_start_epoch = datetime.fromisoformat(rollup.period_start).timestamp()
            p_end_epoch = datetime.fromisoformat(rollup.period_end).timestamp()
        except Exception:
            p_start_epoch = time.time() - rollup.duration_seconds
            p_end_epoch = time.time()

        try:
            with self._lock, self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    INSERT INTO telemetry_rollups (
                        period_start, period_end, period_start_epoch, period_end_epoch,
                        duration_seconds, sample_count, tier,
                        cpu_avg, cpu_min, cpu_max, cpu_p95,
                        ram_avg_gb, ram_min_gb, ram_max_gb, ram_percent_avg, ram_percent_max,
                        disk_read_avg_mbs, disk_read_max_mbs, disk_read_total_mb,
                        disk_write_avg_mbs, disk_write_max_mbs, disk_write_total_mb,
                        network_rx_avg_mbs, network_rx_max_mbs, network_rx_total_mb,
                        network_tx_avg_mbs, network_tx_max_mbs, network_tx_total_mb,
                        raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (
                        rollup.period_start,
                        rollup.period_end,
                        p_start_epoch,
                        p_end_epoch,
                        rollup.duration_seconds,
                        rollup.sample_count,
                        rollup.tier,
                        rollup.cpu_avg,
                        rollup.cpu_min,
                        rollup.cpu_max,
                        rollup.cpu_p95,
                        rollup.ram_avg_gb,
                        rollup.ram_min_gb,
                        rollup.ram_max_gb,
                        rollup.ram_percent_avg,
                        rollup.ram_percent_max,
                        rollup.disk_read_avg_mbs,
                        rollup.disk_read_max_mbs,
                        rollup.disk_read_total_mb,
                        rollup.disk_write_avg_mbs,
                        rollup.disk_write_max_mbs,
                        rollup.disk_write_total_mb,
                        rollup.network_rx_avg_mbs,
                        rollup.network_rx_max_mbs,
                        rollup.network_rx_total_mb,
                        rollup.network_tx_avg_mbs,
                        rollup.network_tx_max_mbs,
                        rollup.network_tx_total_mb,
                        json.dumps(rollup.model_dump(), ensure_ascii=False),
                    ),
                )
                conn.commit()
                return True
        except Exception as ex:
            logger.error(f'Ошибка при сохранении rollup бакета: {ex}')
            return False

    def get_system_rollups(
        self,
        tier: str = '1m',
        start_epoch: Optional[float] = None,
        end_epoch: Optional[float] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Возвращает сжатые бакеты метрик за период.

        Args:
            tier: Уровень сжатия ('1m', '5m', '1h', etc.).
            start_epoch: Начальная эпоха выборки.
            end_epoch: Конечная эпоха выборки.
            limit: Лимит записей.

        Returns:
            List[Dict[str, Any]]: Список строк из telemetry_rollups.
        """
        query = 'SELECT * FROM telemetry_rollups WHERE tier = ?'
        params: List[Any] = [tier]
        if start_epoch is not None:
            query += ' AND period_start_epoch >= ?'
            params.append(start_epoch)
        if end_epoch is not None:
            query += ' AND period_end_epoch <= ?'
            params.append(end_epoch)
        query += ' ORDER BY period_start_epoch DESC LIMIT ?'
        params.append(limit)

        results: List[Dict[str, Any]] = []
        try:
            with self._lock, self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                for row in cursor.fetchall():
                    results.append(dict(row))
        except Exception as ex:
            logger.error(f'Ошибка при получении rollups: {ex}')
        return results

    def save_reboot_session(self, session: Any) -> int:
        """Сохраняет запись о сессии перезагрузки / выключения Windows в SQLite.

        Args:
            session: Экземпляр RebootSession или словарь с полями сессии.

        Returns:
            int: ID сохраненной записи в таблице reboot_history.
        """
        data = session.model_dump() if hasattr(session, 'model_dump') else (
            session.__dict__ if hasattr(session, '__dict__') else dict(session)
        )
        boot_id = str(data.get('boot_id') or f"reboot-{int(time.time())}")
        boot_time = str(data.get('boot_time') or datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'))
        prev_boot = data.get('previous_boot_time')
        uptime_sec = data.get('uptime_seconds')
        uptime_human = data.get('uptime_human')
        st = data.get('shutdown_type')
        if hasattr(st, 'value'):
            shutdown_type = str(st.value)
        elif isinstance(st, str):
            shutdown_type = st.split('.')[-1]
        else:
            shutdown_type = 'UNKNOWN'
        likely_class = str(data.get('likely_class') or 'unknown')
        conclusion = str(data.get('conclusion') or '')
        init_proc = data.get('initiating_process')
        init_user = data.get('initiating_user')
        shutdown_act = data.get('shutdown_action')
        reason_txt = data.get('reason_text')
        reason_cd = data.get('reason_code')
        bugcheck_cd = data.get('bugcheck_code')
        bugcheck_params_json = json.dumps(data.get('bugcheck_params') or [], ensure_ascii=False)
        p_btn_ts = data.get('power_button_timestamp')
        wu_kb = data.get('windows_update_kb')
        svc_inst = data.get('service_installed')
        evidence_json = json.dumps(data.get('evidence') or [], ensure_ascii=False)
        events_chain_json = json.dumps(
            [e.model_dump() if hasattr(e, 'model_dump') else e for e in (data.get('events_chain') or [])],
            ensure_ascii=False,
            default=str,
        )
        raw_json = json.dumps(data, ensure_ascii=False, default=str)
        created_at = time.time()

        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO reboot_history (
                    boot_id, boot_time, previous_boot_time, uptime_seconds, uptime_human,
                    shutdown_type, likely_class, conclusion, initiating_process, initiating_user,
                    shutdown_action, reason_text, reason_code, bugcheck_code, bugcheck_params_json,
                    power_button_timestamp, windows_update_kb, service_installed,
                    evidence_json, events_chain_json, raw_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                boot_id, boot_time, prev_boot, uptime_sec, uptime_human,
                shutdown_type, likely_class, conclusion, init_proc, init_user,
                shutdown_act, reason_txt, reason_cd, bugcheck_cd, bugcheck_params_json,
                p_btn_ts, wu_kb, svc_inst, evidence_json, events_chain_json, raw_json, created_at
            ))
            conn.commit()
            return cursor.lastrowid or 0

    def get_reboot_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Извлекает историю сессий перезагрузок из SQLite базы данных.

        Args:
            limit: Максимальное количество записей.

        Returns:
            List[Dict[str, Any]]: Список словарей с детализированной информацией о сессиях.
        """
        results: List[Dict[str, Any]] = []
        try:
            with self._lock, self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT * FROM reboot_history ORDER BY boot_time DESC, created_at DESC LIMIT ?',
                    (limit,)
                )
                for row in cursor.fetchall():
                    item = dict(row)
                    for f in ('bugcheck_params_json', 'evidence_json', 'events_chain_json', 'raw_json'):
                        if item.get(f):
                            try:
                                item[f.replace('_json', '')] = json.loads(item[f])
                            except Exception:
                                pass
                    results.append(item)
        except Exception as ex:
            logger.error(f'Ошибка извлечения истории перезагрузок из БД: {ex}')
        return results

    def get_latest_reboot_session(self) -> Optional[Dict[str, Any]]:
        """Возвращает самую последнюю запись сессии перезагрузки из SQLite.

        Returns:
            Optional[Dict[str, Any]]: Словарь с полями последней сессии или None.
        """
        history = self.get_reboot_history(limit=1)
        return history[0] if history else None

    # -------------------------------------------------------------------------
    # Расширенный системный аудит (Defender, Startup, VSS, Users)
    # -------------------------------------------------------------------------

    def save_extended_audit(self, audit: Any, timestamp: Optional[str] = None) -> int:
        """Сохраняет срез расширенного аудита безопасности, автозагрузки, VSS и пользователей.

        Args:
            audit: Объект ExtendedSystemAuditReport или словарь с аудитом.
            timestamp: Время среза (если None, берется текущее).

        Returns:
            int: ID созданной записи в таблице system_extended_audits.
        """
        now = datetime.now(timezone.utc)
        ts = timestamp or (audit.timestamp if hasattr(audit, 'timestamp') else now.isoformat())
        created_at = now.timestamp()

        data_dict = audit.model_dump() if hasattr(audit, 'model_dump') else (dict(audit) if isinstance(audit, dict) else {})
        hostname = data_dict.get('hostname') or ''
        defender = data_dict.get('defender', {})
        startup = data_dict.get('startup', {})
        vss = data_dict.get('vss', {})
        users = data_dict.get('users', {})

        def_cfa = 1 if defender.get('cfa_enabled') else 0
        def_asr = int(defender.get('asr_enabled_count') or defender.get('asr_rules_count') or 0)
        def_excl = int(defender.get('exclusions_count') or 0)
        def_threats = int(defender.get('active_threats_count') or 0)

        startup_count = int(startup.get('total_entries') or 0)
        vss_count = int(vss.get('total_snapshots_count') or 0)
        users_total = int(users.get('total_users_count') or 0)
        users_admin = int(users.get('admin_users_count') or 0)

        raw_json = json.dumps(data_dict, ensure_ascii=False)

        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO system_extended_audits (
                    timestamp, created_at, hostname,
                    defender_cfa_enabled, defender_asr_count, defender_exclusions_count, defender_threats_count,
                    startup_entries_count, vss_snapshots_count, users_total_count, users_admin_count,
                    raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                ts, created_at, hostname,
                def_cfa, def_asr, def_excl, def_threats,
                startup_count, vss_count, users_total, users_admin,
                raw_json
            ))
            conn.commit()
            return cursor.lastrowid or 0

    def get_extended_audits(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Возвращает историю расширенных системных аудитов.

        Args:
            limit: Максимальное число записей.

        Returns:
            List[Dict[str, Any]]: Список словарей с историей аудитов.
        """
        results: List[Dict[str, Any]] = []
        try:
            with self._lock, self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT * FROM system_extended_audits ORDER BY created_at DESC LIMIT ?',
                    (limit,)
                )
                for row in cursor.fetchall():
                    item = dict(row)
                    if item.get('raw_json'):
                        try:
                            item['data'] = json.loads(item['raw_json'])
                        except Exception:
                            pass
                    results.append(item)
        except Exception as ex:
            logger.error(f'Ошибка извлечения расширенных аудитов из БД: {ex}')
        return results

    def get_latest_extended_audit(self) -> Optional[Dict[str, Any]]:
        """Возвращает последний расширенный системный аудит.

        Returns:
            Optional[Dict[str, Any]]: Словарь последнего аудита или None.
        """
        audits = self.get_extended_audits(limit=1)
        return audits[0] if audits else None