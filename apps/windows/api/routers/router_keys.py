# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard API - Router Keys Module
# =============================================================================
# Description:
#   Router для управления API ключами.
#
# Usage Examples:
#   Python API:
#     from src.api.routers.core.router_keys import KeyCreateRequest
#
#     service = KeyCreateRequest()
#
# File: router_keys.py
# Project: ai-breadboard
# Package: src.api.routers.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 13:36:00
# =============================================================================

"""Router для управления API ключами."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Literal
from types import SimpleNamespace

from logger import logger
from src.ai.gemini.gemini_api_key_state import reset_all_quotas, reset_quota, mark_exhausted, load_api_keys

router = APIRouter(prefix="/api/keys", tags=["router_keys"])

class KeyCreateRequest(BaseModel):
    """Запрос на создание нового API‑ключа."""
    name: str = Field(..., description="Человекочитаемое название ключа")
    role: Literal["admin", "user"] = Field(..., description="Роль доступа")

class KeyUpdateRequest(BaseModel):
    """Запрос на обновление существующего ключа."""
    name: str | None = None
    role: Literal["admin", "user"] | None = None

def _mask_key(key: str) -> str:
    """Возвращает скрытую версию ключа, показывая только последние 4 символа."""
    return "*" * (len(key) - 4) + key[-4:]

def _load_keys_from_file() -> List[dict]:
    """Загружает ключи из gemini_keys.json."""
    try:
        from src.utils.jjson import j_loads_ns
        from src.ai.gemini.gemini_api_key_state import _SECRETS_DIR, _KEYS_FILE
        
        if not _KEYS_FILE.exists():
            logger.warning(f'Файл ключей не найден: {_KEYS_FILE}')
            return []
        
        keys_data = j_loads_ns(_KEYS_FILE)
        # Convert SimpleNamespace to dict recursively
        if isinstance(keys_data, SimpleNamespace):
            keys_data = {k: vars(v) if isinstance(v, SimpleNamespace) else v 
                        for k, v in vars(keys_data).items()}
        
        result = []
        for name, data in keys_data.items():
            if isinstance(data, dict):
                result.append({
                    "id": name,
                    "name": name,
                    "role": "admin",
                    "key": data.get("value", ""),
                    "status": data.get("status", "active"),
                    "exhausted": data.get("status") == "exhausted",
                    "exhausted_at": data.get("exhausted_at", ""),
                    "last_run": data.get("last_run", "")
                })
        return result
    except Exception as e:
        logger.error(f"Ошибка загрузки ключей из файла: {e}")
        return []

def _check_exhaustion() -> None:
    """Поднимает ошибку, если достигнут лимит количества ключей."""
    if len(_FAKE_DB) >= _MAX_KEYS:
        raise HTTPException(status_code=400, detail="Достигнут лимит количества API‑ключей")

class KeyEntry(BaseModel):
    """Представление ключа в ответах API."""
    id: str
    name: str
    role: str
    masked_key: str
    status: str = "active"
    exhausted: bool = False
    exhausted_at: str = ""
    last_run: str = ""

@router.get("/", response_model=List[KeyEntry])
async def list_keys() -> List[KeyEntry]:
    keys = _load_keys_from_file()
    return [KeyEntry(
        id=rec["id"],
        name=rec["name"],
        role=rec["role"],
        masked_key=_mask_key(rec["key"]),
        status=rec.get("status", "active"),
        exhausted=rec.get("exhausted", False),
        exhausted_at=rec.get("exhausted_at", ""),
        last_run=rec.get("last_run", "")
    ) for rec in keys]

@router.post("/", response_model=KeyEntry)
async def create_key(req: KeyCreateRequest) -> KeyEntry:
    try:
        from src.ai.gemini.gemini_api_key_state import save_api_key
        # Для создания ключа будем генерировать простой токен (в реальном приложении использовать безопасный генератор)
        import uuid
        key_value = f"GEMINI_{uuid.uuid4().hex}"
        success = save_api_key(req.name, key_value)
        if not success:
            raise HTTPException(status_code=400, detail="Не удалось сохранить ключ")
        return KeyEntry(
            id=req.name,
            name=req.name,
            role=req.role,
            masked_key=_mask_key(key_value),
            status="active"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка создания ключа: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка создания ключа: {str(e)}")

@router.put("/{key_name}", response_model=KeyEntry)
async def update_key(key_name: str, req: KeyUpdateRequest) -> KeyEntry:
    try:
        from src.ai.gemini.gemini_api_key_state import load_api_keys, save_api_key
        keys_data = load_api_keys()[0] if isinstance(load_api_keys(), tuple) else {}
        
        if key_name not in keys_data:
            raise HTTPException(status_code=404, detail=f"Ключ '{key_name}' не найден")
        
        # Обновляем данные ключа
        keys_data[key_name]["status"] = keys_data[key_name].get("status", "active")
        if req.name is not None:
            # Renaming keys is not supported in gemini_api_key_state
            raise HTTPException(status_code=400, detail="Переименование ключей не поддерживается")
        
        # Сохраняем
        from src.ai.gemini.gemini_api_key_state import _save_keys_file, _sync_environment
        _save_keys_file(keys_data)
        _sync_environment(keys_data[key_name].get("value", ""))
        
        return KeyEntry(
            id=key_name,
            name=key_name,
            role="admin",
            masked_key=_mask_key(keys_data[key_name].get("value", "")),
            status=keys_data[key_name].get("status", "active")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка обновления ключа '{key_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка обновления ключа: {str(e)}")

@router.delete("/{key_name}")
async def delete_key(key_name: str) -> dict:
    try:
        from src.ai.gemini.gemini_api_key_state import delete_api_key
        success = delete_api_key(key_name)
        if not success:
            raise HTTPException(status_code=404, detail=f"Ключ '{key_name}' не найден")
        return {"status": "deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка удаления ключа '{key_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка удаления ключа: {str(e)}")

@router.post("/reset-all", response_model=dict)
async def reset_all_keys_quota() -> dict:
    """Сбросить квоты для всех ключей."""
    try:
        reset_count = reset_all_quotas()
        return {"status": "success", "message": f"Квоты сброшены для {reset_count} ключей", "reset_count": reset_count}
    except Exception as e:
        logger.error(f"Ошибка сброса квот: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сброса квот: {str(e)}")

@router.post("/{key_name}/reset-quota", response_model=dict)
async def reset_key_quota(key_name: str) -> dict:
    """Сбросить квоту для конкретного ключа."""
    try:
        result = reset_quota(key_name)
        if result:
            return {"status": "success", "message": f"Квота для ключа '{key_name}' успешно сброшена"}
        else:
            raise HTTPException(status_code=404, detail=f"Ключ '{key_name}' не найден")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка сброса квоты для ключа '{key_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сброса квоты: {str(e)}")

@router.patch("/{key_name}", response_model=dict)
async def toggle_key_status(key_name: str, req: dict) -> dict:
    """Переключить статус ключа (active/disabled)."""
    try:
        from src.ai.gemini.gemini_api_key_state import save_api_key, load_api_keys
        keys_data = load_api_keys()[0] if isinstance(load_api_keys(), tuple) else {}
        
        if key_name not in keys_data:
            raise HTTPException(status_code=404, detail=f"Ключ '{key_name}' не найден")
        
        new_status = req.get("status", "active")
        if new_status not in ["active", "disabled"]:
            raise HTTPException(status_code=400, detail="Недопустимый статус. Допустимые значения: active, disabled")
        
        # Обновляем статус
        keys_data[key_name]["status"] = new_status
        if new_status == "active" and keys_data[key_name].get("exhausted_at"):
            keys_data[key_name]["exhausted_at"] = ""
        
        # Сохраняем
        from src.ai.gemini.gemini_api_key_state import _save_keys_file, _sync_environment
        _save_keys_file(keys_data)
        _sync_environment(keys_data[key_name].get("value", ""))
        
        return {"status": "success", "message": f"Статус ключа '{key_name}' изменен на '{new_status}'"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка переключения статуса ключа '{key_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка переключения статуса: {str(e)}")

def init_router() -> APIRouter:
    """Инициализация роутера ключей."""
    return router

__all__ = ["init_router", "router", "KeyCreateRequest", "KeyEntry", "KeyUpdateRequest", "_check_exhaustion", "_mask_key"]