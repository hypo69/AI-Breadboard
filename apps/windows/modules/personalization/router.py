# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Personalization Router
# =============================================================================
# Description:
#   FastAPI REST API роутер для управления персонализацией Windows:
#   темами, указателем мыши, обоями, экраном блокировки, Windows Spotlight
#   и познавательными карточками AI Spotlight («Learn about this picture»).
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.personalization.router import router as personalization_router
#
# File: router.py
# Project: ai-breadboard
# Package: apps.windows.modules.personalization
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 18:30:00
# =============================================================================

from __future__ import annotations
"""REST API маршруты для подсистемы Personalization & Appearance."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from apps.windows.modules.personalization.ai_spotlight import get_ai_spotlight_engine
from apps.windows.modules.personalization.manager import (
    PersonalizationManager,
    get_personalization_manager,
)
from apps.windows.modules.personalization.models import (
    AISpotlightAnalysisRequest,
    AISpotlightImageInfo,
    CursorSettings,
    CursorUpdateRequest,
    PersonalizationOverviewResponse,
    SpotlightUpdateRequest,
    ThemeApplyRequest,
    WallpaperSettings,
    WallpaperUpdateRequest,
    WindowsSpotlightSettings,
    WindowsThemeInfo,
)

router = APIRouter(prefix="", tags=["Personalization & Appearance"])
_pm: PersonalizationManager = get_personalization_manager()
_ai_engine = get_ai_spotlight_engine()


@router.get("/overview", response_model=PersonalizationOverviewResponse)
async def get_personalization_overview() -> PersonalizationOverviewResponse:
    """Получение сводной информации по темам, курсору, обоям и Spotlight."""
    return _pm.get_overview()


# =============================================================================
# 1. Темы Windows
# =============================================================================
@router.get("/themes", response_model=List[WindowsThemeInfo])
async def list_available_themes() -> List[WindowsThemeInfo]:
    """Получение списка установленных тем Windows (.theme)."""
    return _pm.get_theme_list()


@router.post("/theme/apply")
@router.post("/theme")
async def apply_windows_theme(request: ThemeApplyRequest) -> Dict[str, Any]:
    """Применение темы оформления, переключение Dark/Light режима и акцентного цвета."""
    return _pm.apply_theme(request)


@router.get("/state")
async def get_personalization_state() -> Dict[str, Any]:
    """Data-First срез параметров персонализации из таблицы personalization_snapshots."""
    return _pm.get_state()


@router.get("/history")
async def get_personalization_history(limit: int = Query(100, ge=1, le=1000), group: Optional[str] = None) -> List[Dict[str, Any]]:
    """Журнал изменений из таблицы personalization_change_history."""
    return _pm.store.history(limit=limit, group=group)


# =============================================================================
# 2. Указатель мыши и Курсор
# =============================================================================
@router.get("/cursor", response_model=CursorSettings)
async def get_cursor_configuration() -> CursorSettings:
    """Получение текущих настроек указателя мыши (размер 1..128, цвет, шлейф, скорость)."""
    return _pm.get_cursor_settings()


@router.put("/cursor", response_model=CursorSettings)
@router.post("/cursor", response_model=CursorSettings)
async def update_cursor_configuration(request: CursorUpdateRequest) -> CursorSettings:
    """Обновление параметров указателя мыши с фиксацией в telemetry.db."""
    return _pm.update_cursor(request)


# =============================================================================
# 3. Обои рабочего стола и Экран блокировки
# =============================================================================
@router.get("/wallpaper", response_model=WallpaperSettings)
async def get_wallpaper_configuration() -> WallpaperSettings:
    """Получение текущих параметров фонового рисунка и масштабирования."""
    return _pm.get_wallpaper_settings()


@router.put("/wallpaper", response_model=WallpaperSettings)
@router.post("/wallpaper", response_model=WallpaperSettings)
async def update_wallpaper_configuration(request: WallpaperUpdateRequest) -> WallpaperSettings:
    """Установка новых обоев рабочего стола и режима масштабирования."""
    return _pm.update_wallpaper(request)


# =============================================================================
# 4. Windows Spotlight
# =============================================================================
@router.get("/spotlight", response_model=WindowsSpotlightSettings)
async def get_windows_spotlight_configuration() -> WindowsSpotlightSettings:
    """Получение статуса службы Windows Spotlight."""
    return _pm.get_spotlight_settings()


@router.post("/spotlight", response_model=WindowsSpotlightSettings)
async def update_windows_spotlight_configuration(request: SpotlightUpdateRequest) -> WindowsSpotlightSettings:
    """Настройка службы Windows Spotlight для рабочего стола и экрана блокировки."""
    return _pm.update_spotlight(request)


# =============================================================================
# 5. AI Spotlight (Медиа-интеллект и «О фотографии»)
# =============================================================================
@router.get("/ai-spotlight/current", response_model=AISpotlightImageInfo)
async def get_current_wallpaper_ai_analysis() -> AISpotlightImageInfo:
    """Глубокий анализ текущего изображения рабочего стола в стиле «Learn about this picture»."""
    res = _pm.get_current_ai_spotlight()
    if not res:
        raise HTTPException(status_code=404, detail="Не удалось определить текущие обои для анализа")
    return res


@router.post("/ai-spotlight/analyze", response_model=AISpotlightImageInfo)
async def analyze_image_with_ai_spotlight(request: AISpotlightAnalysisRequest) -> AISpotlightImageInfo:
    """Проведение семантического анализа произвольного изображения с привязкой гео-координат и исторических фактов."""
    img_path = request.image_path or _pm._read_current_wallpaper_path()
    if not img_path:
        raise HTTPException(status_code=400, detail="Путь к изображению не указан")

    return _ai_engine.analyze_image(
        image_path=img_path,
        prompt_focus=request.prompt_focus,
        is_current_wallpaper=(img_path == _pm._read_current_wallpaper_path()),
    )


@router.get("/ai-spotlight/gallery", response_model=List[AISpotlightImageInfo])
async def get_ai_spotlight_gallery() -> List[AISpotlightImageInfo]:
    """Получение сохраненных карточек знаний и истории проанализированных изображений."""
    return _ai_engine.get_all_saved_images()


def init_router() -> APIRouter:
    """Фабрика инициализации роутера."""
    return router
