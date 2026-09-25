# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Apps Unified Telemetry & Logging System (SQLite Primary + On-Demand CSV)
# =============================================================================
# Description:
#   Централизованный модуль телеметрии и логирования для приложений AI-Breadboard.
#   Использует базу данных SQLite (telemetry.db) как Single Source of Truth.
#   Прямая запись в CSV по умолчанию отключена (enable_csv_mirroring=False)
#   для экономии ресурсов накопителя и CPU. Выгрузка CSV осуществляется On-Demand.
#   Поддерживает опциональную пакетную буферизацию в памяти (In-Memory Batching).
#
# Examples:
#   >>> from apps.common.csv_logger import AppCsvLogger, log_poll, export_to_csv
#   >>> logger = AppCsvLogger("cloudflared_monitor")
#   >>> logger.log_poll(poll_type="ping", metric_name="latency", value=15.2, unit="ms")
#   >>> export_to_csv(app="cloudflared_monitor")
#
# File: csv_logger.py
# Project: ai-breadboard
# Package: apps.common
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модуль централизованного логирования приложений и телеметрии в SQLite с On-Demand CSV."""

from __future__ import annotations

import csv
import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from logger import logger

_LOCK = threading.Lock()
_LOG_DIR_OVERRIDE: Optional[Path] = None

# Флаг зеркалирования в CSV (по умолчанию False — Single Source of Truth в SQLite)
_ENV_MIRROR = (
    os.environ.get("AI_BREADBOARD_ENABLE_MIRRORING_LOGS_TO_CSV")
    or os.environ.get("AI_BREADBOARD_ENABLE_CSV_MIRRORING", "0")
).lower() in ("1", "true", "yes")
_ENABLE_MIRRORING_LOGS_TO_CSV: bool = _ENV_MIRROR

# Флаг пакетной буферизации в памяти (по умолчанию False)
_ENV_BATCH = (
    os.environ.get("AI_BREADBOARD_ENABLE_MEMORY_BATCHING")
    or os.environ.get("AI_BREADBOARD_ENABLE_BATCHING", "0")
).lower() in ("1", "true", "yes")
_ENABLE_MEMORY_BATCHING: bool = _ENV_BATCH


def is_mirroring_logs_to_csv_enabled() -> bool:
    """Проверяет, включено ли синхронное дублирование в CSV-файлы.

    Returns:
        bool: True если зеркалирование логов в CSV включено, иначе False.
    """
    global _ENABLE_MIRRORING_LOGS_TO_CSV
    return _ENABLE_MIRRORING_LOGS_TO_CSV


# Алиас для обратной совместимости
is_csv_mirroring_enabled = is_mirroring_logs_to_csv_enabled


def set_mirroring_logs_to_csv(enabled: bool) -> None:
    """Устанавливает режим синхронного дублирования логов в CSV-файлы.

    Args:
        enabled: True для включения синхронной записи CSV, False для только SQLite.
    """
    global _ENABLE_MIRRORING_LOGS_TO_CSV
    _ENABLE_MIRRORING_LOGS_TO_CSV = enabled
    logger.debug(f"Режим зеркалирования логов в CSV изменен: {enabled}")


# Алиас для обратной совместимости
set_csv_mirroring = set_mirroring_logs_to_csv


def is_memory_batching_enabled() -> bool:
    """Проверяет, включена ли пакетная буферизация в памяти.

    Returns:
        bool: True если буферизация включена, иначе False.
    """
    global _ENABLE_MEMORY_BATCHING
    return _ENABLE_MEMORY_BATCHING


def set_memory_batching(enabled: bool) -> None:
    """Включает или выключает пакетную буферизацию записей в памяти.

    Args:
        enabled: True для включения буферизации, False для прямой немедленной записи.
    """
    global _ENABLE_MEMORY_BATCHING
    _ENABLE_MEMORY_BATCHING = enabled
    if not enabled:
        flush_batch_buffer()
    logger.debug(f"Режим пакетной буферизации изменен: {enabled}")


def get_apps_log_dir() -> Path:
    """Возвращает и создает целевой каталог для логов приложений и телеметрии.

    Приоритет разрешения пути:
    1. Переопределение через set_apps_log_dir_override (для тестов).
    2. Переменные окружения AI_BREADBOARD_LOGS_DIR / TELEMETRY_LOGS_DIR.
    3. Параметр storage.telemetry_logs_dir / storage.logs_dir из root config.json.
    4. Стандартный каталог %APPDATA%/AI-Breadboard/apps/windows/telemetry/logs.

    Returns:
        Path: Абсолютный путь к директории логов приложений.
    """
    global _LOG_DIR_OVERRIDE
    if _LOG_DIR_OVERRIDE is not None:
        _LOG_DIR_OVERRIDE.mkdir(parents=True, exist_ok=True)
        return _LOG_DIR_OVERRIDE

    # 1. Проверка переменных окружения
    env_dir = os.environ.get("AI_BREADBOARD_LOGS_DIR") or os.environ.get("TELEMETRY_LOGS_DIR")
    if env_dir:
        p = Path(env_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    # 2. Проверка центрального config.json
    try:
        root_dir = Path(__file__).resolve().parent.parent.parent
        cfg_file = root_dir / "config.json"
        if cfg_file.exists():
            with open(cfg_file, "r", encoding="utf-8") as f:
                cfg_data = json.load(f)
                storage_cfg = cfg_data.get("storage", {})
                custom_logs = storage_cfg.get("telemetry_logs_dir") or storage_cfg.get("logs_dir")
                if custom_logs:
                    p = Path(custom_logs)
                    if not p.is_absolute():
                        p = root_dir / p
                    p.mkdir(parents=True, exist_ok=True)
                    return p
    except Exception:
        pass

    # 3. Стандартный системный путь %APPDATA%
    appdata = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
    if appdata and os.path.exists(appdata):
        base_dir = Path(appdata)
    else:
        base_dir = Path.home() / ".config"

    log_dir = base_dir / "AI-Breadboard" / "apps" / "windows" / "telemetry" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def set_apps_log_dir_override(path: Optional[Path]) -> None:
    """Устанавливает переопределение каталога логов (для изоляции в тестах).

    Args:
        path: Пользовательский путь или None для сброса.
    """
    global _LOG_DIR_OVERRIDE
    _LOG_DIR_OVERRIDE = path


# Алиас для удобства тестирования
set_log_dir_override = set_apps_log_dir_override


def _format_cell(val: Any) -> str:
    """Форматирует произвольное значение для ячейки CSV."""
    if val is None:
        return ""
    if isinstance(val, (dict, list)):
        try:
            return json.dumps(val, ensure_ascii=False)
        except Exception:
            return str(val)
    if isinstance(val, bool):
        return "true" if val else "false"
    return str(val)


def _get_storage() -> Optional[Any]:
    """Возвращает экземпляр SQLite хранилища телеметрии (ленивый импорт для исключения циклических зависимостей)."""
    try:
        from apps.windows.telemetry.storage import TelemetryStorage
        if _LOG_DIR_OVERRIDE is not None:
            db_file = _LOG_DIR_OVERRIDE / "telemetry.db"
            return TelemetryStorage.get_instance(db_path=db_file)
        return TelemetryStorage.get_instance()
    except Exception as ex:
        logger.debug(f"Не удалось получить TelemetryStorage: {ex}")
        return None


# -----------------------------------------------------------------------------
# Внутренний буфер памяти для пакетной записи (опциональный)
# -----------------------------------------------------------------------------
class _MemoryBatcher:
    """Легковесный потокобезопасный буфер записей в памяти."""

    def __init__(self, max_batch: int = 50, auto_flush_interval: float = 3.0) -> None:
        self._lock = threading.Lock()
        self._polls: List[Dict[str, Any]] = []
        self._events: List[Dict[str, Any]] = []
        self._param_changes: List[Dict[str, Any]] = []
        self.max_batch = max_batch
        self.auto_flush_interval = auto_flush_interval
        self._last_flush = time.time()

    def add_poll(self, poll_data: Dict[str, Any]) -> None:
        with self._lock:
            self._polls.append(poll_data)
            if len(self._polls) >= self.max_batch or (time.time() - self._last_flush) >= self.auto_flush_interval:
                self.flush_unlocked()

    def add_event(self, event_data: Dict[str, Any]) -> None:
        with self._lock:
            self._events.append(event_data)
            if len(self._events) >= self.max_batch or (time.time() - self._last_flush) >= self.auto_flush_interval:
                self.flush_unlocked()

    def add_param_change(self, param_data: Dict[str, Any]) -> None:
        with self._lock:
            self._param_changes.append(param_data)
            if len(self._param_changes) >= self.max_batch or (time.time() - self._last_flush) >= self.auto_flush_interval:
                self.flush_unlocked()

    def flush_unlocked(self) -> None:
        storage = _get_storage()
        if storage is None:
            return

        if self._polls:
            batch = self._polls[:]
            self._polls.clear()
            try:
                storage.save_app_polls_batch(batch)
            except Exception as ex:
                logger.debug(f"Ошибка сброса пачки app_polls: {ex}")

        if self._events:
            batch = self._events[:]
            self._events.clear()
            try:
                storage.save_app_events_batch(batch)
            except Exception as ex:
                logger.debug(f"Ошибка сброса пачки app_events: {ex}")

        if self._param_changes:
            batch = self._param_changes[:]
            self._param_changes.clear()
            try:
                storage.save_app_param_changes_batch(batch)
            except Exception as ex:
                logger.debug(f"Ошибка сброса пачки app_param_changes: {ex}")

        self._last_flush = time.time()

    def flush(self) -> None:
        with self._lock:
            self.flush_unlocked()


_BATCHER = _MemoryBatcher()


def flush_batch_buffer() -> None:
    """Принудительно сбрасывает все буферизованные в памяти записи в SQLite."""
    _BATCHER.flush()


def _write_csv_direct(
    filename: str,
    headers: Sequence[str],
    row_data: Sequence[Any],
) -> Path:
    """Физически записывает строку в CSV файл на диске с защитой мьютексом."""
    if not filename.lower().endswith(".csv"):
        filename = f"{filename}.csv"

    log_dir = get_apps_log_dir()
    file_path = log_dir / filename
    formatted_row = [_format_cell(x) for x in row_data]

    with _LOCK:
        try:
            file_exists = file_path.exists() and file_path.stat().st_size > 0
            with open(file_path, mode="a", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(headers)
                writer.writerow(formatted_row)
        except Exception as ex:
            logger.warning(f"Не удалось записать CSV-лог в {file_path}: {ex}")

    return file_path


def write_csv_row(
    filename: str,
    headers: Sequence[str],
    row_data: Sequence[Any],
) -> Path:
    """Записывает строку лога в SQLite (Single Source of Truth) и CSV.

    Args:
        filename: Имя файла (например, 'cloudflared_status_polls.csv').
        headers: Список имен колонок заголовка.
        row_data: Последовательность значений для записи в строку.

    Returns:
        Path: Путь к записанному файлу лога.
    """
    if not filename.lower().endswith(".csv"):
        filename = f"{filename}.csv"

    # 1. Сохраняем в SQLite базу данных
    storage = _get_storage()
    if storage is not None:
        try:
            payload = dict(zip(headers, row_data))
            storage.save_custom_record(source_file=filename, payload=payload)
        except Exception as ex:
            logger.debug(f"Не удалось записать custom_record в SQLite: {ex}")

    # 2. Физическая запись в CSV файл
    return _write_csv_direct(filename, headers, row_data)


def log_event(
    app: str,
    event_type: str,
    status: str = "OK",
    details: Any = "",
    filename: Optional[str] = None,
) -> Path:
    """Логирует событие приложения в SQLite (Single Source of Truth) и опционально в CSV.

    Args:
        app: Имя приложения (например, 'cloudflared_monitor').
        event_type: Тип события (например, 'service_start', 'ticket_create').
        status: Статус операции ('OK', 'SUCCESS', 'FAILED', 'WARNING').
        details: Дополнительные детали, словарь или текстовое описание.
        filename: Опциональное имя файла. Если не указано, используется '{app}_events.csv'.

    Returns:
        Path: Путь к файлу лога (или целевой путь On-Demand).
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    target_file = filename or f"{app}_events.csv"

    # 1. Сохранение в SQLite
    if _ENABLE_MEMORY_BATCHING:
        _BATCHER.add_event({
            "app": app,
            "event_type": event_type,
            "status": status,
            "details": details,
            "timestamp": now_iso,
        })
    else:
        storage = _get_storage()
        if storage is not None:
            try:
                storage.save_app_event(
                    app=app,
                    event_type=event_type,
                    status=status,
                    details=details,
                    timestamp=now_iso,
                )
            except Exception as ex:
                logger.debug(f"Не удалось записать app_event в SQLite: {ex}")

    # 2. Физическая запись в CSV при включенном флаге зеркалирования
    if _ENABLE_MIRRORING_LOGS_TO_CSV:
        headers = ["timestamp", "app", "event_type", "status", "details"]
        row = [now_iso, app, event_type, status, details]
        return _write_csv_direct(target_file, headers, row)

    return get_apps_log_dir() / target_file


def log_param_change(
    app: str,
    param_name: str,
    old_value: Any,
    new_value: Any,
    status: str = "SUCCESS",
    user: str = "system",
    details: Any = "",
    filename: Optional[str] = None,
) -> Path:
    """Логирует изменение параметра/настройки приложения в SQLite и опционально в CSV.

    Args:
        app: Имя приложения (например, 'system_control_center').
        param_name: Наименование параметра (например, 'sec.uac_level', 'rag_mode').
        old_value: Предыдущее значение.
        new_value: Новое устанавливаемое значение.
        status: Статус изменения ('SUCCESS', 'FAILED', 'ROLLBACK').
        user: Пользователь или подсистема, инициировавшая изменение.
        details: Дополнительные метаданные.
        filename: Опциональное имя файла. Если не указано, используется '{app}_param_changes.csv'.

    Returns:
        Path: Путь к файлу лога.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    target_file = filename or f"{app}_param_changes.csv"

    # 1. Сохранение в SQLite
    if _ENABLE_MEMORY_BATCHING:
        _BATCHER.add_param_change({
            "app": app,
            "param_name": param_name,
            "old_value": old_value,
            "new_value": new_value,
            "status": status,
            "user": user,
            "details": details,
            "timestamp": now_iso,
        })
    else:
        storage = _get_storage()
        if storage is not None:
            try:
                storage.save_app_param_change(
                    app=app,
                    param_name=param_name,
                    old_value=old_value,
                    new_value=new_value,
                    status=status,
                    user=user,
                    details=details,
                    timestamp=now_iso,
                )
            except Exception as ex:
                logger.debug(f"Не удалось записать app_param_change в SQLite: {ex}")

    # 2. Физическая запись в CSV при включенном зеркалировании
    if _ENABLE_MIRRORING_LOGS_TO_CSV:
        headers = [
            "timestamp",
            "app",
            "param_name",
            "old_value",
            "new_value",
            "status",
            "user",
            "details",
        ]
        row = [now_iso, app, param_name, old_value, new_value, status, user, details]
        return _write_csv_direct(target_file, headers, row)

    return get_apps_log_dir() / target_file


def log_poll(
    app: str,
    poll_type: str,
    metric_name: str,
    value: Any,
    unit: str = "",
    status: str = "OK",
    details: Any = "",
    filename: Optional[str] = None,
) -> Path:
    """Логирует факт опроса телеметрии, метрики или статуса в SQLite и опционально в CSV.

    Args:
        app: Имя приложения (например, 'hwinfo', 'website_monitor').
        poll_type: Категория опроса ('sensor_read', 'status_check', 'metrics_fetch').
        metric_name: Название опрашиваемой метрики ('cpu_temp', 'reachability').
        value: Полученное значение.
        unit: Единица измерения (°C, %, ms, bool и т.д.).
        status: Статус проверки ('OK', 'ALERT', 'UNREACHABLE', 'ERROR').
        details: Дополнительный контекст или JSON-объект.
        filename: Опциональное имя файла. Если не указано, используется '{app}_poll_events.csv'.

    Returns:
        Path: Путь к файлу лога.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    target_file = filename or f"{app}_poll_events.csv"

    # 1. Сохранение в SQLite
    if _ENABLE_MEMORY_BATCHING:
        _BATCHER.add_poll({
            "app": app,
            "poll_type": poll_type,
            "metric_name": metric_name,
            "value": value,
            "unit": unit,
            "status": status,
            "details": details,
            "timestamp": now_iso,
        })
    else:
        storage = _get_storage()
        if storage is not None:
            try:
                storage.save_app_poll(
                    app=app,
                    poll_type=poll_type,
                    metric_name=metric_name,
                    value=value,
                    unit=unit,
                    status=status,
                    details=details,
                    timestamp=now_iso,
                )
            except Exception as ex:
                logger.debug(f"Не удалось записать app_poll в SQLite: {ex}")

    # 2. Физическая запись в CSV при включенном зеркалировании
    if _ENABLE_MIRRORING_LOGS_TO_CSV:
        headers = [
            "timestamp",
            "app",
            "poll_type",
            "metric_name",
            "value",
            "unit",
            "status",
            "details",
        ]
        row = [now_iso, app, poll_type, metric_name, value, unit, status, details]
        return _write_csv_direct(target_file, headers, row)

    return get_apps_log_dir() / target_file


def log_custom_csv(
    filename: str,
    headers: Sequence[str],
    row: Sequence[Any],
) -> Path:
    """Записывает кастомную запись в SQLite и опционально в CSV.

    Args:
        filename: Имя файла с расширением или без.
        headers: Список заголовков колонок.
        row: Значения строки.

    Returns:
        Path: Путь к целевому файлу.
    """
    return write_csv_row(filename, headers, row)


# -----------------------------------------------------------------------------
# On-Demand генерация CSV из базы данных SQLite
# -----------------------------------------------------------------------------
def export_app_polls_to_csv(
    app: Optional[str] = None,
    output_path: Optional[Union[str, Path]] = None,
    limit: int = 50000,
) -> Path:
    """Генерирует CSV-файл опросов приложения из SQLite по требованию (On-Demand).

    Args:
        app: Имя приложения (опционально).
        output_path: Путь для сохранения CSV (по умолчанию в get_apps_log_dir()).
        limit: Лимит записей.

    Returns:
        Path: Путь к созданному CSV-файлу.
    """
    flush_batch_buffer()
    storage = _get_storage()
    if storage is None:
        raise RuntimeError("TelemetryStorage недоступен для экспорта CSV")

    target = Path(output_path) if output_path else get_apps_log_dir() / (f"{app}_poll_events.csv" if app else "all_app_polls.csv")
    return storage.export_app_polls_to_csv(app=app, output_path=target, limit=limit)


def export_app_events_to_csv(
    app: Optional[str] = None,
    output_path: Optional[Union[str, Path]] = None,
    limit: int = 50000,
) -> Path:
    """Генерирует CSV-файл событий приложения из SQLite по требованию (On-Demand).

    Args:
        app: Имя приложения (опционально).
        output_path: Путь для сохранения CSV.
        limit: Лимит записей.

    Returns:
        Path: Путь к созданному CSV-файлу.
    """
    flush_batch_buffer()
    storage = _get_storage()
    if storage is None:
        raise RuntimeError("TelemetryStorage недоступен для экспорта CSV")

    target = Path(output_path) if output_path else get_apps_log_dir() / (f"{app}_events.csv" if app else "all_app_events.csv")
    return storage.export_app_events_to_csv(app=app, output_path=target, limit=limit)


def export_app_param_changes_to_csv(
    app: Optional[str] = None,
    output_path: Optional[Union[str, Path]] = None,
    limit: int = 50000,
) -> Path:
    """Генерирует CSV-файл изменений параметров из SQLite по требованию (On-Demand).

    Args:
        app: Имя приложения (опционально).
        output_path: Путь для сохранения CSV.
        limit: Лимит записей.

    Returns:
        Path: Путь к созданному CSV-файлу.
    """
    flush_batch_buffer()
    storage = _get_storage()
    if storage is None:
        raise RuntimeError("TelemetryStorage недоступен для экспорта CSV")

    target = Path(output_path) if output_path else get_apps_log_dir() / (f"{app}_param_changes.csv" if app else "all_app_param_changes.csv")
    return storage.export_app_param_changes_to_csv(app=app, output_path=target, limit=limit)


def export_to_csv(
    app: Optional[str] = None,
    target_type: str = "all",
    output_dir: Optional[Union[str, Path]] = None,
) -> Dict[str, Path]:
    """Универсальный экспорт данных приложения из SQLite в CSV-файлы (On-Demand).

    Args:
        app: Имя приложения (например, 'cloudflared_monitor').
        target_type: Тип выгрузки ('polls', 'events', 'params', 'all').
        output_dir: Каталог для сохранения (по умолчанию get_apps_log_dir()).

    Returns:
        Dict[str, Path]: Словарь сгенерированных путей {тип: путь_к_файлу}.
    """
    flush_batch_buffer()
    out_dir = Path(output_dir) if output_dir else get_apps_log_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    res: Dict[str, Path] = {}

    prefix = f"{app}_" if app else "all_"

    if target_type in ("polls", "all"):
        p = export_app_polls_to_csv(app=app, output_path=out_dir / f"{prefix}poll_events.csv")
        res["polls"] = p

    if target_type in ("events", "all"):
        p = export_app_events_to_csv(app=app, output_path=out_dir / f"{prefix}events.csv")
        res["events"] = p

    if target_type in ("params", "all"):
        p = export_app_param_changes_to_csv(app=app, output_path=out_dir / f"{prefix}param_changes.csv")
        res["params"] = p

    return res


class AppCsvLogger:
    """Объектный интерфейс логирования и телеметрии для конкретного приложения."""

    def __init__(self, app_name: str) -> None:
        """Инициализирует логгер приложения.

        Args:
            app_name: Имя приложения (например, 'trading_terminal', 'aida64').
        """
        self.app_name = app_name

    def log_event(
        self,
        event_type: str,
        status: str = "OK",
        details: Any = "",
        filename: Optional[str] = None,
    ) -> Path:
        """Логирует событие приложения в SQLite и опционально в CSV."""
        return log_event(
            app=self.app_name,
            event_type=event_type,
            status=status,
            details=details,
            filename=filename,
        )

    def log_param_change(
        self,
        param_name: str,
        old_value: Any,
        new_value: Any,
        status: str = "SUCCESS",
        user: str = "system",
        details: Any = "",
        filename: Optional[str] = None,
    ) -> Path:
        """Логирует изменение параметра приложения в SQLite и опционально в CSV."""
        return log_param_change(
            app=self.app_name,
            param_name=param_name,
            old_value=old_value,
            new_value=new_value,
            status=status,
            user=user,
            details=details,
            filename=filename,
        )

    def log_poll(
        self,
        poll_type: str,
        metric_name: str,
        value: Any,
        unit: str = "",
        status: str = "OK",
        details: Any = "",
        filename: Optional[str] = None,
    ) -> Path:
        """Логирует опрос телеметрии/сенсоров/статуса в SQLite и опционально в CSV."""
        return log_poll(
            app=self.app_name,
            poll_type=poll_type,
            metric_name=metric_name,
            value=value,
            unit=unit,
            status=status,
            details=details,
            filename=filename,
        )

    def log_custom(
        self,
        filename: str,
        headers: Sequence[str],
        row: Sequence[Any],
    ) -> Path:
        """Логирует кастомную строку в указанный журнал."""
        return log_custom_csv(filename=filename, headers=headers, row=row)

    def export_csv(
        self,
        target_type: str = "all",
        output_dir: Optional[Union[str, Path]] = None,
    ) -> Dict[str, Path]:
        """Экспортирует данные данного приложения в CSV-файлы по требованию (On-Demand).

        Args:
            target_type: Тип ('polls', 'events', 'params', 'all').
            output_dir: Каталог назначения.

        Returns:
            Dict[str, Path]: Сгенерированные файлы.
        """
        return export_to_csv(app=self.app_name, target_type=target_type, output_dir=output_dir)
