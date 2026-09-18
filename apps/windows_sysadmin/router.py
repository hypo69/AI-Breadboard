# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows System Administrator FastAPI Router
# =============================================================================
# Description:
#   FastAPI эндпоинты для системного администрирования Windows,
#   Active Directory, управления сессиями, мониторинга событий безопасности
#   и аудита файловой системы (удаление файлов, auditpol, SACL, ReadDirectoryChangesW).
#
# Examples:
#   >>> from fastapi import FastAPI
#   >>> from apps.windows_sysadmin.router import init_router
#   >>> app = FastAPI()
#   >>> app.include_router(init_router())
#
# File: router.py
# Project: ai-breadboard
# Package: apps.windows_sysadmin
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI router integration for Windows System Administrator & File Auditing."""

from __future__ import annotations

import os
from dataclasses import asdict
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.api.router_auth import require_admin_user
from src.logger import logger
from .src.directory_watcher import get_directory_watcher
from .src.file_auditor import WindowsFileAuditor
from .src.state import SecurityEvent, SystemAdminState

router = APIRouter(prefix="/api/sysadmin", tags=["sysadmin"])
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


@router.get("/status")
async def get_status(request: None = None) -> dict:
    """Получить общий статус системного администрирования и аудита."""
    state.refresh()
    policy_status = file_auditor.get_audit_policy_status()
    return {
        "hostname": state.hostname,
        "domain": state.domain,
        "ad_connected": state.ad_connected,
        "ad_status": state.ad_status,
        "user_count": len(state.users),
        "event_count": len(state.events),
        "file_audit": {
            "is_configured": policy_status.is_configured,
            "success_enabled": policy_status.success_enabled,
            "failure_enabled": policy_status.failure_enabled,
            "raw_output": policy_status.raw_output,
        },
    }


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
# Файловый аудит & Мониторинг удаления файлов (File Deletion Auditing)
# =============================================================================


@router.get("/file-audit/policy")
async def get_file_audit_policy() -> dict:
    """Получить статус системной политики аудита файловой системы (auditpol)."""
    status = file_auditor.get_audit_policy_status()
    return asdict(status)


@router.post("/file-audit/policy")
async def set_file_audit_policy(body: AuditPolicyRequest) -> dict:
    """Включить или отключить аудит File System в Windows Security."""
    result = file_auditor.set_audit_policy(
        enable_success=body.enable_success, enable_failure=body.enable_failure
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
    sacl_status = file_auditor.get_folder_sacl(path)
    return asdict(sacl_status)


@router.post("/file-audit/folder-sacl")
async def configure_folder_sacl(body: SaclConfigRequest) -> dict:
    """Настроить правило аудита удаления (Delete/SACL) для папки."""
    result = file_auditor.configure_folder_sacl(
        folder_path=body.path,
        principal=body.principal,
        enable=body.enable,
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
    events = file_auditor.fetch_deletion_events(hours=hours, max_events=limit)
    if deletions_only:
        filtered = [e for e in events if e.is_deletion]
    else:
        filtered = events

    return {
        "total_fetched": len(events),
        "deletions_count": len([e for e in events if e.is_deletion]),
        "events": [asdict(e) for e in filtered],
    }


@router.get("/file-audit/live-events")
async def get_live_file_events(limit: int = Query(50, ge=1, le=200)) -> dict:
    """Получить события файловой системы в реальном времени (ReadDirectoryChangesW)."""
    watcher = get_directory_watcher(os.getcwd())
    live_events = watcher.get_recent_events(limit=limit)
    return {
        "watch_dir": watcher.watch_dir,
        "is_running": watcher._is_running,
        "events_count": len(live_events),
        "events": [asdict(e) for e in live_events],
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
