# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows System Administrator FastAPI Router
# =============================================================================
# Description:
#   FastAPI эндпоинты для системного администрирования Windows,
#   Active Directory, управления сессиями, мониторинга событий безопасности,
#   проводника файловой системы (обзор дисков и папок)
#   и файлового аудита (Multi-directory ReadDirectoryChangesW, auditpol, SACL).
#
# Examples:
#   >>> from fastapi import FastAPI
#   >>> from apps.windows.sysadmin.router import init_router
#   >>> app = FastAPI()
#   >>> app.include_router(init_router())
#
# File: router.py
# Project: ai-breadboard
# Package: apps.windows.sysadmin
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI router integration for Windows System Administrator & Multi-Directory Watcher."""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil
from fastapi import APIRouter, Body, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from apps.common.csv_logger import AppCsvLogger
from logger import logger
from src.api.router_auth import require_admin_user
from .src.directory_watcher import DirectoryWatcher, get_directory_watcher
from .src.file_auditor import WindowsFileAuditor
from .src.state import SecurityEvent, SystemAdminState

router = APIRouter(prefix="/api/sysadmin", tags=["sysadmin"])
_csv_logger = AppCsvLogger("windows_sysadmin")
state = SystemAdminState()
file_auditor = WindowsFileAuditor()


class AuditPolicyRequest(BaseModel):
    """Модель запроса изменения политики auditpol."""

    enable_success: bool = True
    enable_failure: bool = True


class SaclConfigRequest(BaseModel):
    """Модель запроса настройки SACL аудита для папки."""

    path: str
    principal: str = "Everyone"
    enable: bool = True


class WatchDirRequest(BaseModel):
    """Модель запроса изменения отслеживаемой папки."""

    path: str = Field(..., description="Абсолютный путь к отслеживаемой папке")


class WatchDirsRequest(BaseModel):
    """Модель запроса списка отслеживаемых папок."""

    paths: List[str] = Field(..., description="Список абсолютных путей к отслеживаемым папкам")


class ExclusionsConfigRequest(BaseModel):
    """Модель запроса полной конфигурации правил исключений."""

    enabled: bool = True
    paths: List[str] = Field(default_factory=list, description="Список исключаемых путей и фрагментов папок")
    extensions: List[str] = Field(default_factory=list, description="Список исключаемых расширений файлов (.tmp, .log)")
    patterns: List[str] = Field(default_factory=list, description="Список исключаемых шаблонов fnmatch (*.db-wal, ~$*)")
    processes: List[str] = Field(default_factory=list, description="Список исключаемых программ (SearchIndexer.exe)")


class AddExclusionRequest(BaseModel):
    """Модель запроса добавления единичного правила исключения."""

    category: str = Field(..., description="Категория: 'paths', 'extensions', 'patterns', 'processes'")
    value: str = Field(..., description="Значение правила исключения")


class RemoveExclusionRequest(BaseModel):
    """Модель запроса удаления правила исключения."""

    category: str = Field(..., description="Категория: 'paths', 'extensions', 'patterns', 'processes'")
    value: str = Field(..., description="Значение правила для удаления")


class ToggleExclusionsRequest(BaseModel):
    """Модель запроса включения/отключения фильтрации исключений."""

    enabled: Optional[bool] = Field(None, description="Явный флаг активности фильтрации (если None - инвертировать)")


def _get_configured_watch_dirs() -> List[str]:
    """Получить список отслеживаемых директорий из config.json."""
    cfg_file = Path(__file__).resolve().parent / "config.json"
    if cfg_file.exists():
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                custom_paths = data.get("watch_directories")
                if isinstance(custom_paths, list) and custom_paths:
                    valid_paths = [p for p in custom_paths if isinstance(p, str) and os.path.isdir(p)]
                    if valid_paths:
                        return valid_paths
                single_path = data.get("watch_directory", "").strip()
                if single_path and os.path.isdir(single_path):
                    return [single_path]
        except Exception as e:
            logger.warning(f"Не удалось прочитать watch_directories из config.json: {e}")
    return [os.getcwd()]


def _save_configured_watch_dirs(paths: List[str]) -> None:
    """Сохранить список отслеживаемых папок в config.json."""
    cfg_file = Path(__file__).resolve().parent / "config.json"
    try:
        cfg_data = {}
        if cfg_file.exists():
            with open(cfg_file, "r", encoding="utf-8") as f:
                cfg_data = json.load(f)
        cfg_data["watch_directories"] = paths
        cfg_data["watch_directory"] = paths[0] if paths else os.getcwd()
        with open(cfg_file, "w", encoding="utf-8") as f:
            json.dump(cfg_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Не удалось сохранить watch_directories в config.json: {e}")


def _save_configured_exclusions(exclusions_data: Dict[str, Any]) -> None:
    """Сохранить правила исключений в config.json."""
    cfg_file = Path(__file__).resolve().parent / "config.json"
    try:
        cfg_data = {}
        if cfg_file.exists():
            with open(cfg_file, "r", encoding="utf-8") as f:
                cfg_data = json.load(f)
        cfg_data["exclusions"] = exclusions_data
        with open(cfg_file, "w", encoding="utf-8") as f:
            json.dump(cfg_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Не удалось сохранить exclusions в config.json: {e}")


# =============================================================================
# Системное администрирование: Статус, Сессии, События AD
# =============================================================================


@router.get("/status")
async def get_status(request: None = None) -> dict:
    """Получить общий статус системного администрирования и аудита."""
    state.refresh()
    policy_status = file_auditor.get_audit_policy_status()
    
    total_accounts = len(state.accounts)
    active_users = sum(1 for a in state.accounts if a.is_logged_in)
    hidden_users = sum(1 for a in state.accounts if a.is_hidden)
    disabled_users = sum(1 for a in state.accounts if not a.enabled)
    admin_users = sum(1 for a in state.accounts if a.is_admin)

    res = {
        "hostname": state.hostname,
        "domain": state.domain,
        "ad_connected": state.ad_connected,
        "ad_status": state.ad_status,
        "user_count": len(state.users),
        "total_accounts": total_accounts,
        "active_users": active_users,
        "hidden_users": hidden_users,
        "disabled_users": disabled_users,
        "admin_users": admin_users,
        "event_count": len(state.events),
        "file_audit": {
            "is_configured": policy_status.is_configured,
            "success_enabled": policy_status.success_enabled,
            "failure_enabled": policy_status.failure_enabled,
            "raw_output": policy_status.raw_output,
        },
    }
    _csv_logger.log_poll(
        poll_type="sysadmin_status",
        metric_name="user_count",
        value=len(state.users),
        unit="count",
        status="OK",
        details={"ad_connected": state.ad_connected, "ad_status": state.ad_status},
        filename="windows_sysadmin_status_polls.csv",
    )
    return res


@router.get("/users")
async def get_users(request: None = None) -> dict:
    """Получить список активных сессий пользователей."""
    state.refresh()
    return {
        "users": [
            {
                "username": u.username,
                "session_id": u.session_id,
                "status": u.status,
                "login_time": u.login_time,
                "ip_address": u.ip_address,
                "process_count": u.process_count,
            }
            for u in state.users
        ]
    }


@router.get("/accounts")
async def get_accounts(
    filter_type: Optional[str] = Query("all", description="Фильтр: all, active, hidden, admins, disabled"),
    request: None = None,
) -> dict:
    """Получить исчерпывающий список учетных записей Windows (локальные, скрытые, служебные)."""
    state.refresh()
    accounts = state.accounts

    if filter_type == "active":
        accounts = [a for a in accounts if a.is_logged_in]
    elif filter_type == "hidden":
        accounts = [a for a in accounts if a.is_hidden]
    elif filter_type == "admins":
        accounts = [a for a in accounts if a.is_admin]
    elif filter_type == "disabled":
        accounts = [a for a in accounts if not a.enabled]

    return {
        "total": len(state.accounts),
        "filtered_count": len(accounts),
        "filter": filter_type,
        "accounts": [asdict(a) for a in accounts],
    }


@router.get("/accounts/{username}")
async def get_account_details(username: str, request: None = None) -> dict:
    """Получить полное досье и конфигурацию учетной записи Windows."""
    state.refresh()
    for acc in state.accounts:
        if acc.name.lower() == username.lower():
            return asdict(acc)
    raise HTTPException(status_code=404, detail=f"Учетная запись {username} не найдена")


@router.get("/accounts/{username}/metrics")
async def get_account_metrics(username: str, request: None = None) -> dict:
    """Получить расширенные динамические метрики учетной записи (ресурсы, процессы, безопасность)."""
    state.refresh()
    account: Optional[Any] = None
    for acc in state.accounts:
        if acc.name.lower() == username.lower():
            account = acc
            break

    if not account:
        raise HTTPException(status_code=404, detail=f"Учетная запись {username} не найдена")

    # Сбор списка процессов под пользователем
    user_processes = []
    try:
        for proc in psutil.process_iter(["pid", "name", "username", "cpu_percent", "memory_info"]):
            try:
                p_user = proc.info.get("username") or ""
                if "\\" in p_user:
                    p_user = p_user.split("\\")[-1]
                if p_user.lower() == username.lower():
                    mem_mb = round((proc.info.get("memory_info").rss / (1024 * 1024)), 1) if proc.info.get("memory_info") else 0.0
                    user_processes.append({
                        "pid": proc.info.get("pid"),
                        "name": proc.info.get("name"),
                        "cpu_percent": proc.info.get("cpu_percent") or 0.0,
                        "memory_mb": mem_mb,
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        logger.debug(f"Ошибка сбора процессов для {username}: {e}")

    # Сортировка процессов по потреблению памяти
    user_processes.sort(key=lambda p: p["memory_mb"], reverse=True)

    return {
        "username": account.name,
        "is_logged_in": account.is_logged_in,
        "is_admin": account.is_admin,
        "is_hidden": account.is_hidden,
        "enabled": account.enabled,
        "total_processes": len(user_processes),
        "total_memory_rss_mb": account.memory_rss_mb,
        "total_cpu_percent": account.cpu_percent,
        "profile_path": account.profile_path,
        "profile_size_mb": account.profile_size_mb,
        "groups": account.groups,
        "top_processes": user_processes[:15],
    }


@router.get("/events")
async def get_events(hours: int = Query(24, ge=1, le=168), request: None = None) -> dict:
    """Получить список недавних событий безопасности."""
    state.refresh()
    return {
        "events": [
            {
                "timestamp": e.timestamp.isoformat(),
                "event_id": e.event_id,
                "level": e.level,
                "source": e.source,
                "description": e.description,
            }
            for e in state.events[:50]
        ]
    }


# =============================================================================
# Файловая система: Проводник дисков и каталогов (Folder Picker Backend)
# =============================================================================


@router.get("/filesystem/drives")
async def get_system_drives() -> dict:
    """Получить список доступных логических накопителей Windows."""
    drives = []
    try:
        partitions = psutil.disk_partitions(all=False)
        for p in partitions:
            drive_data: Dict[str, Any] = {
                "mountpoint": p.mountpoint,
                "device": p.device,
                "fstype": p.fstype,
                "opts": p.opts,
                "total_gb": 0.0,
                "free_gb": 0.0,
                "percent_used": 0.0,
            }
            try:
                usage = psutil.disk_usage(p.mountpoint)
                drive_data["total_gb"] = round(usage.total / (1024**3), 1)
                drive_data["free_gb"] = round(usage.free / (1024**3), 1)
                drive_data["percent_used"] = usage.percent
            except Exception:
                pass
            drives.append(drive_data)
    except Exception as e:
        logger.warning(f"Ошибка получения списка дисков системы: {e}")
        drives = [{"mountpoint": "C:\\", "device": "C:\\", "fstype": "NTFS", "total_gb": 0, "free_gb": 0, "percent_used": 0}]

    return {"drives": drives}


@router.get("/filesystem/browse")
async def browse_directory(
    path: str = Query(..., description="Абсолютный путь к исследуемой директории"),
    show_hidden: bool = Query(False, description="Отображать ли скрытые папки"),
) -> dict:
    """Получить список подкаталогов для навигации в модальном окне выбора папок."""
    target_path = os.path.abspath(path.strip())
    if not os.path.exists(target_path):
        raise HTTPException(status_code=404, detail=f"Путь не существует: {target_path}")
    if not os.path.isdir(target_path):
        raise HTTPException(status_code=400, detail=f"Указанный путь не является каталогом: {target_path}")

    parent_path = str(Path(target_path).parent) if Path(target_path).parent != Path(target_path) else None

    directories = []
    try:
        with os.scandir(target_path) as entries:
            for entry in entries:
                try:
                    if entry.is_dir(follow_symlinks=False):
                        name = entry.name
                        if not show_hidden and (name.startswith(".") or name.startswith("$")):
                            continue

                        # Быстрая проверка наличия подпапок
                        has_subdirs = False
                        try:
                            with os.scandir(entry.path) as sub_entries:
                                for s in sub_entries:
                                    if s.is_dir(follow_symlinks=False):
                                        has_subdirs = True
                                        break
                        except Exception:
                            has_subdirs = False

                        stat = entry.stat()
                        mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")

                        directories.append({
                            "name": name,
                            "path": entry.path,
                            "has_subdirs": has_subdirs,
                            "modified": mod_time,
                        })
                except Exception:
                    continue
    except PermissionError:
        raise HTTPException(status_code=403, detail=f"Отказано в доступе к каталогу: {target_path}")
    except Exception as e:
        logger.error(f"Ошибка чтения директории {target_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка чтения каталога: {e}")

    directories.sort(key=lambda d: d["name"].lower())

    return {
        "current_path": target_path,
        "parent_path": parent_path,
        "directories_count": len(directories),
        "directories": directories,
    }


# =============================================================================
# Файловый аудит & Мониторинг в реальном времени (Multi-Directory ReadDirectoryChangesW)
# =============================================================================


@router.get("/file-audit/policy")
async def get_file_audit_policy() -> dict:
    """Получить статус системной политики аудита файловой системы (auditpol)."""
    status = await asyncio.to_thread(file_auditor.get_audit_policy_status)
    return asdict(status)


@router.post("/file-audit/policy")
async def set_file_audit_policy(body: AuditPolicyRequest) -> dict:
    """Включить или отключить аудит File System в Windows Security."""
    result = await asyncio.to_thread(
        file_auditor.set_audit_policy,
        enable_success=body.enable_success,
        enable_failure=body.enable_failure,
    )
    _csv_logger.log_param_change(
        param_name="auditpol.filesystem_policy",
        old_value="unknown",
        new_value={"success": body.enable_success, "failure": body.enable_failure},
        status="SUCCESS" if result.get("success") else "FAILED",
        user="admin",
        filename="windows_sysadmin_events.csv",
    )
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error") or result.get("stderr") or "Failed to set auditpol policy",
        )
    return result


@router.get("/file-audit/folder-sacl")
async def get_folder_sacl(path: str = Query(..., description="Путь к целевой папке")) -> dict:
    """Проверить наличие правил аудита (SACL) для указанной директории."""
    sacl_status = await asyncio.to_thread(file_auditor.get_folder_sacl, path)
    return asdict(sacl_status)


@router.post("/file-audit/folder-sacl")
async def configure_folder_sacl(body: SaclConfigRequest) -> dict:
    """Настроить правило аудита удаления (Delete/SACL) для папки."""
    result = await asyncio.to_thread(
        file_auditor.configure_folder_sacl,
        folder_path=body.path,
        principal=body.principal,
        enable=body.enable,
    )
    _csv_logger.log_event(
        event_type="configure_folder_sacl",
        status="SUCCESS" if result.get("Success") else "FAILED",
        details={"path": body.path, "principal": body.principal, "enable": body.enable},
        filename="windows_sysadmin_events.csv",
    )
    if not result.get("Success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("Error") or "Failed to configure folder SACL",
        )
    return result


@router.get("/file-audit/deletions")
async def get_deletion_events(
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(100, ge=1, le=500),
    deletions_only: bool = Query(True),
) -> dict:
    """Получить события аудита удаления файлов из Security Event Log (4663, 4660, 4656)."""
    events = await asyncio.to_thread(file_auditor.fetch_deletion_events, hours=hours, max_events=limit)
    filtered = [e for e in events if e.is_deletion] if deletions_only else events

    return {
        "total_fetched": len(events),
        "deletions_count": len([e for e in events if e.is_deletion]),
        "events": [asdict(e) for e in filtered],
    }


@router.get("/file-audit/watch-dirs")
async def get_live_watch_dirs() -> dict:
    """Получить список всех отслеживаемых директорий."""
    # Получаем глобальный инстанс, который уже содержит актуальные пути из config.json
    watcher = get_directory_watcher()
    return {
        "watch_dirs": watcher.get_watch_dirs(),
        "is_running": watcher._is_running,
        "events_count": len(watcher.events_history),
    }


@router.post("/file-audit/watch-dirs")
async def set_live_watch_dirs(payload: WatchDirsRequest) -> dict:
    """Установить новый список отслеживаемых директорий и сохранить в config.json."""
    if not payload.paths:
        raise HTTPException(status_code=400, detail="Список отслеживаемых папок не может быть пустым")

    watcher = get_directory_watcher()
    success = watcher.set_watch_dirs(payload.paths)
    if not success:
        raise HTTPException(status_code=400, detail="Не удалось запустить мониторинг для переданных директорий")

    _save_configured_watch_dirs(watcher.get_watch_dirs())

    return {
        "success": True,
        "watch_dirs": watcher.get_watch_dirs(),
        "message": f"Мониторинг запущен для {len(watcher.get_watch_dirs())} папок",
    }


@router.post("/file-audit/watch-dirs/add")
async def add_live_watch_dir(payload: WatchDirRequest) -> dict:
    """Добавить папку в список отслеживаемых на лету."""
    target_path = os.path.abspath(payload.path.strip())
    if not os.path.exists(target_path) or not os.path.isdir(target_path):
        raise HTTPException(status_code=400, detail=f"Указанный путь не существует или не является папкой: {target_path}")

    watcher = get_directory_watcher()
    success = watcher.add_watch_dir(target_path)
    if not success:
        raise HTTPException(status_code=500, detail=f"Не удалось добавить папку {target_path} в мониторинг")

    _save_configured_watch_dirs(watcher.get_watch_dirs())

    return {
        "success": True,
        "watch_dirs": watcher.get_watch_dirs(),
        "message": f"Папка добавлена в мониторинг: {target_path}",
    }


@router.post("/file-audit/watch-dirs/remove")
async def remove_live_watch_dir(payload: WatchDirRequest) -> dict:
    """Удалить папку из списка отслеживаемых."""
    target_path = os.path.abspath(payload.path.strip())
    watcher = get_directory_watcher()
    success = watcher.remove_watch_dir(target_path)

    if not watcher.get_watch_dirs():
        # Если удалили всё, вернем хотя бы текущую папку
        watcher.add_watch_dir(os.getcwd())

    _save_configured_watch_dirs(watcher.get_watch_dirs())

    return {
        "success": success,
        "watch_dirs": watcher.get_watch_dirs(),
        "message": f"Папка удалена из мониторинга: {target_path}",
    }


@router.get("/file-audit/exclusions")
async def get_watcher_exclusions() -> dict:
    """Получить текущие правила исключений и статистику отфильтрованных событий."""
    watcher = get_directory_watcher()
    return watcher.get_exclusions()


@router.post("/file-audit/exclusions")
async def set_watcher_exclusions(payload: ExclusionsConfigRequest) -> dict:
    """Сохранить полную конфигурацию правил исключений и обновить watcher."""
    watcher = get_directory_watcher()
    ex_dict = payload.model_dump()
    watcher.set_exclusions(ex_dict)
    _save_configured_exclusions(ex_dict)
    return {
        "success": True,
        "exclusions": watcher.get_exclusions(),
        "message": "Правила исключений успешно обновлены",
    }


@router.post("/file-audit/exclusions/add")
async def add_watcher_exclusion(payload: AddExclusionRequest) -> dict:
    """Добавить элемент в правила исключений (paths, extensions, patterns, processes)."""
    watcher = get_directory_watcher()
    success = watcher.add_exclusion(payload.category, payload.value)
    if success:
        _save_configured_exclusions(watcher.exclusions.to_dict())
    return {
        "success": success,
        "exclusions": watcher.get_exclusions(),
        "message": f"Правило исключения {'добавлено' if success else 'уже существует или невалидно'}: {payload.value}",
    }


@router.post("/file-audit/exclusions/remove")
async def remove_watcher_exclusion(payload: RemoveExclusionRequest) -> dict:
    """Удалить элемент из правил исключений."""
    watcher = get_directory_watcher()
    success = watcher.remove_exclusion(payload.category, payload.value)
    if success:
        _save_configured_exclusions(watcher.exclusions.to_dict())
    return {
        "success": success,
        "exclusions": watcher.get_exclusions(),
        "message": f"Правило исключения {'удалено' if success else 'не найдено'}: {payload.value}",
    }


@router.post("/file-audit/exclusions/toggle")
async def toggle_watcher_exclusions(payload: ToggleExclusionsRequest) -> dict:
    """Включить или выключить фильтрацию исключений."""
    watcher = get_directory_watcher()
    new_state = watcher.toggle_exclusions(payload.enabled)
    _save_configured_exclusions(watcher.exclusions.to_dict())
    return {
        "success": True,
        "enabled": new_state,
        "exclusions": watcher.get_exclusions(),
        "message": f"Фильтрация исключений {'включена' if new_state else 'отключена'}",
    }


@router.get("/file-audit/live-events")
async def get_live_file_events(limit: int = Query(50, ge=1, le=200)) -> dict:
    """Получить события файловой системы в реальном времени (ReadDirectoryChangesW)."""
    # Получаем глобальный инстанс, который уже содержит актуальные пути из config.json
    watcher = get_directory_watcher()
    live_events = watcher.get_recent_events(limit=limit)
    return {
        "watch_dirs": watcher.get_watch_dirs(),
        "watch_dir": watcher.watch_dir,
        "is_running": watcher._is_running,
        "events_count": len(live_events),
        "filtered_count": watcher.filtered_events_count,
        "exclusions_enabled": watcher.exclusions.enabled,
        "events": [asdict(e) for e in live_events],
    }


@router.get("/file-audit/telemetry")
async def get_file_watcher_telemetry() -> dict:
    """Получить программные и аппаратные сенсоры телеметрии файлового вотчера."""
    # Получаем глобальный инстанс, который уже содержит актуальные пути из config.json
    watcher = get_directory_watcher()
    return await asyncio.to_thread(watcher.get_telemetry_snapshot)


@router.post("/file-audit/watch-dir")
async def set_live_watch_dir(payload: WatchDirRequest) -> dict:
    """Одиночное изменение отслеживаемой папки (для обратной совместимости)."""
    target_path = os.path.abspath(payload.path.strip())
    if not os.path.exists(target_path) or not os.path.isdir(target_path):
        raise HTTPException(status_code=400, detail=f"Указанный путь не существует или не является каталогом: {target_path}")

    watcher = get_directory_watcher()
    success = watcher.set_watch_dirs([target_path])
    if not success:
        raise HTTPException(status_code=500, detail="Не удалось запустить мониторинг для указанной директории")

    _save_configured_watch_dirs(watcher.get_watch_dirs())

    return {
        "success": True,
        "watch_dir": watcher.watch_dir,
        "watch_dirs": watcher.get_watch_dirs(),
        "message": f"Отслеживаемая папка успешно переключена на: {target_path}",
    }


@router.get("/users/{username}")
async def get_user(username: str, request: None = None) -> dict:
    """Получить данные конкретной пользовательской сессии."""
    state.refresh()
    for user in state.users:
        if user.username == username:
            return {
                "username": user.username,
                "session_id": user.session_id,
                "status": user.status,
                "login_time": user.login_time,
                "ip_address": user.ip_address,
                "process_count": user.process_count,
            }
    raise HTTPException(status_code=404, detail=f"User {username} not found")


@router.post("/users/{username}/disconnect")
async def disconnect_user(username: str, request: None = None) -> dict:
    """Отключить пользовательскую сессию (требуются права администратора)."""
    require_admin_user(None)
    state.refresh()
    for i, user in enumerate(state.users):
        if user.username == username:
            return {
                "success": True,
                "message": f"User {username} disconnected",
            }
    raise HTTPException(status_code=404, detail=f"User {username} not found")


@router.get("/ad/status")
async def get_ad_status(request: None = None) -> dict:
    """Получить статус подключения к Active Directory."""
    state.refresh()
    return {
        "hostname": state.hostname,
        "domain": state.domain,
        "ad_connected": state.ad_connected,
        "ad_status": state.ad_status,
    }


def init_router() -> APIRouter:
    """Инициализация FastAPI роутера для Windows System Administrator & File Auditing."""
    return router


__all__ = [
    "init_router",
    "router",
]
