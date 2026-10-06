# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard API - Router System Module
# =============================================================================
# Description:
#   Системный роутер FastAPI для предоставления диагностических и телеметрических эндпоинтов.
#
#   Зачем нужен этот модуль:
#     1. Предоставление системной телеметрии: эндпоинты для получения текущих снимков системы
#        (CPU, память, процессы, сенсоры) через интеграцию с SystemCollector.
#     2. Интеллектуальная диагностика: интеграция с SystemDiagnosticEngine и GroupedTelemetryBuilder
#        для выявления аномалий, группировки метрик и генерации рекомендаций.
#     3. Единый фасад для UI и агентов: прозрачный доступ фронтенда и LLM к данным о состоянии хоста.
#
# Usage Examples:
#   Python API:
#     from fastapi import FastAPI
#     from src.api.routers.core.router_system import router as system_router
#
#     app = FastAPI()
#     app.include_router(system_router, prefix="/api/system")
#
# File: router_system.py
# Project: ai-breadboard
# Package: src.api.routers.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 00:25:00
# =============================================================================

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter
from apps.windows.telemetry import SystemCollector
from apps.windows.telemetry_research.diagnostic_engine import SystemDiagnosticEngine
from apps.windows.telemetry_research.grouped_telemetry import (
    GroupDiagnoseRequest,
    GroupDiagnosticResult,
    GroupedTelemetryBuilder,
    SynthesisDiagnosticResult,
    SynthesisRequest,
    TelemetryGroupInfo,
)

router = APIRouter(prefix="/api/v1/system", tags=["system-diagnostics"])
_collector: Optional[SystemCollector] = None
_diagnostician: Optional[SystemDiagnosticEngine] = None
_builder = GroupedTelemetryBuilder()


def get_collector() -> SystemCollector:
    """Получить экземпляр системного коллектора."""
    global _collector
    if _collector is None:
        _collector = SystemCollector()
    return _collector


def get_diagnostician(chat_model: Optional[Any] = None) -> SystemDiagnosticEngine:
    """Получить экземпляр системного диагноста."""
    global _diagnostician
    if _diagnostician is None or chat_model is not None:
        _diagnostician = SystemDiagnosticEngine(chat_model=chat_model)
    return _diagnostician


@router.get("/router_system/ping", tags=["system-diagnostics"])
async def ping() -> dict:
    """Проверка доступности роутера."""
    return {"status": "ok"}


@router.get("/diagnose/groups", response_model=List[TelemetryGroupInfo])
async def get_diagnose_groups() -> List[TelemetryGroupInfo]:
    """Возвращает срез телеметрии, разбитый на 4 специализированные группы."""
    collector = get_collector()
    snapshot = await collector.get_snapshot(process_limit=15)
    return _builder.build_all_groups(snapshot)


@router.post("/diagnose/group", response_model=GroupDiagnosticResult)
async def diagnose_group_endpoint(req: GroupDiagnoseRequest) -> GroupDiagnosticResult:
    """Диагностика одной группы телеметрии."""
    diagnostician = get_diagnostician()
    return await diagnostician.diagnose_group(
        group_id=req.group_id,
        payload=req.payload,
        title=req.title or req.group_id,
    )


@router.post("/diagnose/synthesize", response_model=SynthesisDiagnosticResult)
async def synthesize_diagnostics_endpoint(req: SynthesisRequest) -> SynthesisDiagnosticResult:
    """Синтез общего вердикта и индекса здоровья по всем доменам."""
    diagnostician = get_diagnostician()
    return await diagnostician.synthesize_final_report(req.groups)


def init_router(chat_model: Optional[Any] = None) -> APIRouter:
    """Инициализация и возврат системного роутера."""
    if chat_model is not None:
        get_diagnostician(chat_model=chat_model)
    return router