"""Central research engine coordinating collection, multi-model execution, and reports."""
from __future__ import annotations
import asyncio
from typing import Any, Dict, List, Optional
from logger import logger
from .src.analyzer import WikipediaArticleAnalyzer
from .src.collector import WikipediaCollector
from .src.comparator import ResearchComparator
from .src.models import ArticleAnalysisResult, LanguageComparisonReport, LanguageExperimentRequest, ModelComparisonReport, ModelExperimentRequest, WikipediaArticleMeta

class WikipediaResearchEngine:
    """Главный координатор исследований статей Википедии и сравнительного анализа моделей."""

    def __init__(self, chat_model: Any=None) -> None:
        """Инициализация движка.

        Args:
            chat_model (Any): Экземпляр UnifiedChatModel или базовой модели.
        """
        self.collector = WikipediaCollector()
        self.analyzer = WikipediaArticleAnalyzer(chat_model=chat_model)
        self.comparator = ResearchComparator()
        self._history: List[Any] = []
        logger.debug('WikipediaResearchEngine initialized successfully.')

    async def search_topics(self, query: str, lang: str='en') -> List[Dict[str, Any]]:
        """Поиск доступных статей в Википедии.

        Args:
            query (str): Поисковая фраза.
            lang (str): Языковой раздел.

        Returns:
            List[Dict[str, Any]]: Найденные статьи с превью.
        """
        return await self.collector.search_article(query, lang=lang, limit=8)

    async def run_language_experiment(self, req: LanguageExperimentRequest) -> LanguageComparisonReport:
        """Запуск Эксперимента A: Исследование одной темы на нескольких языках одной моделью.

        Args:
            req (LanguageExperimentRequest): Параметры эксперимента.

        Returns:
            LanguageComparisonReport: Отчет с кросс-языковым сравнением.
        """
        logger.info(f"Starting Language Experiment (Exp A) for topic='{req.topic}', model='{req.model}'")
        articles: Dict[str, WikipediaArticleMeta] = await self.collector.collect_multilingual_articles(req.topic, req.languages)
        analysis_tasks = []
        langs_order = []
        for lang, article in articles.items():
            langs_order.append(lang)
            analysis_tasks.append(self.analyzer.analyze_article(article=article, topic=req.topic, model_name=req.model, dimensions=req.dimensions))
        analysis_results_list = await asyncio.gather(*analysis_tasks)
        results: Dict[str, ArticleAnalysisResult] = {lang: res for lang, res in zip(langs_order, analysis_results_list)}
        report = self.comparator.build_language_comparison_report(topic=req.topic, model_used=req.model, articles=articles, results=results)
        self._history.append(report)
        return report

    async def run_model_experiment(self, req: ModelExperimentRequest) -> ModelComparisonReport:
        """Запуск Эксперимента B: Исследование статей одной темы набором разных AI-моделей.

        Args:
            req (ModelExperimentRequest): Параметры эксперимента.

        Returns:
            ModelComparisonReport: Отчет со сравнительной матрицей моделей.
        """
        logger.info(f"Starting Model Benchmark (Exp B) for topic='{req.topic}', models={req.models}")
        articles: Dict[str, WikipediaArticleMeta] = await self.collector.collect_multilingual_articles(req.topic, req.languages)
        matrix: Dict[str, Dict[str, ArticleAnalysisResult]] = {}
        tasks = []
        task_meta = []
        for lang, article in articles.items():
            matrix[lang] = {}
            for model_name in req.models:
                task_meta.append((lang, model_name))
                tasks.append(self.analyzer.analyze_article(article=article, topic=req.topic, model_name=model_name, dimensions=req.dimensions))
        results_list = await asyncio.gather(*tasks)
        for (lang, model_name), res in zip(task_meta, results_list):
            matrix[lang][model_name] = res
        report = self.comparator.build_model_comparison_report(topic=req.topic, languages=req.languages, models=req.models, matrix=matrix)
        self._history.append(report)
        return report

    def get_history(self) -> List[Any]:
        """Возвращает историю проведенных экспериментов."""
        return self._history