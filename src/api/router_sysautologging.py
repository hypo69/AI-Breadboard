# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: System Auto-Logging and CSV Management Router
# =============================================================================
# Description:
#   FastAPI роутер для управления системой автологгирования сенсоров,
#   настройки интервалов опроса в config_tc.json / config.json, запуска и
#   остановки движка AutoLogEngine, а также инспекции, чтения, очистки и
#   скачивания сгенерированных CSV-файлов логов в %APPDATA%/AI-Breadboard/apps/logs.
#
#   Эндпоинты роутера /sysautologging:
#   - GET  /sysautologging/status           - Статус автологгирования
#   - GET  /sysautologging/config           - Конфигурация логгеров
#   - POST /sysautologging/config           - Обновление конфигурации
#   - POST /sysautologging/start            - Запуск движка
#   - POST /sysautologging/stop             - Остановка движка
#   - POST /sysautologging/poll-all         - Опрос всех логгеров
#   - POST /sysautologging/poll/{name}      - Опрос конкретного логгера
#   - GET  /sysautologging/files            - Список CSV-файлов
#   - GET  /sysautologging/file/{name}      - Чтение CSV-файла
#   - DELETE /sysautologging/file/{name}    - Удаление CSV-файла
#   - GET  /sysautologging/download/{name}  - Скачивание CSV-файла
#
# File: router_sysautologging.py
# Project: ai-breadboard
# Package: src.api
# Author: Kiro (AI Assistant)
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI роутер управления системным автологгированием и CSV-логами сенсоров."""

from __future__ import annotations

import csv
import io
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from apps.common.autolog_engine import (
    AutoLogEngine,
    autolog_engine,
    load_autolog_config,
    parse_interval_seconds,
)
from apps.common.csv_logger import get_apps_log_dir
from header import __root__
from logger import logger

router = APIRouter(prefix="/sysautologging", tags=["sysautologging"])


class LoggerConfigItem(BaseModel):
    """Модель конфигурации отдельного логгера сенсора."""

    interval: str = Field(default="1 minute", description="Интервал опроса (например, '5 seconds', '1 hour')")
    enabled: bool = Field(default=True, description="Флаг активности логгера")


class AutoLogConfigRequest(BaseModel):
    """Модель запроса обновления конфигурации автологгирования."""

    enable_autolog: Optional[bool] = Field(default=None, description="Глобальный флаг автологгирования")
    default_interval: Optional[str] = Field(default=None, description="Интервал по умолчанию")
    loggers: Optional[Dict[str, LoggerConfigItem]] = Field(default=None, description="Словарь настроек логгеров")


def _get_active_config_file() -> Path:
    """Определяет путь к активному файлу конфигурации (config_tc.json или config.json)."""
    cfg_env = os.getenv("AIBREADBOARD_CONFIG") or os.getenv("CONFIG_FILE")
    if cfg_env:
        p = Path(cfg_env)
        if p.is_absolute() and p.exists():
            return p
        if (__root__ / cfg_env).exists():
            return __root__ / cfg_env

    for candidate in ("config_tc.json", "config.json"):
        p = __root__ / candidate
        if p.exists():
            return p

    return __root__ / "config.json"


def _format_file_size(size_bytes: int) -> str:
    """Форматирует размер файла в человекочитаемый вид."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    return f"{size_bytes / (1024 * 1024):.2f} MB"


@router.get("/status")
async def get_sysautolog_status() -> Dict[str, Any]:
    """Возвращает текущий статус активности и диагностические счетчики движка автологгирования.
    
    Returns:
        Dict со статусом, количеством задач, зарегистрированными логгерами и т.д.
        
    Example:
        {
            "status": "success",
            "running": true,
            "active_tasks_count": 5,
            "enable_autolog": true,
            "default_interval": "1 minute",
            "config_file": "config_tc.json",
            "logs_directory": "C:\\Users\\...\\AppData\\Roaming\\AI-Breadboard\\apps\\logs",
            "registered_pollers": ["system_inspector", "hardware_monitor", ...],
            "poll_counts": {"system_inspector": 123, ...},
            "last_poll_timestamps": {"system_inspector": 1695200000.0, ...}
        }
    """
    status = autolog_engine.get_status()
    cfg_file = _get_active_config_file()
    cfg = load_autolog_config(cfg_file)

    return {
        "status": "success",
        "running": status.get("running", False),
        "active_tasks_count": status.get("active_tasks_count", 0),
        "enable_autolog": cfg.get("enable_autolog", True),
        "default_interval": cfg.get("default_interval", "1 minute"),
        "config_file": cfg_file.name,
        "logs_directory": status.get("logs_directory", str(get_apps_log_dir())),
        "registered_pollers": status.get("registered_pollers", []),
        "poll_counts": status.get("poll_counts", {}),
        "last_poll_timestamps": status.get("last_poll_timestamps", {}),
    }


@router.get("/config")
async def get_sysautolog_config() -> Dict[str, Any]:
    """Возвращает детальную конфигурацию всех логгеров из активного конфигурационного файла.
    
    Returns:
        Dict с общей конфигурацией и настройками каждого логгера.
        
    Example:
        {
            "status": "success",
            "config_file": "config_tc.json",
            "enable_autolog": true,
            "default_interval": "1 minute",
            "is_running": true,
            "loggers": {
                "system_inspector": {
                    "interval": "5 seconds",
                    "interval_seconds": 5.0,
                    "enabled": true,
                    "poll_count": 123,
                    "last_poll_timestamp": 1695200000.0,
                    "last_poll": "2026-09-20T...",
                    "is_registered": true
                },
                ...
            }
        }
    """
    cfg_file = _get_active_config_file()
    cfg = load_autolog_config(cfg_file)
    engine_status = autolog_engine.get_status()
    registered = engine_status.get("registered_pollers", [])
    poll_counts = engine_status.get("poll_counts", {})
    last_timestamps = engine_status.get("last_poll_timestamps", {})

    loggers_out: Dict[str, Any] = {}
    cfg_loggers: Dict[str, Any] = cfg.get("loggers", {})

    # Объединяем зарегистрированные логгеры и объявленные в конфиге
    all_logger_names = sorted(set(registered) | set(cfg_loggers.keys()))
    for name in all_logger_names:
        l_cfg = cfg_loggers.get(name, {})
        if isinstance(l_cfg, dict):
            interval = l_cfg.get("interval", cfg.get("default_interval", "1 minute"))
            enabled = bool(l_cfg.get("enabled", True))
        else:
            interval = cfg.get("default_interval", "1 minute")
            enabled = True

        last_ts = last_timestamps.get(name)
        last_str = datetime.fromtimestamp(last_ts, timezone.utc).isoformat() if last_ts else None

        loggers_out[name] = {
            "interval": interval,
            "interval_seconds": parse_interval_seconds(interval),
            "enabled": enabled,
            "poll_count": poll_counts.get(name, 0),
            "last_poll_timestamp": last_ts,
            "last_poll": last_str,
            "is_registered": name in registered,
        }

    return {
        "status": "success",
        "config_file": cfg_file.name,
        "enable_autolog": cfg.get("enable_autolog", True),
        "default_interval": cfg.get("default_interval", "1 minute"),
        "is_running": autolog_engine.is_running(),
        "loggers": loggers_out,
    }


@router.post("/config")
async def update_sysautolog_config(payload: AutoLogConfigRequest) -> Dict[str, Any]:
    """Обновляет конфигурацию логгирования в активном JSON-файле и перезапускает движок.
    
    Позволяет изменить:
    - enable_autolog - глобальный флаг автологгирования
    - default_interval - интервал по умолчанию для всех логгеров
    - loggers - настройки конкретных логгеров (interval, enabled)
    
    Returns:
        Dict со статусом успешности и информацией о примененных изменениях.
    """
    cfg_file = _get_active_config_file()
    if not cfg_file.exists():
        raise HTTPException(status_code=404, detail=f"Файл конфигурации {cfg_file.name} не найден")

    try:
        with open(cfg_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Ошибка чтения конфигурации: {ex}")

    if "logging" not in data or not isinstance(data["logging"], dict):
        data["logging"] = {}

    if payload.enable_autolog is not None:
        data["logging"]["enable_autolog"] = payload.enable_autolog

    if payload.default_interval is not None:
        data["logging"]["default_interval"] = payload.default_interval

    if payload.loggers is not None:
        if "loggers" not in data["logging"] or not isinstance(data["logging"]["loggers"], dict):
            data["logging"]["loggers"] = {}

        for l_name, l_val in payload.loggers.items():
            data["logging"]["loggers"][l_name] = {
                "interval": l_val.interval,
                "enabled": l_val.enabled,
            }

    try:
        with open(cfg_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения конфигурации: {ex}")

    # Перезапускаем движок автологгирования для мгновенного применения новых интервалов
    try:
        await autolog_engine.restart(cfg_file)
    except Exception as ex:
        logger.warning(f"Ошибка при перезапуске движка автологгирования: {ex}")

    return {
        "status": "success",
        "message": f"Конфигурация успешно сохранена в {cfg_file.name} и применена к AutoLogEngine",
        "enable_autolog": data["logging"].get("enable_autolog", True),
        "is_running": autolog_engine.is_running(),
    }


@router.post("/start")
async def start_sysautolog() -> Dict[str, Any]:
    """Запускает движок автологгирования.
    
    Returns:
        Dict со статусом и информацией о запуске.
    """
    cfg_file = _get_active_config_file()
    started = await autolog_engine.start(cfg_file)
    return {
        "status": "success" if started else "disabled",
        "is_running": autolog_engine.is_running(),
        "message": "AutoLogEngine запущен" if started else "AutoLogEngine отключен в конфигурации",
    }


@router.post("/stop")
async def stop_sysautolog() -> Dict[str, Any]:
    """Останавливает движок автологгирования.
    
    Returns:
        Dict со статусом и информацией о остановке.
    """
    await autolog_engine.stop()
    return {
        "status": "success",
        "is_running": autolog_engine.is_running(),
        "message": "AutoLogEngine остановлен",
    }


@router.post("/poll-all")
async def poll_all_loggers() -> Dict[str, Any]:
    """Выполняет немедленный разовый опрос всех зарегистрированных логгеров.
    
    Returns:
        Dict со статусом выполнения для каждого логгера.
    """
    results = autolog_engine.poll_all_once()
    return {
        "status": "success",
        "results": results,
        "total_polled": len(results),
        "successful_count": sum(1 for v in results.values() if v),
    }


@router.post("/poll/{app_name}")
async def poll_specific_logger(app_name: str) -> Dict[str, Any]:
    """Выполняет немедленный разовый опрос конкретного приложения.
    
    Args:
        app_name: Имя приложения для опроса (например, 'system_inspector', 'hardware_monitor').
        
    Returns:
        Dict со статусом опроса.
        
    Raises:
        HTTPException: Если логгер не найден или опрос не удался.
    """
    ok = autolog_engine.poll_logger(app_name)
    if not ok:
        raise HTTPException(status_code=400, detail=f"Не удалось выполнить опрос логгера '{app_name}'")
    return {
        "status": "success",
        "app_name": app_name,
        "message": f"Опрос приложения '{app_name}' успешно выполнен",
    }


@router.get("/files")
async def list_log_files() -> Dict[str, Any]:
    """Возвращает список всех CSV-файлов логов с метаданными (размер, дата, кол-во строк).
    
    Returns:
        Dict со списком файлов и общей статистикой.
        
    Example:
        {
            "status": "success",
            "files": [
                {
                    "filename": "system_inspector_polls.csv",
                    "size_bytes": 1024,
                    "size_human": "1.00 KB",
                    "modified_at": "2026-09-20T...",
                    "modified_timestamp": 1695200000.0,
                    "row_count": 50,
                    "total_lines": 51
                },
                ...
            ],
            "total_files": 5,
            "directory": "C:\\Users\\...\\AppData\\Roaming\\AI-Breadboard\\apps\\logs"
        }
    """
    log_dir = get_apps_log_dir()
    if not log_dir.exists():
        return {"status": "success", "files": [], "total_files": 0, "directory": str(log_dir)}

    files: List[Dict[str, Any]] = []
    for entry in sorted(log_dir.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            stat = entry.stat()
            # Быстрый подсчет строк
            with open(entry, "r", encoding="utf-8-sig", errors="ignore") as f:
                line_count = sum(1 for _ in f)

            files.append({
                "filename": entry.name,
                "size_bytes": stat.st_size,
                "size_human": _format_file_size(stat.st_size),
                "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                "modified_timestamp": stat.st_mtime,
                "row_count": max(0, line_count - 1),
                "total_lines": line_count,
            })
        except Exception as ex:
            logger.debug(f"Ошибка чтения метаданных файла {entry.name}: {ex}")

    return {
        "status": "success",
        "files": files,
        "total_files": len(files),
        "directory": str(log_dir),
    }


@router.get("/file/{filename}")
async def read_log_file(
    filename: str,
    limit: int = Query(default=200, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
) -> Dict[str, Any]:
    """Читает и парсит строки из указанного CSV-файла лога.
    
    Args:
        filename: Имя CSV-файла.
        limit: Максимальное количество строк (по умолчанию 200).
        offset: Смещение для пагинации (по умолчанию 0).
        search: Опциональный поиск по строкам.
        
    Returns:
        Dict с заголовками, строками и статистикой.
        
    Raises:
        HTTPException: Если файл не найден.
    """
    # Защита от path traversal
    safe_name = os.path.basename(filename)
    if not safe_name.lower().endswith(".csv"):
        safe_name = f"{safe_name}.csv"

    log_dir = get_apps_log_dir()
    target_path = log_dir / safe_name
    if not target_path.exists() or not target_path.is_file():
        raise HTTPException(status_code=404, detail=f"Файл лога '{safe_name}' не найден")

    headers: List[str] = []
    all_rows: List[List[str]] = []

    try:
        with open(target_path, "r", encoding="utf-8-sig", errors="ignore") as f:
            reader = csv.reader(f)
            first = True
            for row in reader:
                if not row:
                    continue
                if first:
                    headers = row
                    first = False
                    continue

                if search:
                    row_str = " ".join(row).lower()
                    if search.lower() not in row_str:
                        continue

                all_rows.append(row)
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Ошибка разбора CSV файла: {ex}")

    total_rows = len(all_rows)
    # Возвращаем в обратном хронологическом порядке (новые сверху)
    reversed_rows = list(reversed(all_rows))
    paginated_rows = reversed_rows[offset : offset + limit]

    return {
        "status": "success",
        "filename": safe_name,
        "headers": headers,
        "rows": paginated_rows,
        "total_rows": total_rows,
        "limit": limit,
        "offset": offset,
        "search": search or "",
    }


@router.delete("/file/{filename}")
async def delete_log_file(filename: str) -> Dict[str, Any]:
    """Очищает или удаляет указанный CSV-файл лога.
    
    Args:
        filename: Имя CSV-файла для удаления.
        
    Returns:
        Dict со статусом удаления.
        
    Raises:
        HTTPException: Если файл не найден.
    """
    safe_name = os.path.basename(filename)
    if not safe_name.lower().endswith(".csv"):
        safe_name = f"{safe_name}.csv"

    log_dir = get_apps_log_dir()
    target_path = log_dir / safe_name
    if not target_path.exists():
        raise HTTPException(status_code=404, detail=f"Файл '{safe_name}' не найден")

    try:
        target_path.unlink(missing_ok=True)
        return {
            "status": "success",
            "message": f"Файл лога '{safe_name}' успешно удален",
            "filename": safe_name,
        }
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Ошибка удаления файла: {ex}")


@router.get("/download/{filename}")
async def download_log_file(filename: str):
    """Скачивает указанный CSV-файл лога.
    
    Args:
        filename: Имя CSV-файла для скачивания.
        
    Returns:
        FileResponse с CSV-файлом.
        
    Raises:
        HTTPException: Если файл не найден.
    """
    safe_name = os.path.basename(filename)
    if not safe_name.lower().endswith(".csv"):
        safe_name = f"{safe_name}.csv"

    log_dir = get_apps_log_dir()
    target_path = log_dir / safe_name
    if not target_path.exists() or not target_path.is_file():
        raise HTTPException(status_code=404, detail=f"Файл '{safe_name}' не найден")

    return FileResponse(
        path=target_path,
        media_type="text/csv",
        filename=safe_name,
    )


def init_router() -> APIRouter:
    """Инициализирует и возвращает экземпляр APIRouter для системного автологгирования."""
    return router
