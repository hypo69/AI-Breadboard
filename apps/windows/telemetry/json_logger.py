# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Telemetry JSON Stream Logger
# =============================================================================
# Description:
#   Потоковый логгер телеметрии сенсоров с сохранением постоянных датчиков
#   и добавлением только измененных значений в массив `values` с меткой времени.
#   Автоматическая ротация файлов при достижении 50 МБ.
#
# File: json_logger.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Потоковый логгер телеметрии сенсоров с инкрементацией измененных значений и ротацией."""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    from src.logger.logger import logger
except ImportError:
    from logger import logger


class TelemetryJsonLogger:
    """Логгер телеметрии в JSON формате с сохранением структуры датчиков и инкрементом values."""

    def __init__(
        self,
        log_dir: str,
        filename: str = "ai_sensors_polls.json",
        max_file_size_mb: float = 50.0,
    ) -> None:
        """Инициализирует логгер телеметрии.

        Args:
            log_dir: Директория для хранения логов.
            filename: Имя файла лога.
            max_file_size_mb: Максимальный размер файла в МБ перед ротацией (по умолчанию 50 МБ).
        """
        self.log_dir = Path(log_dir)
        self.filename = filename
        self.max_file_size_bytes = int(max_file_size_mb * 1024 * 1024)

        self._lock = threading.Lock()
        self._current_file_size = 0
        self._sensors_registry: Dict[Any, Dict[str, Any]] = {}
        self._last_sensor_values: Dict[Any, float] = {}
        self._last_measurement: Optional[Dict[str, Any]] = None

        # Создаем директорию если она не существует
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._load_existing_sensors()

    def _get_log_file_path(self) -> Path:
        """Возвращает путь к текущему лог-файлу.

        Returns:
            Path: Путь к лог-файлу.
        """
        return self.log_dir / self.filename

    def _load_existing_sensors(self) -> None:
        """Загружает существующие сенсоры и последние значения из файла при инициализации."""
        current_path = self._get_log_file_path()
        if not current_path.exists() or current_path.stat().st_size == 0:
            return

        try:
            with open(current_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                items = []
                if isinstance(data, list):
                    items = data
                elif isinstance(data, dict) and "sensors" in data and isinstance(data["sensors"], list):
                    items = data["sensors"]

                for item in items:
                    if isinstance(item, dict) and "id" in item:
                        sid = item["id"]
                        self._sensors_registry[sid] = item
                        values_list = item.get("values", [])
                        if values_list and isinstance(values_list, list):
                            last_val = values_list[-1]
                            if isinstance(last_val, dict) and "num" in last_val:
                                self._last_sensor_values[sid] = last_val["num"]
        except Exception as e:
            logger.warning(f"Не удалось загрузить существующий лог-файл: {e}")

    def _rotate_file(self) -> None:
        """Ротирует текущий лог-файл с сохранением метки времени (timestamp)."""
        current_path = self._get_log_file_path()
        if not current_path.exists():
            return

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        stem = self.filename.rsplit(".", 1)[0]
        ext = self.filename.rsplit(".", 1)[1] if "." in self.filename else "json"
        rotated_name = f"{stem}_{timestamp}.{ext}"
        rotated_path = self.log_dir / rotated_name

        try:
            current_path.rename(rotated_path)
            logger.info(f"Лог-файл телеметрии ротирован (>= 50MB): {rotated_path}")
            self._current_file_size = 0
            # Очищаем массивы values у зарегистрированных сенсоров для нового файла
            for sensor_data in self._sensors_registry.values():
                sensor_data["values"] = []
            self._last_sensor_values.clear()
        except Exception as e:
            logger.error(f"Ошибка ротации лог-файла: {e}")

    def _check_and_rotate(self) -> None:
        """Проверяет размер файла и ротирует если достигнут лимит."""
        current_path = self._get_log_file_path()
        if current_path.exists():
            try:
                self._current_file_size = current_path.stat().st_size
            except OSError:
                self._current_file_size = 0

        if self._current_file_size >= self.max_file_size_bytes:
            self._rotate_file()

    def record_sensors(
        self,
        sensor_items: List[Dict[str, Any]],
        timestamp: Optional[str] = None,
        only_changed: bool = True,
    ) -> bool:
        """Регистрирует сенсоры и инкрементирует измененные значения в массив `values`.

        Args:
            sensor_items: Список показаний датчиков с полями id, hardware_name,
                          hardware_type, sensor_category, sensor_name, unit, value.
            timestamp: Временная метка ISO формата.
            only_changed: Если True, добавляет замер только при изменении значения.

        Returns:
            bool: True если данные успешно обновлены/записаны.
        """
        now_ts = timestamp or datetime.now(timezone.utc).isoformat()

        with self._lock:
            self._check_and_rotate()
            current_path = self._get_log_file_path()
            has_updates = False

            for item in sensor_items:
                sensor_id = item.get("id")
                hw_name = item.get("hardware_name", "System")
                hw_type = item.get("hardware_type", "cpu")
                category = item.get("sensor_category", "General")
                s_name = item.get("sensor_name", "Unknown")
                unit = item.get("unit", "")
                val_raw = item.get("value", item.get("value_num", 0.0))

                try:
                    num_val = round(float(val_raw), 2)
                except (ValueError, TypeError):
                    num_val = 0.0

                key = sensor_id if sensor_id is not None else f"{hw_name}_{category}_{s_name}"

                if key not in self._sensors_registry:
                    # Создаем запись сенсора один раз с начальным значением
                    self._sensors_registry[key] = {
                        "id": key,
                        "hardware_name": hw_name,
                        "hardware_type": hw_type,
                        "sensor_category": category,
                        "sensor_name": s_name,
                        "unit": unit,
                        "values": [
                            {"num": num_val, "time": now_ts}
                        ],
                    }
                    self._last_sensor_values[key] = num_val
                    has_updates = True
                else:
                    # Сенсор уже существует: проверяем изменилось ли значение
                    prev_val = self._last_sensor_values.get(key)
                    if not only_changed or prev_val is None or prev_val != num_val:
                        self._sensors_registry[key]["values"].append({
                            "num": num_val,
                            "time": now_ts,
                        })
                        self._last_sensor_values[key] = num_val
                        has_updates = True

            if not has_updates and current_path.exists():
                return True

            try:
                payload = list(self._sensors_registry.values())
                content = json.dumps(payload, ensure_ascii=False, indent=2)

                # Атомарная запись через временный файл
                tmp_path = current_path.with_suffix(".tmp")
                with open(tmp_path, "w", encoding="utf-8") as f:
                    f.write(content)
                tmp_path.replace(current_path)

                self._current_file_size = current_path.stat().st_size
                self._last_measurement = {"timestamp": now_ts, "sensors_count": len(payload)}
                return True

            except Exception as e:
                logger.error(f"Ошибка записи структурированных сенсоров: {e}")
                return False

    def log(self, data: Any) -> bool:
        """Совместимый метод логирования."""
        if isinstance(data, list):
            return self.record_sensors(data)
        elif isinstance(data, dict) and "sensors" in data and isinstance(data["sensors"], list):
            return self.record_sensors(data["sensors"], timestamp=data.get("timestamp"))
        elif isinstance(data, dict) and "hardware" in data and "sensors" in data["hardware"]:
            return self.record_sensors(data["hardware"]["sensors"], timestamp=data.get("timestamp"))
        else:
            with self._lock:
                self._check_and_rotate()
                current_path = self._get_log_file_path()
                try:
                    line = json.dumps(data, ensure_ascii=False, default=str) + "\n"
                    with open(current_path, "a", encoding="utf-8") as f:
                        f.write(line)
                    self._current_file_size += len(line.encode("utf-8"))
                    self._last_measurement = data
                    return True
                except Exception as e:
                    logger.error(f"Ошибка записи в лог: {e}")
                    return False

    def log_batch(self, measurements: List[Dict[str, Any]]) -> int:
        """Записывает пачку измерений в JSON файл."""
        written = 0
        for m in measurements:
            if self.log(m):
                written += 1
        return written

    def get_last_measurement(self) -> Optional[Dict[str, Any]]:
        """Возвращает последнюю записанную телеметрию."""
        return self._last_measurement

    def get_sensors_registry(self) -> List[Dict[str, Any]]:
        """Возвращает текущий список зарегистрированных сенсоров с инкрементированными значениями."""
        with self._lock:
            return list(self._sensors_registry.values())

    def get_log_file_size(self) -> int:
        """Возвращает текущий размер лог-файла в байтах."""
        current_path = self._get_log_file_path()
        if current_path.exists():
            try:
                return current_path.stat().st_size
            except OSError:
                return 0
        return 0

    def get_log_file_path(self) -> Path:
        """Возвращает путь к текущему лог-файлу."""
        return self._get_log_file_path()
