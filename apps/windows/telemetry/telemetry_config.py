# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry - Telemetry Config
# =============================================================================
# Description:
#   Менеджер конфигурации сбора телеметрии и сенсоров.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.telemetry_config import TelemetryConfigManager
#
#     service = TelemetryConfigManager()
#
# File: telemetry_config.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Менеджер конфигурации сбора телеметрии и сенсоров."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

class TelemetryConfigManager:
    """Менеджер конфигурации для централизованного управления сенсорами."""

    def __init__(self, config_path: Optional[str]=None) -> None:
        """Инициализирует менеджер конфигурации.

        Args:
            config_path: Путь к файлу конфигурации (по умолчанию: apps/windows/telemetry/config.json).
        """
        if config_path:
            self._config_path = config_path
        else:
            telemetry_cfg = Path(__file__).parent / 'config.json'
            self._config_path = str(telemetry_cfg)
        self._config: Dict[str, Any] = {}
        self._sensors_config: Dict[str, Dict[str, Any]] = {}
        self._default_interval = 5.0
        self._fast_interval = 30.0
        self._fast_duration_days = 2
        self._aggregation_interval = 3600.0
        self._heavy_interval = 60.0
        self._heavy_disk_scan_interval = 43200.0
        self._heavy_mode_max_duration_days = 5.0
        self._heavy_mode_auto_switch_enabled = True
        self._mode = 'hybrid'
        self._max_db_size_mb = 50.0
        self._retention_days = 7
        self._db_cleanup_interval_seconds = 300.0
        self._auto_vacuum_enabled = True
        self._load_config()

    def _load_config(self) -> None:
        """Загружает конфигурацию из JSON файла."""
        try:
            with open(self._config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
                if 'sensors' in self._config:
                    self._sensors_config = self._config.get('sensors', {})
                elif 'telemetry' in self._config and 'sensors' in self._config['telemetry']:
                    self._sensors_config = self._config['telemetry'].get('sensors', {})
                else:
                    self._sensors_config = {}
                raw_interval = self._config.get('interval_seconds', self._config.get('telemetry', {}).get('interval_seconds', 5.0))
                self._default_interval = float(raw_interval) if raw_interval is not None else 5.0
                raw_heavy = self._config.get('heavy_interval_seconds', self._config.get('telemetry', {}).get('heavy_interval_seconds', 60.0))
                self._heavy_interval = float(raw_heavy) if raw_heavy is not None else 60.0
                raw_disk_interval = self._config.get('heavy_disk_scan_interval_seconds')
                self._heavy_disk_scan_interval = float(raw_disk_interval) if raw_disk_interval is not None else 43200.0
                raw_max_days = self._config.get('heavy_mode_max_duration_days')
                self._heavy_mode_max_duration_days = float(raw_max_days) if raw_max_days is not None else 5.0
                self._heavy_mode_auto_switch_enabled = bool(self._config.get('heavy_mode_auto_switch_enabled', True))
                self._mode = str(self._config.get('mode', self._config.get('telemetry', {}).get('mode', 'hybrid'))).lower()
                
                raw_max_db = self._config.get('max_db_size_mb', self._config.get('max_file_size_mb', 50.0))
                self._max_db_size_mb = float(raw_max_db) if raw_max_db is not None else 50.0
                raw_retention = self._config.get('retention_days', 7)
                self._retention_days = int(raw_retention) if raw_retention is not None else 7
                raw_cleanup_interval = self._config.get('db_cleanup_interval_seconds', 300.0)
                self._db_cleanup_interval_seconds = float(raw_cleanup_interval) if raw_cleanup_interval is not None else 300.0
                self._auto_vacuum_enabled = bool(self._config.get('auto_vacuum_enabled', True))
        except FileNotFoundError:
            self._config = {}
            self._sensors_config = {}
            self._default_interval = 5.0
            self._heavy_interval = 60.0
            self._heavy_disk_scan_interval = 43200.0
            self._heavy_mode_max_duration_days = 5.0
            self._heavy_mode_auto_switch_enabled = True
            self._mode = 'hybrid'
            self._max_db_size_mb = 50.0
            self._retention_days = 7
            self._db_cleanup_interval_seconds = 300.0
            self._auto_vacuum_enabled = True
        except json.JSONDecodeError as e:
            raise ValueError(f'Ошибка парсинга {self._config_path}: {e}')

    @property
    def config_path(self) -> str:
        """Возвращает путь к активному файлу конфигурации."""
        return self._config_path

    def get_fast_interval(self) -> float:
        """Возвращает интервал быстрого режима (сек)."""
        return getattr(self, '_fast_interval', 30.0)

    def get_fast_duration_days(self) -> int:
        """Возвращает длительность быстрого режима в днях."""
        return getattr(self, '_fast_duration_days', 2)

    def get_aggregation_interval(self) -> float:
        """Возвращает интервал агрегации (сек)."""
        return getattr(self, '_aggregation_interval', 3600.0)

    def get_mode(self) -> str:
        """Возвращает режим сбора: minimal, hybrid, full."""
        return self._mode if self._mode in ('minimal', 'hybrid', 'full') else 'hybrid'

    def get_interval_seconds(self) -> float:
        """Возвращает быстрый интервал сбора телеметрии."""
        return self._default_interval

    def get_heavy_interval_seconds(self) -> float:
        """Возвращает периодический интервал тяжелых сенсоров."""
        return self._heavy_interval

    def get_heavy_disk_scan_interval(self) -> float:
        """Возвращает интервал тяжелой проверки дисков (в секундах)."""
        return getattr(self, '_heavy_disk_scan_interval', 43200.0)

    def get_heavy_mode_max_duration_days(self) -> float:
        """Возвращает максимальную непрерывную длительность тяжелого режима (в днях)."""
        return getattr(self, '_heavy_mode_max_duration_days', 5.0)

    def is_heavy_auto_switch_enabled(self) -> bool:
        """Возвращает флаг разрешения автопереключения тяжелого режима в легкий."""
        return getattr(self, '_heavy_mode_auto_switch_enabled', True)

    def get_top_processes(self) -> int:
        """Возвращает число сохраняемых процессов с наибольшей нагрузкой."""
        return int(self._config.get('top_processes', 25))

    def get_buffer_mode(self) -> str:
        """Возвращает режим буферизации телеметрии ('memory', 'file', 'direct')."""
        mode = str(self._config.get('buffer_mode', 'memory')).lower()
        return mode if mode in ('memory', 'file', 'direct') else 'memory'

    def get_buffer_size(self) -> int:
        """Возвращает максимальный размер буфера перед принудительным сбросом в БД."""
        try:
            val = int(self._config.get('buffer_size', 50))
            return max(1, val)
        except (ValueError, TypeError):
            return 50

    def get_flush_interval_seconds(self) -> float:
        """Возвращает периодический интервал сброса буфера в БД (в секундах)."""
        try:
            val = float(self._config.get('flush_interval_seconds', 30.0))
            return max(1.0, val)
        except (ValueError, TypeError):
            return 30.0

    def get_buffer_file(self) -> str:
        """Возвращает имя файла для буферизации в аварийном режиме сбоев."""
        return str(self._config.get('buffer_file', 'telemetry_buffer.jsonl'))

    def get_process_mode(self) -> str:
        """Возвращает режим фильтрации процессов: 'top_n' или 'all'."""
        mode = str(self._config.get('process_mode', 'top_n')).lower()
        return mode if mode in ('top_n', 'all') else 'top_n'

    def get_effective_process_limit(self) -> int:
        """Возвращает эффективное ограничение процессов (0 для Всех процессов)."""
        if self.get_process_mode() == 'all':
            return 0
        limit = self.get_top_processes()
        return limit if limit > 0 else 0

    def is_low_priority(self) -> bool:
        """Возвращает флаг понижения приоритета процесса CPU."""
        return bool(self._config.get('low_priority', True))

    def get_heavy_collectors(self) -> Dict[str, bool]:
        """Возвращает словарь активности тяжелых коллекторов."""
        default_collectors = {'hardware_sensors': True, 'storage_smart': True, 'network_ping': True, 'inventory_wmi': False}
        custom = self._config.get('heavy_collectors', {})
        default_collectors.update(custom)
        return default_collectors

    def get_max_db_size_mb(self) -> float:
        """Возвращает максимальный разрешенный размер SQLite базы данных (в МБ)."""
        try:
            val = float(self._config.get('max_db_size_mb', self._config.get('max_file_size_mb', 50.0)))
            return max(1.0, val)
        except (ValueError, TypeError):
            return 50.0

    def get_retention_days(self) -> int:
        """Возвращает срок хранения сырых записей телеметрии (в днях)."""
        try:
            val = int(self._config.get('retention_days', 7))
            return max(1, val)
        except (ValueError, TypeError):
            return 7

    def get_db_cleanup_interval_seconds(self) -> float:
        """Возвращает интервал периодической проверки и очистки БД (в секундах)."""
        try:
            val = float(self._config.get('db_cleanup_interval_seconds', 300.0))
            return max(10.0, val)
        except (ValueError, TypeError):
            return 300.0

    def is_auto_vacuum_enabled(self) -> bool:
        """Возвращает флаг разрешения авто-вакуума (VACUUM) SQLite при усечении."""
        return bool(self._config.get('auto_vacuum_enabled', True))

    def get_sensor_config(self, sensor_name: str) -> Dict[str, Any]:
        """Возвращает конфигурацию конкретного сенсора."""
        return self._sensors_config.get(sensor_name, {'enabled': False})

    def is_sensor_enabled(self, sensor_name: str) -> bool:
        """Проверяет, включен ли сенсор."""
        config = self.get_sensor_config(sensor_name)
        return config.get('enabled', False)

    def get_sensor_interval(self, sensor_name: str) -> float:
        """Возвращает интервал опроса сенсора."""
        config = self.get_sensor_config(sensor_name)
        return config.get('interval_seconds', self._default_interval)

    def get_sensor_metrics(self, sensor_name: str) -> List[str]:
        """Возвращает список метрик для сенсора."""
        config = self.get_sensor_config(sensor_name)
        return config.get('metrics', [])

    def get_all_sensor_names(self) -> List[str]:
        """Возвращает список всех имен сенсоров."""
        return list(self._sensors_config.keys())

    def get_enabled_sensors(self) -> List[str]:
        """Возвращает список включенных сенсоров."""
        return [name for name, config in self._sensors_config.items() if config.get('enabled', False)]

    def get_general_config(self) -> Dict[str, Any]:
        """Возвращает общую конфигурацию (без сенсоров)."""
        return {k: v for k, v in self._config.items() if k != 'sensors'}

    def get_config(self) -> Dict[str, Any]:
        """Возвращает полную конфигурацию телеметрии."""
        return self._config.copy()

    @property
    def config(self) -> Dict[str, Any]:
        """Свойство для получения полной конфигурации."""
        return self.get_config()


    def save_config(self, new_config: Optional[Dict[str, Any]]=None) -> bool:
        """Сохраняет текущую или переданную конфигурацию в файл.

        Args:
            new_config: Опциональный словарь новых параметров.

        Returns:
            bool: True при успешном сохранении.
        """
        if new_config:
            self._config.update(new_config)
            if 'sensors' in new_config:
                self._sensors_config = new_config['sensors']
            if 'interval_seconds' in new_config:
                self._default_interval = float(new_config['interval_seconds'])
            if 'heavy_interval_seconds' in new_config:
                self._heavy_interval = float(new_config['heavy_interval_seconds'])
            if 'heavy_disk_scan_interval_seconds' in new_config:
                self._heavy_disk_scan_interval = float(new_config['heavy_disk_scan_interval_seconds'])
            if 'heavy_mode_max_duration_days' in new_config:
                self._heavy_mode_max_duration_days = float(new_config['heavy_mode_max_duration_days'])
            if 'heavy_mode_auto_switch_enabled' in new_config:
                self._heavy_mode_auto_switch_enabled = bool(new_config['heavy_mode_auto_switch_enabled'])
            if 'mode' in new_config:
                self._mode = str(new_config['mode']).lower()
            if 'max_db_size_mb' in new_config:
                self._max_db_size_mb = float(new_config['max_db_size_mb'])
            if 'retention_days' in new_config:
                self._retention_days = int(new_config['retention_days'])
            if 'db_cleanup_interval_seconds' in new_config:
                self._db_cleanup_interval_seconds = float(new_config['db_cleanup_interval_seconds'])
            if 'auto_vacuum_enabled' in new_config:
                self._auto_vacuum_enabled = bool(new_config['auto_vacuum_enabled'])
        try:
            target_path = Path(self._config_path)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    def reload(self) -> None:
        """Перезагружает конфигурацию из файла."""
        self._load_config()