# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Plugins User-Plugins News_Feed -   Init  
# =============================================================================
# Description:
#   Smart News Feed and Personalization Plugin Package.
#
# Usage Examples:
#   Python API:
#     from plugins.user-plugins.news_feed.__init__ import get_news_engine
#
#     res = get_news_engine()
#
# File: __init__.py
# Project: ai-breadboard
# Package: plugins.user-plugins.news_feed
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:23:11
# =============================================================================

from __future__ import annotations
"""Smart News Feed and Personalization Plugin Package."""

from typing import Optional
from plugins.news_feed.models import NewsArticleModel, UserFeedbackRequest, UserInterestProfile, UserPreferencesUpdate
from plugins.news_feed.user_learner import UserNewsLearner
from plugins.news_feed.news_engine import NewsEngine
from plugins.news_feed.plugin import NewsFeedPlugin, plugin
__all__ = ['NewsArticleModel', 'UserFeedbackRequest', 'UserInterestProfile', 'UserPreferencesUpdate', 'UserNewsLearner', 'NewsEngine', 'NewsFeedPlugin', 'get_news_engine', 'plugin']
_news_engine_instance: Optional[NewsEngine] = None

def get_news_engine(ai_model=None) -> NewsEngine:
    """Get or create singleton NewsEngine instance.

    Args:
        ai_model: Optional AI model instance.

    Returns:
        NewsEngine: Global service instance.
    """
    global _news_engine_instance
    if _news_engine_instance is None:
        _news_engine_instance = NewsEngine(ai_model=ai_model)
    elif ai_model is not None and _news_engine_instance.ai_model is None:
        _news_engine_instance.ai_model = ai_model
    return _news_engine_instance