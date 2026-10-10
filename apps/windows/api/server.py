# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows API - Server & Router Auto-Discovery
# =============================================================================
# Description:
#   Слой 7: FastAPI сервер и механизм динамического Auto-Discovery роутеров.
#
# Usage Examples:
#   Python API:
#     from apps.windows.api.server import create_app, discover_and_register_routers
#
# File: server.py
# Project: ai-breadboard
# Package: apps.windows.api
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 12:41:00
# =============================================================================

from __future__ import annotations
"""FastAPI серверная фабрика и автоматическое обнаружение REST API роутеров."""

import importlib
import json
import os
import pkgutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, APIRouter, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from logger import logger
from apps.windows.api.config_helper import save_ai_config, resolve_active_config_path

# Пути к статике и конфигурации
_MODULE_DIR = Path(__file__).resolve().parent
_CONFIG_PATH = _MODULE_DIR / "config.json"
_WEBGUI_DIR = _MODULE_DIR / "webgui"
_TC_INDEX = _WEBGUI_DIR / "apps" / "index.html"
_PROJECT_ROOT = _MODULE_DIR.parents[2]


def load_config() -> Dict[str, Any]:
    """Загружает конфигурацию сервиса из config.json."""
    if _CONFIG_PATH.is_file():
        try:
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            logger.warning(f"[API Server] Ошибка чтения конфигурации {_CONFIG_PATH}: {exc}")
    return {}


def load_tc_config(profile: Optional[str] = None) -> Dict[str, Any]:
    """Загрузка конфигурации для Test Computer / Windows App.

    Args:
        profile: Имя профиля конфигурации (например tc, su).

    Returns:
        Dict[str, Any]: Словарь с параметрами конфигурации.
    """
    candidates: List[Path] = []

    if profile:
        candidates.append(_PROJECT_ROOT / "start_scenarios_config" / f"{profile}.json")
        candidates.append(_PROJECT_ROOT / "config" / f"{profile}.json")

    env_cfg = os.getenv("AIBREADBOARD_CONFIG") or os.getenv("CONFIG_FILE")
    if env_cfg:
        p = Path(env_cfg)
        candidates.append(p if p.is_absolute() else _PROJECT_ROOT / p)
        candidates.append(_PROJECT_ROOT / "start_scenarios_config" / p.name)

    candidates.extend([
        _PROJECT_ROOT / "start_scenarios_config" / "tc.json",
        _PROJECT_ROOT / "start_scenarios_config" / "su.json",
        _PROJECT_ROOT / "config" / "tc.json",
        _PROJECT_ROOT / "config_tc.json",
        _MODULE_DIR.parent / "config.json",
        _CONFIG_PATH,
        _PROJECT_ROOT / "config.json",
    ])

    for cand in candidates:
        if cand.exists() and cand.is_file():
            try:
                with open(cand, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
            except Exception as exc:
                logger.warning(f"[API Server] Ошибка чтения конфигурации {cand}: {exc}")

    return {}


def discover_and_register_routers(app: FastAPI, package_path: str = "apps.windows") -> None:
    """Динамическое сканирование и подсоединение REST API роутеров."""
    try:
        package = importlib.import_module(package_path)
    except Exception as err:
        logger.error(f"[AutoDiscovery] Не удалось импортировать базовый пакет {package_path}: {err}")
        return

    if not hasattr(package, "__path__"):
        return

    for _, module_name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        if (
            module_name.endswith(".router")
            or "routers.router_" in module_name
            or module_name.endswith(".router_capabilities")
            or module_name.endswith(".system_inspector_router")
            or module_name.endswith(".router_process_activity")
        ):
            try:
                mod = importlib.import_module(module_name)
                router = getattr(mod, "router", None)
                if router is None and hasattr(mod, "init_router"):
                    try:
                        router = mod.init_router()
                    except Exception:
                        pass
                if isinstance(router, APIRouter):
                    if router not in app.routes:
                        app.include_router(router)
                        logger.debug(f"[AutoDiscovery] Успешно зарегистрирован роутер: {module_name}")
            except Exception as router_err:
                logger.warning(f"[AutoDiscovery] Пропуск роутера {module_name} из-за ошибки: {router_err}")


def create_app() -> FastAPI:
    """Создаёт и конфигурирует масштабируемый FastAPI-сервис Windows API с Auto-Discovery."""
    config = load_config()
    server_cfg = config.get("server", {})

    app = FastAPI(
        title=server_cfg.get("title", "AI-Breadboard Windows Internal API"),
        description=server_cfg.get("description", "Сервис TC/Windows: телеметрия, дашборды, диагностика."),
        version="2.0.0",
        docs_url="/docs",
        redoc_url=None,
        openapi_url="/openapi.json",
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1",
            "https://127.0.0.1",
            "http://localhost",
            "https://localhost",
        ],
        allow_origin_regex=r"https?://(127\.0\.0\.1|localhost)(:\d+)?",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 1. Сначала регистрируем явно сконфигурированные роутеры из config.json (для кастомных параметров)
    routers_list: List[Dict[str, Any]] = config.get("routers", [])
    registered_modules = set()
    
    # Создаем экземпляры моделей один раз для всех роутеров, которым они нужны
    chat_model: Optional[Any] = None
    narrator_model: Optional[Any] = None
    
    try:
        from src.ai.orchestration.unified_chat import UnifiedChatModel
        tc_cfg = load_tc_config()
        ai_cfg_sec = tc_cfg.get("ai_providers_and_models_configuration") or tc_cfg.get("ai") or {}
        default_provider = ai_cfg_sec.get("default_provider", "")
        default_model = ai_cfg_sec.get("default_model", "")
        if not default_provider:
            default_provider = "gemini"
        if not default_model:
            providers = ai_cfg_sec.get("providers", {})
            if isinstance(providers, dict) and default_provider in providers:
                default_model = providers[default_provider].get("default_model") or providers[default_provider].get("model", "")
        if not default_model:
            default_model = "gemini-3.1-flash-lite"

        chat_model = UnifiedChatModel(provider=default_provider, model=default_model)
        if ai_cfg_sec.get("enable_narrator", False):
            narrator_model = UnifiedChatModel(provider=default_provider, model=default_model)
        else:
            narrator_model = None
    except Exception as model_err:
        logger.warning(f"[API Server] Не удалось инициализировать модели: {model_err}")
    
    for entry in routers_list:
        if not entry.get("enabled", True):
            continue
        module_path = entry.get("module")
        if not module_path:
            continue
        factory_name = entry.get("factory", "init_router")
        kwargs = dict(entry.get("kwargs") or {})
        if entry.get("inject_app"):
            kwargs["app"] = app
            kwargs.setdefault("state", None)
        if entry.get("inject_models"):
            kwargs["chat_model"] = chat_model
            kwargs["narrator_model"] = narrator_model

        try:
            mod = importlib.import_module(module_path)
            factory = getattr(mod, factory_name)
            router = factory(**kwargs)
            if isinstance(router, APIRouter):
                app.include_router(router)
                registered_modules.add(module_path)
        except Exception as exc:
            logger.warning(f"[API Server] Ошибка регистрации роутера {module_path}: {exc}")

    # 2. Затем выполняем динамическое обнаружение (Auto-Discovery) для всех модулей apps.windows
    discover_and_register_routers(app, "apps.windows")

    # -------------------------------------------------------------------------
    # Системные и UI точки входа
    # -------------------------------------------------------------------------
    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon() -> Response:
        """Отдача иконки favicon.ico."""
        fav_candidates = [
            _WEBGUI_DIR / "favicon.ico",
            _WEBGUI_DIR / "assets" / "favicon.ico",
        ]
        for fav in fav_candidates:
            if fav.exists() and fav.is_file():
                return FileResponse(fav)
        return Response(status_code=204)

    # TC UI точка входа
    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    @app.get("/tc", response_class=HTMLResponse, include_in_schema=False)
    @app.get("/tc/", response_class=HTMLResponse, include_in_schema=False)
    @app.get("/apps", response_class=HTMLResponse, include_in_schema=False)
    @app.get("/apps/", response_class=HTMLResponse, include_in_schema=False)
    @app.get("/su", response_class=HTMLResponse, include_in_schema=False)
    @app.get("/su/", response_class=HTMLResponse, include_in_schema=False)
    async def tc_index() -> Response:
        """Возвращает главную HTML-страницу Test Computer интерфейса."""
        if _TC_INDEX.exists():
            return FileResponse(
                _TC_INDEX,
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                },
            )
        return HTMLResponse("<h1>TC WebGUI (apps/index.html) not found</h1>", status_code=404)

    # Health-check
    @app.get("/health", tags=["system"])
    @app.get("/internal/health", tags=["system"], include_in_schema=False)
    async def health() -> dict:
        return {
            "status": "ok",
            "service": "windows-internal-api",
            "webgui_dir": str(_WEBGUI_DIR),
            "webgui_exists": _WEBGUI_DIR.exists(),
            "tc_index_exists": _TC_INDEX.exists(),
            "configured_routers_count": len(routers_list),
        }

    # -------------------------------------------------------------------------
    # Эндпоинты статусов приложений и настроек ИИ
    # -------------------------------------------------------------------------
    @app.get("/api/v1/apps/status", tags=["apps"])
    @app.get("/api/apps/status", tags=["apps"])
    async def get_apps_status(profile: Optional[str] = None) -> Dict[str, Any]:
        """Возвращает статус доступности приложений для формирования меню."""
        cfg = load_tc_config(profile)
        apps_sec = cfg.get("apps", {})
        enabled_list = apps_sec.get("enabled", []) if isinstance(apps_sec, dict) else []
        disabled_list = apps_sec.get("disabled", []) if isinstance(apps_sec, dict) else []

        apps_map: Dict[str, Dict[str, Any]] = {}
        for item in enabled_list:
            apps_map[item] = {"enabled": True, "name": item}
        for item in disabled_list:
            apps_map[item] = {"enabled": False, "name": item}

        ai_config = cfg.get("ai", {})
        if not ai_config:
            global_cfg = load_tc_config()
            ai_config = global_cfg.get("ai", {})

        return {
            "status": "ok",
            "apps": apps_map,
            "ai": ai_config,
        }

    @app.get("/auth/settings", tags=["auth"])
    @app.get("/api/v1/auth/settings", tags=["auth"])
    async def get_user_settings(request: Request) -> Dict[str, Any]:
        """Чтение активных настроек пользователя и модели."""
        try:
            from src.user_manager import user_manager
            settings = user_manager.get_user_settings(1) or {}
        except Exception:
            settings = {}

        if not settings.get("model"):
            cfg = load_tc_config()
            ai_sec = cfg.get("ai_providers_and_models_configuration") or cfg.get("ai", {})
            prov = ai_sec.get("default_provider") or ai_sec.get("provider", "gemini")
            model = ai_sec.get("default_model") or (ai_sec.get(prov, {}).get("model", "") if isinstance(ai_sec.get(prov), dict) else "")
            settings.setdefault("model", f"{prov}:{model}" if model else (model or prov))
            settings.setdefault("provider", prov)

        settings.setdefault("status", "ok")
        settings.setdefault("favorite_models", {})
        return settings

    @app.post("/auth/settings", tags=["auth"])
    @app.post("/api/v1/auth/settings", tags=["auth"])
    async def update_user_settings(request: Request) -> Dict[str, Any]:
        """Сохранение активной модели пользователя."""
        try:
            body = await request.json()
            try:
                from src.user_manager import user_manager
                user_manager.update_user_settings(
                    1,
                    theme=body.get("theme"),
                    language=body.get("language"),
                    tts_enabled=body.get("tts_enabled"),
                    system_instruction=body.get("system_instruction"),
                    model=body.get("model"),
                    tts_system=body.get("tts_system"),
                    tts_voice=body.get("tts_voice"),
                    rag_enabled=body.get("rag_enabled"),
                )
            except Exception:
                pass

            if body.get("model") or body.get("provider"):
                save_ai_config(provider=body.get("provider", ""), model_name=body.get("model", ""))

            return {"status": "ok", "saved": body}
        except Exception:
            return {"status": "ok"}

    @app.get("/api/v1/chat/active-model", tags=["chat"])
    @app.get("/api/v1/tc/model", tags=["chat"])
    async def get_chat_active_model(profile: Optional[str] = None) -> Dict[str, Any]:
        """Возвращает активную модель ИИ."""
        try:
            from src.user_manager import user_manager
            settings = user_manager.get_user_settings(1) or {}
            if settings.get("model"):
                user_model = settings.get("model")
                if ":" in user_model:
                    prov, mod = user_model.split(":", 1)
                elif user_model.startswith("agy-"):
                    prov, mod = "agy", user_model
                else:
                    prov, mod = "gemini", user_model
                return {"status": "ok", "provider": prov, "model": mod, "config_file": "user_settings"}
        except Exception:
            pass

        cfg = load_tc_config(profile)
        ai_sec = cfg.get("ai_providers_and_models_configuration") or cfg.get("ai", {})
        prov = ai_sec.get("default_provider") or ai_sec.get("provider", "gemini")
        model = ai_sec.get("default_model") or (ai_sec.get(prov, {}).get("model", "") if isinstance(ai_sec.get(prov), dict) else "")
        if not model and isinstance(ai_sec.get("providers"), dict) and prov in ai_sec["providers"]:
            model = ai_sec["providers"][prov].get("model", "")
        return {"status": "ok", "provider": prov, "model": model or "gemini-3.1-flash-lite", "config_file": "tc.json"}

    @app.get("/api/v1/chat/models", tags=["chat"])
    async def get_available_chat_models() -> Dict[str, Any]:
        """Список доступных моделей ИИ для дропдауна."""
        try:
            from src.ai.model_manager import get_available_models
            return {
                "models": {
                    "gemini": get_available_models("gemini") or ["gemini-3.1-flash-lite", "gemini-3.1-flash"],
                    "gemini_cli": get_available_models("gemini_cli") or ["gemini_cli:gemini-3.1-flash-lite"],
                    "agy": get_available_models("agy") or ["agy-gemini-3.6-flash"],
                    "foundry": get_available_models("foundry") or ["foundry:qwen2.5-1.5b"],
                    "ollama": get_available_models("ollama") or ["ollama:llama3.1"],
                }
            }
        except Exception:
            return {
                "models": {
                    "gemini": ["gemini-3.1-flash-lite", "gemini-3.1-flash"],
                    "gemini_cli": ["gemini_cli:gemini-3.1-flash-lite"],
                    "agy": ["agy-gemini-3.6-flash"],
                }
            }

    @app.get("/api/admin/system_instruction", tags=["admin"])
    @app.get("/api/v1/admin/system_instruction", tags=["admin"])
    @app.get("/api/v1/tc/model-instruction", tags=["admin"])
    async def get_system_instruction_fallback() -> Dict[str, Any]:
        """Получение системной инструкции."""
        try:
            from src.user_manager import user_manager
            settings = user_manager.get_user_settings(1) or {}
            if settings.get("system_instruction") or settings.get("tc_system_instruction"):
                return {"status": "success", "content": settings.get("system_instruction") or settings.get("tc_system_instruction")}
        except Exception:
            pass
        prompt_file = _PROJECT_ROOT / "prompts" / "tc" / "system_instruction.md"
        if not prompt_file.exists():
            prompt_file = _PROJECT_ROOT / "prompts" / "chat" / "system_instruction.md"
        if prompt_file.exists():
            try:
                return {"status": "success", "content": prompt_file.read_text(encoding="utf-8", errors="replace")}
            except Exception:
                pass
        return {"status": "success", "content": "Вы — интеллектуальный ассистент платформы AI Breadboard."}

    @app.post("/api/admin/system_instruction", tags=["admin"])
    @app.post("/api/v1/admin/system_instruction", tags=["admin"])
    @app.post("/api/v1/tc/model-instruction", tags=["admin"])
    async def set_system_instruction_fallback(request: Request) -> Dict[str, Any]:
        """Сохранение системной инструкции."""
        try:
            body = await request.json()
            content = body.get("content") or body.get("instruction") or body.get("system_instruction") or ""
            if content:
                try:
                    from src.user_manager import user_manager
                    user_manager.update_user_settings(1, system_instruction=content, tc_system_instruction=content)
                except Exception:
                    pass
                prompt_file = _PROJECT_ROOT / "prompts" / "tc" / "system_instruction.md"
                prompt_file.parent.mkdir(parents=True, exist_ok=True)
                prompt_file.write_text(content, encoding="utf-8")
            return {"status": "success", "content": content}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    # Статические файлы TC
    if _WEBGUI_DIR.exists():
        app.mount("/webinterface", StaticFiles(directory=_WEBGUI_DIR), name="tc-webinterface")
        app.mount("/html", StaticFiles(directory=_WEBGUI_DIR), name="tc-html")
        if (_WEBGUI_DIR / "apps").exists():
            app.mount("/apps/static", StaticFiles(directory=_WEBGUI_DIR / "apps"), name="tc-apps-static")

    return app


# Алиас для совместимости
create_internal_app = create_app

__all__ = [
    "create_app",
    "create_internal_app",
    "discover_and_register_routers",
    "load_config",
    "load_tc_config",
]
