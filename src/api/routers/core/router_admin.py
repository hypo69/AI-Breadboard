# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard API - Router Admin Module
# =============================================================================
# Description:
#   Минимальная реализация роутера router_admin с поддержкой статуса приложений.
#
# Usage Examples:
#   Python API:
#     from src.api.routers.core.router_admin import get_apps_status
#
#     res = get_apps_status()
#     print(res)
#
# File: router_admin.py
# Project: ai-breadboard
# Package: src.api.routers.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

"""Минимальная реализация роутера router_admin с поддержкой статуса приложений."""

from fastapi import APIRouter
import os
import json
from pathlib import Path

router = APIRouter()

# Регистратор приложений: ключи идентифицируют каждое приложение в системе.
# Список основан на приложениях, проверяемых в тестах.
APPS_REGISTRY = {
    "scenarios": {},
    "chat": {},
    "trading_terminal": {},
    "network_terminal": {},
    "system_inspector": {},
    "windows_sysadmin": {},
    "cloudflared_monitor": {},
    "gcloud_monitor": {},
    "website_monitor": {},
    "user_assistant": {},
    "system_control_center": {},
    "system_log_viewer": {},
    "windows_startup_auditor": {},
    "software_audit": {},
    "registry_viewer": {},
    "wikipedia_research": {},
    "helpdesk": {},
    "ai_breadboard_admin": {},
    "enterprise_knowledge": {}
}

def _load_config(profile: str | None = None) -> dict:
    """Загружает конфигурационный файл.

    При `profile='tc'` ищет `tc.json` или `config_tc.json` в корне проекта.
    Если задана переменная окружения `CONFIG_FILE`, используется её путь.
    Иначе ищутся типовые файлы в корневой директории.
    Возвращает словарь вида {"config_file": <имя>, "data": <содержимое>}
    """
    # Корень проекта (директория, где находится main.py)
    project_root = Path(__file__).parents[3]
    if profile == "tc":
        for name in ("tc.json", "config_tc.json"):
            p = project_root / name
            if p.exists():
                return {"config_file": p.name, "data": json.loads(p.read_text(encoding="utf-8"))}
    env_path = os.getenv("CONFIG_FILE")
    if env_path:
        p = Path(env_path)
        if not p.is_absolute():
            p = project_root / p
        if p.exists():
            return {"config_file": p.name, "data": json.loads(p.read_text(encoding="utf-8"))}
    # Поиск типовых файлов
    for name in ("config_tc.json", "tc.json", "config.json"):
        p = project_root / name
        if p.exists():
            return {"config_file": p.name, "data": json.loads(p.read_text(encoding="utf-8"))}
    return {"config_file": None, "data": {}}

def _build_apps_status(cfg: dict) -> dict:
    """Строит статус всех приложений на основе конфигурации.

    Поддерживаемые форматы:
    - dict с `enable_all` (bool) и ``apps`` как dict/list.
    - dict ``apps`` со списками ``enabled`` и ``disabled``.
    - список имён приложений (включаются только они).
    """
    apps_cfg = cfg.get("apps", {})
    enable_all = apps_cfg.get("enable_all", True)
    # Базовый статус: включено/выключено в зависимости от enable_all
    status = {
        app_id: {"key": app_id, "tab": f"tab-{app_id}", "enabled": enable_all}
        for app_id in APPS_REGISTRY
    }
    # Если apps_cfg - список имен
    if isinstance(apps_cfg, list):
        for app_id in status:
            status[app_id]["enabled"] = False
        for name in apps_cfg:
            if name in status:
                status[name]["enabled"] = True
        return status
    # Если dict
    if isinstance(apps_cfg, dict):
        # Явные списки enabled/disabled
        enabled_set = set(apps_cfg.get("enabled", []))
        disabled_set = set(apps_cfg.get("disabled", []))
        if enabled_set:
            # Переопределяем: всё выключено, затем включаем указанные
            for app_id in status:
                status[app_id]["enabled"] = False
            for name in enabled_set:
                if name in status:
                    status[name]["enabled"] = True
        # Применяем disabled (приоритет выше)
        for name in disabled_set:
            if name in status:
                status[name]["enabled"] = False
        # Прямые булевы флаги для отдельных приложений
        for name, flag in apps_cfg.items():
            if name in ("enable_all", "enabled", "disabled"):
                continue
            if isinstance(flag, bool) and name in status:
                status[name]["enabled"] = flag
    return status

def get_apps_status(profile: str | None = None) -> dict:
    """Возвращает статус всех приложений и информацию о конфиге.

    Структура возвращаемого словаря:
    {
        "status": "ok",
        "config_file": <имя файла> | None,
        "enable_all": <bool>,
        "apps": {<app_id>: {"key": ..., "tab": ..., "enabled": <bool>}, ...}
    }
    """
    cfg_wrap = _load_config(profile)
    cfg_data = cfg_wrap.get("data", {})
    apps_status = _build_apps_status(cfg_data)
    return {
        "status": "ok",
        "config_file": cfg_wrap.get("config_file"),
        "enable_all": cfg_data.get("apps", {}).get("enable_all", True),
        "apps": apps_status,
    }

@router.get('/router_admin/ping', tags=["router_admin"])
async def ping() -> dict:
    """Проверка доступности роутера."""
    return {"status": "ok"}

def init_router() -> APIRouter:
    """Инициализация и возврат роутера."""
    return router

def init_skills_router() -> APIRouter:
    """Инициализация под‑роутера init_skills_router."""
    sub_router = APIRouter()

    @sub_router.get('/router_admin/init_skills_router/ping')
    async def sub_ping() -> dict:
        return {"status": "ok"}
    return sub_router

def init_plugins_router() -> APIRouter:
    """Инициализация под‑роутера init_plugins_router."""
    sub_router = APIRouter()

    @sub_router.get('/router_admin/init_plugins_router/ping')
    async def sub_ping() -> dict:
        return {"status": "ok"}
    return sub_router

def init_apps_router() -> APIRouter:
    """Инициализация под‑роутера init_apps_router."""
    sub_router = APIRouter()

    @sub_router.get('/router_admin/init_apps_router/ping')
    async def sub_ping() -> dict:
        return {"status": "ok"}
    return sub_router

def init_user_storage_router() -> APIRouter:
    """Инициализация под‑роутера init_user_storage_router."""
    sub_router = APIRouter()

    @sub_router.get('/router_admin/init_user_storage_router/ping')
    async def sub_ping() -> dict:
        return {"status": "ok"}
    return sub_router

def init_sync_router() -> APIRouter:
    """Инициализация под‑роутера init_sync_router."""
    sub_router = APIRouter()

    @sub_router.get('/router_admin/init_sync_router/ping')
    async def sub_ping() -> dict:
        return {"status": "ok"}
    return sub_router

__all__ = ["router", "init_router", "get_apps_status", "APPS_REGISTRY"]