# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Api Routers - Router Process Activity
# =============================================================================
# Description:
#   FastAPI REST эндпоинты для веб-вкладки «Отслеживание активности процесса»
#   (Process Intelligence & Activity Deep Dive). Реализует контракты выборки
#   инстансов, метрик временных рядов, генеалогического дерева (Lineage),
#   файловой и сетевой активности, а также SafeOps управления.
#
# Usage Examples:
#   Python API:
#     from apps.windows.api.routers.router_process_activity import init_router
#
#     router = init_router()
#
# File: router_process_activity.py
# Project: ai-breadboard
# Package: apps.windows.api.routers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 11:53:00
# =============================================================================

from __future__ import annotations
"""FastAPI REST эндпоинты для отслеживания активности процессов (Process Intelligence)."""

import asyncio
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

try:
    from logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from apps.windows.core.process_activity_engine import ProcessActivityEngine
from apps.windows.telemetry.models import (
    ProcessFileEventRecord,
    ProcessInstanceRecord,
    ProcessLineageNode,
    ProcessSafeOpsRequest,
    ProcessSafeOpsResponse,
    ProcessSampleRecord,
    ProcessSocketRecord,
)


def init_router(prefix: str = "/api/v1/telemetry/instances", **kwargs: Any) -> APIRouter:
    """Инициализирует и возвращает FastAPI APIRouter для инспектора инстансов процессов.

    Args:
        prefix: Базовый префикс маршрутов.

    Returns:
        APIRouter: Сконфигурированный роутер FastAPI.
    """
    router = APIRouter(prefix=prefix, tags=["Process Activity Deep Dive"])
    engine = ProcessActivityEngine.get_instance()

    @router.get("/active", response_model=List[ProcessInstanceRecord])
    async def get_active_instances(
        limit: int = Query(100, ge=1, le=500, description="Лимит возвращаемых процессов"),
        search: Optional[str] = Query(None, description="Поисковый запрос по имени, PID или instance_id"),
    ) -> List[ProcessInstanceRecord]:
        """Получение списка всех активных процессов текущей сессии."""
        try:
            eng = ProcessActivityEngine.get_instance()
            return await asyncio.to_thread(eng.get_active_instances, limit=limit, search=search)
        except Exception as exc:
            logger.error(f"[RouterProcessActivity] Ошибка получения активных процессов: {exc}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(exc))

    @router.get("/history", response_model=List[ProcessInstanceRecord])
    async def get_history_instances(
        limit: int = Query(50, ge=1, le=500, description="Лимит записей"),
        offset: int = Query(0, ge=0, description="Смещение выборки"),
        search: Optional[str] = Query(None, description="Поисковый запрос по имени или PID"),
    ) -> List[ProcessInstanceRecord]:
        """Получение списка завершенных инстансов процессов (исторические срезы)."""
        try:
            eng = ProcessActivityEngine.get_instance()
            return await asyncio.to_thread(eng.get_history_instances, limit=limit, offset=offset, search=search)
        except Exception as exc:
            logger.error(f"[RouterProcessActivity] Ошибка получения истории инстансов: {exc}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(exc))

    @router.get("/{instance_id}", response_model=ProcessInstanceRecord)
    async def get_instance_details(instance_id: int) -> ProcessInstanceRecord:
        """Получение подробного паспорта и текущего статуса конкретного инстанса."""
        try:
            eng = ProcessActivityEngine.get_instance()
            record = await asyncio.to_thread(eng.get_instance_details, instance_id=instance_id)
            if not record:
                raise HTTPException(status_code=404, detail=f"Инстанс процесса #{instance_id} не найден")
            return record
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"[RouterProcessActivity] Ошибка получения инстанса #{instance_id}: {exc}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(exc))

    @router.get("/{instance_id}/samples", response_model=List[ProcessSampleRecord])
    async def get_instance_samples(
        instance_id: int,
        limit: int = Query(300, ge=1, le=2000, description="Лимит точек данных"),
        from_time: Optional[str] = Query(None, description="Начало временного интервала (ISO-8601)"),
        to_time: Optional[str] = Query(None, description="Конец временного интервала (ISO-8601)"),
    ) -> List[ProcessSampleRecord]:
        """Получение временного ряда метрик (CPU, RAM, GPU, IO) за выбранный интервал."""
        try:
            eng = ProcessActivityEngine.get_instance()
            return await asyncio.to_thread(
                eng.get_instance_samples,
                instance_id=instance_id,
                limit=limit,
                from_time=from_time,
                to_time=to_time,
            )
        except Exception as exc:
            logger.error(f"[RouterProcessActivity] Ошибка получения сэмплов #{instance_id}: {exc}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(exc))

    @router.get("/{instance_id}/lineage", response_model=ProcessLineageNode)
    async def get_instance_lineage(instance_id: int) -> ProcessLineageNode:
        """Получение интерактивного дерева предков и потомков инстанса процесса."""
        try:
            eng = ProcessActivityEngine.get_instance()
            return await asyncio.to_thread(eng.get_instance_lineage, instance_id=instance_id)
        except ValueError as val_err:
            raise HTTPException(status_code=404, detail=str(val_err))
        except Exception as exc:
            logger.error(f"[RouterProcessActivity] Ошибка получения lineage #{instance_id}: {exc}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(exc))

    @router.get("/{instance_id}/file-activity", response_model=List[ProcessFileEventRecord])
    async def get_instance_file_activity(
        instance_id: int,
        limit: int = Query(100, ge=1, le=1000, description="Лимит событий"),
        action: Optional[str] = Query(None, description="Фильтр по типу: CREATE, MODIFY, DELETE, RENAME"),
        extension: Optional[str] = Query(None, description="Фильтр по расширению файла (например .json, .log)"),
    ) -> List[ProcessFileEventRecord]:
        """Получение файловых событий по instance_id."""
        try:
            eng = ProcessActivityEngine.get_instance()
            return await asyncio.to_thread(
                eng.get_instance_file_activity,
                instance_id=instance_id,
                limit=limit,
                action=action,
                extension=extension,
            )
        except Exception as exc:
            logger.error(f"[RouterProcessActivity] Ошибка получения файловых событий #{instance_id}: {exc}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(exc))

    @router.get("/{instance_id}/sockets", response_model=List[ProcessSocketRecord])
    async def get_instance_sockets(instance_id: int) -> List[ProcessSocketRecord]:
        """Получение активных сетевых сокетов и удаленных соединений процесса."""
        try:
            eng = ProcessActivityEngine.get_instance()
            return await asyncio.to_thread(eng.get_instance_sockets, instance_id=instance_id)
        except Exception as exc:
            logger.error(f"[RouterProcessActivity] Ошибка получения сокетов #{instance_id}: {exc}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(exc))

    @router.post("/{instance_id}/action", response_model=ProcessSafeOpsResponse)
    async def execute_safeops_action(
        instance_id: int, payload: ProcessSafeOpsRequest
    ) -> ProcessSafeOpsResponse:
        """Выполнение SafeOps действий над процессом (kill, suspend, resume, dump, priority)."""
        try:
            eng = ProcessActivityEngine.get_instance()
            return await asyncio.to_thread(eng.execute_safe_action, instance_id=instance_id, request=payload)
        except Exception as exc:
            logger.error(f"[RouterProcessActivity] Ошибка SafeOps действия #{instance_id}: {exc}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(exc))

    return router


router = init_router()

__all__ = ["router", "init_router"]

