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
# Updated: 2026-10-01 13:13:56
# =============================================================================

"""Router для управления API ключами."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Literal

router = APIRouter(prefix="/api/keys", tags=["router_keys"])

# Пример данных (в реальном приложении будет БД)
_FAKE_DB: List[dict] = []
_MAX_KEYS = 5

class KeyCreateRequest(BaseModel):
    """Запрос на создание нового API‑ключа."""
    name: str = Field(..., description="Человекочитаемое название ключа")
    role: Literal["admin", "user"] = Field(..., description="Роль доступа")

class KeyUpdateRequest(BaseModel):
    """Запрос на обновление существующего ключа."""
    name: str | None = None
    role: Literal["admin", "user"] | None = None

class KeyEntry(BaseModel):
    """Представление ключа в ответах API."""
    id: str
    name: str
    role: str
    masked_key: str

def _mask_key(key: str) -> str:
    """Возвращает скрытую версию ключа, показывая только последние 4 символа."""
    return "*" * (len(key) - 4) + key[-4:]

def _check_exhaustion() -> None:
    """Поднимает ошибку, если достигнут лимит количества ключей."""
    if len(_FAKE_DB) >= _MAX_KEYS:
        raise HTTPException(status_code=400, detail="Достигнут лимит количества API‑ключей")

@router.get("/", response_model=List[KeyEntry])
async def list_keys() -> List[KeyEntry]:
    return [KeyEntry(id=rec["id"], name=rec["name"], role=rec["role"], masked_key=_mask_key(rec["key"])) for rec in _FAKE_DB]

@router.post("/", response_model=KeyEntry)
async def create_key(req: KeyCreateRequest) -> KeyEntry:
    _check_exhaustion()
    # Генерируем простой ключ (в продакшене использовать безопасный генератор)
    import uuid
    new_key = uuid.uuid4().hex
    entry = {"id": uuid.uuid4().hex, "name": req.name, "role": req.role, "key": new_key}
    _FAKE_DB.append(entry)
    return KeyEntry(id=entry["id"], name=entry["name"], role=entry["role"], masked_key=_mask_key(new_key))

@router.put("/{key_id}", response_model=KeyEntry)
async def update_key(key_id: str, req: KeyUpdateRequest) -> KeyEntry:
    for rec in _FAKE_DB:
        if rec["id"] == key_id:
            if req.name is not None:
                rec["name"] = req.name
            if req.role is not None:
                rec["role"] = req.role
            return KeyEntry(id=rec["id"], name=rec["name"], role=rec["role"], masked_key=_mask_key(rec["key"]))
    raise HTTPException(status_code=404, detail="Ключ не найден")

@router.delete("/{key_id}")
async def delete_key(key_id: str) -> dict:
    global _FAKE_DB
    new_db = [rec for rec in _FAKE_DB if rec["id"] != key_id]
    if len(new_db) == len(_FAKE_DB):
        raise HTTPException(status_code=404, detail="Ключ не найден")
    _FAKE_DB = new_db
    return {"status": "deleted"}

def init_router() -> APIRouter:
    """Инициализация роутера ключей."""
    return router

__all__ = ["init_router", "router", "KeyCreateRequest", "KeyEntry", "KeyUpdateRequest", "_check_exhaustion", "_mask_key"]