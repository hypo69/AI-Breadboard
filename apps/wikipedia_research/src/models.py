# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Wikipedia Research Pydantic Data Models
# =============================================================================
# Description:
#   Data models and schemas for Wikipedia article collection, multidimensional
#   AI analysis metrics, language comparison (Exp A), and model benchmark (Exp B).
#
# File: models.py
# Project: ai-breadboard
# Package: apps.wikipedia_research.src
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Pydantic schemas and data models for Wikipedia Research Laboratory."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WikipediaArticleMeta(BaseModel):
    """Метаданные статьи Wikipedia на конкретном языке."""
    lang: str = Field(..., description="Код языка статьи (en, ru, he, de, fr и т.д.)")
    title: str = Field(..., description="Заголовок статьи в данном языковом разделе")
    url: str = Field(..., description="Прямой URL страницы Википедии")
    page_id: Optional[int] = Field(default=None, description="Идентификатор страницы в Wikipedia")
    extract: str = Field(default="", description="Вводная выжимка статьи (lead section)")
    full_text: str = Field(default="", description="Нормализованный текстовый контент статьи")
    word_count: int = Field(default=0, description="Количество слов")
    char_count: int = Field(default=0, description="Количество символов")
    sections: List[str] = Field(default_factory=list, description="Список разделов/оглавление статьи")
    pageviews_last_30d: Optional[int] = Field(default=None, description="Количество просмотров за 30 дней")
    langlinks: Dict[str, str] = Field(default_factory=dict, description="Интервики-ссылки {lang_code: title}")


class AnalysisDimensions(BaseModel):
    """Измерения анализа статьи по шкалам и аспектам."""
    sentiment: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Тональность от -1.0 (резко негативная) до +1.0 (резко позитивная)",
    )
    subjectivity: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Степень субъективности от 0.0 (строго нейтрально-фактологично) до 1.0 (субъективно)",
    )
    criticism: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Уровень критических акцентов от 0.0 (нет критики) до 1.0 (сильная критика)",
    )
    praise: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Уровень хвалебных/апологетических акцентов от 0.0 до 1.0",
    )
    uncertainty: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Уровень неопределенности/спекуляций и предположений от 0.0 до 1.0",
    )
    controversial_claims_count: int = Field(
        default=0,
        ge=0,
        description="Количество зафиксированных спорных или поляризующих утверждений",
    )
    framing_tone: str = Field(
        default="neutral",
        description="Преобладающий нарративный фрейминг (neutral, defensive, critical, heroic, legalistic, etc.)",
    )
    key_narratives: List[str] = Field(
        default_factory=list,
        description="Ключевые смысловые нарративы и акценты, выделенные моделью",
    )
    controversial_claims: List[str] = Field(
        default_factory=list,
        description="Список выявленных спорных или дискуссионных тезисов",
    )
    summary_verdict: str = Field(
        default="",
        description="Краткий аналитический вердикт модели по нейтральности и подаче материала",
    )


class ArticleAnalysisResult(BaseModel):
    """Результат анализа одной статьи одной моделью."""
    topic: str = Field(..., description="Исследуемая тема")
    lang: str = Field(..., description="Язык статьи")
    model_name: str = Field(..., description="Имя/идентификатор задействованной AI-модели")
    article_title: str = Field(..., description="Заголовок статьи")
    article_url: str = Field(..., description="URL статьи")
    metrics: AnalysisDimensions = Field(..., description="Оценки и измерения анализа")
    created_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Временная метка выполнения",
    )
    raw_response: Optional[str] = Field(default=None, description="Сырой ответ модели при отладке")


class LanguageComparisonReport(BaseModel):
    """Отчет эксперимента A: сравнение одной темы в разных языковых разделах одной моделью."""
    experiment_id: str = Field(..., description="Уникальный ID эксперимента")
    experiment_type: str = Field(default="language_comparison", description="Тип эксперимента")
    topic: str = Field(..., description="Тема исследования")
    model_used: str = Field(..., description="Модель, проводившая анализ всех языков")
    languages: List[str] = Field(..., description="Список исследованных языков")
    articles: Dict[str, WikipediaArticleMeta] = Field(
        default_factory=dict,
        description="Метаданные собранных статей по языкам",
    )
    results: Dict[str, ArticleAnalysisResult] = Field(
        default_factory=dict,
        description="Результаты анализа по языкам {lang_code: result}",
    )
    metrics_summary_table: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Сводная таблица сравнения метрик между языками",
    )
    cross_language_insights: List[str] = Field(
        default_factory=list,
        description="Выводы о расхождениях в подаче темы между языковыми разделами",
    )
    created_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Время генерации",
    )


class ModelComparisonReport(BaseModel):
    """Отчет эксперимента B: сравнение интерпретации статей разными AI-моделями."""
    experiment_id: str = Field(..., description="Уникальный ID эксперимента")
    experiment_type: str = Field(default="model_comparison", description="Тип эксперимента")
    topic: str = Field(..., description="Тема исследования")
    languages: List[str] = Field(..., description="Исследуемые языки")
    models: List[str] = Field(..., description="Список участвовавших AI-моделей")
    matrix: Dict[str, Dict[str, ArticleAnalysisResult]] = Field(
        default_factory=dict,
        description="Матрица результатов {lang: {model_name: result}}",
    )
    sentiment_grid: Dict[str, Dict[str, float]] = Field(
        default_factory=dict,
        description="Сетка тональности {lang: {model_name: sentiment_score}}",
    )
    subjectivity_grid: Dict[str, Dict[str, float]] = Field(
        default_factory=dict,
        description="Сетка субъективности {lang: {model_name: subjectivity_score}}",
    )
    model_alignment_insights: List[str] = Field(
        default_factory=list,
        description="Анализ согласованности моделей и расхождений в их оценках",
    )
    created_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Время генерации",
    )


class LanguageExperimentRequest(BaseModel):
    """Запрос на запуск эксперимента сравнения языков (Experiment A)."""
    topic: str = Field(..., description="Тема для поиска в Википедии")
    languages: List[str] = Field(
        default=["en", "ru", "he", "de", "fr"],
        description="Список кодов языков",
    )
    model: str = Field(default="gemini", description="Модель для анализа")
    dimensions: List[str] = Field(
        default=["sentiment", "subjectivity", "criticism", "praise", "uncertainty", "controversial_claims", "framing"],
        description="Выбранные аспекты анализа",
    )


class ModelExperimentRequest(BaseModel):
    """Запрос на запуск эксперимента сравнения моделей (Experiment B)."""
    topic: str = Field(..., description="Тема для поиска в Википедии")
    languages: List[str] = Field(
        default=["en", "ru", "he"],
        description="Список языков",
    )
    models: List[str] = Field(
        default=["gemini", "foundry", "ollama"],
        description="Список моделей для сопоставления",
    )
    dimensions: List[str] = Field(
        default=["sentiment", "subjectivity", "criticism", "praise", "uncertainty", "controversial_claims", "framing"],
        description="Выбранные аспекты анализа",
    )
