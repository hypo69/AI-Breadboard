# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI Chat Application FastAPI Router
# =============================================================================
# Description:
#   FastAPI REST API роутер для микросервиса AI Chat: управление состоянием,
#   историей диалоговых сессий и параметрами выполнения.
#
# File: router.py
# Project: ai-breadboard
# Package: apps.chat
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from apps.chat.engine import ChatEngine
from logger import logger

router = APIRouter(prefix="/api/v1/apps/chat", tags=["apps_chat"])
_engine = ChatEngine()


class SessionCreateRequest(BaseModel):
    """Модель создания или сохранения диалоговой сессии."""
    id: str = Field(..., description="Уникальный идентификатор сессии")
    userId: Optional[str] = Field("", description="Идентификатор пользователя")
    title: Optional[str] = Field("New Chat", description="Заголовок чата")
    isCustomTitle: Optional[bool] = Field(False, description="Пользовательский заголовок")
    createdAt: Optional[int] = Field(0, description="Временная метка создания")
    updatedAt: Optional[int] = Field(0, description="Временная метка обновления")
    messages: List[Dict[str, Any]] = Field(default_factory=list, description="Список сообщений")
    chatHistory: List[Dict[str, Any]] = Field(default_factory=list, description="История контекста диалога")


@router.get("/status")
async def get_chat_status() -> Dict[str, Any]:
    """Возвращает текущий статус приложения AI Chat."""
    return _engine.get_status()


@router.get("/config")
async def get_chat_config() -> Dict[str, Any]:
    """Возвращает конфигурационные параметры приложения AI Chat."""
    return _engine.get_config()


@router.get("/sessions")
async def list_chat_sessions(user_id: Optional[str] = Query("", alias="userId")) -> List[Dict[str, Any]]:
    """Возвращает список сохраненных сессий диалогов."""
    return _engine.list_sessions(user_id=user_id or "")


@router.get("/sessions/{session_id}")
async def get_chat_session(session_id: str) -> Dict[str, Any]:
    """Возвращает данные конкретной сессии диалога."""
    session = _engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Сессия {session_id} не найдена")
    return session


@router.post("/sessions")
async def save_chat_session(data: SessionCreateRequest) -> Dict[str, Any]:
    """Сохраняет или обновляет сессию диалога."""
    success = _engine.save_session(data.model_dump())
    if not success:
        raise HTTPException(status_code=500, detail="Не удалось сохранить сессию диалога")
    return {"status": "ok", "id": data.id}


@router.delete("/sessions/{session_id}")
async def delete_chat_session(session_id: str) -> Dict[str, Any]:
    """Удаляет сессию диалога."""
    success = _engine.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Не удалось удалить сессию {session_id}")
    return {"status": "ok", "deleted": session_id}


@router.delete("/sessions")
async def clear_all_chat_sessions() -> Dict[str, Any]:
    """Очищает все сохраненные диалоговые сессии."""
    success = _engine.clear_all_sessions()
    if not success:
        raise HTTPException(status_code=500, detail="Не удалось очистить сессии")
    return {"status": "ok", "message": "Все сессии успешно очищены"}


def init_router(chat_model: Optional[Any] = None, narrator_model: Optional[Any] = None) -> APIRouter:
    """Фабричная функция инициализации роутера приложения Chat.

    Args:
        chat_model: Экземпляр основной модели чата (опционально).
        narrator_model: Экземпляр модели диктора (опционально).

    Returns:
        APIRouter: Сконфигурированный FastAPI роутер.
    """
    return router
