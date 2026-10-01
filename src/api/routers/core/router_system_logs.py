# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard API - Router System Logs Module
# =============================================================================
# Description:
#   Реализация роутера `router_system_logs`.
#
# Usage Examples:
#   Python API:
#     from src.api.routers.core.router_system_logs import ExplainRequest
#
#     service = ExplainRequest()
#
# File: router_system_logs.py
# Project: ai-breadboard
# Package: src.api.routers.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

"""Реализация роутера `router_system_logs`.
Включает модель `ExplainRequest` и функцию `explain_event`, которые предоставляют
описания и рекомендации для системных журналов Windows."""

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Optional
import re

router = APIRouter()

class ExplainRequest(BaseModel):
    """Запрос для объяснения события системного журнала.
    Поля соответствуют тем, которые используются в тестах.
    """
    provider: str = Field(..., description="Имя поставщика/источника журнала")
    event_id: int = Field(..., description="Идентификатор события в журнале")
    level: str = Field(..., description="Уровень события (Info, Warning, Error и т.д.)")
    message: str = Field(..., description="Текст сообщения события")
    channel: Optional[str] = Field(None, description="Канал журнала (если применимо)")

async def explain_event(req: ExplainRequest) -> dict:
    """Генерирует простое объяснение события.
    На данный момент реализовано эвристическое заполнение без обращения к LLM.
    Тесты проверяют наличие ключей `summary`, `root_cause` и `recommendations`
    и некоторые ожидаемые подстроки.
    """
    # Эвристика для известных провайдеров
    summary = f"Системное событие {req.provider} (ID {req.event_id})"
    root_cause = req.message
    recommendations: List[str] = []

    provider_low = req.provider.lower()
    if "bits" in provider_low:
        summary = f"BITS (Background Intelligent Transfer Service) – событие {req.event_id}"
        match = re.search(r"ErrorCode:\s*(\d+)", req.message)
        if match:
            code = match.group(1)
            root_cause = f"Код ошибки {code} в BITS"
            recommendations.append("Проверить статус подключения к интернету")
            recommendations.append("Перезапустить службу BITS: Restart-Service BITS")
        else:
            recommendations.append("Проверить состояние службы BITS")
    elif "distributedcom" in provider_low or "dcom" in provider_low:
        summary = f"Distributed COM – событие {req.event_id}"
        recommendations.append("Проверить настройки DCOM и права локальной активации")
    else:
        recommendations.append("Провести обычный анализ журнала")

    return {
        "summary": summary,
        "root_cause": root_cause,
        "recommendations": recommendations,
    }

@router.get('/router_system_logs/ping', tags=['router_system_logs'])
async def ping() -> dict:
    """Проверка доступности роутера."""
    return {'status': 'ok'}

@router.post('/api/system/logs/explain', tags=['router_system_logs'])
async def explain_endpoint(req: ExplainRequest) -> dict:
    """Эндпоинт, вызывающий `explain_event`. Тесты используют функцию напрямую.
    """
    return await explain_event(req)

def init_router() -> APIRouter:
    """Инициализация и возврат роутера."""
    return router