# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Telemetry SQLite Database Storage
# =============================================================================
# Description:
#   Постоянное локальное хранилище системных срезов, процессов, событий,
#   аппаратных датчиков и архивов аудита в SQLite базе данных.
#   Обеспечивает транзакционную надежность и индексирование.
#
# Examples:
#   >>> from apps.windows.telemetry.storage import TelemetryStorage
#   >>> storage = TelemetryStorage()
#   >>> snapshot_id = storage.save_snapshot(snapshot)
#   >>> history = storage.get_snapshots(limit=50)
#
# File: storage.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модуль управления постоянным SQLite хранилищем системной телеметрии."""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    from src.logger.logger import logger
except ImportError:
    from logger import logger

from apps.windows.telemetry.models import (
    HardwareArchiveEntry,
    SystemSnapshot,
)


class TelemetryStorage:
    """Менеджер базы данных SQLite для персистентного хранения телеметрии."""

    _instance: Optional[TelemetryStorage] = None
    _lock = threading.RLock()

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        """Инициализирует подключение к базе данных телеметрии.

        Args:
            db_path: Путь к файлу SQLite базы данных (по умолчанию: logs/telemetry.db).
        """
        if db_path is None:
            appdata = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
            if appdata and os.path.exists(appdata):
                base_dir = Path(appdata)
            else:
                base_dir = Path.home() / ".config"

            target_dir = base_dir / "AI-Breadboard" / "apps" / "windows" / "telemetry" / "logs"
            target_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = target_dir / "telemetry.db"

            # Бесшовная миграция старой БД, если она лежала в родительской папке
            old_db_path = target_dir.parent / "telemetry.db"
            if old_db_path.exists() and not self.db_path.exists():
                try:
                    import shutil
                    shutil.copy2(old_db_path, self.db_path)
                    logger.info(f"Существующая база данных скопирована из {old_db_path} в {self.db_path}")
                except Exception as ex:
                    logger.warning(f"Не удалось скопировать старую базу данных: {ex}")
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

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
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=10.0,
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self) -> None:
        """Инициализирует структуру таблиц и индексов в базе данных."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Таблица системных снимков
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_snapshots (
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
                    network_recv_bytes_sec REAL,
                    raw_json TEXT
                );
            """)

            # 2. Таблица снимков процессов
            cursor.execute("""
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
                    FOREIGN KEY (snapshot_id) REFERENCES system_snapshots(id) ON DELETE CASCADE
                );
            """)
            try:
                cursor.execute("ALTER TABLE process_snapshots ADD COLUMN num_handles INTEGER DEFAULT 0;")
            except sqlite3.OperationalError:
                pass

            # 3. Таблица показаний сенсоров
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sensor_polls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sensor_id TEXT,
                    timestamp TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    hardware_name TEXT,
                    hardware_type TEXT,
                    sensor_category TEXT,
                    sensor_name TEXT,
                    unit TEXT,
                    value REAL,
                    raw_json TEXT
                );
            """)

            # 4. Таблица событий и корреляций телеметрии
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    event_type TEXT NOT NULL,
                    severity TEXT DEFAULT 'info',
                    event_details TEXT,
                    raw_json TEXT
                );
            """)

            # 5. Таблица архивов аудита оборудования
            cursor.execute("""
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
            """)

            # 6. Таблица периодических опросов и метрик приложений
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_polls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    app TEXT NOT NULL,
                    poll_type TEXT,
                    metric_name TEXT NOT NULL,
                    value REAL,
                    unit TEXT,
                    status TEXT DEFAULT 'OK',
                    details TEXT,
                    raw_json TEXT
                );
            """)

            # 7. Таблица событий приложений
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    app TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    status TEXT DEFAULT 'OK',
                    details TEXT,
                    raw_json TEXT
                );
            """)

            # 8. Таблица изменений параметров приложений
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_param_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    app TEXT NOT NULL,
                    param_name TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    status TEXT DEFAULT 'SUCCESS',
                    user TEXT DEFAULT 'system',
                    details TEXT,
                    raw_json TEXT
                );
            """)

            # 9. Таблица событий устройств (подключение/отключение/дребезг/ошибки PnP)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS device_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    event_type TEXT NOT NULL,
                    device_instance_id TEXT NOT NULL,
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
            """)

            # 10. Таблица произвольных записей и таблиц логов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS custom_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    source_file TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
            """)

            # 10. Таблица зафиксированных выбросов и всплесков процессов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS process_outliers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_id INTEGER,
                    timestamp TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    pid INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    status TEXT,
                    cpu_percent REAL,
                    memory_mb REAL,
                    memory_percent REAL,
                    num_threads INTEGER,
                    username TEXT,
                    details TEXT
                );
            """)

            # 11. Таблица агрегированных срезов процессов (обобщение записей старше 2 минут)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS process_rollups_2min (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    period_start TEXT NOT NULL,
                    period_end TEXT NOT NULL,
                    period_start_epoch REAL NOT NULL,
                    period_end_epoch REAL NOT NULL,
                    name TEXT NOT NULL,
                    pid INTEGER,
                    username TEXT,
                    sample_count INTEGER NOT NULL,
                    avg_cpu_percent REAL NOT NULL,
                    max_cpu_percent REAL NOT NULL,
                    min_cpu_percent REAL NOT NULL,
                    avg_memory_mb REAL NOT NULL,
                    max_memory_mb REAL NOT NULL,
                    min_memory_mb REAL NOT NULL,
                    avg_num_threads REAL NOT NULL,
                    outliers_count INTEGER DEFAULT 0
                );
            """)

            # 12. Таблица долгосрочной суточной статистики процессов (обобщение данных старше 1 дня)
            cursor.execute("""
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
            """)

            # Индексы для ускорения выборок
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_created_at ON system_snapshots(created_at);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON system_snapshots(timestamp);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_processes_snapshot_id ON process_snapshots(snapshot_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_processes_name_pid ON process_snapshots(name, pid);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sensor_polls_sensor_time ON sensor_polls(sensor_id, created_at);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_events_type_time ON telemetry_events(event_type, created_at);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_hardware_audits_archive_id ON hardware_audits(archive_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_polls_app_time ON app_polls(app, created_at);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_polls_metric ON app_polls(metric_name, created_at);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_events_app_time ON app_events(app, created_at);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_events_type ON app_events(event_type, created_at);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_param_changes_app ON app_param_changes(app, created_at);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_custom_records_src ON custom_records(source_file, created_at);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_proc_outliers_name_time ON process_outliers(name, created_at);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_proc_rollups_2min_name_time ON process_rollups_2min(name, period_end_epoch);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_proc_rollups_daily_name_date ON process_rollups_daily(name, date);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_device_events_type_time ON device_events(event_type, created_at);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_device_events_instance ON device_events(device_instance_id, created_at);")

            conn.commit()

    def save_snapshot(self, snapshot: SystemSnapshot, top_n: int = 20) -> int:
        """Сохраняет срез системной телеметрии и Top-N активных процессов в БД.

        Args:
            snapshot: Снимок телеметрии SystemSnapshot.
            top_n: Количество сохраняемых процессов из топа.

        Returns:
            int: ID созданного снимка в таблице system_snapshots.
        """
        now_dt = datetime.now(timezone.utc)
        ts_str = snapshot.timestamp or now_dt.isoformat()
        now_epoch = now_dt.timestamp()

        net_sent = 0.0
        net_recv = 0.0
        if snapshot.network:
            net_sent = sum(getattr(i, "bytes_sent_sec", 0.0) or 0.0 for i in snapshot.network)
            net_recv = sum(getattr(i, "bytes_recv_sec", 0.0) or 0.0 for i in snapshot.network)

        gpu_load = 0.0
        gpu_temp = 0.0
        if snapshot.gpus and len(snapshot.gpus) > 0:
            gpu = snapshot.gpus[0]
            gpu_load = (
                getattr(gpu, "load_percent", None)
                if getattr(gpu, "load_percent", None) is not None
                else getattr(gpu, "utilization_gpu_pct", 0.0)
            ) or 0.0
            gpu_temp = (
                getattr(gpu, "temperature_celsius", None)
                if getattr(gpu, "temperature_celsius", None) is not None
                else getattr(gpu, "temperature_gpu_c", 0.0)
            ) or 0.0

        try:
            current_json = snapshot.model_dump_json()
        except Exception:
            current_json = "{}"

        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO system_snapshots (
                    timestamp,
                    created_at,
                    hostname,
                    uptime_seconds,
                    cpu_total_percent,
                    cpu_frequency_mhz,
                    memory_total_gb,
                    memory_used_gb,
                    memory_percent,
                    swap_percent,
                    gpu_load_percent,
                    gpu_temp_c,
                    disk_read_bytes_sec,
                    disk_write_bytes_sec,
                    disk_read_count_sec,
                    disk_write_count_sec,
                    network_sent_bytes_sec,
                    network_recv_bytes_sec,
                    raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ts_str,
                now_epoch,
                snapshot.hostname,
                snapshot.uptime_seconds,
                snapshot.cpu.total_percent if snapshot.cpu else 0.0,
                snapshot.cpu.frequency_mhz if snapshot.cpu else 0.0,
                snapshot.memory.total_gb if snapshot.memory else 0.0,
                snapshot.memory.used_gb if snapshot.memory else 0.0,
                snapshot.memory.percent if snapshot.memory else 0.0,
                snapshot.memory.swap_percent if snapshot.memory else 0.0,
                gpu_load,
                gpu_temp,
                snapshot.disk_io.read_bytes_per_sec if snapshot.disk_io else 0.0,
                snapshot.disk_io.write_bytes_per_sec if snapshot.disk_io else 0.0,
                snapshot.disk_io.read_count_per_sec if snapshot.disk_io else 0.0,
                snapshot.disk_io.write_count_per_sec if snapshot.disk_io else 0.0,
                net_sent,
                net_recv,
                current_json,
            ))

            snapshot_id = cursor.lastrowid or 0

            # Сохраняем Top-N или все процессы
            raw_procs = snapshot.top_processes or []
            processes = raw_procs if (top_n is None or top_n <= 0) else raw_procs[:top_n]
            proc_rows = []
            for p in processes:
                proc_rows.append((
                    snapshot_id,
                    ts_str,
                    getattr(p, "pid", 0),
                    getattr(p, "name", "unknown"),
                    getattr(p, "status", ""),
                    getattr(p, "cpu_percent", 0.0) or 0.0,
                    getattr(p, "memory_mb", 0.0) or 0.0,
                    getattr(p, "memory_percent", 0.0) or 0.0,
                    getattr(p, "num_threads", 0) or 0,
                    getattr(p, "num_handles", 0) or 0,
                    getattr(p, "username", "") or "",
                    getattr(p, "read_bytes_sec", 0.0) or 0.0,
                    getattr(p, "write_bytes_sec", 0.0) or 0.0,
                ))

            if proc_rows:
                cursor.executemany("""
                    INSERT INTO process_snapshots (
                        snapshot_id,
                        timestamp,
                        pid,
                        name,
                        status,
                        cpu_percent,
                        memory_mb,
                        memory_percent,
                        num_threads,
                        num_handles,
                        username,
                        read_bytes_sec,
                        write_bytes_sec
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, proc_rows)

            conn.commit()
            return snapshot_id

    def save_sensor_poll(
        self,
        sensor_item: Dict[str, Any],
        timestamp: Optional[str] = None,
    ) -> int:
        """Сохраняет единичное измерение аппаратного датчика в БД.

        Args:
            sensor_item: Словарь с данными датчика (id, hardware_name, value и др.).
            timestamp: Временная метка ISO (если None, генерируется текущая).

        Returns:
            int: ID добавленной записи.
        """
        now_dt = datetime.now(timezone.utc)
        ts_str = timestamp or sensor_item.get("timestamp") or now_dt.isoformat()
        now_epoch = now_dt.timestamp()

        sid = str(sensor_item.get("id") or "")
        hw_name = sensor_item.get("hardware_name", "System")
        hw_type = sensor_item.get("hardware_type", "cpu")
        cat = sensor_item.get("sensor_category", "General")
        s_name = sensor_item.get("sensor_name", "Unknown")
        unit = sensor_item.get("unit", "")
        raw_val = sensor_item.get("value", sensor_item.get("value_num", 0.0))

        try:
            val_float = round(float(raw_val), 2)
        except (ValueError, TypeError):
            val_float = 0.0

        raw_json = json.dumps(sensor_item, ensure_ascii=False, default=str)

        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sensor_polls (
                    sensor_id,
                    timestamp,
                    created_at,
                    hardware_name,
                    hardware_type,
                    sensor_category,
                    sensor_name,
                    unit,
                    value,
                    raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sid,
                ts_str,
                now_epoch,
                hw_name,
                hw_type,
                cat,
                s_name,
                unit,
                val_float,
                raw_json,
            ))
            conn.commit()
            return cursor.lastrowid or 0

    def save_sensor_polls_batch(
        self,
        items: List[Dict[str, Any]],
        timestamp: Optional[str] = None,
    ) -> int:
        """Сохраняет пакет измерений сенсоров в базу данных за одну транзакцию.

        Args:
            items: Список показаний датчиков.
            timestamp: Общая временная метка пакета.

        Returns:
            int: Количество успешно сохраненных записей.
        """
        if not items:
            return 0

        now_dt = datetime.now(timezone.utc)
        ts_str = timestamp or now_dt.isoformat()
        now_epoch = now_dt.timestamp()

        rows = []
        for s in items:
            sid = str(s.get("id") or "")
            hw_name = s.get("hardware_name", "System")
            hw_type = s.get("hardware_type", "cpu")
            cat = s.get("sensor_category", "General")
            s_name = s.get("sensor_name", "Unknown")
            unit = s.get("unit", "")
            raw_val = s.get("value", s.get("value_num", 0.0))
            try:
                val_float = round(float(raw_val), 2)
            except (ValueError, TypeError):
                val_float = 0.0
            r_json = json.dumps(s, ensure_ascii=False, default=str)

            rows.append((
                sid,
                ts_str,
                now_epoch,
                hw_name,
                hw_type,
                cat,
                s_name,
                unit,
                val_float,
                r_json,
            ))

        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT INTO sensor_polls (
                    sensor_id,
                    timestamp,
                    created_at,
                    hardware_name,
                    hardware_type,
                    sensor_category,
                    sensor_name,
                    unit,
                    value,
                    raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, rows)
            conn.commit()
            return len(rows)

    def save_event(
        self,
        event_type: str,
        event_details: Dict[str, Any],
        severity: str = "info",
        timestamp: Optional[str] = None,
    ) -> int:
        """Сохраняет событие телеметрии или обнаруженную аномалию.

        Args:
            event_type: Тип события (process_start, file_event, hardware_change и т.д.).
            event_details: Детализированный словарь параметров события.
            severity: Уровень важности (info, warning, error, critical).
            timestamp: Временная метка события.

        Returns:
            int: ID созданной записи события.
        """
        now_dt = datetime.now(timezone.utc)
        ts_str = timestamp or now_dt.isoformat()
        now_epoch = now_dt.timestamp()

        details_str = json.dumps(event_details, ensure_ascii=False, default=str)

        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO telemetry_events (
                    timestamp,
                    created_at,
                    event_type,
                    severity,
                    event_details,
                    raw_json
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                ts_str,
                now_epoch,
                event_type,
                severity,
                details_str,
                details_str,
            ))
            conn.commit()
            return cursor.lastrowid or 0

    def save_hardware_archive(self, archive_entry: HardwareArchiveEntry) -> int:
        """Сохраняет срез аудита оборудования в таблицу hardware_audits.

        Args:
            archive_entry: Запись архива аудита оборудования.

        Returns:
            int: ID добавленной записи.
        """
        now_epoch = datetime.now(timezone.utc).timestamp()
        raw_json = archive_entry.model_dump_json()

        report = archive_entry.report
        prob_count = report.problem_devices_count if report else 0
        outdated_count = report.outdated_drivers_count if report else 0

        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO hardware_audits (
                    archive_id,
                    timestamp,
                    created_at,
                    devices_count,
                    problem_devices_count,
                    outdated_drivers_count,
                    changes_count,
                    raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                archive_entry.archive_id,
                archive_entry.timestamp,
                now_epoch,
                archive_entry.devices_count,
                prob_count,
                outdated_count,
                archive_entry.changes_count,
                raw_json,
            ))
            conn.commit()
            return cursor.lastrowid or 0

    def get_snapshots(
        self,
        limit: int = 60,
        since_epoch: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Извлекает исторические срезы системной телеметрии.

        Args:
            limit: Максимальное число возвращаемых срезов.
            since_epoch: Фильтр по минимальной эпохе времени.

        Returns:
            List[Dict[str, Any]]: Список словарей системных срезов.
        """
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            if since_epoch is not None:
                cursor.execute("""
                    SELECT * FROM system_snapshots
                    WHERE created_at >= ?
                    ORDER BY id DESC
                    LIMIT ?
                """, (since_epoch, limit))
            else:
                cursor.execute("""
                    SELECT * FROM system_snapshots
                    ORDER BY id DESC
                    LIMIT ?
                """, (limit,))

            return [dict(row) for row in cursor.fetchall()]

    def get_snapshot_processes(self, snapshot_id: int) -> List[Dict[str, Any]]:
        """Извлекает список процессов, зафиксированных в конкретном снимке.

        Args:
            snapshot_id: Идентификатор снимка.

        Returns:
            List[Dict[str, Any]]: Список процессов в снимке.
        """
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM process_snapshots
                WHERE snapshot_id = ?
                ORDER BY cpu_percent DESC, memory_mb DESC
            """, (snapshot_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_process_history(
        self,
        name: Optional[str] = None,
        pid: Optional[int] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Извлекает историю поведения конкретного процесса по имени или PID.

        Args:
            name: Имя процесса (подстрока).
            pid: Идентификатор процесса.
            limit: Лимит записей.

        Returns:
            List[Dict[str, Any]]: История метрик процесса.
        """
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            if pid is not None and name is not None:
                cursor.execute("""
                    SELECT * FROM process_snapshots
                    WHERE pid = ? AND name LIKE ?
                    ORDER BY id DESC LIMIT ?
                """, (pid, f"%{name}%", limit))
            elif pid is not None:
                cursor.execute("""
                    SELECT * FROM process_snapshots
                    WHERE pid = ?
                    ORDER BY id DESC LIMIT ?
                """, (pid, limit))
            elif name is not None:
                cursor.execute("""
                    SELECT * FROM process_snapshots
                    WHERE name LIKE ?
                    ORDER BY id DESC LIMIT ?
                """, (f"%{name}%", limit))
            else:
                cursor.execute("""
                    SELECT * FROM process_snapshots
                    ORDER BY id DESC LIMIT ?
                """, (limit,))

            return [dict(row) for row in cursor.fetchall()]

    def get_latest_processes(
        self,
        limit: int = 50,
        sort_by: str = "cpu",
    ) -> List[Dict[str, Any]]:
        """Извлекает процессы из самого последнего зафиксированного снимка в базе данных SQLite.

        Args:
            limit: Максимальное количество процессов (Top-N, 0 для Всех процессов).
            sort_by: Поле сортировки ('cpu', 'memory'/'ram', 'handles'/'descriptors').

        Returns:
            List[Dict[str, Any]]: Список словарей с метриками процессов последнего замера.
        """
        sort_key = (sort_by or "cpu").lower()
        if sort_key in ("handles", "descriptors"):
            order_col = "num_handles DESC, cpu_percent DESC"
        elif sort_key in ("memory", "ram"):
            order_col = "memory_mb DESC, cpu_percent DESC"
        else:
            order_col = "cpu_percent DESC, memory_mb DESC"

        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(id) FROM system_snapshots;")
            row = cursor.fetchone()
            last_snap_id = row[0] if row and row[0] is not None else None

            if last_snap_id is None:
                cursor.execute("SELECT MAX(snapshot_id) FROM process_snapshots;")
                row = cursor.fetchone()
                last_snap_id = row[0] if row and row[0] is not None else None

            if last_snap_id is None:
                return []

            if limit is not None and limit > 0:
                cursor.execute(f"""
                    SELECT pid, name, status, cpu_percent, memory_mb, memory_percent,
                           num_threads, num_handles, username, read_bytes_sec, write_bytes_sec, timestamp
                    FROM process_snapshots
                    WHERE snapshot_id = ?
                    ORDER BY {order_col}
                    LIMIT ?
                """, (last_snap_id, limit))
            else:
                cursor.execute(f"""
                    SELECT pid, name, status, cpu_percent, memory_mb, memory_percent,
                           num_threads, num_handles, username, read_bytes_sec, write_bytes_sec, timestamp
                    FROM process_snapshots
                    WHERE snapshot_id = ?
                    ORDER BY {order_col}
                """, (last_snap_id,))

            return [dict(r) for r in cursor.fetchall()]

    def aggregate_process_metrics_2min(
        self,
        cutoff_seconds: int = 120,
        outlier_cpu_threshold: float = 30.0,
    ) -> Dict[str, int]:
        """Обобщает записи процессов старше двух минут по средним показателям с сохранением выбросов.

        Находит все детальные записи процессов старше `cutoff_seconds` (по умолчанию 120 с):
        1. Идентифицирует выбросы (CPU >= outlier_cpu_threshold или пики) и сохраняет в `process_outliers`.
        2. Рассчитывает средние, минимальные и максимальные значения по каждому процессу.
        3. Сохраняет агрегированные сводки в таблицу `process_rollups_2min`.
        4. Удаляет обработанные детальные записи из `process_snapshots` для экономии места.

        Args:
            cutoff_seconds: Временной порог в секундах (по умолчанию 120 с / 2 мин).
            outlier_cpu_threshold: Порог процента CPU, считающийся выбросом (по умолчанию 30.0%).

        Returns:
            Dict[str, int]: Количество созданных агрегатов, сохраненных выбросов и удаленных строк.
        """
        now_epoch = datetime.now(timezone.utc).timestamp()
        cutoff_epoch = now_epoch - cutoff_seconds

        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()

            # Получаем все детальные записи процессов старше cutoff_epoch
            cursor.execute("""
                SELECT p.id, p.snapshot_id, p.timestamp, p.pid, p.name, p.status,
                       p.cpu_percent, p.memory_mb, p.memory_percent, p.num_threads,
                       p.username, s.created_at as snap_epoch
                FROM process_snapshots p
                JOIN system_snapshots s ON p.snapshot_id = s.id
                WHERE s.created_at < ?
                ORDER BY p.name, p.pid, s.created_at ASC
            """, (cutoff_epoch,))
            raw_rows = cursor.fetchall()

            if not raw_rows:
                return {"rollups_created": 0, "outliers_saved": 0, "raw_deleted": 0}

            # 1. Выделяем выбросы
            outlier_rows = []
            for r in raw_rows:
                cpu_val = float(r["cpu_percent"] or 0.0)
                if cpu_val >= outlier_cpu_threshold:
                    outlier_rows.append((
                        r["snapshot_id"],
                        r["timestamp"],
                        r["snap_epoch"],
                        r["pid"],
                        r["name"],
                        r["status"] or "running",
                        cpu_val,
                        float(r["memory_mb"] or 0.0),
                        float(r["memory_percent"] or 0.0),
                        int(r["num_threads"] or 1),
                        r["username"] or "",
                        f"Outlier detected: CPU={cpu_val:.1f}% >= {outlier_cpu_threshold}%",
                    ))

            outliers_saved = 0
            if outlier_rows:
                cursor.executemany("""
                    INSERT INTO process_outliers (
                        snapshot_id, timestamp, created_at, pid, name, status,
                        cpu_percent, memory_mb, memory_percent, num_threads, username, details
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, outlier_rows)
                outliers_saved = len(outlier_rows)

            # 2. Группируем записи по (name, pid) для расчета средних и экстремумов
            from collections import defaultdict
            grouped = defaultdict(list)
            for r in raw_rows:
                key = (r["name"], r["pid"])
                grouped[key].append(r)

            rollup_rows = []
            for (p_name, p_pid), procs in grouped.items():
                sample_count = len(procs)
                p_start = procs[0]["timestamp"]
                p_end = procs[-1]["timestamp"]
                p_start_epoch = procs[0]["snap_epoch"]
                p_end_epoch = procs[-1]["snap_epoch"]
                p_user = procs[-1]["username"] or ""

                cpus = [float(p["cpu_percent"] or 0.0) for p in procs]
                mems = [float(p["memory_mb"] or 0.0) for p in procs]
                threads = [int(p["num_threads"] or 1) for p in procs]

                avg_cpu = round(sum(cpus) / sample_count, 2)
                max_cpu = round(max(cpus), 2)
                min_cpu = round(min(cpus), 2)

                avg_mem = round(sum(mems) / sample_count, 2)
                max_mem = round(max(mems), 2)
                min_mem = round(min(mems), 2)

                avg_threads = round(sum(threads) / sample_count, 1)
                proc_outliers = sum(1 for c in cpus if c >= outlier_cpu_threshold)

                rollup_rows.append((
                    p_start,
                    p_end,
                    p_start_epoch,
                    p_end_epoch,
                    p_name,
                    p_pid,
                    p_user,
                    sample_count,
                    avg_cpu,
                    max_cpu,
                    min_cpu,
                    avg_mem,
                    max_mem,
                    min_mem,
                    avg_threads,
                    proc_outliers,
                ))

            if rollup_rows:
                cursor.executemany("""
                    INSERT INTO process_rollups_2min (
                        period_start, period_end, period_start_epoch, period_end_epoch,
                        name, pid, username, sample_count, avg_cpu_percent, max_cpu_percent,
                        min_cpu_percent, avg_memory_mb, max_memory_mb, min_memory_mb,
                        avg_num_threads, outliers_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, rollup_rows)

            # 3. Удаляем обобщенные детальные записи из process_snapshots
            raw_ids = [r["id"] for r in raw_rows]
            cursor.execute(f"""
                DELETE FROM process_snapshots
                WHERE id IN ({','.join(['?'] * len(raw_ids))})
            """, raw_ids)

            conn.commit()
            logger.info(
                f"Обобщение процессов (> {cutoff_seconds}с) выполнено: "
                f"агрегатов={len(rollup_rows)}, выбросов={outliers_saved}, удалено_сырых={len(raw_ids)}"
            )
            return {
                "rollups_created": len(rollup_rows),
                "outliers_saved": outliers_saved,
                "raw_deleted": len(raw_ids),
            }

    def aggregate_process_metrics_daily(
        self,
        cutoff_days: int = 1,
    ) -> Dict[str, int]:
        """Обобщает агрегаты процессов старше одного дня в суточную статистику.

        Args:
            cutoff_days: Порог устаревания в днях (по умолчанию 1 день / 24 часа).

        Returns:
            Dict[str, int]: Количество созданных суточных записей и очищенных 2-минутных агрегатов.
        """
        now_epoch = datetime.now(timezone.utc).timestamp()
        cutoff_epoch = now_epoch - (cutoff_days * 86400)

        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, period_start, period_end, period_end_epoch, name,
                       sample_count, avg_cpu_percent, max_cpu_percent,
                       avg_memory_mb, max_memory_mb, outliers_count
                FROM process_rollups_2min
                WHERE period_end_epoch < ?
                ORDER BY name, period_start_epoch ASC
            """, (cutoff_epoch,))
            old_rollups = cursor.fetchall()

            if not old_rollups:
                return {"daily_rollups_created": 0, "2min_rollups_cleaned": 0}

            from collections import defaultdict
            # Группируем по (date, name)
            grouped_daily = defaultdict(list)
            for r in old_rollups:
                d_str = r["period_start"][:10] if len(r["period_start"]) >= 10 else "unknown"
                key = (d_str, r["name"])
                grouped_daily[key].append(r)

            daily_rows = []
            for (d_str, p_name), items in grouped_daily.items():
                total_samples = sum(int(it["sample_count"]) for it in items)
                if total_samples <= 0:
                    continue
                # Взвешенное среднее CPU и Memory
                weighted_cpu = sum(float(it["avg_cpu_percent"]) * int(it["sample_count"]) for it in items) / total_samples
                max_cpu = max(float(it["max_cpu_percent"]) for it in items)
                weighted_mem = sum(float(it["avg_memory_mb"]) * int(it["sample_count"]) for it in items) / total_samples
                max_mem = max(float(it["max_memory_mb"]) for it in items)
                total_outliers = sum(int(it["outliers_count"] or 0) for it in items)
                last_seen = max(it["period_end"] for it in items)

                daily_rows.append((
                    d_str,
                    p_name,
                    total_samples,
                    round(weighted_cpu, 2),
                    round(max_cpu, 2),
                    round(weighted_mem, 2),
                    round(max_mem, 2),
                    total_outliers,
                    last_seen,
                ))

            if daily_rows:
                cursor.executemany("""
                    INSERT INTO process_rollups_daily (
                        date, name, sample_count, avg_cpu_percent, max_cpu_percent,
                        avg_memory_mb, max_memory_mb, outliers_count, last_seen
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, daily_rows)

            del_ids = [r["id"] for r in old_rollups]
            cursor.execute(f"""
                DELETE FROM process_rollups_2min
                WHERE id IN ({','.join(['?'] * len(del_ids))})
            """, del_ids)

            conn.commit()
            logger.info(
                f"Суточное обобщение процессов (> {cutoff_days} дн.) выполнено: "
                f"суточных_записей={len(daily_rows)}, очищено_2min_агрегатов={len(del_ids)}"
            )
            return {
                "daily_rollups_created": len(daily_rows),
                "2min_rollups_cleaned": len(del_ids),
            }

    def get_process_stats(
        self,
        name: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Возвращает историческую статистику процессов, включая агрегаты и выбросы.

        Args:
            name: Фильтр по имени процесса (подстрока, опционально).
            limit: Лимит записей.

        Returns:
            Dict[str, Any]: Словарь с краткосрочными агрегатами, суточной статистикой и выбросами.
        """
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Недавние агрегаты (2min rollups)
            if name:
                cursor.execute("""
                    SELECT * FROM process_rollups_2min
                    WHERE name LIKE ?
                    ORDER BY id DESC LIMIT ?
                """, (f"%{name}%", limit))
            else:
                cursor.execute("""
                    SELECT * FROM process_rollups_2min
                    ORDER BY id DESC LIMIT ?
                """, (limit,))
            rollups_2min = [dict(r) for r in cursor.fetchall()]

            # 2. Долгосрочная суточная статистика
            if name:
                cursor.execute("""
                    SELECT * FROM process_rollups_daily
                    WHERE name LIKE ?
                    ORDER BY date DESC LIMIT ?
                """, (f"%{name}%", limit))
            else:
                cursor.execute("""
                    SELECT * FROM process_rollups_daily
                    ORDER BY date DESC LIMIT ?
                """, (limit,))
            daily_stats = [dict(r) for r in cursor.fetchall()]

            # 3. Зафиксированные выбросы
            if name:
                cursor.execute("""
                    SELECT * FROM process_outliers
                    WHERE name LIKE ?
                    ORDER BY id DESC LIMIT ?
                """, (f"%{name}%", limit))
            else:
                cursor.execute("""
                    SELECT * FROM process_outliers
                    ORDER BY id DESC LIMIT ?
                """, (limit,))
            outliers = [dict(r) for r in cursor.fetchall()]

            return {
                "name_filter": name,
                "rollups_2min": rollups_2min,
                "daily_stats": daily_stats,
                "outliers": outliers,
                "total_rollups_count": len(rollups_2min),
                "total_outliers_count": len(outliers),
            }

    def get_events(
        self,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Извлекает список зафиксированных событий телеметрии.

        Args:
            event_type: Фильтр по типу события.
            limit: Лимит записей.

        Returns:
            List[Dict[str, Any]]: Список событий телеметрии.
        """
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            if event_type:
                cursor.execute("""
                    SELECT * FROM telemetry_events
                    WHERE event_type = ?
                    ORDER BY id DESC LIMIT ?
                """, (event_type, limit))
            else:
                cursor.execute("""
                    SELECT * FROM telemetry_events
                    ORDER BY id DESC LIMIT ?
                """, (limit,))

            return [dict(row) for row in cursor.fetchall()]

    def get_sensor_history(
        self,
        sensor_id: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Извлекает историю показаний сенсоров.

        Args:
            sensor_id: Идентификатор конкретного сенсора.
            category: Категория сенсора (Temperatures, Load, Clocks и др.).
            limit: Лимит записей.

        Returns:
            List[Dict[str, Any]]: Список измерений сенсоров.
        """
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            if sensor_id and category:
                cursor.execute("""
                    SELECT * FROM sensor_polls
                    WHERE sensor_id = ? AND sensor_category = ?
                    ORDER BY id DESC LIMIT ?
                """, (sensor_id, category, limit))
            elif sensor_id:
                cursor.execute("""
                    SELECT * FROM sensor_polls
                    WHERE sensor_id = ?
                    ORDER BY id DESC LIMIT ?
                """, (sensor_id, limit))
            elif category:
                cursor.execute("""
                    SELECT * FROM sensor_polls
                    WHERE sensor_category = ?
                    ORDER BY id DESC LIMIT ?
                """, (category, limit))
            else:
                cursor.execute("""
                    SELECT * FROM sensor_polls
                    ORDER BY id DESC LIMIT ?
                """, (limit,))

            return [dict(row) for row in cursor.fetchall()]

    def get_latest_sensors(self) -> List[Dict[str, Any]]:
        """Извлекает последнее актуальное значение для каждого сенсора.

        Returns:
            List[Dict[str, Any]]: Список последних замеров всех сенсоров.
        """
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s1.* FROM sensor_polls s1
                INNER JOIN (
                    SELECT sensor_id, MAX(id) as max_id
                    FROM sensor_polls
                    GROUP BY sensor_id
                ) s2 ON s1.id = s2.max_id
                ORDER BY s1.sensor_category, s1.sensor_name;
            """)
            return [dict(row) for row in cursor.fetchall()]

    def save_app_poll(
        self,
        app: str,
        poll_type: str,
        metric_name: str,
        value: Any,
        unit: str = "",
        status: str = "OK",
        details: Any = "",
        timestamp: Optional[str] = None,
    ) -> int:
        """Сохраняет запись периодического опроса метрики приложения в БД SQLite.

        Args:
            app: Имя приложения (например, 'cloudflared_monitor', 'trading_terminal').
            poll_type: Категория опроса ('status_check', 'metrics_fetch', 'sensor_read').
            metric_name: Название метрики.
            value: Численное или строковое значение.
            unit: Единица измерения.
            status: Статус проверки ('OK', 'ALERT', 'ERROR').
            details: Дополнительные детали или словарь.
            timestamp: ISO временная метка.

        Returns:
            int: ID созданной записи.
        """
        now_dt = datetime.now(timezone.utc)
        ts_str = timestamp or now_dt.isoformat()
        now_epoch = now_dt.timestamp()

        try:
            val_num = float(value) if value is not None and not isinstance(value, (dict, list)) else None
        except (ValueError, TypeError):
            val_num = None

        details_str = json.dumps(details, ensure_ascii=False) if isinstance(details, (dict, list)) else str(details or "")
        raw_json = json.dumps({
            "app": app, "poll_type": poll_type, "metric_name": metric_name,
            "value": value, "unit": unit, "status": status, "details": details,
        }, ensure_ascii=False)

        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO app_polls (
                    timestamp, created_at, app, poll_type, metric_name, value, unit, status, details, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (ts_str, now_epoch, app, poll_type, metric_name, val_num, unit, status, details_str, raw_json))
            conn.commit()
            return int(cursor.lastrowid or 0)

    def save_app_event(
        self,
        app: str,
        event_type: str,
        status: str = "OK",
        details: Any = "",
        timestamp: Optional[str] = None,
    ) -> int:
        """Сохраняет событие приложения в SQLite.

        Args:
            app: Имя приложения (например, 'windows_backup', 'helpdesk').
            event_type: Тип события ('service_start', 'backup_complete', 'ticket_create').
            status: Статус выполнения ('OK', 'SUCCESS', 'FAILED').
            details: Дополнительные метаданные или описание.
            timestamp: ISO временная метка.

        Returns:
            int: ID созданной записи.
        """
        now_dt = datetime.now(timezone.utc)
        ts_str = timestamp or now_dt.isoformat()
        now_epoch = now_dt.timestamp()

        details_str = json.dumps(details, ensure_ascii=False) if isinstance(details, (dict, list)) else str(details or "")
        raw_json = json.dumps({
            "app": app, "event_type": event_type, "status": status, "details": details,
        }, ensure_ascii=False)

        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO app_events (
                    timestamp, created_at, app, event_type, status, details, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (ts_str, now_epoch, app, event_type, status, details_str, raw_json))
            conn.commit()
            return int(cursor.lastrowid or 0)

    def save_app_param_change(
        self,
        app: str,
        param_name: str,
        old_value: Any,
        new_value: Any,
        status: str = "SUCCESS",
        user: str = "system",
        details: Any = "",
        timestamp: Optional[str] = None,
    ) -> int:
        """Сохраняет факт изменения параметра конфигурации в SQLite.

        Args:
            app: Имя приложения.
            param_name: Имя параметра.
            old_value: Предыдущее значение.
            new_value: Новое значение.
            status: Статус операции ('SUCCESS', 'FAILED').
            user: Пользователь или подсистема.
            details: Дополнительные детали.
            timestamp: ISO временная метка.

        Returns:
            int: ID созданной записи.
        """
        now_dt = datetime.now(timezone.utc)
        ts_str = timestamp or now_dt.isoformat()
        now_epoch = now_dt.timestamp()

        old_str = json.dumps(old_value, ensure_ascii=False) if isinstance(old_value, (dict, list)) else str(old_value or "")
        new_str = json.dumps(new_value, ensure_ascii=False) if isinstance(new_value, (dict, list)) else str(new_value or "")
        details_str = json.dumps(details, ensure_ascii=False) if isinstance(details, (dict, list)) else str(details or "")
        raw_json = json.dumps({
            "app": app, "param_name": param_name, "old_value": old_value,
            "new_value": new_value, "status": status, "user": user, "details": details,
        }, ensure_ascii=False)

        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO app_param_changes (
                    timestamp, created_at, app, param_name, old_value, new_value, status, user, details, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (ts_str, now_epoch, app, param_name, old_str, new_str, status, user, details_str, raw_json))
            conn.commit()
            return int(cursor.lastrowid or 0)

    def save_custom_record(
        self,
        source_file: str,
        payload: Dict[str, Any],
        timestamp: Optional[str] = None,
    ) -> int:
        """Сохраняет произвольную запись лога в SQLite.

        Args:
            source_file: Имя исходного журнала (например, 'file_watcher_anomalies.csv').
            payload: Данные строки в виде словаря.
            timestamp: ISO временная метка.

        Returns:
            int: ID созданной записи.
        """
        now_dt = datetime.now(timezone.utc)
        ts_str = timestamp or payload.get("timestamp") or payload.get("time") or now_dt.isoformat()
        now_epoch = now_dt.timestamp()
        payload_str = json.dumps(payload, ensure_ascii=False)

        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO custom_records (
                    timestamp, created_at, source_file, payload_json
                ) VALUES (?, ?, ?, ?)
            """, (ts_str, now_epoch, source_file, payload_str))
            conn.commit()
            return int(cursor.lastrowid or 0)

    def get_app_polls(
        self,
        app: Optional[str] = None,
        metric_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Извлекает историю опросов приложений из SQLite.

        Args:
            app: Имя приложения (опционально).
            metric_name: Имя метрики (опционально).
            limit: Максимальное количество записей.

        Returns:
            List[Dict[str, Any]]: Список записей опросов.
        """
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            if app and metric_name:
                cursor.execute("""
                    SELECT * FROM app_polls WHERE app = ? AND metric_name = ?
                    ORDER BY id DESC LIMIT ?
                """, (app, metric_name, limit))
            elif app:
                cursor.execute("""
                    SELECT * FROM app_polls WHERE app = ?
                    ORDER BY id DESC LIMIT ?
                """, (app, limit))
            else:
                cursor.execute("SELECT * FROM app_polls ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_app_events(
        self,
        app: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Извлекает события приложений из SQLite.

        Args:
            app: Имя приложения.
            event_type: Тип события.
            limit: Лимит записей.

        Returns:
            List[Dict[str, Any]]: Список событий.
        """
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            if app and event_type:
                cursor.execute("""
                    SELECT * FROM app_events WHERE app = ? AND event_type = ?
                    ORDER BY id DESC LIMIT ?
                """, (app, event_type, limit))
            elif app:
                cursor.execute("""
                    SELECT * FROM app_events WHERE app = ?
                    ORDER BY id DESC LIMIT ?
                """, (app, limit))
            else:
                cursor.execute("SELECT * FROM app_events ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_app_param_changes(
        self,
        app: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Извлекает историю изменения настроек и параметров приложений."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            if app:
                cursor.execute("""
                    SELECT * FROM app_param_changes WHERE app = ?
                    ORDER BY id DESC LIMIT ?
                """, (app, limit))
            else:
                cursor.execute("SELECT * FROM app_param_changes ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_custom_records(
        self,
        source_file: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Извлекает кастомные записи логов из SQLite."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            if source_file:
                cursor.execute("""
                    SELECT * FROM custom_records WHERE source_file = ?
                    ORDER BY id DESC LIMIT ?
                """, (source_file, limit))
            else:
                cursor.execute("SELECT * FROM custom_records ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def save_app_polls_batch(self, polls: List[Dict[str, Any]]) -> int:
        """Сохраняет пачку опросов приложений в SQLite за одну транзакцию.

        Args:
            polls: Список словарей параметров опросов.

        Returns:
            int: Количество сохраненных записей.
        """
        if not polls:
            return 0
        now_dt = datetime.now(timezone.utc)
        now_epoch = now_dt.timestamp()

        rows = []
        for p in polls:
            ts_str = p.get("timestamp") or now_dt.isoformat()
            app = p.get("app", "unknown")
            poll_type = p.get("poll_type", "poll")
            metric_name = p.get("metric_name", "metric")
            val = p.get("value")
            try:
                val_num = float(val) if val is not None and not isinstance(val, (dict, list)) else None
            except (ValueError, TypeError):
                val_num = None
            unit = p.get("unit", "")
            status = p.get("status", "OK")
            details = p.get("details", "")
            details_str = json.dumps(details, ensure_ascii=False) if isinstance(details, (dict, list)) else str(details or "")
            raw_json = json.dumps({
                "app": app, "poll_type": poll_type, "metric_name": metric_name,
                "value": val, "unit": unit, "status": status, "details": details,
            }, ensure_ascii=False)
            rows.append((ts_str, now_epoch, app, poll_type, metric_name, val_num, unit, status, details_str, raw_json))

        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT INTO app_polls (
                    timestamp, created_at, app, poll_type, metric_name, value, unit, status, details, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, rows)
            conn.commit()
            return len(rows)

    def save_app_events_batch(self, events: List[Dict[str, Any]]) -> int:
        """Сохраняет пачку событий приложений в SQLite за одну транзакцию.

        Args:
            events: Список словарей событий.

        Returns:
            int: Количество сохраненных записей.
        """
        if not events:
            return 0
        now_dt = datetime.now(timezone.utc)
        now_epoch = now_dt.timestamp()

        rows = []
        for ev in events:
            ts_str = ev.get("timestamp") or now_dt.isoformat()
            app = ev.get("app", "unknown")
            event_type = ev.get("event_type", "event")
            status = ev.get("status", "OK")
            details = ev.get("details", "")
            details_str = json.dumps(details, ensure_ascii=False) if isinstance(details, (dict, list)) else str(details or "")
            raw_json = json.dumps({
                "app": app, "event_type": event_type, "status": status, "details": details,
            }, ensure_ascii=False)
            rows.append((ts_str, now_epoch, app, event_type, status, details_str, raw_json))

        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT INTO app_events (
                    timestamp, created_at, app, event_type, status, details, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, rows)
            conn.commit()
            return len(rows)

    def save_app_param_changes_batch(self, param_changes: List[Dict[str, Any]]) -> int:
        """Сохраняет пачку изменений параметров приложений за одну транзакцию.

        Args:
            param_changes: Список словарей изменений параметров.

        Returns:
            int: Количество сохраненных записей.
        """
        if not param_changes:
            return 0
        now_dt = datetime.now(timezone.utc)
        now_epoch = now_dt.timestamp()

        rows = []
        for pc in param_changes:
            ts_str = pc.get("timestamp") or now_dt.isoformat()
            app = pc.get("app", "unknown")
            param_name = pc.get("param_name", "param")
            old_val = pc.get("old_value")
            new_val = pc.get("new_value")
            old_str = json.dumps(old_val, ensure_ascii=False) if isinstance(old_val, (dict, list)) else str(old_val or "")
            new_str = json.dumps(new_val, ensure_ascii=False) if isinstance(new_val, (dict, list)) else str(new_val or "")
            status = pc.get("status", "SUCCESS")
            user = pc.get("user", "system")
            details = pc.get("details", "")
            details_str = json.dumps(details, ensure_ascii=False) if isinstance(details, (dict, list)) else str(details or "")
            raw_json = json.dumps({
                "app": app, "param_name": param_name, "old_value": old_val,
                "new_value": new_val, "status": status, "user": user, "details": details,
            }, ensure_ascii=False)
            rows.append((ts_str, now_epoch, app, param_name, old_str, new_str, status, user, details_str, raw_json))

        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT INTO app_param_changes (
                    timestamp, created_at, app, param_name, old_value, new_value, status, user, details, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, rows)
            conn.commit()
            return len(rows)

    def save_device_event(
        self,
        event: Dict[str, Any],
        timestamp: Optional[str] = None,
    ) -> int:
        """Сохраняет событие устройства (подключение/отключение/дребезг/ошибка PnP) в БД.

        Args:
            event: Словарь с полями DeviceTransitionEvent.
            timestamp: ISO временная метка.

        Returns:
            int: ID созданной записи.
        """
        now_dt = datetime.now(timezone.utc)
        ts_str = timestamp or event.get("timestamp") or now_dt.isoformat()
        now_epoch = now_dt.timestamp()
        raw_json = json.dumps(event, ensure_ascii=False, default=str)

        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO device_events (
                    timestamp, created_at, event_type, device_instance_id,
                    friendly_name, device_class, category, has_problem,
                    problem_code, status_code, manufacturer,
                    flapping_count, uptime_seconds, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ts_str,
                now_epoch,
                event.get("event_type", ""),
                event.get("device_instance_id", ""),
                event.get("friendly_name", ""),
                event.get("device_class", ""),
                event.get("category", ""),
                int(bool(event.get("has_problem", False))),
                event.get("problem_code", 0),
                event.get("status_code", 0),
                event.get("manufacturer", ""),
                event.get("flapping_count_in_window", 0),
                event.get("uptime_seconds", 0.0),
                raw_json,
            ))
            conn.commit()
            return cursor.lastrowid or 0

    def get_device_events(
        self,
        event_type: Optional[str] = None,
        device_instance_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Извлекает события устройств из БД.

        Args:
            event_type: Фильтр по типу (CONNECTED, DISCONNECTED, FLAPPING_ALERT, ERROR_STATE_CHANGED).
            device_instance_id: Фильтр по конкретному устройству.
            limit: Лимит записей.

        Returns:
            List[Dict[str, Any]]: Список событий.
        """
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            if event_type and device_instance_id:
                cursor.execute("""
                    SELECT * FROM device_events
                    WHERE event_type = ? AND device_instance_id = ?
                    ORDER BY id DESC LIMIT ?
                """, (event_type, device_instance_id, limit))
            elif event_type:
                cursor.execute("""
                    SELECT * FROM device_events
                    WHERE event_type = ?
                    ORDER BY id DESC LIMIT ?
                """, (event_type, limit))
            elif device_instance_id:
                cursor.execute("""
                    SELECT * FROM device_events
                    WHERE device_instance_id = ?
                    ORDER BY id DESC LIMIT ?
                """, (device_instance_id, limit))
            else:
                cursor.execute("""
                    SELECT * FROM device_events ORDER BY id DESC LIMIT ?
                """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_storage_stats(self) -> Dict[str, Any]:
        """Возвращает агрегированную статистику базы данных телеметрии.

        Returns:
            Dict[str, Any]: Статистика таблиц и размер БД.
        """
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM system_snapshots;")
            snap_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM process_snapshots;")
            proc_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM sensor_polls;")
            sensors_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM telemetry_events;")
            events_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM hardware_audits;")
            audits_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM app_polls;")
            app_polls_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM app_events;")
            app_events_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM app_param_changes;")
            app_params_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM custom_records;")
            custom_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM device_events;")
            device_events_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM process_outliers;")
            outliers_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM process_rollups_2min;")
            rollups_2min_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM process_rollups_daily;")
            rollups_daily_count = cursor.fetchone()[0]

            size_bytes = self.db_path.stat().st_size if self.db_path.exists() else 0
            size_mb = round(size_bytes / (1024 * 1024), 2)

            return {
                "db_path": str(self.db_path),
                "snapshots_count": snap_count,
                "process_snapshots_count": proc_count,
                "process_outliers_count": outliers_count,
                "process_rollups_2min_count": rollups_2min_count,
                "process_rollups_daily_count": rollups_daily_count,
                "sensor_polls_count": sensors_count,
                "events_count": events_count,
                "hardware_audits_count": audits_count,
                "app_polls_count": app_polls_count,
                "app_events_count": app_events_count,
                "app_param_changes_count": app_params_count,
                "custom_records_count": custom_count,
                "device_events_count": device_events_count,
                "file_size_mb": size_mb,
            }

    def cleanup_old_records(self, retention_days: int = 7) -> int:
        """Удаляет устаревшие записи телеметрии старше указанного количества дней.

        Args:
            retention_days: Срок хранения данных в днях (по умолчанию 7 дней).

        Returns:
            int: Количество удаленных основных снимков.
        """
        threshold_epoch = datetime.now(timezone.utc).timestamp() - (retention_days * 86400)
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM system_snapshots WHERE created_at < ?", (threshold_epoch,))
            old_ids = [row[0] for row in cursor.fetchall()]

            if old_ids:
                cursor.execute(
                    "DELETE FROM process_snapshots WHERE snapshot_id IN (SELECT id FROM system_snapshots WHERE created_at < ?)",
                    (threshold_epoch,),
                )
                cursor.execute("DELETE FROM system_snapshots WHERE created_at < ?", (threshold_epoch,))

            cursor.execute("DELETE FROM sensor_polls WHERE created_at < ?", (threshold_epoch,))
            cursor.execute("DELETE FROM telemetry_events WHERE created_at < ?", (threshold_epoch,))
            cursor.execute("DELETE FROM app_polls WHERE created_at < ?", (threshold_epoch,))
            cursor.execute("DELETE FROM app_events WHERE created_at < ?", (threshold_epoch,))
            cursor.execute("DELETE FROM app_param_changes WHERE created_at < ?", (threshold_epoch,))
            cursor.execute("DELETE FROM custom_records WHERE created_at < ?", (threshold_epoch,))
            conn.commit()

            deleted_count = len(old_ids)
            logger.info(f"Очищено {deleted_count} устаревших снимков телеметрии (старше {retention_days} дн.)")
            return deleted_count

