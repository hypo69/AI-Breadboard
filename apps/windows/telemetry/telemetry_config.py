# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry - Telemetry Config
# =============================================================================
# Description:
#   Менеджер конфигурации сбора телеметрии и сенсоров с поддержкой
#   динамического перечитывания config.json на лету.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.telemetry_config import TelemetryConfigManager
#
#     config_mgr = TelemetryConfigManager()
#     interval = config_mgr.get_interval_seconds()
#     if config_mgr.check_and_reload():
#         print("Конфигурация обновлена!")
#
# File: telemetry_config.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 07:28:00
# =============================================================================

from __future__ import annotations
"""Менеджер конфигурации сбора телеметрии и сенсоров."""

import json
import os
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional


def get_default_telemetry_config_path() -> Path:
    """Возвращает путь по умолчанию к файлу конфигурации телеметрии в %APPDATA%.

    Если целевой файл в %APPDATA%/AI-Breadboard/apps/windows/telemetry/config.json отсутствует,
    выполняется попытка скопировать шаблон из пакета модуля.

    Returns:
        Path: Путь к файлу конфигурации.
    """
    appdata = os.environ.get('APPDATA') or os.environ.get('LOCALAPPDATA')
    if appdata and os.path.exists(appdata):
        base_dir = Path(appdata)
    else:
        base_dir = Path.home() / '.config'
    target_path = base_dir / 'AI-Breadboard' / 'apps' / 'windows' / 'telemetry' / 'config.json'

    if not target_path.exists():
        bundled_template = Path(__file__).parent / 'config.json'
        if bundled_template.is_file():
            try:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(bundled_template, target_path)
            except Exception:
                return bundled_template
    return target_path


def parse_interval_to_seconds(val: Any, default: float = 5.0) -> float:
    """Преобразует строковое или числовое значение интервала в секунды (float).

    Поддерживает:
        - Числа (int, float): 5 -> 5.0, 0.5 -> 0.5
        - Строковые числа: "5", "5.0" -> 5.0
        - Строки с единицами времени:
            - Секунды: "5s", "5 seconds", "5 сек", "5 секунд" -> 5.0
            - Минуты: "1m", "1 minute", "5 minutes", "2 мин" -> 60.0 / 300.0 / 120.0
            - Часы: "1h", "1 hour", "6 hours", "1 час" -> 3600.0 / 21600.0
            - Дни: "1d", "1 day", "7 days", "1 день" -> 86400.0 / 604800.0

    Args:
        val: Значение интервала из конфигурации.
        default: Значение по умолчанию в секундах.

    Returns:
        float: Интервал в секундах (минимум 0.001 при валидном положительном значении).
    """
    if val is None:
        return float(default)
    if isinstance(val, (int, float)):
        return max(0.001, float(val))
    if isinstance(val, str):
        val_str = val.strip().lower()
        if not val_str:
            return float(default)
        try:
            return max(0.001, float(val_str))
        except ValueError:
            pass
        match = re.match(r"^([\d.]+)\s*([a-zа-я]+)?$", val_str)
        if match:
            try:
                num = float(match.group(1))
                unit = match.group(2) or "s"
                if unit in ("s", "sec", "second", "seconds", "сек", "секунд", "секунды", "секунда"):
                    return max(0.001, num)
                elif unit in ("m", "min", "minute", "minutes", "мин", "минут", "минуты", "минута"):
                    return max(0.001, num * 60.0)
                elif unit in ("h", "hr", "hour", "hours", "ч", "час", "часа", "часов"):
                    return max(0.001, num * 3600.0)
                elif unit in ("d", "day", "days", "д", "день", "дня", "дней"):
                    return max(0.001, num * 86400.0)
            except ValueError:
                pass
    return float(default)


class TelemetryConfigManager:
    """Менеджер конфигурации для централизованного управления сенсорами и интервалами."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        """Инициализирует менеджер конфигурации.

        Args:
            config_path: Путь к файлу конфигурации (по умолчанию: %APPDATA%/AI-Breadboard/apps/windows/telemetry/config.json).
        """
        if config_path:
            self._config_path = str(config_path)
        else:
            self._config_path = str(get_default_telemetry_config_path())
        self._config: Dict[str, Any] = {}
        self._sensors_config: Dict[str, Dict[str, Any]] = {}
        self._loggers_config: Dict[str, Dict[str, Any]] = {}
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
        self._flush_interval_seconds = 30.0
        self._auto_vacuum_enabled = True
        self._last_mtime_ns: int = 0
        self._load_config()

    def _load_config(self) -> None:
        """Загружает конфигурацию из JSON файла с фиксацией времени модификации."""
        try:
            cfg_path = Path(self._config_path)
            if cfg_path.is_file():
                self._last_mtime_ns = cfg_path.stat().st_mtime_ns
            with open(self._config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
                if 'sensors' in self._config:
                    self._sensors_config = self._config.get('sensors', {})
                elif 'telemetry' in self._config and 'sensors' in self._config['telemetry']:
                    self._sensors_config = self._config['telemetry'].get('sensors', {})
                else:
                    self._sensors_config = {}

                self._loggers_config = self._config.get('loggers', {})

                raw_interval = self._config.get('interval_seconds', self._config.get('interval', self._config.get('telemetry', {}).get('interval_seconds', 5.0)))
                self._default_interval = parse_interval_to_seconds(raw_interval, 5.0)

                raw_heavy = self._config.get('heavy_interval_seconds', self._config.get('heavy_interval', self._config.get('telemetry', {}).get('heavy_interval_seconds', 60.0)))
                self._heavy_interval = parse_interval_to_seconds(raw_heavy, 60.0)

                raw_disk_interval = self._config.get('heavy_disk_scan_interval_seconds')
                self._heavy_disk_scan_interval = parse_interval_to_seconds(raw_disk_interval, 43200.0)

                raw_fast_interval = self._config.get('fast_interval_seconds')
                self._fast_interval = parse_interval_to_seconds(raw_fast_interval, 30.0)

                self._fast_duration_days = int(self._config.get('fast_duration_days', 2))

                raw_agg = self._config.get('aggregation_interval_seconds', self._config.get('rollup_interval_seconds'))
                self._aggregation_interval = parse_interval_to_seconds(raw_agg, 3600.0)

                raw_max_days = self._config.get('heavy_mode_max_duration_days')
                self._heavy_mode_max_duration_days = float(raw_max_days) if raw_max_days is not None else 5.0

                self._heavy_mode_auto_switch_enabled = bool(self._config.get('heavy_mode_auto_switch_enabled', True))
                self._mode = str(self._config.get('mode', self._config.get('telemetry', {}).get('mode', 'hybrid'))).lower()

                raw_max_db = self._config.get('max_db_size_mb', self._config.get('max_file_size_mb', 50.0))
                self._max_db_size_mb = float(raw_max_db) if raw_max_db is not None else 50.0

                raw_retention = self._config.get('retention_days', 7)
                self._retention_days = int(raw_retention) if raw_retention is not None else 7

                raw_cleanup_interval = self._config.get('db_cleanup_interval_seconds')
                self._db_cleanup_interval_seconds = parse_interval_to_seconds(raw_cleanup_interval, 300.0)

                raw_flush_interval = self._config.get('flush_interval_seconds')
                self._flush_interval_seconds = parse_interval_to_seconds(raw_flush_interval, 30.0)

                self._auto_vacuum_enabled = bool(self._config.get('auto_vacuum_enabled', True))
        except FileNotFoundError:
            self._config = {}
            self._sensors_config = {}
            self._loggers_config = {}
            self._default_interval = 5.0
            self._heavy_interval = 60.0
            self._heavy_disk_scan_interval = 43200.0
            self._heavy_mode_max_duration_days = 5.0
            self._heavy_mode_auto_switch_enabled = True
            self._mode = 'hybrid'
            self._max_db_size_mb = 50.0
            self._retention_days = 7
            self._db_cleanup_interval_seconds = 300.0
            self._flush_interval_seconds = 30.0
            self._auto_vacuum_enabled = True
        except json.JSONDecodeError as e:
            raise ValueError(f'Ошибка парсинга {self._config_path}: {e}')

    @property
    def config_path(self) -> str:
        """Возвращает путь к активному файлу конфигурации."""
        return self._config_path

    def check_and_reload(self) -> bool:
        """Проверяет модификацию файла config.json на диске и перезагружает параметры 'на лету'.

        Returns:
            bool: True если конфигурация изменилась и успешно перезагружена, иначе False.
        """
        try:
            cfg_path = Path(self._config_path)
            if not cfg_path.is_file():
                return False
            current_mtime_ns = cfg_path.stat().st_mtime_ns
            if current_mtime_ns != self._last_mtime_ns:
                self._load_config()
                return True
        except Exception:
            pass
        return False

    def reload(self) -> None:
        """Принудительно перезагружает конфигурацию из файла."""
        self._load_config()

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
        """Возвращает быстрый базовый интервал сбора телеметрии."""
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
        return getattr(self, '_flush_interval_seconds', 30.0)

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
        return getattr(self, '_db_cleanup_interval_seconds', 300.0)

    def is_auto_vacuum_enabled(self) -> bool:
        """Возвращает флаг разрешения авто-вакуума (VACUUM) SQLite при усечении."""
        return bool(self._config.get('auto_vacuum_enabled', True))

    def get_sensor_config(self, sensor_name: str) -> Dict[str, Any]:
        """Возвращает конфигурацию конкретного сенсора."""
        return self._sensors_config.get(sensor_name, {'enabled': False})

    def is_sensor_enabled(self, sensor_name: str) -> bool:
        """Проверяет, включен ли сенсор."""
        config = self.get_sensor_config(sensor_name)
        return bool(config.get('enabled', False))

    def get_sensor_interval(self, sensor_name: str) -> float:
        """Возвращает интервал опроса сенсора в секундах."""
        config = self.get_sensor_config(sensor_name)
        raw = config.get('interval_seconds', config.get('interval', self._default_interval))
        return parse_interval_to_seconds(raw, self._default_interval)

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

    def get_logger_interval(self, logger_name: str, default: float = 60.0) -> float:
        """Возвращает интервал опроса логгера приложения в секундах."""
        logger_info = self._loggers_config.get(logger_name, {})
        if isinstance(logger_info, dict):
            raw = logger_info.get('interval', self._config.get('default_interval'))
            return parse_interval_to_seconds(raw, default)
        return float(default)

    def is_logger_enabled(self, logger_name: str, default: bool = True) -> bool:
        """Проверяет активность логгера приложения."""
        logger_info = self._loggers_config.get(logger_name, {})
        if isinstance(logger_info, dict):
            return bool(logger_info.get('enabled', default))
        return default

    def get_all_intervals(self) -> Dict[str, Any]:
        """Возвращает сводный словарь всех настроенных интервалов системы."""
        return {
            'default_interval_seconds': self.get_interval_seconds(),
            'heavy_interval_seconds': self.get_heavy_interval_seconds(),
            'fast_interval_seconds': self.get_fast_interval(),
            'aggregation_interval_seconds': self.get_aggregation_interval(),
            'heavy_disk_scan_interval_seconds': self.get_heavy_disk_scan_interval(),
            'db_cleanup_interval_seconds': self.get_db_cleanup_interval_seconds(),
            'flush_interval_seconds': self.get_flush_interval_seconds(),
            'sensors': {
                name: self.get_sensor_interval(name)
                for name in self.get_all_sensor_names()
            },
            'loggers': {
                name: self.get_logger_interval(name)
                for name in self._loggers_config.keys()
            }
        }

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

    def save_config(self, new_config: Optional[Dict[str, Any]] = None) -> bool:
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
            if 'loggers' in new_config:
                self._loggers_config = new_config['loggers']
            if 'interval_seconds' in new_config:
                self._default_interval = parse_interval_to_seconds(new_config['interval_seconds'], 5.0)
            if 'heavy_interval_seconds' in new_config:
                self._heavy_interval = parse_interval_to_seconds(new_config['heavy_interval_seconds'], 60.0)
            if 'heavy_disk_scan_interval_seconds' in new_config:
                self._heavy_disk_scan_interval = parse_interval_to_seconds(new_config['heavy_disk_scan_interval_seconds'], 43200.0)
            if 'fast_interval_seconds' in new_config:
                self._fast_interval = parse_interval_to_seconds(new_config['fast_interval_seconds'], 30.0)
            if 'aggregation_interval_seconds' in new_config:
                self._aggregation_interval = parse_interval_to_seconds(new_config['aggregation_interval_seconds'], 3600.0)
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
                self._db_cleanup_interval_seconds = parse_interval_to_seconds(new_config['db_cleanup_interval_seconds'], 300.0)
            if 'flush_interval_seconds' in new_config:
                self._flush_interval_seconds = parse_interval_to_seconds(new_config['flush_interval_seconds'], 30.0)
            if 'auto_vacuum_enabled' in new_config:
                self._auto_vacuum_enabled = bool(new_config['auto_vacuum_enabled'])
        try:
            target_path = Path(self._config_path)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            if target_path.is_file():
                self._last_mtime = target_path.stat().st_mtime
            return True
        except Exception:
            return False