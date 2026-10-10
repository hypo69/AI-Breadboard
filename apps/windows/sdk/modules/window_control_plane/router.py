# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Window Management Control Plane Router
# =============================================================================
# Description:
#   FastAPI REST API роутер для Windows Window Management Control Plane (/api/v1/window-management).
#   Предоставляет доступ к 295 системным настройкам управления окнами, DWM, панели задач,
#   мониторов и политик оболочки с поддержкой живой телеметрии, Dry-Run и отката изменений.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.window_control_plane.router import init_router
#
#     router = init_router()
#
# File: router.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.window_control_plane
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 18:00:00
# =============================================================================

from __future__ import annotations
"""FastAPI REST API роутер для Window Management Control Plane."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Path as FPath
from logger import logger
from apps.windows.sdk.modules.window_control_plane.manager import (
    WindowManagementControlPlane,
    get_window_control_plane,
)
from apps.windows.sdk.modules.window_control_plane.models import (
    BatchApplyRequest,
    BatchApplyResponse,
    ControlPlaneSummaryResponse,
    DocStatus,
    RiskLevel,
    SettingApplyRequest,
    SettingApplyResponse,
    SettingCategory,
    SettingPreviewResponse,
    SettingRollbackResponse,
    SettingValueResponse,
    SupportStatus,
    WindowSettingDefinition,
)

router = APIRouter(prefix="/api/v1/window-management", tags=["Windows Window Management Control Plane"])
_plane: WindowManagementControlPlane = get_window_control_plane()


def init_router() -> APIRouter:
    """Инициализация и получение роутера FastAPI.

    Returns:
        APIRouter: Экземпляр настроенного роутера.
    """
    return router


# =============================================================================
# Каталог и аналитика
# =============================================================================
@router.get("/summary", response_model=ControlPlaneSummaryResponse)
async def get_control_plane_summary() -> ControlPlaneSummaryResponse:
    """Сводный аналитический отчет по всем 295 параметрам Control Plane."""
    return _plane.get_summary()


@router.get("/categories")
async def get_categories_overview() -> Dict[str, Any]:
    """Список всех 15 системных категорий с детальным распределением параметров."""
    overview = _plane.get_categories_overview()
    return {
        "total_categories": len(overview),
        "categories": overview,
    }


@router.get("/catalog")
async def get_catalog(
    query: Optional[str] = Query(None, description="Поисковый запрос по названию или описанию (RU/EN)"),
    category: Optional[SettingCategory] = Query(None, description="Фильтр по одной из 15 системных категорий"),
    support_status: Optional[SupportStatus] = Query(None, description="Фильтр по статусу поддержки (Safe, Admin, Compat, Unsupported)"),
    doc_status: Optional[DocStatus] = Query(None, description="Фильтр по типу документации (documented_api, policy, registry_compat)"),
    risk: Optional[RiskLevel] = Query(None, description="Фильтр по уровню риска (safe, low, medium, high, critical)"),
    requires_elevation: Optional[bool] = Query(None, description="Фильтр по требованию прав администратора"),
    requires_restart: Optional[bool] = Query(None, description="Фильтр по требованию перезапуска системы/проводника"),
    limit: int = Query(500, ge=1, le=500, description="Максимальное количество возвращаемых параметров"),
    offset: int = Query(0, ge=0, description="Смещение выборки"),
) -> Dict[str, Any]:
    """Получение полного или отфильтрованного списка параметров Windows Control Plane."""
    items = _plane.search_settings(
        query=query,
        category=category,
        support_status=support_status,
        doc_status=doc_status,
        risk=risk,
        requires_elevation=requires_elevation,
        requires_restart=requires_restart,
        limit=limit,
        offset=offset,
    )
    return {
        "total": len(items),
        "limit": limit,
        "offset": offset,
        "settings": [x.to_dict() for x in items],
    }


# =============================================================================
# Детализация и чтение живых значений
# =============================================================================
@router.get("/settings/{setting_id}")
async def get_setting_details(
    setting_id: str = FPath(..., description="Идентификатор системного параметра"),
    read_live: bool = Query(True, description="Выполнять ли немедленное чтение живого значения из системы"),
) -> Dict[str, Any]:
    """Получение подробных метаданных параметра и его текущего живого значения."""
    setting = _plane.get_setting_by_id(setting_id)
    if not setting:
        raise HTTPException(status_code=404, detail=f"Параметр '{setting_id}' не найден в каталоге.")

    live_val = None
    if read_live:
        live_val = _plane.get_live_value(setting_id)

    return {
        "definition": setting.to_dict(),
        "live_state": live_val.model_dump() if live_val else None,
    }


@router.get("/categories/{category_id}/live", response_model=List[SettingValueResponse])
async def get_category_live_values(
    category_id: SettingCategory = FPath(..., description="Идентификатор категории"),
) -> List[SettingValueResponse]:
    """Чтение живых значений всех параметров заданной категории."""
    return _plane.get_category_live_values(category_id)


# =============================================================================
# Симуляция (Preview / Dry-Run) и Применение
# =============================================================================
@router.post("/settings/{setting_id}/preview", response_model=SettingPreviewResponse)
async def preview_setting_change(
    setting_id: str = FPath(..., description="Идентификатор системного параметра"),
    payload: Dict[str, Any] = ...,
) -> SettingPreviewResponse:
    """Сухой прогон (Dry-Run) изменения параметра: валидация, проверка рисков и оценка точек восстановления."""
    val = payload.get("value")
    res = _plane.preview_setting(setting_id, val)
    if not res:
        raise HTTPException(status_code=404, detail=f"Параметр '{setting_id}' не найден.")
    return res


@router.post("/settings/{setting_id}/apply", response_model=SettingApplyResponse)
async def apply_setting_change(
    setting_id: str = FPath(..., description="Идентификатор системного параметра"),
    request: SettingApplyRequest = ...,
) -> SettingApplyResponse:
    """Безопасное применение изменения системного параметра Windows."""
    res = _plane.apply_setting(setting_id, request)
    if not res.success and res.error == "SettingNotFound":
        raise HTTPException(status_code=404, detail=res.message)
    return res


@router.post("/batch-apply", response_model=BatchApplyResponse)
async def apply_batch_settings(
    request: BatchApplyRequest,
) -> BatchApplyResponse:
    """Пакетное применение группы параметров с созданием единой точки восстановления."""
    return _plane.apply_batch(request)


# =============================================================================
# Журнал аудита и откат (Rollback) в telemetry.db
# =============================================================================
@router.get("/history")
async def get_changes_history(
    limit: int = Query(100, ge=1, le=1000, description="Количество последних записей аудита"),
    offset: int = Query(0, ge=0, description="Смещение выборки"),
    setting_id: Optional[str] = Query(None, description="Фильтр по идентификатору параметра"),
    category: Optional[str] = Query(None, description="Фильтр по категории"),
) -> List[Dict[str, Any]]:
    """Получение журнала аудита примененных изменений параметров из telemetry.db."""
    return _plane.get_history(limit=limit, offset=offset, setting_id=setting_id, category=category)


@router.post("/rollback/{change_id}", response_model=SettingRollbackResponse)
async def rollback_setting_change(
    change_id: str = FPath(..., description="Уникальный идентификатор изменения из истории"),
) -> SettingRollbackResponse:
    """Откат изменения к исходному значению до применения с фиксацией в telemetry.db."""
    res = _plane.rollback_change(change_id)
    if not res.rolled_back and "не найдена" in res.message:
        raise HTTPException(status_code=404, detail=res.message)
    return res


@router.post("/rollback-last", response_model=SettingRollbackResponse)
async def rollback_last_setting_change() -> SettingRollbackResponse:
    """Быстрый откат последнего совершенного изменения из telemetry.db."""
    res = _plane.rollback_last()
    if not res.rolled_back:
        raise HTTPException(status_code=400, detail=res.message)
    return res
