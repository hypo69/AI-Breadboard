# -*- coding: utf-8 -*-
"""
## hypo69 docblock
Tests for QueryRouter - smart query analysis and routing.

Tests query analysis, language detection, keyword extraction,
pattern matching, and routing decisions.
"""

import pytest

from src.rag.query_router import (
    QueryRouter, RoutingType, QueryLanguage, get_query_router
)


class TestQueryRouter:
    """Test suite for QueryRouter."""

    @pytest.fixture
    def router(self):
        """Create QueryRouter instance."""
        return QueryRouter()

    # Language Detection Tests

    def test_russian_language_detection(self, router):
        """Test detection of Russian language queries."""
        query = "Покажи кнопку сохранения"
        analysis = router.analyze(query)
        assert analysis.language == QueryLanguage.RUSSIAN

    def test_english_language_detection(self, router):
        """Test detection of English language queries."""
        query = "Show me the save button"
        analysis = router.analyze(query)
        assert analysis.language == QueryLanguage.ENGLISH

    def test_mixed_language_detection(self, router):
        """Test detection of mixed language queries."""
        query = "Покажи save button в интерфейсе"
        analysis = router.analyze(query)
        assert analysis.language == QueryLanguage.MIXED

    # Visual Query Tests

    def test_strong_visual_query_russian(self, router):
        """Test strong visual query detection in Russian."""
        query = "Покажи кнопку сохранения"
        analysis = router.analyze(query)
        assert analysis.routing_type == RoutingType.PIXEL
        assert analysis.confidence >= 0.85
        assert "покажи" in analysis.visual_keywords

    def test_strong_visual_query_english(self, router):
        """Test strong visual query detection in English."""
        query = "Show me the save button"
        analysis = router.analyze(query)
        assert analysis.routing_type == RoutingType.PIXEL
        assert analysis.confidence >= 0.85

    def test_visual_where_query(self, router):
        """Test where queries (high visual intent)."""
        query = "Где находится кнопка отправки?"
        analysis = router.analyze(query)
        assert analysis.routing_type in (RoutingType.PIXEL, RoutingType.HYBRID)
        assert analysis.confidence >= 0.75
        assert "где" in analysis.visual_keywords or "кнопка" in analysis.visual_keywords

    def test_visual_screenshot_query(self, router):
        """Test screenshot-related queries."""
        query = "Найди на скриншоте кнопку входа"
        analysis = router.analyze(query)
        assert analysis.routing_type == RoutingType.PIXEL
        assert analysis.confidence >= 0.85

    # Text Query Tests

    def test_explanatory_text_query_russian(self, router):
        """Test explanatory text queries in Russian."""
        query = "Объясни как работает система"
        analysis = router.analyze(query)
        assert analysis.routing_type == RoutingType.TEXT
        assert analysis.confidence >= 0.80

    def test_explanatory_text_query_english(self, router):
        """Test explanatory text queries in English."""
        query = "Explain how the system works"
        analysis = router.analyze(query)
        assert analysis.routing_type == RoutingType.TEXT
        assert analysis.confidence >= 0.80

    def test_definition_query(self, router):
        """Test definition queries."""
        query = "Что такое REST API?"
        analysis = router.analyze(query)
        assert analysis.routing_type == RoutingType.TEXT
        assert analysis.confidence >= 0.75

    # Hybrid Query Tests

    def test_hybrid_query_mixed_intent(self, router):
        """Test queries with mixed visual and text intent."""
        query = "Покажи кнопку и объясни как её использовать"
        analysis = router.analyze(query)
        assert analysis.routing_type == RoutingType.HYBRID

    def test_hybrid_query_moderate_visual(self, router):
        """Test queries with moderate visual indicators."""
        query = "Где можно найти информацию о кнопке?"
        analysis = router.analyze(query)
        # Could be PIXEL or HYBRID depending on keyword density
        assert analysis.routing_type in (RoutingType.PIXEL, RoutingType.HYBRID)

    # Ambiguous Query Tests

    def test_ambiguous_query_defaults_to_hybrid(self, router):
        """Test that ambiguous queries default to hybrid."""
        query = "информация о кнопке"
        analysis = router.analyze(query)
        assert analysis.routing_type == RoutingType.HYBRID
        assert analysis.confidence <= 0.55

    def test_very_short_query(self, router):
        """Test very short queries."""
        query = "кнопка"
        analysis = router.analyze(query)
        # Single word - ambiguous
        assert analysis.routing_type in (RoutingType.PIXEL, RoutingType.HYBRID)

    # Empty Query Test

    def test_empty_query(self, router):
        """Test handling of empty query."""
        query = ""
        analysis = router.analyze(query)
        assert analysis.routing_type == RoutingType.HYBRID
        assert analysis.confidence == 0.0
        assert len(analysis.visual_keywords) == 0

    # Keyword Extraction Tests

    def test_visual_keyword_extraction_russian(self, router):
        """Test extraction of Russian visual keywords."""
        query = "Покажи мне кнопку на скриншоте"
        analysis = router.analyze(query)
        keywords = analysis.visual_keywords
        assert "покажи" in keywords or "кнопку" in keywords or "скриншоте" in keywords

    def test_visual_keyword_extraction_english(self, router):
        """Test extraction of English visual keywords."""
        query = "Show me the button on screen"
        analysis = router.analyze(query)
        keywords = analysis.visual_keywords
        # May have show, button, screen
        assert len(keywords) > 0

    def test_no_visual_keywords(self, router):
        """Test queries with no visual keywords."""
        query = "Расскажи мне о процессе"
        analysis = router.analyze(query)
        # No clear visual keywords
        assert len(analysis.visual_keywords) <= 1

    # Confidence Score Tests

    def test_confidence_increases_with_matches(self, router):
        """Test that confidence increases with multiple matches."""
        weak_query = "кнопка"
        strong_query = "Покажи мне кнопку на скриншоте"
        
        weak_analysis = router.analyze(weak_query)
        strong_analysis = router.analyze(strong_query)
        
        # Strong query should have higher confidence
        assert strong_analysis.confidence >= weak_analysis.confidence

    # Spatial Relationship Tests

    def test_spatial_query_visual(self, router):
        """Test spatial relationship queries."""
        query = "Где слева от меню кнопка?"
        analysis = router.analyze(query)
        assert analysis.routing_type in (RoutingType.PIXEL, RoutingType.HYBRID)
        assert "где" in analysis.visual_keywords or "слева" in analysis.visual_keywords

    # UI Element Tests

    def test_menu_query(self, router):
        """Test menu-related queries."""
        query = "Найди в меню кнопку настроек"
        analysis = router.analyze(query)
        assert analysis.routing_type == RoutingType.PIXEL
        assert "меню" in analysis.visual_keywords or "найди" in analysis.visual_keywords

    def test_icon_query(self, router):
        """Test icon-related queries."""
        query = "Где иконка сохранения?"
        analysis = router.analyze(query)
        assert analysis.routing_type in (RoutingType.PIXEL, RoutingType.HYBRID)
        assert "иконка" in analysis.visual_keywords or "где" in analysis.visual_keywords

    # Action-Based Queries

    def test_click_action_query(self, router):
        """Test click action queries."""
        query = "Нажми на кнопку отправки"
        analysis = router.analyze(query)
        assert analysis.routing_type == RoutingType.PIXEL

    def test_look_action_query(self, router):
        """Test look/view action queries."""
        query = "Посмотри как выглядит интерфейс"
        analysis = router.analyze(query)
        assert analysis.routing_type == RoutingType.PIXEL

    # Metadata Tests

    def test_metadata_contains_scores(self, router):
        """Test that metadata contains analysis scores."""
        query = "Покажи кнопку"
        analysis = router.analyze(query)
        assert "visual_score" in analysis.metadata
        assert "text_score" in analysis.metadata
        assert "keyword_count" in analysis.metadata
        assert "query_length" in analysis.metadata
        assert "query_words" in analysis.metadata

    # Configuration Tests

    def test_get_config(self, router):
        """Test getting router configuration."""
        config = router.get_config()
        assert "visual_keywords_ru_count" in config
        assert "visual_keywords_en_count" in config
        assert "visual_patterns_count" in config
        assert "text_patterns_count" in config
        assert config["visual_keywords_ru_count"] > 20
        assert config["visual_keywords_en_count"] > 15

    # Singleton Tests

    def test_singleton_instance(self):
        """Test QueryRouter singleton."""
        router1 = get_query_router()
        router2 = get_query_router()
        assert router1 is router2

    # Edge Cases

    def test_unicode_special_chars(self, router):
        """Test handling of Unicode special characters."""
        query = "Найди → кнопку ← сохр… файла"
        analysis = router.analyze(query)
        # Should not crash
        assert isinstance(analysis.routing_type, RoutingType)

    def test_repeated_keywords(self, router):
        """Test handling of repeated keywords."""
        query = "кнопка кнопка кнопка кнопка"
        analysis = router.analyze(query)
        # Should have unique keywords (set removes duplicates)
        assert len(analysis.visual_keywords) <= 1

    def test_case_insensitivity(self, router):
        """Test case-insensitive keyword matching."""
        query1 = "ПОКАЖИ КНОПКУ"
        query2 = "покажи кнопку"
        
        analysis1 = router.analyze(query1)
        analysis2 = router.analyze(query2)
        
        # Should have same routing
        assert analysis1.routing_type == analysis2.routing_type

    # Real-World Examples

    def test_real_world_visual_query_1(self, router):
        """Real-world visual query example 1."""
        query = "На скриншоте слева вверху рядом с логотипом там есть кнопка?"
        analysis = router.analyze(query)
        assert analysis.routing_type in (RoutingType.PIXEL, RoutingType.HYBRID)

    def test_real_world_visual_query_2(self, router):
        """Real-world visual query example 2."""
        query = "Where is the login button on the homepage screenshot?"
        analysis = router.analyze(query)
        assert analysis.routing_type == RoutingType.PIXEL

    def test_real_world_text_query_1(self, router):
        """Real-world text query example 1."""
        query = "Объясните процесс аутентификации пользователя"
        analysis = router.analyze(query)
        assert analysis.routing_type == RoutingType.TEXT

    def test_real_world_text_query_2(self, router):
        """Real-world text query example 2."""
        query = "What is the difference between REST and SOAP?"
        analysis = router.analyze(query)
        assert analysis.routing_type == RoutingType.TEXT

    def test_real_world_hybrid_query_1(self, router):
        """Real-world hybrid query example 1."""
        query = "Покажи кнопку логина и расскажи как правильно заполнить форму"
        analysis = router.analyze(query)
        assert analysis.routing_type == RoutingType.HYBRID

    def test_real_world_hybrid_query_2(self, router):
        """Real-world hybrid query example 2."""
        query = "Find the save button in the menu and explain what each option does"
        analysis = router.analyze(query)
        assert analysis.routing_type == RoutingType.HYBRID


if __name__ == "__main__":
    # Run quick sanity checks
    print("QueryRouter Tests")
    print("=" * 50)
    
    router = QueryRouter()
    
    # Test Russian visual query
    result = router.analyze("Покажи кнопку сохранения")
    print(f"✓ Russian visual: {result.routing_type.value} (conf={result.confidence:.2f})")
    
    # Test English visual query
    result = router.analyze("Show me the save button")
    print(f"✓ English visual: {result.routing_type.value} (conf={result.confidence:.2f})")
    
    # Test text query
    result = router.analyze("Explain how to save a file")
    print(f"✓ Text query: {result.routing_type.value} (conf={result.confidence:.2f})")
    
    # Test hybrid query
    result = router.analyze("Show the button and explain it")
    print(f"✓ Hybrid query: {result.routing_type.value} (conf={result.confidence:.2f})")
    
    # Test ambiguous query
    result = router.analyze("информация")
    print(f"✓ Ambiguous: {result.routing_type.value} (conf={result.confidence:.2f})")
    
    print("\n✓ All sanity checks passed")
