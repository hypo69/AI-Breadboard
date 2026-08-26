# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Модели данных подсистемы RAG
# =============================================================================
# Описание:
#   Датаклассы и перечисления для универсального доменно-независимого
#   RAG-поиска и маршрутизации запросов RAG-First.
#
# File: models.py
# Project: ai-assistant
# Package: core.rag
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class RAGDecisionType(str, Enum):
    """Тип решения маршрутизатора RAG."""
    DIRECT_ANSWER = "direct_answer"
    LLM_FALLBACK = "llm_fallback"


@dataclass
class RAGSearchResult:
    """Результат семантического поиска в RAG-индексе."""
    title: str = ""
    file: str = ""
    path: str = ""
    text: str = ""
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RAGRouteDecision:
    """Решение RAG-движка по обработке запроса пользователя."""
    decision_type: RAGDecisionType = RAGDecisionType.LLM_FALLBACK
    is_direct: bool = False
    direct_text: str = ""
    direct_voice: str = ""
    context_text: str = ""
    confidence_score: float = 0.0
    raw_results: List[Dict[str, Any]] = field(default_factory=list)
    status_message: str = ""
