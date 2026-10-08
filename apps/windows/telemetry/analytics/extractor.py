# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry_Research - Extractor
# =============================================================================
# Description:
#   Загрузчик и парсер логов телеметрии из файлов и директорий.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry_research.extractor import TelemetryDataExtractor
#
#     service = TelemetryDataExtractor()
#
# File: extractor.py
# Project: ai-breadboard
# Package: apps.windows.telemetry_research
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Загрузчик и парсер логов телеметрии из файлов и директорий."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Union

try:
    from logger import logger
except ImportError:
    from logger import logger

try:
    from apps.windows.telemetry.sqlite import TelemetryStorage
except ImportError:
    TelemetryStorage = None


class TelemetryDataExtractor:
    """Извлекатель и нормализатор данных из базы данных и файлов логов телеметрии."""

    def __init__(
        self,
        default_log_dirs: Optional[List[Union[str, Path]]] = None,
        storage: Optional[Any] = None,
    ) -> None:
        """Инициализация извлекателя логов.

        Args:
            default_log_dirs: Список базовых директорий для поиска логов по умолчанию.
            storage: Экземпляр хранилища SQLite базы данных.
        """
        self._storage = storage
        base_proj = Path(__file__).resolve().parents[3]
        appdata = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
        self.default_log_dirs = (
            [Path(p) for p in default_log_dirs]
            if default_log_dirs
            else [
                base_proj / "logs" / "telemetry",
                Path(appdata) / "AI-Breadboard" / "apps" / "logs",
                Path(appdata) / "AI-Breadboard" / "apps" / "windows" / "telemetry" / "logs",
                base_proj / "data" / "telemetry" / "hardware_archives",
            ]
        )

    @property
    def storage(self) -> Optional[Any]:
        """Получить экземпляр SQLite хранилища телеметрии."""
        if self._storage is None and TelemetryStorage is not None:
            try:
                self._storage = TelemetryStorage.get_instance()
            except Exception:
                self._storage = None
        return self._storage

    def discover_log_files(self, search_dir: Optional[Union[str, Path]] = None) -> List[Path]:
        """Обнаружить все доступные файлы логов и базы данных телеметрии.

        Args:
            search_dir: Опциональная конкретная директория для поиска.

        Returns:
            List[Path]: Список обнаруженных путей к файлам логов.
        """
        dirs_to_scan = [Path(search_dir)] if search_dir else self.default_log_dirs
        found_files: List[Path] = []
        for d in dirs_to_scan:
            if not d.exists() or not d.is_dir():
                continue
            for pattern in ("*.db", "*.json", "*.jsonl", "*.log", "*.csv"):
                try:
                    for file_path in d.glob(pattern):
                        if file_path.is_file() and file_path.stat().st_size > 0:
                            found_files.append(file_path)
                except Exception as ex:
                    logger.warning(f"Ошибка сканирования директории {d} по шаблону {pattern}: {ex}")

        seen = set()
        unique_files = []
        for f in found_files:
            resolved = str(f.resolve())
            if resolved not in seen:
                seen.add(resolved)
                unique_files.append(f)
        return unique_files

    def parse_file(self, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """Распарсить конкретный файл логов или базу данных телеметрии.

        Args:
            file_path: Путь к файлу лога (.db, .json, .jsonl, .csv).

        Returns:
            List[Dict[str, Any]]: Список нормализованных записей с метками времени.
        """
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            logger.warning(f"Файл логов не найден: {path}")
            return []

        suffix = path.suffix.lower()
        if suffix == ".db":
            return self.load_from_sqlite_db(path)

        entries: List[Dict[str, Any]] = []
        try:
            if suffix in (".jsonl", ".log"):
                with path.open("r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line_str = line.strip()
                        if not line_str:
                            continue
                        try:
                            data = json.loads(line_str)
                            if isinstance(data, dict):
                                entries.append(self._normalize_entry(data, source_file=path.name))
                        except json.JSONDecodeError:
                            continue
            elif suffix == ".json":
                with path.open("r", encoding="utf-8", errors="replace") as f:
                    try:
                        content = json.load(f)
                        if isinstance(content, list):
                            for item in content:
                                if isinstance(item, dict):
                                    entries.append(self._normalize_entry(item, source_file=path.name))
                        elif isinstance(content, dict):
                            if "measurements" in content and isinstance(content["measurements"], list):
                                for item in content["measurements"]:
                                    if isinstance(item, dict):
                                        entries.append(self._normalize_entry(item, source_file=path.name))
                            elif "records" in content and isinstance(content["records"], list):
                                for item in content["records"]:
                                    if isinstance(item, dict):
                                        entries.append(self._normalize_entry(item, source_file=path.name))
                            else:
                                entries.append(self._normalize_entry(content, source_file=path.name))
                    except json.JSONDecodeError:
                        f.seek(0)
                        for line in f:
                            line_str = line.strip()
                            if not line_str:
                                continue
                            try:
                                data = json.loads(line_str)
                                if isinstance(data, dict):
                                    entries.append(self._normalize_entry(data, source_file=path.name))
                            except Exception:
                                continue
        except Exception as err:
            logger.error(f"Ошибка чтения файла логов {path}: {err}")
        return entries

    def get_default_db_path(self) -> Optional[Path]:
        """Получить путь к активной базе данных telemetry.db."""
        if self.storage and hasattr(self.storage, "db_path") and self.storage.db_path and Path(self.storage.db_path).exists():
            return Path(self.storage.db_path)
        appdata = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Roaming")
        candidates = [
            Path(appdata) / "AI-Breadboard" / "apps" / "windows" / "telemetry" / "logs" / "telemetry.db",
            Path(__file__).resolve().parents[3] / "logs" / "telemetry" / "telemetry.db",
            Path(appdata) / "AI-Breadboard" / "apps" / "logs" / "telemetry.db",
        ]
        for p in candidates:
            if p.exists() and p.is_file():
                return p
        return None

    def get_current_system_state(
        self, db_path: Optional[Union[str, Path]] = None, limit: int = 100
    ) -> Dict[str, Any]:
        """Получить актуальное состояние системы и временные ряды последних замеров из SQLite БД.

        Args:
            db_path: Путь к файлу telemetry.db (если не указан, используется база по умолчанию).
            limit: Количество последних точек временного ряда (по умолчанию 100).

        Returns:
            Dict[str, Any]: Словарь с текущим срезом метрик, временными рядами, сенсорами и процессами.
        """
        target_db = Path(db_path) if db_path else self.get_default_db_path()
        if not target_db or not target_db.exists():
            return {
                "status": "not_found",
                "message": "База данных telemetry.db не найдена",
                "db_path": str(target_db) if target_db else None,
                "latest_snapshot": {},
                "time_series": {},
                "sensors": [],
                "top_processes": [],
                "recent_events": [],
            }

        try:
            import sqlite3
            conn = sqlite3.connect(str(target_db), timeout=5.0)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}

            # 1. Последние системные снепшоты (хронологический порядок для графиков)
            snapshots: List[Dict[str, Any]] = []
            total_snapshots = 0
            if "system_snapshots" in tables:
                cursor.execute("SELECT count(*) FROM system_snapshots")
                total_snapshots = cursor.fetchone()[0]

                cursor.execute(
                    "SELECT * FROM system_snapshots ORDER BY id DESC LIMIT ?", (max(10, min(limit, 2000)),)
                )
                raw_snaps = [dict(r) for r in cursor.fetchall()]
                # Переворачиваем, чтобы временной ряд шел от старых к новым
                snapshots = list(reversed(raw_snaps))

            latest = snapshots[-1] if snapshots else {}

            # 2. Формирование временных рядов
            time_series = {
                "labels": [],
                "cpu_load": [],
                "cpu_freq_ghz": [],
                "ram_percent": [],
                "ram_used_gb": [],
                "gpu_load": [],
                "gpu_temp": [],
                "disk_read_mb": [],
                "disk_write_mb": [],
                "net_recv_kb": [],
                "net_sent_kb": [],
            }

            for s in snapshots:
                ts_str = str(s.get("timestamp", ""))
                # Короткая метка времени HH:MM:SS
                short_time = ts_str[11:19] if len(ts_str) >= 19 else ts_str
                time_series["labels"].append(short_time)
                time_series["cpu_load"].append(round(float(s.get("cpu_total_percent") or 0.0), 1))
                freq_mhz = float(s.get("cpu_frequency_mhz") or 0.0)
                time_series["cpu_freq_ghz"].append(round(freq_mhz / 1000.0, 2) if freq_mhz > 0 else 0.0)
                time_series["ram_percent"].append(round(float(s.get("memory_percent") or 0.0), 1))
                time_series["ram_used_gb"].append(round(float(s.get("memory_used_gb") or 0.0), 2))
                time_series["gpu_load"].append(round(float(s.get("gpu_load_percent") or 0.0), 1))
                time_series["gpu_temp"].append(round(float(s.get("gpu_temp_c") or 0.0), 1))

                # Диск: байты/сек -> MB/s
                rb = float(s.get("disk_read_bytes_sec") or 0.0)
                wb = float(s.get("disk_write_bytes_sec") or 0.0)
                time_series["disk_read_mb"].append(round(rb / (1024 * 1024), 2))
                time_series["disk_write_mb"].append(round(wb / (1024 * 1024), 2))

                # Сеть: байты/сек -> KB/s
                nr = float(s.get("network_recv_bytes_sec") or 0.0)
                ns = float(s.get("network_sent_bytes_sec") or 0.0)
                time_series["net_recv_kb"].append(round(nr / 1024, 1))
                time_series["net_sent_kb"].append(round(ns / 1024, 1))

            # 3. Актуальные сенсоры (LHM / Hardware)
            sensors: List[Dict[str, Any]] = []
            if "sensor_polls" in tables:
                cursor.execute(
                    """
                    SELECT sensor_name, sensor_category, unit, value, hardware_name, timestamp
                    FROM sensor_polls
                    ORDER BY id DESC LIMIT 50
                    """
                )
                seen_sensors = set()
                for r in cursor.fetchall():
                    s_dict = dict(r)
                    key = f"{s_dict.get('hardware_name')}_{s_dict.get('sensor_name')}"
                    if key not in seen_sensors:
                        seen_sensors.add(key)
                        sensors.append(s_dict)

            # 4. Топ активных процессов
            top_processes: List[Dict[str, Any]] = []
            if "process_snapshots" in tables and latest.get("id"):
                cursor.execute(
                    """
                    SELECT pid, name, cpu_percent, memory_mb, memory_percent, num_threads, username, status
                    FROM process_snapshots
                    WHERE snapshot_id = ?
                    ORDER BY cpu_percent DESC LIMIT 15
                    """,
                    (latest["id"],),
                )
                top_processes = [dict(r) for r in cursor.fetchall()]

            if not top_processes and "process_outliers" in tables:
                cursor.execute(
                    """
                    SELECT pid, name, cpu_percent, memory_mb, memory_percent, num_threads, username, status
                    FROM process_outliers
                    ORDER BY id DESC LIMIT 15
                    """
                )
                top_processes = [dict(r) for r in cursor.fetchall()]

            # 5. Последние события
            recent_events: List[Dict[str, Any]] = []
            if "device_events" in tables:
                cursor.execute(
                    """
                    SELECT timestamp, event_type, friendly_name, category, has_problem, problem_code
                    FROM device_events
                    ORDER BY id DESC LIMIT 8
                    """
                )
                for r in cursor.fetchall():
                    d = dict(r)
                    d["source"] = "device"
                    recent_events.append(d)

            if "w64_events" in tables:
                cursor.execute(
                    """
                    SELECT timestamp, event_type, path, name, pid, provider
                    FROM w64_events
                    ORDER BY id DESC LIMIT 8
                    """
                )
                for r in cursor.fetchall():
                    d = dict(r)
                    d["source"] = "system_activity"
                    recent_events.append(d)

            recent_events.sort(key=lambda x: str(x.get("timestamp", "")), reverse=True)
            recent_events = recent_events[:15]

            stat_info = target_db.stat()
            conn.close()

            return {
                "status": "ok",
                "db_path": str(target_db.resolve()),
                "db_name": target_db.name,
                "db_size_bytes": stat_info.st_size,
                "db_size_mb": round(stat_info.st_size / (1024 * 1024), 2),
                "total_snapshots": total_snapshots,
                "returned_points": len(snapshots),
                "latest_snapshot": latest,
                "time_series": time_series,
                "sensors": sensors,
                "top_processes": top_processes,
                "recent_events": recent_events,
            }
        except Exception as ex:
            logger.error(f"Ошибка получения текущего состояния из telemetry.db: {ex}")
            return {
                "status": "error",
                "message": str(ex),
                "db_path": str(target_db) if target_db else None,
                "latest_snapshot": {},
                "time_series": {},
                "sensors": [],
                "top_processes": [],
                "recent_events": [],
            }

    def load_from_sqlite_db(self, db_path: Union[str, Path], limit: int = 5000) -> List[Dict[str, Any]]:
        """Загрузить исторические записи телеметрии напрямую из произвольного SQLite файла.

        Args:
            db_path: Путь к файлу базы данных SQLite.
            limit: Максимальное число извлекаемых записей.

        Returns:
            List[Dict[str, Any]]: Список нормализованных записей из БД.
        """
        records: List[Dict[str, Any]] = []
        try:
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Проверка наличия таблиц
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}

            if "system_snapshots" in tables:
                cursor.execute("SELECT * FROM system_snapshots ORDER BY id DESC LIMIT ?", (limit,))
                for row in cursor.fetchall():
                    row_dict = dict(row)
                    row_dict["source_file"] = f"{Path(db_path).name}:system_snapshots"
                    records.append(self._normalize_entry(row_dict, source_file=f"{Path(db_path).name}:system_snapshots"))

            if "sensor_polls" in tables:
                cursor.execute("SELECT * FROM sensor_polls ORDER BY id DESC LIMIT ?", (limit,))
                for row in cursor.fetchall():
                    row_dict = dict(row)
                    row_dict["source_file"] = f"{Path(db_path).name}:sensor_polls"
                    records.append(self._normalize_entry(row_dict, source_file=f"{Path(db_path).name}:sensor_polls"))

            if "telemetry_events" in tables:
                cursor.execute("SELECT * FROM telemetry_events ORDER BY id DESC LIMIT ?", (limit,))
                for row in cursor.fetchall():
                    row_dict = dict(row)
                    row_dict["source_file"] = f"{Path(db_path).name}:telemetry_events"
                    records.append(self._normalize_entry(row_dict, source_file=f"{Path(db_path).name}:telemetry_events"))

            conn.close()
        except Exception as ex:
            logger.warning(f"Ошибка загрузки телеметрии из БД SQLite {db_path}: {ex}")
        return records

    def load_from_database(self, limit: int = 2000) -> List[Dict[str, Any]]:
        """Загрузить исторические записи телеметрии из стандартного хранилища.

        Args:
            limit: Максимальное число извлекаемых записей.

        Returns:
            List[Dict[str, Any]]: Список нормализованных записей из БД.
        """
        if self.storage is None:
            return []
        records: List[Dict[str, Any]] = []
        try:
            snapshots = self.storage.get_snapshots(limit=limit)
            for snap in snapshots:
                rec = dict(snap) if not isinstance(snap, dict) and hasattr(snap, "__dict__") else (snap if isinstance(snap, dict) else {})
                rec["source_file"] = "sqlite:system_snapshots"
                records.append(self._normalize_entry(rec, source_file="sqlite:system_snapshots"))
            sensor_polls = self.storage.get_sensor_history(limit=limit)
            for s in sensor_polls:
                rec = dict(s) if not isinstance(s, dict) and hasattr(s, "__dict__") else (s if isinstance(s, dict) else {})
                rec["source_file"] = "sqlite:sensor_polls"
                records.append(self._normalize_entry(rec, source_file="sqlite:sensor_polls"))
            events = self.storage.get_events(limit=limit)
            for ev in events:
                rec = dict(ev) if not isinstance(ev, dict) and hasattr(ev, "__dict__") else (ev if isinstance(ev, dict) else {})
                rec["source_file"] = "sqlite:telemetry_events"
                records.append(self._normalize_entry(rec, source_file="sqlite:telemetry_events"))
        except Exception as ex:
            logger.warning(f"Ошибка загрузки телеметрии из базы данных: {ex}")
        return records

    def load_all_records(
        self,
        source: Optional[Union[str, Path, List[Dict[str, Any]]]] = None,
        include_database: bool = True,
    ) -> List[Dict[str, Any]]:
        """Загрузить все записи телеметрии из источника, базы данных или найденных файлов.

        Args:
            source: Путь к директории, файлу или готовый список записей.
            include_database: Загружать ли записи из базы данных SQLite.

        Returns:
            List[Dict[str, Any]]: Отсортированный по времени список записей телеметрии.
        """
        if isinstance(source, list):
            return [self._normalize_entry(x, source_file="memory") for x in source if isinstance(x, dict)]

        all_records: List[Dict[str, Any]] = []
        if source:
            source_path = Path(source)
            if source_path.is_file():
                all_records.extend(self.parse_file(source_path))
            elif source_path.is_dir():
                for f in self.discover_log_files(source_path):
                    all_records.extend(self.parse_file(f))
        else:
            if include_database:
                all_records.extend(self.load_from_database())
            for f in self.discover_log_files():
                all_records.extend(self.parse_file(f))

        all_records.sort(key=lambda item: item.get("timestamp", ""))
        return all_records

    def _normalize_entry(self, raw: Dict[str, Any], source_file: str = "") -> Dict[str, Any]:
        """Привести сырую запись телеметрии к единому стандарту.

        Args:
            raw: Исходный словарь данных.
            source_file: Имя исходного файла.

        Returns:
            Dict[str, Any]: Нормализованная запись.
        """
        normalized = dict(raw)
        normalized.setdefault("source_file", source_file)
        ts = raw.get("timestamp") or raw.get("time") or raw.get("created_at") or raw.get("recorded_at")
        if not ts:
            ts = datetime.now(timezone.utc).isoformat()
        elif isinstance(ts, (int, float)):
            try:
                ts = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
            except Exception:
                ts = str(ts)
        else:
            ts = str(ts)
        normalized["timestamp"] = ts
        return normalized
