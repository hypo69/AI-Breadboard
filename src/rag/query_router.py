# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Query Router for Smart Document Search Routing
# =============================================================================
# Description:
#   Analyzes user queries to determine optimal search strategy:
#   - text: Only search text documents (TF-IDF/Gemini)
#   - pixel: Only search images (CLIP → FAISS)
#   - hybrid: Search both text and images
#
#   Uses keyword analysis, query patterns, and heuristics to route queries.
#
# File: query_router.py
# Project: ai-breadboard
# Package: src.rag
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from src.logger import logger


class RoutingType(str, Enum):
    """Query routing decision types."""
    TEXT = "text"
    PIXEL = "pixel"
    HYBRID = "hybrid"


class QueryLanguage(str, Enum):
    """Detected query language."""
    RUSSIAN = "russian"
    ENGLISH = "english"
    MIXED = "mixed"


@dataclass
class QueryAnalysis:
    """
    ## hypo69 docblock
    Result of query analysis with routing decision.

    Attributes:
        query: Original query string
        routing_type: Recommended search strategy
        language: Detected query language
        visual_keywords: Found visual indicator keywords
        confidence: Confidence score 0-1 for routing decision
        reason: Human-readable explanation
        metadata: Additional analysis metadata
    """
    query: str
    routing_type: RoutingType
    language: QueryLanguage
    visual_keywords: List[str]
    confidence: float
    reason: str
    metadata: Dict[str, any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class QueryRouter:
    """
    ## hypo69 docblock
    Smart query router for determining search strategy.

    Analyzes queries for visual indicators and language patterns
    to route to optimal search provider(s).

    Attributes:
        visual_keywords_ru: Russian visual indicator keywords
        visual_keywords_en: English visual indicator keywords
        visual_patterns: Regex patterns for visual intent
    """

    # Russian visual indicator keywords (high confidence)
    VISUAL_KEYWORDS_RU: Set[str] = {
        # Direct visual commands
        "покажи", "показать", "покажет",
        "найди", "найдите", "найти",
        "где", "где-то",
        "скриншот", "экран", "экране",
        "интерфейс", "интерфейса",
        "кнопка", "кнопку", "кнопке",
        "меню", "меню",
        "иконка", "иконку",
        "выглядит", "выглядит", "видно", "виден",
        "как выглядит", "как видит",
        "внешний", "внешний вид",
        "слева", "справа", "сверху", "снизу",
        "рядом", "рядом с",
        "около", "рядом", "возле",
        "посмотри", "смотри",
        "скриншотом", "скриншотов",
        "фото", "картинка", "изображение",
        "визуально", "визуальный",
        "выглядит", "выглядит",
        "нажми", "нажмите",
        "кликни", "кликните",
    }

    # English visual indicator keywords
    VISUAL_KEYWORDS_EN: Set[str] = {
        # Direct visual commands
        "show", "shows", "showing",
        "find", "look",
        "where", "where is",
        "screenshot", "screen",
        "interface", "UI",
        "button", "buttons",
        "menu", "menus",
        "icon", "icons",
        "looks", "look like", "looks like",
        "appearance", "visual",
        "left", "right", "top", "bottom",
        "next to", "beside",
        "image", "picture", "photo",
        "visually", "visual",
        "click", "tap",
        "see", "visible",
    }

    # Regex patterns for visual intent (high confidence)
    VISUAL_PATTERNS: List[Tuple[str, float]] = [
        (r"(покажи|показать).*?(кнопку|меню|интерфейс|скриншот)", 0.95),  # Show button/menu
        (r"где.*?(кнопка|меню|иконка|элемент)", 0.90),  # Where is button/menu
        (r"как.*?(выглядит|видно|видит)", 0.85),  # How it looks
        (r"(слева|справа|сверху|снизу).*?от", 0.80),  # Spatial relations
        (r"на.*?(скриншоте|экране|интерфейсе)", 0.85),  # On screenshot/screen
        (r"найди.*?(на картинк|на изображени|на фото)", 0.90),  # Find in image
        (r"(?i)(show|find).*?(button|menu|interface|icon)", 0.95),  # English patterns
        (r"(?i)where.*?(is|are).*?(button|menu|icon)", 0.90),  # English where
    ]

    # Regex patterns for text intent (low confidence for pixel)
    TEXT_PATTERNS: List[Tuple[str, float]] = [
        (r"объясни|объяснить|опиши|описать", 0.90),  # Explain/describe
        (r"как.*?работает|как.*?использ", 0.85),  # How it works
        (r"что такое|определени|суть", 0.90),  # Definition/explanation
        (r"процесс|алгоритм|инструкция", 0.85),  # Process/algorithm
        (r"(?i)explain|describe|what is|how does", 0.90),  # English patterns
    ]

    def __init__(self):
        """Initialize Query Router."""
        logger.info("[QueryRouter] Initialized")

    def analyze(self, query: str) -> QueryAnalysis:
        """
        ## hypo69 docblock
        Analyze query and determine routing strategy.

        Args:
            query (str): User query string

        Returns:
            QueryAnalysis: Analysis result with routing decision
        """
        query = query.strip()
        if not query:
            return QueryAnalysis(
                query=query,
                routing_type=RoutingType.HYBRID,
                language=QueryLanguage.MIXED,
                visual_keywords=[],
                confidence=0.0,
                reason="Empty query - defaulting to hybrid",
                metadata={}
            )

        # 1. Detect language
        language = self._detect_language(query)

        # 2. Extract visual keywords
        visual_keywords = self._extract_visual_keywords(query, language)

        # 3. Check visual patterns
        visual_pattern_score = self._check_visual_patterns(query)

        # 4. Check text patterns
        text_pattern_score = self._check_text_patterns(query)

        # 5. Determine routing
        routing, confidence, reason = self._determine_routing(
            query=query,
            visual_keywords=visual_keywords,
            visual_score=visual_pattern_score,
            text_score=text_pattern_score,
            language=language
        )

        analysis = QueryAnalysis(
            query=query,
            routing_type=routing,
            language=language,
            visual_keywords=visual_keywords,
            confidence=confidence,
            reason=reason,
            metadata={
                "visual_score": visual_pattern_score,
                "text_score": text_pattern_score,
                "keyword_count": len(visual_keywords),
                "query_length": len(query),
                "query_words": len(query.split()),
            }
        )

        logger.info(
            f"[QueryRouter] Analyzed: {query[:50]}... → {routing.value} "
            f"(confidence={confidence:.2f})"
        )

        return analysis

    def _detect_language(self, query: str) -> QueryLanguage:
        """
        ## hypo69 docblock
        Detect query language (Russian, English, or mixed).

        Args:
            query (str): Query string

        Returns:
            QueryLanguage: Detected language
        """
        # Russian Cyrillic range
        russian_chars = sum(1 for c in query if '\u0400' <= c <= '\u04FF')
        # English letters
        english_chars = sum(1 for c in query if c.isascii() and c.isalpha())
        # Other
        total_chars = len(query)

        if russian_chars > total_chars * 0.5:
            return QueryLanguage.RUSSIAN
        elif english_chars > total_chars * 0.5:
            return QueryLanguage.ENGLISH
        else:
            return QueryLanguage.MIXED

    def _extract_visual_keywords(self, query: str, language: QueryLanguage) -> List[str]:
        """
        ## hypo69 docblock
        Extract visual indicator keywords from query.

        Args:
            query (str): Query string
            language (QueryLanguage): Detected language

        Returns:
            List[str]: Found visual keywords
        """
        found_keywords: List[str] = []
        query_lower = query.lower()

        # Tokenize query into words
        words = re.findall(r'\b\w+\b', query_lower)

        # Check Russian keywords
        if language in (QueryLanguage.RUSSIAN, QueryLanguage.MIXED):
            for word in words:
                if word in self.VISUAL_KEYWORDS_RU:
                    found_keywords.append(word)

        # Check English keywords
        if language in (QueryLanguage.ENGLISH, QueryLanguage.MIXED):
            for word in words:
                if word in self.VISUAL_KEYWORDS_EN:
                    found_keywords.append(word)

        return list(set(found_keywords))  # Remove duplicates

    def _check_visual_patterns(self, query: str) -> float:
        """
        ## hypo69 docblock
        Check regex patterns for visual intent.

        Args:
            query (str): Query string

        Returns:
            float: Confidence score 0-1
        """
        max_score = 0.0

        for pattern, confidence in self.VISUAL_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                max_score = max(max_score, confidence)

        return max_score

    def _check_text_patterns(self, query: str) -> float:
        """
        ## hypo69 docblock
        Check regex patterns for text intent.

        Args:
            query (str): Query string

        Returns:
            float: Confidence score 0-1
        """
        max_score = 0.0

        for pattern, confidence in self.TEXT_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                max_score = max(max_score, confidence)

        return max_score

    def _determine_routing(
        self,
        query: str,
        visual_keywords: List[str],
        visual_score: float,
        text_score: float,
        language: QueryLanguage
    ) -> Tuple[RoutingType, float, str]:
        """
        ## hypo69 docblock
        Determine routing decision based on analysis.

        Args:
            query: Original query
            visual_keywords: Found visual keywords
            visual_score: Visual pattern confidence
            text_score: Text pattern confidence
            language: Detected language

        Returns:
            Tuple of (RoutingType, confidence, reason)
        """
        # Strong visual intent indicators
        if visual_score >= 0.85 or len(visual_keywords) >= 3:
            if text_score < 0.5:
                return (
                    RoutingType.PIXEL,
                    min(0.95, visual_score + 0.1),
                    f"Strong visual indicators: keywords={visual_keywords}, pattern_score={visual_score:.2f}"
                )
            else:
                return (
                    RoutingType.HYBRID,
                    (visual_score + text_score) / 2,
                    f"Mixed intent: visual={visual_keywords}, both patterns detected"
                )

        # Moderate visual intent
        if visual_score >= 0.75 or len(visual_keywords) >= 2:
            return (
                RoutingType.HYBRID,
                (visual_score + 0.5) / 2,
                f"Moderate visual indicators: keywords={visual_keywords}, pattern_score={visual_score:.2f}"
            )

        # Strong text intent
        if text_score >= 0.85:
            return (
                RoutingType.TEXT,
                text_score,
                f"Text intent detected: pattern_score={text_score:.2f}"
            )

        # Check keyword ratio for weak signals
        query_words = len(query.split())
        keyword_ratio = len(visual_keywords) / max(1, query_words)

        if keyword_ratio >= 0.2:  # 20% or more keywords
            return (
                RoutingType.HYBRID,
                min(0.7, 0.5 + keyword_ratio),
                f"Keyword density indicates visual intent: {keyword_ratio:.0%}"
            )

        # Default to hybrid for ambiguous cases
        return (
            RoutingType.HYBRID,
            0.5,
            "Ambiguous query - defaulting to hybrid search"
        )

    def get_config(self) -> Dict[str, any]:
        """
        ## hypo69 docblock
        Get router configuration and keyword lists.

        Returns:
            Dict with configuration details
        """
        return {
            "visual_keywords_ru_count": len(self.VISUAL_KEYWORDS_RU),
            "visual_keywords_en_count": len(self.VISUAL_KEYWORDS_EN),
            "visual_patterns_count": len(self.VISUAL_PATTERNS),
            "text_patterns_count": len(self.TEXT_PATTERNS),
            "routing_types": [rt.value for rt in RoutingType],
            "languages": [lang.value for lang in QueryLanguage],
        }


# Singleton instance
_query_router: Optional[QueryRouter] = None


def get_query_router() -> QueryRouter:
    """
    ## hypo69 docblock
    Get or create singleton QueryRouter instance.

    Returns:
        QueryRouter: Singleton instance
    """
    global _query_router
    if _query_router is None:
        _query_router = QueryRouter()
    return _query_router
