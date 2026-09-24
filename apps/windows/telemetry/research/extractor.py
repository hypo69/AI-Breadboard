# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Telemetry Data Extractor and Log Loader
# =============================================================================
# Description:
#   Загрузчик и парсер разнородных логов телеметрии: сенсорных замеров,
#   событий устройств, архивов аудита и системных метрик.
#
# Examples:
#   >>> from apps.windows.telemetry.research.extractor import TelemetryDataExtractor
#   >>> extractor = TelemetryDataExtractor()
#   >>> records = extractor.load_from_directory("logs/telemetry")
#
# File: extractor.py
# Project: ai-breadboard
# Package: apps.windows.telemetry.research
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Загрузчик и парсер логов телеметрии из файлов и директорий."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Union

from logger import logger
from apps.windows.telemetry.storage import TelemetryStorage


class TelemetryDataExtractor:
    """Извлекатель и нормализатор данных из базы данных и файлов логов телеметрии."""

    def __init__(
        self,
        default_log_dirs: Optional[List[Union[str, Path]]] = None,
        storage: Optional[TelemetryStorage] = None,
    ) -> None:
        """Инициализация извлекателя логов.

        Args:
            default_log_dirs: Список базовых директорий для поиска логов по умолчанию.
            storage: Экземпляр хранилища SQLite базы данных.
        """
        self._storage = storage
        base_proj = Path(__file__).resolve().parent.parent.parent.parent.parent
        appdata = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))

        self.default_log_dirs = [Path(p) for p in default_log_dirs] if default_log_dirs else [
            base_proj / "logs" / "telemetry",
            Path(appdata) / "AI-Breadboard" / "apps" / "logs",
            Path(appdata) / "AI-Breadboard" / "apps" / "windows" / "telemetry" / "logs",
            base_proj / "data" / "telemetry" / "hardware_archives",
        ]

    @property
    def storage(self) -> TelemetryStorage:
        """Получить экземпляр SQLite хранилища телеметрии."""
        if self._storage is None:
            self._storage = TelemetryStorage.get_instance()
        return self._storage

    def discover_log_files(self, search_dir: Optional[Union[str, Path]] = None) -> List[Path]:
        """Обнаружить все доступные файлы логов телеметрии.

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
            for pattern in ("*.json", "*.jsonl", "*.log", "*.csv"):
                try:
                    for file_path in d.glob(pattern):
                        if file_path.is_file() and file_path.stat().st_size > 0:
                            found_files.append(file_path)
                except Exception as ex:
                    logger.warning(f"Ошибка сканирования директории {d} по шаблону {pattern}: {ex}")

        # Удаляем дубликаты сохраняя порядок
        seen = set()
        unique_files = []
        for f in found_files:
            resolved = str(f.resolve())
            if resolved not in seen:
                seen.add(resolved)
                unique_files.append(f)

        return unique_files

    def parse_file(self, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """Распарсить конкретный файл логов телеметрии.

        Args:
            file_path: Путь к файлу лога (.json, .jsonl, .csv).

        Returns:
            List[Dict[str, Any]]: Список нормализованных записей с метками времени.
        """
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            logger.warning(f"Файл логов не найден: {path}")
            return []

        entries: List[Dict[str, Any]] = []
        try:
            suffix = path.suffix.lower()
            if suffix == ".jsonl" or suffix == ".log":
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
                            # Проверяем, это одиночный срез или обертка над списком
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
                        # Попробуем прочитать построчно если файл jsonl со расширением .json
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

    def load_from_database(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Загрузить исторические записи телеметрии напрямую из базы данных SQLite.

        Args:
            limit: Максимальное число извлекаемых записей.

        Returns:
            List[Dict[str, Any]]: Список нормализованных записей из БД.
        """
        records: List[Dict[str, Any]] = []
        try:
            snapshots = self.storage.get_snapshots(limit=limit)
            for snap in snapshots:
                rec = dict(snap)
                rec["source_file"] = "sqlite:system_snapshots"
                records.append(self._normalize_entry(rec, source_file="sqlite:system_snapshots"))

            sensor_polls = self.storage.get_sensor_history(limit=limit)
            for s in sensor_polls:
                rec = dict(s)
                rec["source_file"] = "sqlite:sensor_polls"
                records.append(self._normalize_entry(rec, source_file="sqlite:sensor_polls"))

            events = self.storage.get_events(limit=limit)
            for ev in events:
                rec = dict(ev)
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

        # Сортируем записи по временной метке
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

        # Нормализация временной метки
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
