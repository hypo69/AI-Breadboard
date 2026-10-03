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
# Updated: 2026-10-04 01:20:00
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

from header import __root__


def _load_config(profile: str | None = None) -> dict:
    """Загружает конфигурационный файл.

    При `profile='tc'` ищет `tc.json` или `config_tc.json` в корне проекта.
    Если задана переменная окружения `CONFIG_FILE`, используется её путь.
    Иначе ищутся типовые файлы в корневой директории.
    Возвращает словарь вида {"config_file": <имя>, "data": <содержимое>}
    """
    if profile in ("tc", "test-computer", "test_computer", "apps_tc"):
        for candidate in [
            __root__ / "start_scenarios_config" / "tc.json",
            __root__ / "config" / "tc.json",
            __root__ / "config_tc.json",
            __root__ / "tc.json",
        ]:
            if candidate.exists():
                return {"config_file": candidate.name, "data": json.loads(candidate.read_text(encoding="utf-8"))}
    env_path = os.getenv("CONFIG_FILE")
    if env_path:
        p = Path(env_path)
        if not p.is_absolute():
            p = __root__ / p
        if p.exists():
            return {"config_file": p.name, "data": json.loads(p.read_text(encoding="utf-8"))}
    # Поиск типовых файлов
    for candidate in [
        __root__ / "start_scenarios_config" / "tc.json",
        __root__ / "config" / "tc.json",
        __root__ / "config_tc.json",
        __root__ / "tc.json",
        __root__ / "config.json",
    ]:
        if candidate.exists():
            return {"config_file": candidate.name, "data": json.loads(candidate.read_text(encoding="utf-8"))}
    return {"config_file": None, "data": {}}

ALIASES_MAP = {
    "windows_sysadmin": {"windows_sysadmin", "windows_admin", "sysadmin", "admin", "windows-sysadmin", "windows-admin", "tab-windows-sysadmin", "tab-windows-admin"},
    "system_control_center": {"system_control_center", "system_control", "control_center", "system-control-center"},
    "system_log_viewer": {"system_log_viewer", "log_viewer", "system_logs", "system-log-viewer"},
    "system_inspector": {"system_inspector", "inspector", "system-inspector"},
    "network_terminal": {"network_terminal", "network", "terminal", "network-terminal"},
    "windows_startup_auditor": {"windows_startup_auditor", "startup_auditor", "startup", "windows-startup-auditor"},
    "software_audit": {"software_audit", "software-audit", "software_transparency_scanner", "transparency_scanner"},
    "registry_viewer": {"registry_viewer", "registry-viewer", "registry"},
    "cloudflared_monitor": {"cloudflared_monitor", "cloudflared", "cloudflared-monitor", "tunnel_monitor"},
    "gcloud_monitor": {"gcloud_monitor", "gcloud", "gcloud-monitor"},
    "website_monitor": {"website_monitor", "website", "web_monitor", "website-monitor"},
    "user_assistant": {"user_assistant", "assistant", "user-assistant"},
    "trading_terminal": {"trading_terminal", "trading", "trading-terminal"},
    "scenarios": {"scenarios", "start_scenarios"},
    "chat": {"chat", "ai_chat"},
}

def _matches_app(name: str, app_id: str) -> bool:
    norm_name = str(name).strip().lower()
    if norm_name in ALIASES_MAP.get(app_id, set()):
        return True
    return norm_name in (app_id, app_id.replace('_', '-'), app_id.replace('windows_', ''), f"tab-{app_id.replace('_', '-')}")

def _build_apps_status(cfg: dict) -> tuple[dict, bool]:
    """Строит статус всех приложений на основе конфигурации.

    Поддерживаемые форматы:
    - dict с `enable_all` (bool) и ``apps`` как dict/list.
    - dict ``apps`` со списками ``enabled`` и ``disabled``.
    - список имён приложений (включаются только они).
    """
    apps_cfg = cfg.get("apps", {})
    if isinstance(apps_cfg, list):
        enable_all = False
    elif isinstance(apps_cfg, dict):
        if "enabled" in apps_cfg and isinstance(apps_cfg["enabled"], list):
            enable_all = False
        elif "enable_all" in apps_cfg and isinstance(apps_cfg["enable_all"], bool):
            enable_all = apps_cfg["enable_all"]
        else:
            enable_all = True
    else:
        enable_all = True

    # Базовый статус: включено/выключено в зависимости от enable_all
    status = {
        app_id: {"key": app_id, "tab": f"tab-{app_id.replace('_', '-')}", "enabled": enable_all}
        for app_id in APPS_REGISTRY
    }
    # Если apps_cfg - список имен
    if isinstance(apps_cfg, list):
        for app_id in status:
            status[app_id]["enabled"] = False
        for name in apps_cfg:
            for app_id in status:
                if _matches_app(name, app_id):
                    status[app_id]["enabled"] = True
        return status, enable_all

    # Если dict
    if isinstance(apps_cfg, dict):
        # Явные списки enabled/disabled
        enabled_set = {str(item).strip().lower() for item in apps_cfg.get("enabled", []) if item}
        disabled_set = {str(item).strip().lower() for item in apps_cfg.get("disabled", []) if item}
        if "enabled" in apps_cfg and isinstance(apps_cfg["enabled"], list):
            # Переопределяем: всё выключено, затем включаем указанные
            for app_id in status:
                status[app_id]["enabled"] = False
            for name in enabled_set:
                for app_id in status:
                    if _matches_app(name, app_id):
                        status[app_id]["enabled"] = True
        # Применяем disabled (приоритет выше)
        for name in disabled_set:
            for app_id in status:
                if _matches_app(name, app_id):
                    status[app_id]["enabled"] = False
        # Прямые булевы флаги для отдельных приложений
        for name, flag in apps_cfg.items():
            if name in ("enable_all", "enabled", "disabled"):
                continue
            if isinstance(flag, bool):
                for app_id in status:
                    if _matches_app(name, app_id):
                        status[app_id]["enabled"] = flag
    return status, enable_all

def get_apps_status(profile: str | None = None) -> dict:
    """Возвращает статус всех приложений и информацию о конфиге."""
    cfg_wrap = _load_config(profile)
    cfg_data = cfg_wrap.get("data", {})
    apps_status, enable_all = _build_apps_status(cfg_data)
    return {
        "status": "ok",
        "config_file": cfg_wrap.get("config_file"),
        "enable_all": enable_all,
        "apps": apps_status,
    }

@router.get('/api/v1/apps/status', tags=["apps"])
async def get_apps_status_endpoint(profile: str | None = None) -> dict:
    """Получение статуса всех приложений по стандарту /api/v1/apps/status."""
    return get_apps_status(profile=profile)


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