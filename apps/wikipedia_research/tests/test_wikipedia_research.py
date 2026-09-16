# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Wikipedia Research Test Suite
# =============================================================================
# Description:
#   Comprehensive unit and integration tests for Wikipedia Research application:
#   article collection, normalizer, AI analyzer, comparator, and FastAPI router.
#
# File: test_wikipedia_research.py
# Project: ai-breadboard
# Package: apps.wikipedia_research.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Test suite for Wikipedia Research & Model Benchmark application."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from apps.wikipedia_research.src.normalizer import TextNormalizer
from apps.wikipedia_research.src.models import (
    AnalysisDimensions,
    ArticleAnalysisResult,
    LanguageExperimentRequest,
    ModelExperimentRequest,
    WikipediaArticleMeta,
)
from apps.wikipedia_research.src.collector import WikipediaCollector
from apps.wikipedia_research.src.analyzer import WikipediaArticleAnalyzer
from apps.wikipedia_research.src.comparator import ResearchComparator
from apps.wikipedia_research.engine import WikipediaResearchEngine
from apps.wikipedia_research.router import init_router
from fastapi.testclient import TestClient


# ============================================================================
# Тесты нормализатора текста
# ============================================================================

def test_text_normalizer_clean_text():
    """Проверка очистки HTML, wiki-разметки и сносок."""
    raw = "<p>Artificial intelligence is defined as...</p> [1][источник не указан 50 дней] == History =="
    cleaned = TextNormalizer.clean_text(raw)
    assert "<p>" not in cleaned
    assert "[1]" not in cleaned
    assert "### History" in cleaned
    assert "Artificial intelligence" in cleaned


def test_text_normalizer_stats():
    """Проверка подсчета слов и символов."""
    text = "One two three four five"
    words, chars = TextNormalizer.compute_stats(text)
    assert words == 5
    assert chars == len(text)


def test_text_normalizer_sections():
    """Проверка извлечения оглавления и lead section."""
    text = "Lead paragraph text.\n\n### Origins\n\nOrigin text.\n\n### Future\n\nFuture text."
    lead, sections = TextNormalizer.extract_lead_and_sections(text)
    assert "Lead paragraph text" in lead
    assert sections == ["Origins", "Future"]


# ============================================================================
# Тесты Wikipedia Collector (с моками)
# ============================================================================

@pytest.mark.asyncio
async def test_collector_search_article_mock():
    """Тестирование поиска статей через MediaWiki API."""
    collector = WikipediaCollector()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "query": {
            "search": [
                {"title": "Test Article", "pageid": 101, "snippet": "Snippet text", "wordcount": 500}
            ]
        }
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        results = await collector.search_article("Test", lang="en")
        assert len(results) == 1
        assert results[0]["title"] == "Test Article"
        assert results[0]["pageid"] == 101


@pytest.mark.asyncio
async def test_collector_multilingual_articles_mock():
    """Тестирование параллельного сбора статей на разных языках."""
    collector = WikipediaCollector()
    
    with patch.object(collector, "search_article", new_callable=AsyncMock) as mock_search, \
         patch.object(collector, "get_langlinks", new_callable=AsyncMock) as mock_langlinks, \
         patch.object(collector, "fetch_article", new_callable=AsyncMock) as mock_fetch:
        
        mock_search.return_value = [{"title": "AI"}]
        mock_langlinks.return_value = {"en": "AI", "ru": "ИИ"}
        
        mock_fetch.side_effect = lambda title, lang: WikipediaArticleMeta(
            lang=lang,
            title=title,
            url=f"https://{lang}.wikipedia.org/wiki/{title}",
            extract=f"Summary for {title}",
            full_text=f"Full text for {title}",
            word_count=100,
            char_count=500,
        )
        
        res = await collector.collect_multilingual_articles("AI", ["en", "ru"])
        assert "en" in res
        assert "ru" in res
        assert res["en"].title == "AI"
        assert res["ru"].title == "ИИ"


# ============================================================================
# Тесты AI анализатора и эвристик
# ============================================================================

@pytest.mark.asyncio
async def test_analyzer_with_chat_model_mock():
    """Тестирование анализатора с моком ответа языковой модели."""
    mock_chat = MagicMock()
    mock_json_response = """```json
    {
      "sentiment": -0.15,
      "subjectivity": 0.35,
      "criticism": 0.40,
      "praise": 0.05,
      "uncertainty": 0.20,
      "controversial_claims_count": 3,
      "framing_tone": "critical",
      "key_narratives": ["Escalation", "Humanitarian crisis"],
      "controversial_claims": ["Disputed casualties"],
      "summary_verdict": "Article leans critical."
    }
    ```"""
    mock_chat.ask = AsyncMock(return_value=mock_json_response)

    analyzer = WikipediaArticleAnalyzer(chat_model=mock_chat)
    art = WikipediaArticleMeta(
        lang="en",
        title="Sample War Topic",
        url="https://en.wikipedia.org/wiki/Sample",
        extract="Sample lead",
        full_text="Sample full article content with disputed events.",
    )

    res = await analyzer.analyze_article(art, topic="War Topic", model_name="gemini")
    assert res.metrics.sentiment == -0.15
    assert res.metrics.framing_tone == "critical"
    assert res.metrics.controversial_claims_count == 3
    assert len(res.metrics.key_narratives) == 2


@pytest.mark.asyncio
async def test_analyzer_heuristic_fallback():
    """Тестирование fallback-режима анализатора при отсутствии модели."""
    analyzer = WikipediaArticleAnalyzer(chat_model=None)
    art = WikipediaArticleMeta(
        lang="he",
        title="Sample Topic",
        url="https://he.wikipedia.org/wiki/Sample",
        extract="Sample",
        full_text="Sample text",
    )
    res = await analyzer.analyze_article(art, topic="Topic", model_name="ollama")
    assert isinstance(res.metrics.sentiment, float)
    assert res.metrics.framing_tone in ["neutral_factual", "critical", "cautious", "defensive", "legalistic"]


# ============================================================================
# Тесты Движка сравнения (Comparator & Engine)
# ============================================================================

@pytest.mark.asyncio
async def test_language_experiment_flow():
    """Тестирование полного цикла Эксперимента A."""
    engine = WikipediaResearchEngine(chat_model=None)
    req = LanguageExperimentRequest(
        topic="Neutral Science Topic",
        languages=["en", "ru"],
        model="gemini",
    )
    report = await engine.run_language_experiment(req)
    assert report.topic == "Neutral Science Topic"
    assert len(report.languages) == 2
    assert len(report.metrics_summary_table) == 2
    assert len(report.cross_language_insights) > 0


@pytest.mark.asyncio
async def test_model_experiment_flow():
    """Тестирование полного цикла Эксперимента B."""
    engine = WikipediaResearchEngine(chat_model=None)
    req = ModelExperimentRequest(
        topic="Neutral Science Topic",
        languages=["en", "ru"],
        models=["gemini", "foundry"],
    )
    report = await engine.run_model_experiment(req)
    assert report.topic == "Neutral Science Topic"
    assert "en" in report.sentiment_grid
    assert "gemini" in report.sentiment_grid["en"]
    assert "foundry" in report.sentiment_grid["en"]
    assert len(report.model_alignment_insights) > 0


# ============================================================================
# Тесты FastAPI эндпоинтов
# ============================================================================

def test_fastapi_endpoints():
    """Тестирование REST API эндпоинтов."""
    from fastapi import FastAPI
    app = FastAPI()
    router = init_router()
    app.include_router(router)
    client = TestClient(app)

    # Health check
    res = client.get("/api/v1/wikipedia-research/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    # Languages
    res = client.get("/api/v1/wikipedia-research/languages")
    assert res.status_code == 200
    assert "en" in res.json()
    assert "ru" in res.json()

    # Models
    res = client.get("/api/v1/wikipedia-research/models")
    assert res.status_code == 200
    models = res.json()
    assert any(m["id"] == "gemini" for m in models)
