# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Wikipedia Research Package Initializer
# =============================================================================
# Description:
#   Package initializer for Wikipedia Research and Model Comparison Laboratory.
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.wikipedia_research.src
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Wikipedia Research core components."""

from .models import (
    AnalysisDimensions,
    ArticleAnalysisResult,
    LanguageComparisonReport,
    ModelComparisonReport,
    WikipediaArticleMeta,
    LanguageExperimentRequest,
    ModelExperimentRequest,
)
from .normalizer import TextNormalizer
from .collector import WikipediaCollector, SUPPORTED_LANGUAGES
from .analyzer import WikipediaArticleAnalyzer
from .comparator import ResearchComparator

__all__ = [
    "AnalysisDimensions",
    "ArticleAnalysisResult",
    "LanguageComparisonReport",
    "ModelComparisonReport",
    "WikipediaArticleMeta",
    "LanguageExperimentRequest",
    "ModelExperimentRequest",
    "TextNormalizer",
    "WikipediaCollector",
    "SUPPORTED_LANGUAGES",
    "WikipediaArticleAnalyzer",
    "ResearchComparator",
]
