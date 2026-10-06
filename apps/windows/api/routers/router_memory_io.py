# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Api Routers - Router Memory IO
# =============================================================================
# Description:
#   GET /api/v1/panel/memory-io — загрузка памяти и скорость чтения/записи
#   (байт/с) из таблицы system_snapshots базы telemetry.db.
#
# Usage Examples:
#   Python API:
#     from apps.windows.api.routers.router_memory_io import init_router
#     app.include_router(init_router())
#
# File: router_memory_io.py
# Project: ai-breadboard
# Package: apps.windows.api.routers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-05 23:40:00
# =============================================================================

from __future__ import annotations
"""Роутер панели «Память и ввод-вывод»: опрос метрик исключительно из telemetry.db."""

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from logger import logger
from apps.windows.telemetry.sqlite import TelemetryStorage

_MAX_HISTORY = 300

_SQL_HISTORY = (
    "SELECT id, timestamp, memory_total_gb, memory_used_gb, memory_percent, swap_percent, "
    "disk_read_bytes_sec, disk_write_bytes_sec "
    "FROM system_snapshots ORDER BY id DESC LIMIT ?;"
)


class MemoryBlock(BaseModel):
    """Использование оперативной памяти."""
    name: str = Field(default="RAM", description="Тип / название оперативной памяти")
    summary: str = Field(default="", description="Сводка по модулям RAM")
    total_gb: float = Field(default=0.0, description="Всего RAM, GB")
    used_gb: float = Field(default=0.0, description="Занято RAM, GB")
    free_gb: float = Field(default=0.0, description="Свободно RAM, GB")
    percent: float = Field(default=0.0, description="Загрузка RAM, %")
    swap_percent: float = Field(default=0.0, description="Загрузка файла подкачки, %")


class DiskIoBlock(BaseModel):
    """Скорость дискового ввода-вывода."""
    read_bytes_sec: float = Field(default=0.0, description="Скорость чтения, байт/с")
    write_bytes_sec: float = Field(default=0.0, description="Скорость записи, байт/с")
    total_bytes_sec: float = Field(default=0.0, description="Суммарная скорость, байт/с")


class MemoryIoPoint(BaseModel):
    """Точка истории метрик."""
    timestamp: str = Field(default="", description="Время снимка")
    memory_percent: float = Field(default=0.0, description="Загрузка RAM, %")
    read_bytes_sec: float = Field(default=0.0, description="Чтение, байт/с")
    write_bytes_sec: float = Field(default=0.0, description="Запись, байт/с")


class MemoryIoResponse(BaseModel):
    """Ответ GET /api/v1/panel/memory-io."""
    status: str = Field(default="ok", description="Статус ответа")
    name: str = Field(default="RAM", description="Конфигурация памяти")
    timestamp: str = Field(default="", description="Время последнего снимка")
    memory: MemoryBlock = Field(default_factory=MemoryBlock)
    disk_io: DiskIoBlock = Field(default_factory=DiskIoBlock)
    history: List[MemoryIoPoint] = Field(default_factory=list, description="История (от старых к новым)")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Метаданные запроса")


def _f(value: Any) -> float:
    """Приводит значение из БД к float; NULL становится 0.0."""
    return float(value) if value is not None else 0.0


def build_memory_io(rows: List[Dict[str, Any]]) -> MemoryIoResponse:
    """Собирает ответ из строк system_snapshots базы данных.

    Args:
        rows: Строки снимков от новых к старым.

    Returns:
        MemoryIoResponse: Текущие значения и история из БД.
    """
    if not rows:
        return MemoryIoResponse(meta={"source": "telemetry.db", "table": "system_snapshots", "points": 0})

    last = rows[0]
    total = _f(last.get("memory_total_gb"))
    used = _f(last.get("memory_used_gb"))
    read_bps = _f(last.get("disk_read_bytes_sec"))
    write_bps = _f(last.get("disk_write_bytes_sec"))

    ram_name = f"{round(total)} GB RAM" if total > 0 else "RAM"
    ram_summary = ""

    history = [
        MemoryIoPoint(
            timestamp=str(r.get("timestamp") or ""),
            memory_percent=_f(r.get("memory_percent")),
            read_bytes_sec=_f(r.get("disk_read_bytes_sec")),
            write_bytes_sec=_f(r.get("disk_write_bytes_sec")),
        )
        for r in reversed(rows)
    ]
    return MemoryIoResponse(
        name=ram_name,
        timestamp=str(last.get("timestamp") or ""),
        memory=MemoryBlock(
            name=ram_name,
            summary=ram_summary,
            total_gb=round(total, 2),
            used_gb=round(used, 2),
            free_gb=round(max(total - used, 0.0), 2),
            percent=round(_f(last.get("memory_percent")), 1),
            swap_percent=round(_f(last.get("swap_percent")), 1),
        ),
        disk_io=DiskIoBlock(
            read_bytes_sec=round(read_bps, 1),
            write_bytes_sec=round(write_bps, 1),
            total_bytes_sec=round(read_bps + write_bps, 1),
        ),
        history=history,
        meta={"source": "telemetry.db", "table": "system_snapshots", "points": len(history)},
    )


def init_router(storage: Optional[TelemetryStorage] = None) -> APIRouter:
    """Создаёт роутер /api/v1/panel/memory-io.

    Args:
        storage: Хранилище телеметрии (по умолчанию — синглтон TelemetryStorage в режиме read_only).

    Returns:
        APIRouter: Роутер с эндпоинтом GET /api/v1/panel/memory-io.
    """
    router = APIRouter(tags=["Memory IO Panel"])
    store = storage or TelemetryStorage.get_instance(read_only=True)

    @router.get("/api/v1/panel/memory-io", response_model=MemoryIoResponse)
    async def get_panel_memory_io(
        limit: int = Query(default=30, ge=1, le=_MAX_HISTORY, description="Число точек истории"),
    ) -> MemoryIoResponse:
        """Возвращает последние метрики памяти и дискового ввода-вывода исключительно из базы данных telemetry.db."""
        try:
            with store._lock, store._get_connection() as conn:
                rows = [dict(r) for r in conn.execute(_SQL_HISTORY, (limit,)).fetchall()]
            return build_memory_io(rows)
        except Exception as exc:
            logger.error(f"[router_memory_io] Ошибка чтения метрик памяти из БД: {exc}", exc_info=True)
            return MemoryIoResponse(status="error", meta={"source": "telemetry.db", "error": str(exc)})

    return router


__all__ = ["init_router", "build_memory_io", "MemoryIoResponse"]
