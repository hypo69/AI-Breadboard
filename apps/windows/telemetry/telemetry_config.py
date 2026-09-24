# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Telemetry Configuration Manager
# =============================================================================
# Description:
#   Управление конфигурацией сенсоров и агрегации телеметрии с поддержкой
#   персонализированных интервалов опроса.
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
            config_path: Путь к файлу config.json (по умолчанию: apps/windows/config.json).
        """
        if config_path:
            self._config_path = config_path
        else:
            windows_root_cfg = Path(__file__).parent.parent / "config.json"
            telemetry_cfg = Path(__file__).parent / "config.json"
            if windows_root_cfg.exists():
                self._config_path = str(windows_root_cfg)
            else:
                self._config_path = str(telemetry_cfg)

        self._config: Dict[str, Any] = {}
        self._sensors_config: Dict[str, Dict[str, Any]] = {}
        self._default_interval = 5.0

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
        except FileNotFoundError:
            self._config = {}
            self._sensors_config = {}
            self._default_interval = 5.0
        except json.JSONDecodeError as e:
            raise ValueError(f"Ошибка парсинга config.json: {e}")

    def get_sensor_config(self, sensor_name: str) -> Dict[str, Any]:
        """Возвращает конфигурацию конкретного сенсора.

        Args:
            sensor_name: Имя сенсора (cpu, gpu, ram, disk, network, sensors, internet).

        Returns:
            Dict[str, Any]: Конфигурация сенсора (enabled, interval_seconds, metrics).
        """
        return self._sensors_config.get(sensor_name, {"enabled": False})

    def is_sensor_enabled(self, sensor_name: str) -> bool:
        """Проверяет, включен ли сенсор.

        Args:
            sensor_name: Имя сенсора.

        Returns:
            bool: True если сенсор включен.
        """
        config = self.get_sensor_config(sensor_name)
        return config.get("enabled", False)

    def get_sensor_interval(self, sensor_name: str) -> float:
        """Возвращает интервал опроса сенсора.

        Args:
            sensor_name: Имя сенсора.

        Returns:
            float: Интервал в секундах.
        """
        config = self.get_sensor_config(sensor_name)
        return config.get("interval_seconds", self._default_interval)

    def get_sensor_metrics(self, sensor_name: str) -> List[str]:
        """Возвращает список метрик для сенсора.

        Args:
            sensor_name: Имя сенсора.

        Returns:
            List[str]: Список имен метрик.
        """
        config = self.get_sensor_config(sensor_name)
        return config.get("metrics", [])

    def get_all_sensor_names(self) -> List[str]:
        """Возвращает список всех имен сенсоров.

        Returns:
            List[str]: Список имен сенсоров.
        """
        return list(self._sensors_config.keys())

    def get_enabled_sensors(self) -> List[str]:
        """Возвращает список включенных сенсоров.

        Returns:
            List[str]: Список имен включенных сенсоров.
        """
        return [name for name, config in self._sensors_config.items() if config.get("enabled", False)]

    def get_general_config(self) -> Dict[str, Any]:
        """Возвращает общую конфигурацию (без сенсоров).

        Returns:
            Dict[str, Any]: Общая конфигурация.
        """
        return {k: v for k, v in self._config.items() if k != "sensors"}

    def reload(self) -> None:
        """Перезагружает конфигурацию из файла."""
        self._load_config()
