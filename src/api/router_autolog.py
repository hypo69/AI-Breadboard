# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Applications Auto-Logging and CSV Management Router
# =============================================================================
# Description:
#   FastAPI роутер для управления системой автологгирования приложений,
#   настройки интервалов опроса в config_tc.json / config.json, запуска и
#   остановки движка AutoLogEngine, а также инспекции, чтения, очистки и
#   скачивания сгенерированных CSV-файлов логов в %APPDATA%/AI-Breadboard/apps/logs.
#
# File: router_autolog.py
# Project: ai-breadboard
# Package: src.api
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI роутер управления автологгированием и CSV-логами приложений."""

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

router = APIRouter(prefix="/api/autolog", tags=["autolog"])


class LoggerConfigItem(BaseModel):
    """Модель конфигурации отдельного логгера приложения."""

    interval: str = Field(default="1 minute", description="Интервал опроса (например, '5 seconds', '1 hour')")
    enabled: bool = Field(default=True, description="Флаг активности логгера")


class SensorConfigItem(BaseModel):
    """Модель конфигурации сенсора телеметрии."""

    enabled: bool = Field(default=True, description="Флаг активности сенсора")
    interval_seconds: Optional[float] = Field(default=5.0, description="Интервал опроса сенсора в секундах")
    metrics: Optional[List[str]] = Field(default_factory=list, description="Список собираемых метрик")


class TelemetryOptionsItem(BaseModel):
    """Модель глобальных опций сбора телеметрии."""

    collect_serial_numbers: Optional[bool] = Field(default=True, description="Сбор серийных номеров оборудования")
    collect_hardware_inventory: Optional[bool] = Field(default=True, description="Сбор инвентаризации железа")
    collect_file_events: Optional[bool] = Field(default=True, description="Сбор файловых событий")
    max_file_size_mb: Optional[int] = Field(default=50, description="Максимальный размер лог-файла в МБ")
    watch_directories: Optional[List[str]] = Field(default_factory=list, description="Отслеживаемые директории")


class AutoLogConfigRequest(BaseModel):
    """Модель запроса обновления конфигурации автологгирования и сенсоров."""

    enable_autolog: Optional[bool] = Field(default=None, description="Глобальный флаг автологгирования")
    default_interval: Optional[str] = Field(default=None, description="Интервал по умолчанию")
    loggers: Optional[Dict[str, LoggerConfigItem]] = Field(default=None, description="Словарь настроек логгеров")
    sensors: Optional[Dict[str, SensorConfigItem]] = Field(default=None, description="Словарь настроек сенсоров телеметрии")
    telemetry_options: Optional[TelemetryOptionsItem] = Field(default=None, description="Опции сбора телеметрии")
    raw_json: Optional[str] = Field(default=None, description="Сырой JSON для сохранения из редактора")


def _get_active_config_file() -> Path:
    """Определяет путь к активному файлу конфигурации (~autolog_sensors.json или config.json)."""
    for candidate in (
        __root__ / "start_scenarios_config" / "~autolog_sensors.json",
        __root__ / "start_scenarios_config" / "autolog_sensors.json",
        __root__ / "config" / "autolog_sensors.json",
    ):
        if candidate.exists():
            return candidate

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

    return __root__ / "start_scenarios_config" / "~autolog_sensors.json"


def _format_file_size(size_bytes: int) -> str:
    """Форматирует размер файла в человекочитаемый вид."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    return f"{size_bytes / (1024 * 1024):.2f} MB"


@router.get("/status")
async def get_autolog_status() -> Dict[str, Any]:
    """Возвращает текущий статус активности и диагностические счетчики движка автологгирования."""
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
async def get_autolog_config() -> Dict[str, Any]:
    """Возвращает детальную конфигурацию всех логгеров и сенсоров из активного конфигурационного файла."""
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

    # Сырой JSON для текстового редактора
    raw_json_str = ""
    try:
        if cfg_file.exists():
            raw_json_str = cfg_file.read_text(encoding="utf-8")
    except Exception:
        pass

    # Поддержка legacy формата: сенсоры могут быть в корне, в "logging" или в "telemetry"
    sensors_data = cfg.get("sensors")
    if sensors_data is None:
        sensors_data = cfg.get("logging", {}).get("sensors", {})
    if sensors_data is None:
        sensors_data = cfg.get("telemetry", {}).get("sensors", {})

    telemetry_opts = cfg.get("telemetry_options")
    if telemetry_opts is None:
        telemetry_opts = cfg.get("logging", {}).get("telemetry_options", {})

    return {
        "status": "success",
        "config_file": cfg_file.name,
        "config_path": str(cfg_file),
        "enable_autolog": cfg.get("enable_autolog", True),
        "default_interval": cfg.get("default_interval", "1 minute"),
        "is_running": autolog_engine.is_running(),
        "loggers": loggers_out,
        "sensors": sensors_data or {},
        "telemetry_options": telemetry_opts or {},
        "raw_json": raw_json_str,
    }


@router.post("/config")
async def update_autolog_config(payload: AutoLogConfigRequest) -> Dict[str, Any]:
    """Обновляет конфигурацию логгирования и сенсоров в JSON-файле и перезапускает движок."""
    cfg_file = _get_active_config_file()

    # 1. Если передан сырой JSON — валидируем и сохраняем его
    if payload.raw_json is not None:
        try:
            parsed_data = json.loads(payload.raw_json)
        except Exception as ex:
            raise HTTPException(status_code=400, detail=f"Некорректный JSON: {ex}")

        try:
            with open(cfg_file, "w", encoding="utf-8") as f:
                json.dump(parsed_data, f, indent=2, ensure_ascii=False)
            
            # Синхронизируем парный файл autolog_sensors.json / ~autolog_sensors.json
            partner_name = "autolog_sensors.json" if cfg_file.name == "~autolog_sensors.json" else "~autolog_sensors.json"
            partner_file = cfg_file.parent / partner_name
            if partner_file.parent.exists():
                with open(partner_file, "w", encoding="utf-8") as f:
                    json.dump(parsed_data, f, indent=2, ensure_ascii=False)
        except Exception as ex:
            raise HTTPException(status_code=500, detail=f"Ошибка сохранения JSON: {ex}")

        try:
            await autolog_engine.restart(cfg_file)
        except Exception as ex:
            logger.warning(f"Ошибка при перезапуске движка: {ex}")

        return {
            "status": "success",
            "message": f"Конфигурация успешно обновлена из JSON в {cfg_file.name}",
            "is_running": autolog_engine.is_running(),
        }

    # 2. Обновление структурированных полей
    try:
        if cfg_file.exists():
            with open(cfg_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {"$schema": "https://json-schema.org/draft/2020-12/schema"}
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Ошибка чтения конфигурации: {ex}")

    is_unified_format = "loggers" in data or "sensors" in data or cfg_file.name.endswith("sensors.json")

    target_dict = data if is_unified_format else data.setdefault("logging", {})

    if payload.enable_autolog is not None:
        target_dict["enable_autolog"] = payload.enable_autolog

    if payload.default_interval is not None:
        target_dict["default_interval"] = payload.default_interval

    if payload.loggers is not None:
        if "loggers" not in target_dict or not isinstance(target_dict["loggers"], dict):
            target_dict["loggers"] = {}

        for l_name, l_val in payload.loggers.items():
            target_dict["loggers"][l_name] = {
                "interval": l_val.interval,
                "enabled": l_val.enabled,
            }

    if payload.sensors is not None:
        if "sensors" not in target_dict or not isinstance(target_dict["sensors"], dict):
            target_dict["sensors"] = {}

        for s_name, s_val in payload.sensors.items():
            target_dict["sensors"][s_name] = {
                "enabled": s_val.enabled,
                "interval_seconds": s_val.interval_seconds,
                "metrics": s_val.metrics or [],
            }

    if payload.telemetry_options is not None:
        target_dict["telemetry_options"] = payload.telemetry_options.model_dump(exclude_none=True)

    try:
        with open(cfg_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Синхронизируем парный файл
        if "sensors.json" in cfg_file.name:
            partner_name = "autolog_sensors.json" if cfg_file.name == "~autolog_sensors.json" else "~autolog_sensors.json"
            partner_file = cfg_file.parent / partner_name
            if partner_file.parent.exists():
                with open(partner_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения конфигурации: {ex}")

    # Перезапускаем движок автологгирования
    try:
        await autolog_engine.restart(cfg_file)
    except Exception as ex:
        logger.warning(f"Ошибка при перезапуске движка автологгирования: {ex}")

    return {
        "status": "success",
        "message": f"Конфигурация успешно сохранена в {cfg_file.name} и применена к AutoLogEngine",
        "enable_autolog": target_dict.get("enable_autolog", True),
        "is_running": autolog_engine.is_running(),
    }


@router.post("/start")
async def start_autolog() -> Dict[str, Any]:
    """Запускает движок автологгирования."""
    cfg_file = _get_active_config_file()
    started = await autolog_engine.start(cfg_file)
    return {
        "status": "success" if started else "disabled",
        "is_running": autolog_engine.is_running(),
        "message": "AutoLogEngine запущен" if started else "AutoLogEngine отключен в конфигурации",
    }


@router.post("/stop")
async def stop_autolog() -> Dict[str, Any]:
    """Останавливает движок автологгирования."""
    await autolog_engine.stop()
    return {
        "status": "success",
        "is_running": autolog_engine.is_running(),
        "message": "AutoLogEngine остановлен",
    }


@router.post("/poll-all")
async def poll_all_loggers() -> Dict[str, Any]:
    """Выполняет немедленный разовый опрос всех зарегистрированных логгеров."""
    results = autolog_engine.poll_all_once()
    return {
        "status": "success",
        "results": results,
        "total_polled": len(results),
        "successful_count": sum(1 for v in results.values() if v),
    }


@router.post("/poll/{app_name}")
async def poll_specific_logger(app_name: str) -> Dict[str, Any]:
    """Выполняет немедленный разовый опрос конкретного приложения."""
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
    """Возвращает список всех CSV-файлов логов с метаданными (размер, дата, кол-во строк)."""
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
    """Читает и парсит строки из указанного CSV-файла лога."""
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


@router.get("/export")
async def export_logs_to_csv(
    app: Optional[str] = Query(default=None, description="Имя приложения (например, 'cloudflared_monitor')"),
    target_type: str = Query(default="all", description="Тип выгрузки: 'polls', 'events', 'params', 'all'"),
) -> Dict[str, Any]:
    """Генерирует CSV-файлы логов из базы SQLite по требованию (On-Demand)."""
    try:
        from apps.common.csv_logger import export_to_csv
        generated_files = export_to_csv(app=app, target_type=target_type)
        return {
            "status": "success",
            "app": app or "all",
            "target_type": target_type,
            "exported_files": {k: str(v) for k, v in generated_files.items()},
        }
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Ошибка экспорта в CSV: {ex}")


@router.delete("/file/{filename}")
async def delete_log_file(filename: str) -> Dict[str, Any]:
    """Очищает или удаляет указанный CSV-файл лога."""
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
    """Скачивает указанный CSV-файл лога."""
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


# =============================================================================
# ЭНДПОИНТЫ СЛУЖБЫ ТЕЛЕМЕТРИИ (ai-telemetry.exe)
# =============================================================================

class TelemetryControlRequest(BaseModel):
    """Модель запроса управления процессом телеметрии."""
    action: str = Field(..., description="Действие: start, stop, restart, install-task, uninstall-task")
    mode: Optional[str] = Field(default=None, description="Режим: minimal, hybrid, full")
    interval: Optional[float] = Field(default=None, description="Интервал быстрого сбора")
    heavy_interval: Optional[float] = Field(default=None, description="Интервал тяжелого сбора")


class TelemetryConfigUpdateRequest(BaseModel):
    """Модель обновления конфигурации телеметрии."""
    mode: Optional[str] = Field(default=None, description="Режим: minimal, hybrid, full")
    interval_seconds: Optional[float] = Field(default=None, description="Интервал быстрой телеметрии")
    heavy_interval_seconds: Optional[float] = Field(default=None, description="Интервал тяжелых сенсоров")
    top_processes: Optional[int] = Field(default=None, description="Число процессов в топе")
    low_priority: Optional[bool] = Field(default=None, description="Пониженный приоритет CPU")
    heavy_collectors: Optional[Dict[str, bool]] = Field(default=None, description="Флаги тяжелых сенсоров")


@router.get("/telemetry/status")
async def get_telemetry_service_status() -> Dict[str, Any]:
    """Возвращает живой статус процесса ai-telemetry.exe, потребление RAM/CPU и статус Task Scheduler."""
    import psutil
    import sqlite3
    from apps.windows.telemetry.telemetry_config import TelemetryConfigManager

    cfg_mgr = TelemetryConfigManager()

    # Поиск активных процессов
    running_procs = []
    total_mem = 0.0

    for p in psutil.process_iter(["pid", "name", "cmdline", "memory_info"]):
        try:
            name = (p.info.get("name") or "").lower()
            cmdline = " ".join(p.info.get("cmdline") or [])
            is_match = ("ai-telemetry" in name) or ("telemetry" in cmdline and "main.py" in cmdline)
            if is_match:
                mem_mb = round((p.info.get("memory_info").rss if p.info.get("memory_info") else 0) / (1024 * 1024), 1)
                cpu_p = 0.0
                try:
                    cpu_p = p.cpu_percent(interval=None)
                except Exception:
                    pass
                running_procs.append({
                    "pid": p.info["pid"],
                    "name": p.info.get("name") or "ai-telemetry.exe",
                    "memory_mb": mem_mb,
                    "cpu_percent": cpu_p,
                })
                total_mem += mem_mb
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Подсчет снапшотов в SQLite
    db_path = Path(os.environ.get("APPDATA", os.path.expanduser("~\\AppData\\Roaming"))) / "AI-Breadboard" / "apps" / "windows" / "telemetry" / "logs" / "telemetry.db"
    snapshots_count = 0
    latest_timestamp = None
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path), timeout=2.0)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*), MAX(timestamp) FROM system_snapshots")
            row = cur.fetchone()
            if row:
                snapshots_count = row[0]
                latest_timestamp = row[1]
            conn.close()
        except Exception:
            pass

    # Проверка планировщика заданий Windows
    task_installed = False
    task_state = "NotInstalled"
    wake_to_run = False
    try:
        import subprocess
        ps_cmd = "Get-ScheduledTask -TaskName 'AI-Breadboard-Telemetry' -ErrorAction SilentlyContinue | Select-Object -Property State, @{N='Wake';E={$_.Settings.WakeToRun}} | ConvertTo-Json"
        res = subprocess.run(["powershell.exe", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, timeout=4)
        if res.returncode == 0 and res.stdout.strip():
            task_info = json.loads(res.stdout.strip())
            task_installed = True
            task_state = str(task_info.get("State", "Ready"))
            wake_to_run = bool(task_info.get("Wake", False))
    except Exception:
        pass

    return {
        "is_running": len(running_procs) > 0,
        "processes": running_procs,
        "total_memory_mb": round(total_mem, 1),
        "mode": cfg_mgr.get_mode(),
        "interval_seconds": cfg_mgr.get_interval_seconds(),
        "heavy_interval_seconds": cfg_mgr.get_heavy_interval_seconds(),
        "top_processes": cfg_mgr.get_top_processes(),
        "heavy_collectors": cfg_mgr.get_heavy_collectors(),
        "snapshots_count": snapshots_count,
        "latest_timestamp": latest_timestamp,
        "db_path": str(db_path),
        "task_scheduler": {
            "installed": task_installed,
            "state": task_state,
            "wake_to_run": wake_to_run,
        },
    }


@router.post("/telemetry/control")
async def control_telemetry_service(req: TelemetryControlRequest) -> Dict[str, Any]:
    """Управляет службой телеметрии: start, stop, restart, install-task, uninstall-task."""
    import subprocess

    launcher_path = __root__ / "launchers" / "Run-Telemetry.ps1"
    if not launcher_path.exists():
        raise HTTPException(status_code=500, detail="Лончер Run-Telemetry.ps1 не найден")

    action = req.action.lower()
    valid_actions = ["start", "stop", "restart", "install-task", "uninstall-task"]
    if action not in valid_actions:
        raise HTTPException(status_code=400, detail=f"Недопустимое действие '{action}'. Допустимы: {valid_actions}")

    cmd = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(launcher_path),
        "-Action",
        action,
    ]
    if req.mode:
        cmd.extend(["-Mode", req.mode])
    if req.interval:
        cmd.extend(["-Interval", str(req.interval)])
    if req.heavy_interval:
        cmd.extend(["-HeavyInterval", str(req.heavy_interval)])

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        output_txt = proc.stdout.strip() or proc.stderr.strip()
        return {
            "status": "success" if proc.returncode == 0 else "warning",
            "action": action,
            "returncode": proc.returncode,
            "output": output_txt,
        }
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Ошибка выполнения действия {action}: {ex}")


@router.get("/telemetry/config")
async def get_telemetry_config() -> Dict[str, Any]:
    """Возвращает полную конфигурацию телеметрии."""
    from apps.windows.telemetry.telemetry_config import TelemetryConfigManager
    cfg_mgr = TelemetryConfigManager()
    return {
        "config_file": cfg_mgr.config_path,
        "mode": cfg_mgr.get_mode(),
        "interval_seconds": cfg_mgr.get_interval_seconds(),
        "heavy_interval_seconds": cfg_mgr.get_heavy_interval_seconds(),
        "top_processes": cfg_mgr.get_top_processes(),
        "low_priority": cfg_mgr.is_low_priority(),
        "heavy_collectors": cfg_mgr.get_heavy_collectors(),
        "raw_config": cfg_mgr._config,
    }


@router.post("/telemetry/config")
async def update_telemetry_config(req: TelemetryConfigUpdateRequest) -> Dict[str, Any]:
    """Обновляет и сохраняет конфигурацию телеметрии."""
    from apps.windows.telemetry.telemetry_config import TelemetryConfigManager
    cfg_mgr = TelemetryConfigManager()

    updates = {}
    if req.mode is not None:
        updates["mode"] = req.mode
    if req.interval_seconds is not None:
        updates["interval_seconds"] = req.interval_seconds
    if req.heavy_interval_seconds is not None:
        updates["heavy_interval_seconds"] = req.heavy_interval_seconds
    if req.top_processes is not None:
        updates["top_processes"] = req.top_processes
    if req.low_priority is not None:
        updates["low_priority"] = req.low_priority
    if req.heavy_collectors is not None:
        updates["heavy_collectors"] = req.heavy_collectors

    saved = cfg_mgr.save_config(updates)
    if not saved:
        raise HTTPException(status_code=500, detail="Не удалось сохранить конфигурацию")

    return {
        "status": "success",
        "message": "Конфигурация телеметрии успешно сохранена",
        "config": updates,
    }


def init_router() -> APIRouter:
    """Инициализирует и возвращает экземпляр APIRouter для автологгирования."""
    return router
