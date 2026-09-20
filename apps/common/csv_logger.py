# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Apps Unified CSV Logging System
# =============================================================================
# Description:
#   Централизованный модуль CSV-логгирования для всех приложений AI-Breadboard.
#   Обеспечивает потокобезопасную запись опрашиваемых событий, телеметрии,
#   метрик и изменений параметров в каталог %APPDATA%/AI-Breadboard/apps/logs
#   в формате CSV с автоматическим созданием заголовков и говорящими именами.
#
# File: csv_logger.py
# Project: ai-breadboard
# Package: apps.common
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модуль централизованного CSV-логгирования событий и параметров для приложений."""

from __future__ import annotations

import csv
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from src.logger import logger


_LOCK = threading.Lock()
_LOG_DIR_OVERRIDE: Optional[Path] = None


def get_apps_log_dir() -> Path:
    """Возвращает и создает целевой каталог для CSV-логов приложений.

    Каталог располагается в %APPDATA%/AI-Breadboard/apps/logs (с фоллбэком на
    %LOCALAPPDATA% или ~/.config/AI-Breadboard/apps/logs в кросс-платформенных средах).

    Returns:
        Path: Абсолютный путь к директории логов приложений.
    """
    global _LOG_DIR_OVERRIDE
    if _LOG_DIR_OVERRIDE is not None:
        _LOG_DIR_OVERRIDE.mkdir(parents=True, exist_ok=True)
        return _LOG_DIR_OVERRIDE

    appdata = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
    if appdata and os.path.exists(appdata):
        base_dir = Path(appdata)
    else:
        base_dir = Path.home() / ".config"

    log_dir = base_dir / "AI-Breadboard" / "apps" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def set_apps_log_dir_override(path: Optional[Path]) -> None:
    """Устанавливает переопределение каталога логов (для изоляции в тестах).

    Args:
        path: Пользовательский путь или None для сброса.
    """
    global _LOG_DIR_OVERRIDE
    _LOG_DIR_OVERRIDE = path


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


def write_csv_row(
    filename: str,
    headers: Sequence[str],
    row_data: Sequence[Any],
) -> Path:
    """Потокобезопасно записывает строку в CSV-файл с автоматическим добавлением заголовков.

    Args:
        filename: Имя файла (например, 'cloudflared_status_polls.csv').
        headers: Список имен колонок заголовка.
        row_data: Последовательность значений для записи в строку.

    Returns:
        Path: Путь к записанному файлу.
    """
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


def log_event(
    app: str,
    event_type: str,
    status: str = "OK",
    details: Any = "",
    filename: Optional[str] = None,
) -> Path:
    """Логирует событие приложения в CSV.

    Args:
        app: Имя приложения (например, 'cloudflared_monitor').
        event_type: Тип события (например, 'service_start', 'ticket_create').
        status: Статус операции ('OK', 'SUCCESS', 'FAILED', 'WARNING').
        details: Дополнительные детали, словарь или текстовое описание.
        filename: Опциональное имя файла. Если не указано, используется '{app}_events.csv'.

    Returns:
        Path: Путь к CSV-файлу.
    """
    target_file = filename or f"{app}_events.csv"
    headers = ["timestamp", "app", "event_type", "status", "details"]
    row = [
        datetime.now(timezone.utc).isoformat(),
        app,
        event_type,
        status,
        details,
    ]
    return write_csv_row(target_file, headers, row)


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
    """Логирует изменение параметра/настройки приложения в CSV.

    Args:
        app: Имя приложения (например, 'system_control_center').
        param_name: Наименование параметра (например, 'sec.uac_level', 'rag_mode').
        old_value: Предыдущее значение.
        new_value: Новое устанавливаемое значение.
        status: Статус изменения ('SUCCESS', 'FAILED', 'ROLLBACK').
        user: Пользователь или подсистема, инициировавшая изменение.
        details: Дополнительные метаданные (например, ID снимка или точки восстановления).
        filename: Опциональное имя файла. Если не указано, используется '{app}_param_changes.csv'.

    Returns:
        Path: Путь к CSV-файлу.
    """
    target_file = filename or f"{app}_param_changes.csv"
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
    row = [
        datetime.now(timezone.utc).isoformat(),
        app,
        param_name,
        old_value,
        new_value,
        status,
        user,
        details,
    ]
    return write_csv_row(target_file, headers, row)


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
    """Логирует факт опроса телеметрии, метрики или статуса в CSV.

    Args:
        app: Имя приложения (например, 'hwinfo', 'website_monitor').
        poll_type: Категория опроса (например, 'sensor_read', 'status_check', 'metrics_fetch').
        metric_name: Название опрашиваемой метрики (например, 'cpu_temp', 'reachability').
        value: Полученное значение.
        unit: Единица измерения (°C, %, ms, bool и т.д.).
        status: Статус проверки ('OK', 'ALERT', 'UNREACHABLE', 'ERROR').
        details: Дополнительный контекст или JSON-объект.
        filename: Опциональное имя файла. Если не указано, используется '{app}_poll_events.csv'.

    Returns:
        Path: Путь к CSV-файлу.
    """
    target_file = filename or f"{app}_poll_events.csv"
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
    row = [
        datetime.now(timezone.utc).isoformat(),
        app,
        poll_type,
        metric_name,
        value,
        unit,
        status,
        details,
    ]
    return write_csv_row(target_file, headers, row)


def log_custom_csv(
    filename: str,
    headers: Sequence[str],
    row: Sequence[Any],
) -> Path:
    """Записывает кастомную запись в CSV с заданными заголовками.

    Args:
        filename: Имя файла с расширением или без.
        headers: Список заголовков колонок.
        row: Значения строки.

    Returns:
        Path: Путь к CSV-файлу.
    """
    return write_csv_row(filename, headers, row)


class AppCsvLogger:
    """Объектный интерфейс CSV-логгирования для конкретного приложения."""

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
        """Логирует событие приложения."""
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
        """Логирует изменение параметра приложения."""
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
        """Логирует опрос телеметрии/сенсоров/статуса."""
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
        """Логирует кастомную строку в указанный файл."""
        return log_custom_csv(filename=filename, headers=headers, row=row)
