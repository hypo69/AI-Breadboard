# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: System Telemetry SQLite Storage
# =============================================================================
# Description:
#   Обеспечивает сохранение и извлечение системных метрик и Top-процессов
#   в локальной базе данных SQLite (data/telemetry.db) с поддержкой WAL-режима.
#
# Examples:
#   >>> from apps.windows.telemetry.storage import TelemetryStorage
#   >>> storage = TelemetryStorage()
#   >>> snapshot_id = storage.save_snapshot(snapshot, top_n=20)
#   >>> history = storage.get_snapshots(limit=10)
#
# File: storage.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Хранилище SQLite для системной телеметрии и процессов Windows."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from header import __root__
from src.logger import logger
from apps.windows.telemetry.models import SystemSnapshot, ProcessMetrics


class TelemetryStorage:
    """Класс для управления сохранением и выборкой системной телеметрии в SQLite."""

    def __init__(self, db_path: Optional[Path | str] = None) -> None:
        """Инициализирует подключение к SQLite базе данных телеметрии."""
        if db_path is None:
            self.db_path = __root__ / "data" / "telemetry.db"
        else:
            self.db_path = Path(db_path)

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._last_snapshot_json: Optional[str] = None
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Создает и настраивает соединение с базой данных SQLite."""
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self) -> None:
        """Создает таблицы и индексы в базе данных, если они отсутствуют."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()

            # Таблица снапшотов всей системы
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
                    disk_read_bytes_sec REAL,
                    disk_write_bytes_sec REAL,
                    disk_read_count_sec REAL,
                    disk_write_count_sec REAL,
                    network_sent_bytes_sec REAL,
                    network_recv_bytes_sec REAL,
                    raw_json TEXT
                );
            """)

            # Таблица среза Top-процессов
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
                    username TEXT,
                    read_bytes_sec REAL,
                    write_bytes_sec REAL,
                    FOREIGN KEY (snapshot_id) REFERENCES system_snapshots (id) ON DELETE CASCADE
                );
            """)

            # Таблица логов аудита ПО
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS software_audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    total_apps INTEGER NOT NULL,
                    raw_report TEXT NOT NULL
                );
            """)

            # Создание индексов для быстрой выборки по времени и связям
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sys_snapshots_time ON system_snapshots (created_at);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sys_snapshots_timestamp ON system_snapshots (timestamp);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_proc_snapshots_snap_id ON process_snapshots (snapshot_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_proc_snapshots_name ON process_snapshots (name);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_time ON software_audit_logs (timestamp);")
            conn.commit()

    def save_audit_log(self, total_apps: int, raw_report: str) -> int:
        """Сохраняет отчет аудита ПО в базу данных."""
        now_ts = datetime.now(timezone.utc).isoformat()
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO software_audit_logs (timestamp, total_apps, raw_report)
                VALUES (?, ?, ?)
            """, (now_ts, total_apps, raw_report))
            conn.commit()
            return cursor.lastrowid or 0

    def save_snapshot(self, snapshot: SystemSnapshot, top_n: int = 20) -> int:
        """Сохраняет системный снимок в базу данных только при наличии изменений."""
        current_json = snapshot.model_dump_json()
        if self._last_snapshot_json == current_json:
            return 0  # Снимок не изменился
        
        self._last_snapshot_json = current_json
        
        now_epoch = datetime.now(timezone.utc).timestamp()
        ts_str = snapshot.timestamp or datetime.now(timezone.utc).isoformat()

        # Суммируем сетевую активность
        net_sent = sum(net.bytes_sent_per_sec for net in snapshot.network) if snapshot.network else 0.0
        net_recv = sum(net.bytes_recv_per_sec for net in snapshot.network) if snapshot.network else 0.0

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
                    disk_read_bytes_sec,
                    disk_write_bytes_sec,
                    disk_read_count_sec,
                    disk_write_count_sec,
                    network_sent_bytes_sec,
                    network_recv_bytes_sec,
                    raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                snapshot.disk_io.read_bytes_per_sec if snapshot.disk_io else 0.0,
                snapshot.disk_io.write_bytes_per_sec if snapshot.disk_io else 0.0,
                snapshot.disk_io.read_count_per_sec if snapshot.disk_io else 0.0,
                snapshot.disk_io.write_count_per_sec if snapshot.disk_io else 0.0,
                net_sent,
                net_recv,
                current_json,
            ))

            snapshot_id = cursor.lastrowid or 0

            # Сохраняем Top-N процессов
            processes = (snapshot.top_processes or [])[:top_n]
            proc_rows = []
            for p in processes:
                proc_rows.append((
                    snapshot_id,
                    ts_str,
                    p.pid,
                    p.name,
                    p.status,
                    p.cpu_percent,
                    p.memory_mb,
                    p.memory_percent,
                    p.num_threads,
                    p.username or "",
                    p.read_bytes_sec,
                    p.write_bytes_sec,
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
                        username,
                        read_bytes_sec,
                        write_bytes_sec
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, proc_rows)

            conn.commit()
            return snapshot_id

    def get_snapshots(self, limit: int = 60, since_epoch: Optional[float] = None) -> List[Dict[str, Any]]:
        """Извлекает исторические срезы системной телеметрии."""
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

            rows = cursor.fetchall()
            result = []
            for row in rows:
                d = dict(row)
                result.append(d)
            return result

    def get_snapshot_processes(self, snapshot_id: int) -> List[Dict[str, Any]]:
        """Извлекает список процессов, зафиксированных в конкретном снимке."""
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
        """Извлекает историю поведения конкретного процесса по имени или PID."""
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

    def get_storage_stats(self) -> Dict[str, Any]:
        """Возвращает общую статистику хранилища."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM system_snapshots;")
            snap_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM process_snapshots;")
            proc_count = cursor.fetchone()[0]

            size_bytes = self.db_path.stat().st_size if self.db_path.exists() else 0
            size_mb = round(size_bytes / (1024 * 1024), 2)

            return {
                "db_path": str(self.db_path),
                "snapshots_count": snap_count,
                "process_snapshots_count": proc_count,
                "file_size_mb": size_mb,
            }

    def cleanup_old_records(self, retention_days: int = 7) -> int:
        """Удаляет устаревшие записи телеметрии старше указанного количества дней."""
        threshold_epoch = datetime.now(timezone.utc).timestamp() - (retention_days * 86400)
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM system_snapshots WHERE created_at < ?", (threshold_epoch,))
            old_ids = [row[0] for row in cursor.fetchall()]

            if not old_ids:
                return 0

            cursor.execute("DELETE FROM process_snapshots WHERE snapshot_id IN (SELECT id FROM system_snapshots WHERE created_at < ?)", (threshold_epoch,))
            cursor.execute("DELETE FROM system_snapshots WHERE created_at < ?", (threshold_epoch,))
            conn.commit()
            deleted_count = len(old_ids)
            logger.info(f"Очищено {deleted_count} устаревших снимков телеметрии (старше {retention_days} дн.)")
            return deleted_count
