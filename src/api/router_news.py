# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: FastAPI Smart News Feed and Learning Router
# =============================================================================
# Description:
#   REST API endpoints for fetching personalized news feeds, sending user feedback
#   to adapt interest models, managing topics/RSS sources, and generating AI digests.
#
# File: router_news.py
# Project: ai-breadboard
# Package: src.api
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI router for personalized smart news feed."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from logger import logger
from plugins.news_feed import (
    NewsArticleModel,
    UserFeedbackRequest,
    UserInterestProfile,
    UserPreferencesUpdate,
    get_news_engine,
)
from src.api.router_auth import get_current_user_optional

router = APIRouter(prefix="/api/news", tags=["news"])


def _extract_user_id(request: Request) -> str:
    """Extract authenticated user id or return 'default' for local/guest."""
    user = get_current_user_optional(request)
    if user and getattr(user, "email", None):
        return str(user.email)
    elif user and getattr(user, "id", None):
        return str(user.id)
    return "default"


@router.get("/feed", response_model=List[NewsArticleModel])
async def get_news_feed(
    request: Request,
    force_refresh: bool = Query(False, description="Force re-fetch from RSS sources"),
    limit: int = Query(30, ge=1, le=100, description="Max news items to return")
):
    """Retrieve personalized, ranked news feed for the active user."""
    user_id = _extract_user_id(request)
    engine = get_news_engine()
    articles = engine.get_personalized_feed(user_id=user_id, force_refresh=force_refresh, limit=limit)
    return articles


@router.post("/feedback")
async def post_user_feedback(feedback: UserFeedbackRequest, request: Request):
    """Register user feedback (like, dislike, bookmark, read, hide) and adapt learner."""
    user_id = _extract_user_id(request)
    engine = get_news_engine()
    profile = engine.learner.apply_feedback(user_id=user_id, feedback=feedback)
    return {
        "status": "ok",
        "action": feedback.action,
        "interaction_count": profile.interaction_count,
        "updated_weights": {k: v for k, v in list(profile.topic_weights.items())[:10]}
    }


@router.get("/profile")
async def get_user_news_profile(request: Request):
    """Get the current user interest vector and configuration."""
    user_id = _extract_user_id(request)
    engine = get_news_engine()
    profile = engine.learner.get_profile(user_id=user_id)
    return profile.to_dict()


@router.post("/profile")
async def update_user_news_profile(prefs: UserPreferencesUpdate, request: Request):
    """Manually update preferred topics, negative stop words, or custom RSS feeds."""
    user_id = _extract_user_id(request)
    engine = get_news_engine()
    profile = engine.learner.get_profile(user_id=user_id)

    if prefs.preferred_topics is not None:
        for t in prefs.preferred_topics:
            t_clean = t.strip().lower()
            if t_clean:
                profile.topic_weights[t_clean] = max(profile.topic_weights.get(t_clean, 1.0), 1.5)

    if prefs.ignored_topics is not None:
        for it in prefs.ignored_topics:
            it_clean = it.strip().lower()
            if it_clean and it_clean not in profile.negative_keywords:
                profile.negative_keywords.append(it_clean)
                if it_clean in profile.topic_weights:
                    del profile.topic_weights[it_clean]

    if prefs.custom_sources is not None:
        profile.custom_sources = prefs.custom_sources

    if prefs.min_relevance_threshold is not None:
        profile.min_relevance_threshold = prefs.min_relevance_threshold

    engine.learner.save_profile(profile)
    return {"status": "ok", "profile": profile.to_dict()}


@router.post("/digest")
async def generate_ai_digest(request: Request):
    """Generate on-demand morning/evening summary digest of top relevant news."""
    user_id = _extract_user_id(request)
    engine = get_news_engine()
    digest = await engine.generate_user_digest(user_id=user_id)
    return digest


@router.post("/summarize-article")
async def summarize_single_article(article: NewsArticleModel):
    """Generate crisp 2-sentence AI TL;DR summary for a specific article."""
    engine = get_news_engine()
    summary = await engine.generate_ai_summary(article)
    return {"article_id": article.id, "ai_summary": summary}


def init_router(ai_model=None) -> APIRouter:
    """Initialize router and inject optional AI model into singleton engine."""
    get_news_engine(ai_model=ai_model)
    return router
