# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit Tests for Smart News Feed & Adaptive Learner
# =============================================================================
# Description:
#   Validates user adaptive learning dynamics, keyword extraction, negative
#   keyword penalization, relevance scoring, and API router endpoints.
#
# File: test_news_service.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from plugins.news_feed.models import NewsArticleModel, UserFeedbackRequest, UserInterestProfile
from plugins.news_feed.user_learner import UserNewsLearner, extract_keywords
from plugins.news_feed.news_engine import NewsEngine
from main import app


@pytest.fixture
def temp_learner():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = Path(tf.name)
    learner = UserNewsLearner(db_path=db_path)
    yield learner
    try:
        os.remove(db_path)
    except Exception:
        pass


def test_keyword_extraction():
    text = "Новая языковая модель GPT-5 показала рекордные результаты в Python разработке и AI"
    keywords = extract_keywords(text, tags=["ml", "deeplearning"])
    assert "gpt-5" in keywords
    assert "python" in keywords
    assert "ml" in keywords
    assert "deeplearning" in keywords
    assert "и" not in keywords  # Stop word removed


def test_learner_feedback_loop_positive(temp_learner):
    user_id = "test_user_1"
    profile = temp_learner.get_profile(user_id)
    initial_ai_weight = profile.topic_weights.get("ai", 1.0)

    feedback = UserFeedbackRequest(
        article_id="art_123",
        action="like",
        article_title="Major AI Breakthrough in Reinforcement Learning",
        article_tags=["ai", "rl"],
        category="ai"
    )
    updated_profile = temp_learner.apply_feedback(user_id, feedback)
    
    assert updated_profile.interaction_count == 1
    assert updated_profile.topic_weights.get("ai") > initial_ai_weight
    assert "breakthrough" in updated_profile.topic_weights


def test_learner_feedback_loop_negative(temp_learner):
    user_id = "test_user_2"
    
    feedback = UserFeedbackRequest(
        article_id="art_456",
        action="dislike",
        article_title="Celebrity gossip and drama update",
        article_tags=["gossip"],
        category="celebrity"
    )
    updated_profile = temp_learner.apply_feedback(user_id, feedback)
    assert updated_profile.interaction_count == 1

    # Check scoring penalization
    article = NewsArticleModel(
        id="art_456",
        title="Celebrity gossip and drama update",
        summary="Some drama",
        link="https://example.com/drama",
        source_name="Tabloid",
        category="celebrity",
        tags=["gossip"],
        published_at="2026-09-12"
    )
    score = temp_learner.score_article(article, updated_profile)
    assert score <= 0.35


def test_news_engine_ranking(temp_learner):
    engine = NewsEngine(learner=temp_learner)
    user_id = "test_user_ranking"

    # Train user to love robotics
    temp_learner.apply_feedback(
        user_id,
        UserFeedbackRequest(
            article_id="1",
            action="like",
            article_title="Robotics and autonomous machines revolution",
            article_tags=["robotics", "automation"],
            category="tech"
        )
    )

    art1 = NewsArticleModel(
        id="1",
        title="Modern Robotics and Automation in 2026",
        summary="Advances in autonomous humanoid robotics",
        link="https://example.com/robotics",
        source_name="TechSite",
        category="tech",
        tags=["robotics"],
        published_at="2026-09-12"
    )
    art2 = NewsArticleModel(
        id="2",
        title="Gardening tips for beginners",
        summary="How to plant tomatoes",
        link="https://example.com/garden",
        source_name="GardenSite",
        category="lifestyle",
        tags=["gardening"],
        published_at="2026-09-12"
    )

    ranked = temp_learner.rank_and_filter([art1, art2], user_id=user_id, apply_min_threshold=False)
    assert len(ranked) == 2
    assert ranked[0].id == "1"
    assert ranked[0].relevance_score > ranked[1].relevance_score


def test_fastapi_news_endpoints():
    client = TestClient(app)

    # 1. Profile endpoint
    res = client.get("/api/news/profile")
    assert res.status_code == 200
    data = res.json()
    assert "topic_weights" in data

    # 2. Feedback endpoint
    fb_res = client.post("/api/news/feedback", json={
        "article_id": "test_api_art",
        "action": "like",
        "article_title": "Deep Learning with Neural Networks",
        "article_tags": ["deeplearning"],
        "category": "ai"
    })
    assert fb_res.status_code == 200
    assert fb_res.json()["status"] == "ok"

    # 3. Feed endpoint
    feed_res = client.get("/api/news/feed?limit=10")
    assert feed_res.status_code == 200
    assert isinstance(feed_res.json(), list)
