# -*- coding: utf-8 -*-
"""FastAPI‑router для плагина news_feed.

Экспортирует объект ``router`` (APIRouter), который будет автоматически обнаружен
модулем ``router_loader`` и подключён к приложению.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/news", tags=["News Feed"])

@router.get("/status")
async def status() -> dict:
    """Простейший эндпоинт, показывающий, что плагин подключён.
    Returns:
        dict: ``{"status": "ok"}``.
    """
    return {"status": "ok"}
