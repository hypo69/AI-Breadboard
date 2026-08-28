# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Модульные тесты подсистемы Core RAG
# =============================================================================
# Описание:
#   Тестирование чистых модулей core.rag:
#   - RAGDecisionType, RAGRouteDecision, RAGSearchResult (models.py)
#   - RulesRAG (rules_rag.py)
#   - RAGEngine (engine.py): поиск по базе знаний, проверка threshold, fallback к LLM
#
# File: test_core_rag.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from core.rag.models import RAGDecisionType, RAGRouteDecision, RAGSearchResult
from core.rag.rules_rag import RulesRAG, build_rules_index, collect_prompt_documents
from core.rag.engine import RAGEngine, get_rag_engine


class TestCoreRagModels:
    """Тесты моделей данных RAG."""

    def test_decision_types(self):
        assert RAGDecisionType.DIRECT_ANSWER == "direct_answer"
        assert RAGDecisionType.LLM_FALLBACK == "llm_fallback"

    def test_route_decision_default(self):
        decision = RAGRouteDecision()
        assert decision.decision_type == RAGDecisionType.LLM_FALLBACK
        assert not decision.is_direct
        assert decision.direct_text == ""
        assert decision.direct_voice == ""
        assert decision.context_text == ""
        assert decision.confidence_score == 0.0

    def test_search_result_model(self):
        res = RAGSearchResult(title="Doc 1", text="Sample content", score=0.95)
        assert res.title == "Doc 1"
        assert res.text == "Sample content"
        assert res.score == 0.95


class TestRulesRag:
    """Тесты сборщика и поиска по промптам RulesRAG."""

    def test_collect_prompt_documents(self):
        docs = collect_prompt_documents()
        assert len(docs) > 0
        assert any(d["file"] == "identity.md" for d in docs)

    def test_rules_rag_search_and_context(self):
        mock_model = MagicMock()
        mock_model.encode.return_value = MagicMock(astype=lambda x: MagicMock())
        mock_st_class = MagicMock(return_value=mock_model)
        mock_st_mod = MagicMock(SentenceTransformer=mock_st_class)

        mock_index = MagicMock()
        mock_index.search.return_value = ([[0.1, 0.5]], [[0, 1]])
        mock_faiss_mod = MagicMock()
        mock_faiss_mod.read_index.return_value = mock_index

        import sys
        with patch.dict(sys.modules, {"faiss": mock_faiss_mod, "sentence_transformers": mock_st_mod}), \
             patch("pathlib.Path.exists", return_value=True), \
             patch("pathlib.Path.read_text", return_value='[{"file": "identity.md", "path": "core/identity.md", "text": "Я ассистент"}, {"file": "narrator.md", "path": "narrator.md", "text": "Текст диктора"}]'):
            rag = RulesRAG()
            results = rag.search("диктора", top_k=2)
            assert len(results) == 2
            assert results[0].file == "identity.md"
            assert results[0].score == 0.1

            ctx = rag.build_context("диктора", top_k=2)
            assert "Я ассистент" in ctx
            assert "Текст диктора" in ctx


@pytest.mark.asyncio
class TestRagEngine:
    """Тесты универсального движка RAG-First (RAGEngine)."""

    async def test_engine_empty_query(self):
        engine = RAGEngine()
        decision = await engine.evaluate("")
        assert decision.is_direct
        assert decision.decision_type == RAGDecisionType.DIRECT_ANSWER
        assert "Пожалуйста, введите запрос" in decision.direct_text

    async def test_engine_direct_match_high_score(self):
        engine = RAGEngine(direct_threshold=0.8)
        mock_history = [{"text": "Это готовый ответ из базы знаний", "score": 0.92}]

        with patch("core.rag.engine.search_user_history", new_callable=AsyncMock, return_value=mock_history):
            decision = await engine.evaluate(
                query="Как настроить проект?",
                user_identifier="user_1",
                api_key="secret_key"
            )
            assert decision.is_direct
            assert decision.decision_type == RAGDecisionType.DIRECT_ANSWER
            assert decision.direct_text == "Это готовый ответ из базы знаний"
            assert decision.confidence_score == 0.92

    async def test_engine_llm_fallback_low_score(self):
        engine = RAGEngine(direct_threshold=0.85)
        mock_history = [{"text": "Фрагмент контекста по теме", "score": 0.60}]

        with patch("core.rag.engine.search_user_history", new_callable=AsyncMock, return_value=mock_history), \
             patch("core.rag.engine.get_user_preferences_context", new_callable=AsyncMock, return_value="Любит краткие ответы"):
            decision = await engine.evaluate(
                query="Расскажи что-нибудь новое",
                user_identifier="user_1",
                api_key="secret_key"
            )
            assert not decision.is_direct
            assert decision.decision_type == RAGDecisionType.LLM_FALLBACK
            assert "Фрагмент контекста по теме" in decision.context_text
            assert "Любит краткие ответы" in decision.context_text

    async def test_engine_singleton(self):
        engine1 = get_rag_engine()
        engine2 = get_rag_engine()
        assert engine1 is engine2
