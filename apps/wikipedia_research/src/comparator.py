# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Cross-Language & Cross-Model Comparison Engine
# =============================================================================
# Description:
#   Computes comparative deltas, divergence matrices, alignment scores,
#   and cross-cutting analytical summaries for Experiment A (Language Comparison)
#   and Experiment B (Multi-Model AI Comparison).
#
# File: comparator.py
# Project: ai-breadboard
# Package: apps.wikipedia_research.src
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Comparison engine for language editions (Exp A) and AI model benchmark (Exp B)."""

from __future__ import annotations

import statistics
import uuid
from typing import Any, Dict, List

from .models import (
    ArticleAnalysisResult,
    LanguageComparisonReport,
    ModelComparisonReport,
    WikipediaArticleMeta,
)


class ResearchComparator:
    """Движок сравнительного анализа языковых разделов и моделей ИИ."""

    @staticmethod
    def build_language_comparison_report(
        topic: str,
        model_used: str,
        articles: Dict[str, WikipediaArticleMeta],
        results: Dict[str, ArticleAnalysisResult],
    ) -> LanguageComparisonReport:
        """Формирует отчет Эксперимента A: сравнение языковых версий темы одной моделью.

        Args:
            topic (str): Тема исследования.
            model_used (str): Использованная AI-модель.
            articles (Dict[str, WikipediaArticleMeta]): Собранные статьи.
            results (Dict[str, ArticleAnalysisResult]): Результаты анализа по языкам.

        Returns:
            LanguageComparisonReport: Итоговый отчет с таблицей и инсайтами.
        """
        languages = list(results.keys())
        summary_table: List[Dict[str, Any]] = []

        sentiments: List[float] = []
        subjectivities: List[float] = []

        for lang in languages:
            res = results[lang]
            art = articles.get(lang)
            m = res.metrics

            sentiments.append(m.sentiment)
            subjectivities.append(m.subjectivity)

            summary_table.append(
                {
                    "lang": lang,
                    "title": res.article_title,
                    "sentiment": m.sentiment,
                    "subjectivity": m.subjectivity,
                    "criticism": m.criticism,
                    "praise": m.praise,
                    "uncertainty": m.uncertainty,
                    "claims_count": m.controversial_claims_count,
                    "framing": m.framing_tone,
                    "word_count": art.word_count if art else 0,
                    "pageviews_30d": art.pageviews_last_30d if art else None,
                    "url": res.article_url,
                }
            )

        # Вычисление инсайтов и расхождений
        insights: List[str] = []
        if sentiments:
            max_s = max(sentiments)
            min_s = min(sentiments)
            diff_s = round(max_s - min_s, 3)

            max_lang = languages[sentiments.index(max_s)]
            min_lang = languages[sentiments.index(min_s)]

            insights.append(
                f"Разброс тональности между языками составляет {diff_s} "
                f"(наиболее позитивный: [{max_lang}] {max_s:+.2f}, наиболее критический: [{min_lang}] {min_s:+.2f})."
            )

        if subjectivities:
            avg_subj = round(statistics.mean(subjectivities), 3)
            insights.append(f"Средний уровень субъективности по всем языковым разделам: {avg_subj:.2f}.")

        # Инсайты по фреймингу
        framings = {results[lang].metrics.framing_tone for lang in languages}
        if len(framings) > 1:
            insights.append(
                f"Обнаружена поляризация нарративных рамок: {', '.join(sorted(framings))}."
            )
        else:
            insights.append("Все исследованные языковые разделы используют единый доминирующий фрейминг.")

        exp_id = f"exp_lang_{uuid.uuid4().hex[:8]}"

        return LanguageComparisonReport(
            experiment_id=exp_id,
            topic=topic,
            model_used=model_used,
            languages=languages,
            articles=articles,
            results=results,
            metrics_summary_table=summary_table,
            cross_language_insights=insights,
        )

    @staticmethod
    def build_model_comparison_report(
        topic: str,
        languages: List[str],
        models: List[str],
        matrix: Dict[str, Dict[str, ArticleAnalysisResult]],
    ) -> ModelComparisonReport:
        """Формирует отчет Эксперимента B: сравнение оценки статей разными AI-моделями.

        Args:
            topic (str): Тема исследования.
            languages (List[str]): Список языков.
            models (List[str]): Список моделей.
            matrix (Dict[str, Dict[str, ArticleAnalysisResult]]): Матрица [lang][model].

        Returns:
            ModelComparisonReport: Сводный отчет кросс-модельного бенчмарка.
        """
        sentiment_grid: Dict[str, Dict[str, float]] = {}
        subjectivity_grid: Dict[str, Dict[str, float]] = {}

        for lang in languages:
            sentiment_grid[lang] = {}
            subjectivity_grid[lang] = {}
            for model in models:
                res = matrix.get(lang, {}).get(model)
                if res:
                    sentiment_grid[lang][model] = res.metrics.sentiment
                    subjectivity_grid[lang][model] = res.metrics.subjectivity

        # Анализ согласованности моделей (Model Alignment Insights)
        alignment_insights: List[str] = []

        for lang in languages:
            scores = [sentiment_grid[lang][m] for m in models if m in sentiment_grid.get(lang, {})]
            if len(scores) > 1:
                spread = round(max(scores) - min(scores), 3)
                std_dev = round(statistics.stdev(scores), 3) if len(scores) > 1 else 0.0
                alignment_insights.append(
                    f"Языковой раздел [{lang}]: разброс тональности между моделями = {spread} (σ = {std_dev})."
                )

        # Проверка знака тональности
        for lang in languages:
            signs = [
                (m, sentiment_grid[lang][m])
                for m in models
                if m in sentiment_grid.get(lang, {})
            ]
            pos_models = [m for m, s in signs if s > 0.05]
            neg_models = [m for m, s in signs if s < -0.05]

            if pos_models and neg_models:
                alignment_insights.append(
                    f"⚠️ Полярное расхождение в оценке [{lang}]: модели {pos_models} оценили как умеренно позитивную, а {neg_models} — как негативную."
                )

        exp_id = f"exp_models_{uuid.uuid4().hex[:8]}"

        return ModelComparisonReport(
            experiment_id=exp_id,
            topic=topic,
            languages=languages,
            models=models,
            matrix=matrix,
            sentiment_grid=sentiment_grid,
            subjectivity_grid=subjectivity_grid,
            model_alignment_insights=alignment_insights,
        )
