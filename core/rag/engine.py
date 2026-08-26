# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Универсальный RAG-движок (Core RAG Engine)
# =============================================================================
# Описание:
#   Реализует чистый доменно-независимый алгоритм RAG-First:
#   1. Поиск по базе знаний и истории ответов.
#   2. Если найден точный/высокорелевантный ответ (Score >= threshold) -> возврат ответа напрямую.
#   3. Если прямого ответа нет -> формирование обогащенного RAG-контекста для LLM.
#
# File: engine.py
# Project: ai-assistant
# Package: core.rag
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from core.logger import logger
from core.rag.models import RAGDecisionType, RAGRouteDecision, RAGSearchResult
from core.rag.user_rag import search_user_history, get_user_preferences_context


class RAGEngine:
    """
    ## hypo69 docblock
    Универсальный координатор поиска по базе знаний и маршрутизации RAG-First.
    """

    def __init__(self, direct_threshold: float = 0.85) -> None:
        """
        ## hypo69 docblock
        Инициализация RAG-движка.

        Args:
            direct_threshold (float): Порог уверенности для прямого возврата ответа без вызова LLM.
        """
        self.direct_threshold = direct_threshold

    async def evaluate(
        self,
        query: str,
        user_identifier: str = "",
        api_key: str = "",
        threshold: Optional[float] = None
    ) -> RAGRouteDecision:
        """
        ## hypo69 docblock
        Оценивает входящий запрос: ищет готовый ответ в базе или готовит контекст для LLM.

        Args:
            query (str): Запрос пользователя.
            user_identifier (str): Идентификатор пользователя.
            api_key (str): Ключ API.
            threshold (Optional[float]): Порог уверенности для прямого ответа.

        Returns:
            RAGRouteDecision: Решение движка (прямой ответ или fallback к модели).
        """
        clean_query = query.strip()
        if not clean_query:
            return RAGRouteDecision(
                decision_type=RAGDecisionType.DIRECT_ANSWER,
                is_direct=True,
                direct_text="Пожалуйста, введите запрос.",
                direct_voice="Пожалуйста, введите запрос.",
            )

        active_threshold = threshold if threshold is not None else self.direct_threshold
        context_parts: List[str] = []

        # 1. Поиск по базе знаний / предыдущим сохраненным ответам
        if user_identifier and api_key and len(clean_query) >= 3:
            results = await search_user_history(
                user_identifier,
                api_key,
                clean_query,
                top_k=3,
                threshold=0.45
            )

            if results:
                best_match = results[0]
                best_score = float(best_match.get("score", 0.0))

                # Если есть точный ответ с высоким качеством совпадения
                if best_score >= active_threshold and best_match.get("text"):
                    matched_text = best_match["text"].strip()
                    logger.info(f"[RAGEngine] Найден прямой ответ в RAG (score={best_score:.2f} >= {active_threshold})")
                    return RAGRouteDecision(
                        decision_type=RAGDecisionType.DIRECT_ANSWER,
                        is_direct=True,
                        direct_text=matched_text,
                        direct_voice=matched_text,
                        confidence_score=best_score,
                        raw_results=results,
                        status_message="⚡ Ответ найден в базе знаний...",
                    )

                # Иначе собираем найденные фрагменты как контекст для LLM
                snippets = [item["text"].strip() for item in results if item.get("text")]
                if snippets:
                    context_parts.append("[Контекст из базы знаний]:\n" + "\n---\n".join(snippets))

        # 2. Добавление профиля предпочтений пользователя (если доступно)
        if user_identifier:
            pref_context = await get_user_preferences_context(user_identifier)
            if pref_context:
                context_parts.append(f"[Профиль предпочтений]:\n{pref_context}")

        return RAGRouteDecision(
            decision_type=RAGDecisionType.LLM_FALLBACK,
            is_direct=False,
            context_text="\n\n".join(context_parts),
            confidence_score=0.0,
            status_message="Генерация ответа...",
        )


_engine_instance: Optional[RAGEngine] = None


def get_rag_engine() -> RAGEngine:
    """
    ## hypo69 docblock
    Возвращает синглтон RAGEngine.
    """
    global _engine_instance
    if not _engine_instance:
        _engine_instance = RAGEngine()
    return _engine_instance
