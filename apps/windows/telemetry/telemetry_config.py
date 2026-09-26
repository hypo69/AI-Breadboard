# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Telemetry Configuration Manager
# =============================================================================
# Description:
#   Управление конфигурацией сенсоров и агрегации телеметрии с поддержкой
#   режимов (minimal, hybrid, full) и персонализированных интервалов опроса.
#
# File: telemetry_config.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Менеджер конфигурации сбора телеметрии и сенсоров."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class TelemetryConfigManager:
    """Менеджер конфигурации для централизованного управления сенсорами."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        """Инициализирует менеджер конфигурации.

        Args:
            config_path: Путь к файлу конфигурации (по умолчанию: apps/windows/telemetry/config.json).
        """
        if config_path:
            self._config_path = config_path
        else:
            # Телеметрия должна использовать ТОЛЬКО свою собственную конфигурацию
            telemetry_cfg = Path(__file__).parent / "config.json"
            self._config_path = str(telemetry_cfg)

        self._config: Dict[str, Any] = {}
        self._sensors_config: Dict[str, Dict[str, Any]] = {}
        self._default_interval = 5.0
        self._heavy_interval = 60.0
        self._mode = "hybrid"

        self._load_config()

    def _load_config(self) -> None:
        """Загружает конфигурацию из JSON файла."""
        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                self._config = json.load(f)
                if "sensors" in self._config:
                    self._sensors_config = self._config.get("sensors", {})
                elif "telemetry" in self._config and "sensors" in self._config["telemetry"]:
                    self._sensors_config = self._config["telemetry"].get("sensors", {})
                else:
                    self._sensors_config = {}

                raw_interval = self._config.get(
                    "interval_seconds",
                    self._config.get("telemetry", {}).get("interval_seconds", 5.0),
                )
                self._default_interval = float(raw_interval) if raw_interval is not None else 5.0

                raw_heavy = self._config.get(
                    "heavy_interval_seconds",
                    self._config.get("telemetry", {}).get("heavy_interval_seconds", 60.0),
                )
                self._heavy_interval = float(raw_heavy) if raw_heavy is not None else 60.0

                self._mode = str(
                    self._config.get(
                        "mode",
                        self._config.get("telemetry", {}).get("mode", "hybrid"),
                    )
                ).lower()
        except FileNotFoundError:
            self._config = {}
            self._sensors_config = {}
            self._default_interval = 5.0
            self._heavy_interval = 60.0
            self._mode = "hybrid"
        except json.JSONDecodeError as e:
            raise ValueError(f"Ошибка парсинга {self._config_path}: {e}")

    @property
    def config_path(self) -> str:
        """Возвращает путь к активному файлу конфигурации."""
        return self._config_path

    def get_mode(self) -> str:
        """Возвращает режим сбора: minimal, hybrid, full."""
        return self._mode if self._mode in ("minimal", "hybrid", "full") else "hybrid"

    def get_interval_seconds(self) -> float:
        """Возвращает быстрый интервал сбора телеметрии."""
        return self._default_interval

    def get_heavy_interval_seconds(self) -> float:
        """Возвращает периодический интервал тяжелых сенсоров."""
        return self._heavy_interval

    def get_top_processes(self) -> int:
        """Возвращает число сохраняемых процессов с наибольшей нагрузкой."""
        return int(self._config.get("top_processes", 25))

    def get_process_mode(self) -> str:
        """Возвращает режим фильтрации процессов: 'top_n' или 'all'."""
        mode = str(self._config.get("process_mode", "top_n")).lower()
        return mode if mode in ("top_n", "all") else "top_n"

    def get_effective_process_limit(self) -> int:
        """Возвращает эффективное ограничение процессов (0 для Всех процессов)."""
        if self.get_process_mode() == "all":
            return 0
        limit = self.get_top_processes()
        return limit if limit > 0 else 0

    def is_low_priority(self) -> bool:
        """Возвращает флаг понижения приоритета процесса CPU."""
        return bool(self._config.get("low_priority", True))

    def get_heavy_collectors(self) -> Dict[str, bool]:
        """Возвращает словарь активности тяжелых коллекторов."""
        default_collectors = {
            "hardware_sensors": True,
            "storage_smart": True,
            "network_ping": True,
            "inventory_wmi": False,
        }
        custom = self._config.get("heavy_collectors", {})
        default_collectors.update(custom)
        return default_collectors

    def get_sensor_config(self, sensor_name: str) -> Dict[str, Any]:
        """Возвращает конфигурацию конкретного сенсора."""
        return self._sensors_config.get(sensor_name, {"enabled": False})

    def is_sensor_enabled(self, sensor_name: str) -> bool:
        """Проверяет, включен ли сенсор."""
        config = self.get_sensor_config(sensor_name)
        return config.get("enabled", False)

    def get_sensor_interval(self, sensor_name: str) -> float:
        """Возвращает интервал опроса сенсора."""
        config = self.get_sensor_config(sensor_name)
        return config.get("interval_seconds", self._default_interval)

    def get_sensor_metrics(self, sensor_name: str) -> List[str]:
        """Возвращает список метрик для сенсора."""
        config = self.get_sensor_config(sensor_name)
        return config.get("metrics", [])

    def get_all_sensor_names(self) -> List[str]:
        """Возвращает список всех имен сенсоров."""
        return list(self._sensors_config.keys())

    def get_enabled_sensors(self) -> List[str]:
        """Возвращает список включенных сенсоров."""
        return [name for name, config in self._sensors_config.items() if config.get("enabled", False)]

    def get_general_config(self) -> Dict[str, Any]:
        """Возвращает общую конфигурацию (без сенсоров)."""
        return {k: v for k, v in self._config.items() if k != "sensors"}

    def save_config(self, new_config: Optional[Dict[str, Any]] = None) -> bool:
        """Сохраняет текущую или переданную конфигурацию в файл.

        Args:
            new_config: Опциональный словарь новых параметров.

        Returns:
            bool: True при успешном сохранении.
        """
        if new_config:
            self._config.update(new_config)
            if "sensors" in new_config:
                self._sensors_config = new_config["sensors"]
            if "interval_seconds" in new_config:
                self._default_interval = float(new_config["interval_seconds"])
            if "heavy_interval_seconds" in new_config:
                self._heavy_interval = float(new_config["heavy_interval_seconds"])
            if "mode" in new_config:
                self._mode = str(new_config["mode"]).lower()

        try:
            target_path = Path(self._config_path)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    def reload(self) -> None:
        """Перезагружает конфигурацию из файла."""
        self._load_config()
