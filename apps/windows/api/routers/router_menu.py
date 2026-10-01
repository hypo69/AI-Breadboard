# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Api Routers - Router Menu
# =============================================================================
# Description:
#   Предоставляет эндпоинты FastAPI для чтения и сохранения конфигурации меню
#
# Usage Examples:
#   Python API:
#     from apps.windows.api.routers.router_menu import MenuItem
#
#     service = MenuItem()
#
# File: router_menu.py
# Project: ai-breadboard
# Package: apps.windows.api.routers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Предоставляет эндпоинты FastAPI для чтения и сохранения конфигурации меню"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from header import __root__
from logger import logger

# Пути к директориям меню
_LOCAL_CONFIG_MENUES = Path(__file__).resolve().parents[1] / 'webgui' / 'config_menues'
_SRC_CONFIG_MENUES = __root__ / 'src' / 'api' / 'webgui' / 'config_menues'


def _get_config_path(target: Optional[str] = None) -> Path:
    """Возвращает актуальный путь к файлу конфигурации меню по целевому контексту.

    Args:
        target: Имя контекста (tc, apps, su и т.д.).

    Returns:
        Path: Путь к JSON файлу конфигурации меню.
    """
    file_name = 'tc_menu_config.json'
    if target and target.lower() in ('su', 'user', 'user_assistant'):
        file_name = 'su_menu_config.json'
    elif target and target.lower() not in ('tc', 'apps', 'test_computer'):
        file_name = f"{target.lower()}_menu_config.json"

    # 1. Проверяем локальный каталог webgui приложения Windows
    local_path = _LOCAL_CONFIG_MENUES / file_name
    if local_path.exists():
        return local_path

    # 2. Проверяем глобальный каталог в src/api/webgui
    src_path = _SRC_CONFIG_MENUES / file_name
    if src_path.exists():
        return src_path

    return local_path


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
    """Инициализирует FastAPI роутер для управления конфигурацией меню.

    Returns:
        APIRouter: Настроенный роутер с маршрутами /api/menu/*.
    """
    router = APIRouter(prefix='/api/menu', tags=['menu'])

    @router.get('/config')
    async def get_menu_config(target: Optional[str] = None) -> Dict[str, Any]:
        """Получение текущей конфигурации меню."""
        config_path = _get_config_path(target)
        if not config_path.exists():
            logger.warning(f"[router_menu] Файл конфигурации меню не найден: {config_path}")
            raise HTTPException(status_code=404, detail="Файл конфигурации меню не найден")

        try:
            content = config_path.read_text(encoding='utf-8')
            return json.loads(content)
        except Exception as ex:
            logger.error(f"[router_menu] Ошибка при чтении конфигурации меню: {ex}")
            raise HTTPException(status_code=500, detail=f"Ошибка чтения конфигурации: {ex}")

    @router.post('/config')
    async def save_menu_config(payload: Dict[str, Any], target: Optional[str] = None) -> Dict[str, Any]:
        """Сохранение обновленной конфигурации меню."""
        if not isinstance(payload, dict) or 'menu' not in payload:
            raise HTTPException(
                status_code=400,
                detail="Некорректная структура конфигурации меню (отсутствует секция 'menu')",
            )

        config_path = _get_config_path(target)
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

            # Также синхронизируем в src/api/webgui если путь отличается
            src_path = _SRC_CONFIG_MENUES / config_path.name
            if src_path != config_path and _SRC_CONFIG_MENUES.exists():
                src_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

            logger.info(f"[router_menu] Конфигурация меню успешно сохранена в {config_path.name}")
            return {"status": "ok", "message": f"Конфигурация меню успешно сохранена в {config_path.name}"}
        except Exception as ex:
            logger.error(f"[router_menu] Ошибка при сохранении конфигурации меню: {ex}")
            raise HTTPException(status_code=500, detail=f"Ошибка сохранения конфигурации: {ex}")

    return router


__all__ = ['init_router']
