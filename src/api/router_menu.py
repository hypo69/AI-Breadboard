# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Menu configuration management router
# =============================================================================
# Description:
#   Предоставляет эндпоинты FastAPI для чтения и сохранения конфигурации меню
#   веб-интерфейса Test Computer (/tc) и приложений (/apps).
#
# File: router_menu.py
# Project: ai-breadboard
# Package: src.api
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from header import __root__
from logger import logger

TC_MENU_CONFIG_PATH = __root__ / 'src' / 'api' / 'webgui' / 'config' / 'tc_menu_config.json'


class MenuItem(BaseModel):
    """Модель элемента меню."""
    id: str
    label: str
    icon: Optional[str] = None
    tab: str
    order: Optional[int] = 0
    visible: Optional[bool] = True
    i18n: Optional[str] = None


class MenuSection(BaseModel):
    """Модель разделов меню."""
    topButtons: List[Dict[str, Any]] = Field(default_factory=list)
    sidebarItems: List[Dict[str, Any]] = Field(default_factory=list)


class MenuConfigPayload(BaseModel):
    """Модель полной конфигурации меню."""
    version: Optional[str] = None
    menu: MenuSection
    settings: Optional[Dict[str, Any]] = None


def init_router() -> APIRouter:
    """Инициализирует FastAPI роутер для управления конфигурацией меню."""
    router = APIRouter(prefix='/api/menu', tags=['menu'])

    @router.get('/config')
    async def get_menu_config() -> Dict[str, Any]:
        """
        Получение текущей конфигурации меню из tc_menu_config.json.
        """
        if not TC_MENU_CONFIG_PATH.exists():
            logger.warning(f"Файл конфигурации меню не найден: {TC_MENU_CONFIG_PATH}")
            raise HTTPException(status_code=404, detail="Файл конфигурации меню не найден")

        try:
            content = TC_MENU_CONFIG_PATH.read_text(encoding='utf-8')
            return json.loads(content)
        except Exception as ex:
            logger.error(f"Ошибка при чтении конфигурации меню: {ex}")
            raise HTTPException(status_code=500, detail=f"Ошибка чтения конфигурации: {ex}")

    @router.post('/config')
    async def save_menu_config(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Сохранение обновленной конфигурации меню в tc_menu_config.json.
        """
        if not isinstance(payload, dict) or 'menu' not in payload:
            raise HTTPException(status_code=400, detail="Некорректная структура конфигурации меню (отсутствует секция 'menu')")

        try:
            TC_MENU_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            TC_MENU_CONFIG_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
            logger.info("Конфигурация меню успешно сохранена в tc_menu_config.json")
            return {"status": "ok", "message": "Конфигурация меню успешно сохранена"}
        except Exception as ex:
            logger.error(f"Ошибка при сохранении конфигурации меню: {ex}")
            raise HTTPException(status_code=500, detail=f"Ошибка сохранения конфигурации: {ex}")

    return router
