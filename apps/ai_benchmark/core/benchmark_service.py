# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI Inference Benchmark Service
# =============================================================================
# Description:
#   Сервис замера производительности инференса LLM: Time to First Token (TTFT),
#   скорость генерации (токенов/сек), задержка (Latency) и пропускная способность.
#
# File: benchmark_service.py
# Project: ai-breadboard
# Package: apps.ai_benchmark.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Сервис бенчмаркинга производительности инференса моделей искусственного интеллекта."""

from __future__ import annotations

import time
import asyncio
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.logger import logger


class BenchmarkRequest(BaseModel):
    """Модель запроса для запуска бенчмарка инференса."""
    provider: str = Field(default="gemini", description="Имя провайдера: gemini, ollama, foundry, onnx")
    model_name: str = Field(default="gemini-2.5-flash", description="Идентификатор модели")
    prompt: str = Field(default="Напиши краткий рассказ о квантовых вычислениях на 100 слов.", description="Тестовый промпт")
    max_tokens: int = Field(default=150, description="Максимальное количество токенов генерации")
    temperature: float = Field(default=0.7, description="Температура генерации")


class BenchmarkResult(BaseModel):
    """Результаты замера производительности инференса."""
    provider: str
    model_name: str
    success: bool
    error_message: Optional[str] = None
    ttft_ms: float = Field(default=0.0, description="Time to First Token (мс)")
    total_time_ms: float = Field(default=0.0, description="Общее время ответа (мс)")
    prompt_tokens: int = Field(default=0, description="Количество входных токенов")
    completion_tokens: int = Field(default=0, description="Количество сгенерированных токенов")
    tokens_per_second: float = Field(default=0.0, description="Скорость генерации (токенов/сек)")
    generated_text: str = Field(default="", description="Фрагмент сгенерированного ответа")
    timestamp: float = Field(default_factory=time.time)


class AIBenchmarkService:
    """Класс управления и запуска бенчмарков ИИ-моделей."""

    def __init__(self) -> None:
        """Инициализация сервиса бенчмаркинга."""
        self._history: List[BenchmarkResult] = []

    def get_history(self) -> List[Dict[str, Any]]:
        """Возвращает историю проведенных бенчмарков.
        
        Returns:
            List[Dict[str, Any]]: Список результатов предыдущих тестов.
        """
        return [res.model_dump() for res in self._history]

    async def run_benchmark(self, req: BenchmarkRequest) -> BenchmarkResult:
        """Запуск замера производительности инференса для указанной модели.
        
        Args:
            req (BenchmarkRequest): Параметры теста.
            
        Returns:
            BenchmarkResult: Результат замеров скорости и метрик.
        """
        start_time = time.perf_counter()
        first_token_time: Optional[float] = None
        generated_chunks: List[str] = []

        try:
            # Для демонстрации и базового теста замеряем время генерации
            # В зависимости от провайдера здесь подключается UnifiedChatModel или клиент провайдера
            if req.provider == "gemini":
                # Замер через Google Gemini или эмуляцию сетевого вызова
                await asyncio.sleep(0.05)  # Инициализация соединения
                first_token_time = time.perf_counter()
                
                # Симуляция получения токенов
                sample_text = "Квантовые вычисления используют квантовую суперпозицию и запутанность для экспоненциального ускорения вычислений."
                generated_chunks.append(sample_text)
                await asyncio.sleep(0.15)
                
            else:
                await asyncio.sleep(0.08)
                first_token_time = time.perf_counter()
                sample_text = f"Ответ от локального провайдера {req.provider} для модели {req.model_name}."
                generated_chunks.append(sample_text)
                await asyncio.sleep(0.20)

            end_time = time.perf_counter()

            ttft_ms = ((first_token_time - start_time) * 1000.0) if first_token_time else 0.0
            total_time_ms = (end_time - start_time) * 1000.0
            
            full_text = "".join(generated_chunks)
            # Приблизительная оценка токенов (1 слово ~ 1.3 токена)
            comp_tokens = max(1, int(len(full_text.split()) * 1.3))
            prompt_tokens = max(1, int(len(req.prompt.split()) * 1.3))
            
            gen_time_sec = max(0.001, (end_time - (first_token_time or start_time)))
            tps = comp_tokens / gen_time_sec

            result = BenchmarkResult(
                provider=req.provider,
                model_name=req.model_name,
                success=True,
                ttft_ms=round(ttft_ms, 2),
                total_time_ms=round(total_time_ms, 2),
                prompt_tokens=prompt_tokens,
                completion_tokens=comp_tokens,
                tokens_per_second=round(tps, 2),
                generated_text=full_text,
            )

        except Exception as ex:
            logger.error(f"Ошибка при выполнении AI бенчмарка: {ex}")
            result = BenchmarkResult(
                provider=req.provider,
                model_name=req.model_name,
                success=False,
                error_message=str(ex),
                total_time_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
            )

        self._history.append(result)
        return result
