# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI Breadboard Admin FastAPI Router
# =============================================================================
# Description:
#   FastAPI роутер приложения администратора: эндпоинты для управления системными
#   настройками, инструкциями чата, версионированием, источниками и пользователями.
#
# Examples:
#   >>> from fastapi import FastAPI
#   >>> from apps.ai_breadboard_admin.router import init_router
#   >>> app = FastAPI()
#   >>> app.include_router(init_router())
#
# File: router.py
# Project: AI-Breadboard
# Package: apps.ai_breadboard_admin
# Module: router
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from apps.ai_breadboard_admin.src import (
    AdminConfigManager,
    InstructionsManager,
    SourcesManager,
    UserAdminService,
    WindowsUserManager,
)
from src.logger import logger
from apps.common.csv_logger import AppCsvLogger

router = APIRouter(prefix="/api/v1/ai_breadboard_admin", tags=["ai_breadboard_admin"])
_csv_logger = AppCsvLogger("ai_breadboard_admin")

config_mgr = AdminConfigManager()
instructions_mgr = InstructionsManager()
sources_mgr = SourcesManager()
user_svc = UserAdminService()



def _check_admin_auth(request: Request) -> bool:
    """Проверка прав доступа администратора к эндпоинтам управления.

    Args:
        request (Request): Объект входящего HTTP-запроса FastAPI.

    Returns:
        bool: True, если доступ разрешен.

    Exceptions:
        HTTPException: 401 при отсутствии авторизации, 403 при недостатке прав.
    """
    from src.api.router_auth import is_auth_disabled
    if is_auth_disabled():
        return True

    if request.cookies.get("admin_password_verified") == "true":
        return True

    from src.api.router_auth import verify_jwt_token
    token: str = request.cookies.get("auth_token", "")
    if not token:
        auth_header: str = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    if token:
        user_data = verify_jwt_token(token)
        if user_data:
            from src.user_manager import user_manager
            db_user = user_manager.get_user_by_email(user_data.email)
            if db_user and (db_user.get("is_admin", 0) or db_user.get("role") == "admin"):
                return True
            raise HTTPException(status_code=403, detail="Доступ разрешен только администраторам")

    raise HTTPException(status_code=401, detail="Требуется авторизация администратора")


# ============================================================================
# Модели Pydantic
# ============================================================================

class RagModeRequest(BaseModel):
    mode: str


class WebSearchConfigRequest(BaseModel):
    engine: str
    gemini_model: str = "gemini-2.5-flash"
    gemini_cli_model: str = "gemini-3.1-flash-lite"
    agy_model: str = "agy-flash"


class WebSearchTestRequest(BaseModel):
    query: str
    engine: str = ""


class AppConfigUpdateRequest(BaseModel):
    config: Dict[str, Any]


class InstructionSaveRequest(BaseModel):
    mode: str
    content: str


class InstructionActivateRequest(BaseModel):
    mode: str
    filename: str


class AdminUserCreateRequest(BaseModel):
    email: str
    name: str
    password: str = ""
    role: str = "user"
    is_admin: int = 0
    is_active: int = 1
    is_email_verified: int = 1


class AdminUserUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_admin: Optional[int] = None
    is_active: Optional[int] = None
    is_email_verified: Optional[int] = None
    telegram_id: Optional[int] = None
    telegram_username: Optional[str] = None


class AdminUserPasswordRequest(BaseModel):
    password: str


class OrphanedDirsCleanRequest(BaseModel):
    dirs: Optional[List[str]] = None


class RawSourcesUpdate(BaseModel):
    content: str


# ============================================================================
# Статус и Общая информация
# ============================================================================

@router.get("/status")
async def get_admin_status(request: Request) -> Dict[str, Any]:
    """Получение агрегированного статуса системы и модулей администратора."""
    _check_admin_auth(request)
    users_data = user_svc.get_users_list()
    rag_cfg = config_mgr.get_rag_config()
    search_cfg = config_mgr.get_web_search_config()

    res = {
        "status": "ok",
        "service": "ai_breadboard_admin",
        "rag_mode": rag_cfg.get("mode"),
        "search_engine": search_cfg.get("engine"),
        "total_users": users_data.get("stats", {}).get("total", 0),
        "active_users": users_data.get("stats", {}).get("active", 0),
    }
    _csv_logger.log_poll(
        poll_type="admin_status",
        metric_name="total_users",
        value=res["total_users"],
        unit="count",
        status="OK",
        details={"rag_mode": res["rag_mode"], "search_engine": res["search_engine"], "active_users": res["active_users"]},
        filename="admin_status_polls.csv",
    )
    return res


# ============================================================================
# Управление конфигурацией RAG и Поиска
# ============================================================================

@router.get("/config/rag")
async def get_rag_settings(request: Request) -> Dict[str, str]:
    """Получение конфигурации режима RAG."""
    _check_admin_auth(request)
    return config_mgr.get_rag_config()


@router.post("/config/rag")
async def set_rag_settings(data: RagModeRequest, request: Request) -> Dict[str, Any]:
    """Установка конфигурации режима RAG."""
    _check_admin_auth(request)
    old_cfg = config_mgr.get_rag_config()
    old_mode = old_cfg.get("mode")
    success = config_mgr.set_rag_config(data.mode)
    _csv_logger.log_param_change(
        param_name="rag.mode",
        old_value=old_mode,
        new_value=data.mode,
        status="SUCCESS" if success else "FAILED",
        user="admin",
        filename="admin_config_param_changes.csv",
    )
    if not success:
        raise HTTPException(status_code=500, detail="Не удалось сохранить параметры RAG")
    return {"status": "ok", "mode": data.mode}


@router.get("/config/web-search")
async def get_web_search_settings(request: Request) -> Dict[str, str]:
    """Получение параметров веб-поиска."""
    _check_admin_auth(request)
    return config_mgr.get_web_search_config()


@router.post("/config/web-search")
async def set_web_search_settings(data: WebSearchConfigRequest, request: Request) -> Dict[str, Any]:
    """Установка параметров веб-поиска."""
    _check_admin_auth(request)
    old_cfg = config_mgr.get_web_search_config()
    success = config_mgr.set_web_search_config(
        engine=data.engine,
        gemini_model=data.gemini_model,
        gemini_cli_model=data.gemini_cli_model,
        agy_model=data.agy_model,
    )
    _csv_logger.log_param_change(
        param_name="web_search.config",
        old_value=old_cfg,
        new_value=data.model_dump(),
        status="SUCCESS" if success else "FAILED",
        user="admin",
        filename="admin_config_param_changes.csv",
    )
    if not success:
        raise HTTPException(status_code=500, detail="Не удалось сохранить настройки поиска")
    return {"status": "ok", "config": data.model_dump()}


@router.get("/config/apps/{app_name}")
async def get_app_settings(app_name: str, request: Request) -> Dict[str, Any]:
    """Получение конфигурации конкретного микроприложения из /apps."""
    _check_admin_auth(request)
    cfg = config_mgr.get_app_config(app_name)
    if cfg is None:
        raise HTTPException(status_code=404, detail=f"Конфигурация приложения '{app_name}' не найдена")
    return {"status": "ok", "app": app_name, "config": cfg}


@router.post("/config/apps/{app_name}")
async def set_app_settings(app_name: str, data: AppConfigUpdateRequest, request: Request) -> Dict[str, Any]:
    """Обновление конфигурации микроприложения из /apps."""
    _check_admin_auth(request)
    old_cfg = config_mgr.get_app_config(app_name)
    success = config_mgr.set_app_config(app_name, data.config)
    _csv_logger.log_param_change(
        param_name=f"apps.{app_name}.config",
        old_value=old_cfg,
        new_value=data.config,
        status="SUCCESS" if success else "FAILED",
        user="admin",
        filename="admin_config_param_changes.csv",
    )
    if not success:
        raise HTTPException(status_code=500, detail=f"Не удалось сохранить конфигурацию для '{app_name}'")
    return {"status": "ok", "app": app_name, "config": data.config}



# ============================================================================
# Системные инструкции и промпты
# ============================================================================

@router.get("/instructions")
async def get_system_instruction(request: Request, mode: str = "chat") -> Dict[str, str]:
    """Получение текста активной системной инструкции."""
    _check_admin_auth(request)
    try:
        return instructions_mgr.get_instruction(mode)
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))


@router.post("/instructions/save")
async def save_system_instruction(data: InstructionSaveRequest, request: Request) -> Dict[str, Any]:
    """Сохранение новой версии инструкции и обновление активной."""
    _check_admin_auth(request)
    try:
        res = instructions_mgr.save_instruction(data.mode, data.content)
        _csv_logger.log_param_change(
            param_name=f"instruction.{data.mode}",
            old_value="(previous_version)",
            new_value=data.content[:100] + "...",
            status="SUCCESS",
            user="admin",
            details={"version_file": res.get("version_file")},
            filename="admin_instruction_param_changes.csv",
        )
        # Динамическое обновление активной модели в памяти
        if data.mode == "chat" and hasattr(request.app.state, "chat_model") and request.app.state.chat_model:
            request.app.state.chat_model.update_system_instruction(data.content)
        elif data.mode == "narrator" and hasattr(request.app.state, "narrator_model") and request.app.state.narrator_model:
            request.app.state.narrator_model.update_system_instruction(data.content)
        return res
    except ValueError as ex:
        _csv_logger.log_event("instruction_save_error", status="FAILED", details=str(ex), filename="admin_instruction_param_changes.csv")
        raise HTTPException(status_code=400, detail=str(ex))


@router.get("/instructions/versions")
async def get_instruction_versions_list(request: Request, mode: str = "chat") -> Dict[str, Any]:
    """Получение списка сохраненных версий инструкций."""
    _check_admin_auth(request)
    try:
        return instructions_mgr.list_versions(mode)
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))


@router.post("/instructions/activate")
async def activate_instruction_version(data: InstructionActivateRequest, request: Request) -> Dict[str, Any]:
    """Активация выбранной сохраненной версии инструкции."""
    _check_admin_auth(request)
    try:
        res = instructions_mgr.activate_version(data.mode, data.filename)
        content = res.get("content", "")
        _csv_logger.log_param_change(
            param_name=f"instruction.{data.mode}.active_version",
            old_value="",
            new_value=data.filename,
            status="SUCCESS",
            user="admin",
            filename="admin_instruction_param_changes.csv",
        )
        if data.mode == "chat" and hasattr(request.app.state, "chat_model") and request.app.state.chat_model:
            request.app.state.chat_model.update_system_instruction(content)
        elif data.mode == "narrator" and hasattr(request.app.state, "narrator_model") and request.app.state.narrator_model:
            request.app.state.narrator_model.update_system_instruction(content)
        return res
    except FileNotFoundError as ex:
        raise HTTPException(status_code=404, detail=str(ex))
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))


# ============================================================================
# Источники данных (Sources)
# ============================================================================

@router.get("/sources/raw")
async def get_raw_sources_endpoint(request: Request) -> Dict[str, str]:
    """Получение сырого JSON текста источников данных."""
    _check_admin_auth(request)
    return {"content": sources_mgr.get_sources_raw()}


@router.post("/sources/raw")
async def save_raw_sources_endpoint(data: RawSourcesUpdate, request: Request) -> Dict[str, str]:
    """Сохранение сырого JSON текста источников данных."""
    _check_admin_auth(request)
    try:
        sources_mgr.save_sources_raw(data.content)
        _csv_logger.log_event("sources_raw_saved", status="SUCCESS", details="Updated sources JSON", filename="admin_config_param_changes.csv")
        return {"status": "ok"}
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))
    except IOError as ex:
        raise HTTPException(status_code=500, detail=str(ex))


# ============================================================================
# Администрирование пользователей
# ============================================================================

@router.get("/users")
async def list_users_endpoint(
    request: Request,
    q: str = "",
    role: str = "",
    status: str = "",
) -> Dict[str, Any]:
    """Получение списка пользователей с фильтрацией и статистикой."""
    _check_admin_auth(request)
    return user_svc.get_users_list(q=q, role=role, status=status)


@router.post("/users")
async def create_user_endpoint(data: AdminUserCreateRequest, request: Request) -> Dict[str, Any]:
    """Создание нового пользователя."""
    _check_admin_auth(request)
    try:
        res = user_svc.create_user(
            email=data.email,
            name=data.name,
            password=data.password,
            role=data.role,
            is_admin=data.is_admin,
            is_active=data.is_active,
            is_email_verified=data.is_email_verified,
        )
        _csv_logger.log_event(
            event_type="user_create",
            status="SUCCESS",
            details={"email": data.email, "role": data.role, "is_admin": data.is_admin},
            filename="admin_user_events.csv",
        )
        return res
    except ValueError as ex:
        _csv_logger.log_event("user_create_failed", status="FAILED", details={"email": data.email, "error": str(ex)}, filename="admin_user_events.csv")
        raise HTTPException(status_code=400, detail=str(ex))
    except RuntimeError as ex:
        raise HTTPException(status_code=500, detail=str(ex))


@router.get("/users/{user_id}")
async def get_user_details_endpoint(user_id: int, request: Request) -> Dict[str, Any]:
    """Получение детальной информации о пользователе."""
    _check_admin_auth(request)
    details = user_svc.get_user_details(user_id)
    if not details:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return details


@router.put("/users/{user_id}")
@router.patch("/users/{user_id}")
async def update_user_endpoint(user_id: int, data: AdminUserUpdateRequest, request: Request) -> Dict[str, Any]:
    """Обновление данных пользователя."""
    _check_admin_auth(request)
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    try:
        res = user_svc.update_user(user_id, **updates)
        _csv_logger.log_event(
            event_type="user_update",
            status="SUCCESS",
            details={"user_id": user_id, "updates": list(updates.keys())},
            filename="admin_user_events.csv",
        )
        return res
    except KeyError:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))


@router.post("/users/{user_id}/password")
async def set_user_password_endpoint(user_id: int, data: AdminUserPasswordRequest, request: Request) -> Dict[str, Any]:
    """Сброс и установка пароля пользователя."""
    _check_admin_auth(request)
    try:
        user_svc.set_user_password(user_id, data.password)
        _csv_logger.log_event("user_password_reset", status="SUCCESS", details={"user_id": user_id}, filename="admin_user_events.csv")
        return {"status": "ok", "message": "Пароль успешно обновлен"}
    except KeyError:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))


@router.post("/users/{user_id}/toggle-active")
async def toggle_user_active_endpoint(user_id: int, request: Request) -> Dict[str, Any]:
    """Переключение активности пользователя."""
    _check_admin_auth(request)
    try:
        new_status = user_svc.toggle_user_active(user_id)
        _csv_logger.log_event("user_toggle_active", status="SUCCESS", details={"user_id": user_id, "is_active": new_status}, filename="admin_user_events.csv")
        return {"status": "ok", "is_active": new_status}
    except KeyError:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))


@router.post("/users/{user_id}/toggle-role")
async def toggle_user_role_endpoint(user_id: int, request: Request) -> Dict[str, Any]:
    """Переключение роли пользователя (admin <-> user)."""
    _check_admin_auth(request)
    try:
        res = user_svc.toggle_user_role(user_id)
        _csv_logger.log_event("user_toggle_role", status="SUCCESS", details={"user_id": user_id, "result": res}, filename="admin_user_events.csv")
        return {"status": "ok", **res}
    except KeyError:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))


@router.delete("/users/{user_id}")
async def delete_user_endpoint(user_id: int, request: Request) -> Dict[str, Any]:
    """Удаление пользователя."""
    _check_admin_auth(request)
    try:
        user_svc.delete_user(user_id)
        _csv_logger.log_event("user_delete", status="SUCCESS", details={"user_id": user_id}, filename="admin_user_events.csv")
        return {"status": "ok", "message": f"Пользователь ID {user_id} удален"}
    except KeyError:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))



@router.get("/users/orphaned/dirs")
async def get_orphaned_dirs_endpoint(request: Request) -> Dict[str, Any]:
    """Получение списка осиротевших каталогов пользователей."""
    _check_admin_auth(request)
    return user_svc.get_orphaned_directories()


@router.post("/users/orphaned/clean")
async def clean_orphaned_dirs_endpoint(
    request: Request,
    payload: Optional[OrphanedDirsCleanRequest] = None,
) -> Dict[str, Any]:
    """Очистка осиротевших каталогов пользователей."""
    _check_admin_auth(request)
    dirs = payload.dirs if payload else None
    return user_svc.clean_orphaned_directories(dir_names=dirs)


def init_router() -> APIRouter:
    """Инициализация и экспорт FastAPI роутера администратора.

    Returns:
        APIRouter: Сконфигурированный экземпляр роутера.
    """
    return router


__all__ = [
    "init_router",
    "router",
    "config_mgr",
    "instructions_mgr",
    "sources_mgr",
    "user_svc",
]
