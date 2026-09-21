# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI Benchmark Unit Tests
# =============================================================================
# Description:
#   Тесты для модуля бенчмаркинга инференса ИИ-моделей.
#
# File: test_ai_benchmark.py
# Project: ai-breadboard
# Package: apps.ai_benchmark.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Тесты для сервиса и роутера бенчмаркинга ИИ-моделей."""

import pytest
from apps.ai_benchmark.core.benchmark_service import AIBenchmarkService, BenchmarkRequest


@pytest.mark.asyncio
async def test_ai_benchmark_service_run() -> None:
    """Тест выполнения замера инференса модели."""
    service = AIBenchmarkService()
    req = BenchmarkRequest(
        provider="gemini",
        model_name="gemini-2.5-flash",
        prompt="Тестовый запрос",
        max_tokens=50
    )
    result = await service.run_benchmark(req)
    assert result.success is True
    assert result.tokens_per_second > 0.0
    assert result.total_time_ms > 0.0
    assert len(service.get_history()) == 1


@pytest.mark.asyncio
async def test_ai_benchmark_router_status() -> None:
    """Тест эндпоинта проверки статуса бенчмарка."""
    from apps.ai_benchmark.router import get_status
    status = await get_status()
    assert status["status"] == "ready"
    assert "gemini" in status["supported_providers"]
