# -*- coding: utf-8 -*-
"""Маршрутизатор FastAPI для плагина IFTTT.

Экспортирует объект ``router`` (APIRouter), который будет автоматически обнаружен
модулем ``router_loader`` и включён в приложение.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/ifttt", tags=["IFTTT"])

@router.get("/status")
async def status() -> dict:
    """Возвращает простую информацию о состоянии плагина.

    Returns:
        dict: ``{"status": "ok"}`` – статус плагина IFTTT.
    """
    return {"status": "ok"}
