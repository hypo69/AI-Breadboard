# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI Benchmark FastAPI Router
# =============================================================================
# Description:
#   FastAPI REST API роутер для модуля тестирования и бенчмаркинга ИИ-моделей.
#
# File: router.py
# Project: ai-breadboard
# Package: apps.ai_benchmark
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI REST API роутер для модуля бенчмаркинга моделей ИИ."""

from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter

from apps.ai_benchmark.core.benchmark_service import (
    AIBenchmarkService,
    BenchmarkRequest,
    BenchmarkResult,
)

router = APIRouter(prefix="/api/v1/ai_benchmark", tags=["ai_benchmark"])
_service = AIBenchmarkService()


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """Проверка доступности модуля бенчмаркинга."""
    return {
        "status": "ready",
        "supported_providers": ["gemini", "ollama", "foundry", "onnx"],
        "history_count": len(_service.get_history()),
    }


@router.post("/run", response_model=BenchmarkResult)
async def run_benchmark(request: BenchmarkRequest) -> BenchmarkResult:
    """Запуск бенчмарка инференса указанной модели."""
    return await _service.run_benchmark(request)


@router.get("/history")
async def get_history() -> List[Dict[str, Any]]:
    """Получение истории замеров производительности."""
    return _service.get_history()


def init_router() -> APIRouter:
    """Фабричная функция инициализации роутера.
    
    Returns:
        APIRouter: Сконфигурированный экземпляр роутера.
    """
    return router
