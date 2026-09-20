# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Wikipedia Research FastAPI Router
# =============================================================================
# Description:
#   REST API endpoints for Wikipedia article searching, cross-language
#   comparison (Experiment A), multi-model benchmarks (Experiment B), and
#   supported language/model discovery.
#
# File: router.py
# Project: ai-breadboard
# Package: apps.wikipedia_research
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI router for Wikipedia Research & Model Benchmark application."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query

from src.logger import logger
from apps.common.csv_logger import AppCsvLogger
from .engine import WikipediaResearchEngine
from .src.collector import SUPPORTED_LANGUAGES
from .src.models import (
    LanguageComparisonReport,
    LanguageExperimentRequest,
    ModelComparisonReport,
    ModelExperimentRequest,
)

_default_engine: Optional[WikipediaResearchEngine] = None
_csv_logger = AppCsvLogger("wikipedia_research")


def get_engine(chat_model: Any = None) -> WikipediaResearchEngine:
    """Получение или создание синглтона движка WikipediaResearchEngine."""
    global _default_engine
    if _default_engine is None:
        _default_engine = WikipediaResearchEngine(chat_model=chat_model)
    elif chat_model is not None and _default_engine.analyzer.chat_model is None:
        _default_engine.analyzer.chat_model = chat_model
    return _default_engine


def init_router(state: Any = None) -> APIRouter:
    """Инициализация и настройка FastAPI роутера для Wikipedia Research.

    Args:
        state (Any): AppState объект сервера с инициализированными моделями.

    Returns:
        APIRouter: Сконфигурированный роутер.
    """
    router = APIRouter(prefix="/api/v1/wikipedia-research", tags=["Wikipedia Research"])

    chat_model = getattr(state, "chat_model", None) if state else None
    engine = get_engine(chat_model=chat_model)

    @router.get("/health")
    async def health_check() -> Dict[str, str]:
        """Проверка работоспособности сервиса исследований Википедии."""
        _csv_logger.log_poll(
            poll_type="health",
            metric_name="service_health",
            value="ok",
            unit="status",
            status="ok",
            filename="wikipedia_research_polls.csv",
        )
        return {"status": "ok", "app": "wikipedia_research"}

    @router.get("/languages")
    async def get_supported_languages() -> Dict[str, str]:
        """Возвращает список поддерживаемых языковых разделов Википедии."""
        return SUPPORTED_LANGUAGES

    @router.get("/models")
    async def get_available_models() -> List[Dict[str, str]]:
        """Возвращает список рекомендуемых AI-моделей для сравнительного анализа."""
        return [
            {"id": "gemini", "name": "Google Gemini (Default)", "provider": "gemini"},
            {"id": "foundry", "name": "Microsoft Foundry Local", "provider": "foundry"},
            {"id": "ollama", "name": "Ollama Local LLM", "provider": "ollama"},
            {"id": "onnx", "name": "ONNX Runtime / DirectML", "provider": "onnx"},
            {"id": "openai:gpt-4o-mini", "name": "OpenAI GPT-4o-mini", "provider": "openai"},
            {"id": "deepseek:deepseek-chat", "name": "DeepSeek V3", "provider": "deepseek"},
        ]

    @router.get("/search")
    async def search_wikipedia(
        query: str = Query(..., description="Поисковый запрос"),
        lang: str = Query(default="en", description="Код языка (en, ru, he, de, fr и т.д.)"),
    ) -> List[Dict[str, Any]]:
        """Поиск статей в Википедии по ключевым словам."""
        try:
            results = await engine.search_topics(query, lang=lang)
            _csv_logger.log_event(
                event_type="search_topics",
                status="ok",
                details=f"query={query},lang={lang},found={len(results)}",
                filename="wikipedia_research_events.csv",
            )
            return results
        except Exception as ex:
            logger.error(f"Error searching Wikipedia: {ex}", exc_info=True)
            _csv_logger.log_event(
                event_type="search_topics_failed",
                status="error",
                details=f"query={query},lang={lang},error={ex}",
                filename="wikipedia_research_events.csv",
            )
            raise HTTPException(status_code=500, detail=str(ex))

    @router.post("/experiment/languages", response_model=LanguageComparisonReport)
    async def run_language_experiment(req: LanguageExperimentRequest) -> LanguageComparisonReport:
        """Запуск Эксперимента A: Сравнение представления темы в разных языковых разделах Википедии."""
        try:
            rep = await engine.run_language_experiment(req)
            _csv_logger.log_event(
                event_type="language_experiment_completed",
                status="ok",
                details=f"topic={req.topic},languages={','.join(req.languages)}",
                filename="wikipedia_research_events.csv",
            )
            return rep
        except Exception as ex:
            logger.error(f"Error in Language Experiment: {ex}", exc_info=True)
            _csv_logger.log_event(
                event_type="language_experiment_failed",
                status="error",
                details=f"topic={req.topic},error={ex}",
                filename="wikipedia_research_events.csv",
            )
            raise HTTPException(status_code=500, detail=f"Language Experiment Failed: {ex}")

    @router.post("/experiment/models", response_model=ModelComparisonReport)
    async def run_model_experiment(req: ModelExperimentRequest) -> ModelComparisonReport:
        """Запуск Эксперимента B: Сравнение интерпретации статей темы различными моделями ИИ."""
        try:
            rep = await engine.run_model_experiment(req)
            _csv_logger.log_event(
                event_type="model_experiment_completed",
                status="ok",
                details=f"topic={req.topic},models={','.join(req.model_ids)}",
                filename="wikipedia_research_events.csv",
            )
            return rep
        except Exception as ex:
            logger.error(f"Error in Model Experiment: {ex}", exc_info=True)
            _csv_logger.log_event(
                event_type="model_experiment_failed",
                status="error",
                details=f"topic={req.topic},error={ex}",
                filename="wikipedia_research_events.csv",
            )
            raise HTTPException(status_code=500, detail=f"Model Experiment Failed: {ex}")

    @router.get("/history")
    async def get_experiments_history() -> List[Any]:
        """Получение списка ранее проведенных экспериментов в текущей сессии."""
        return engine.get_history()

    logger.debug("Wikipedia Research router successfully initialized.")
    return router
