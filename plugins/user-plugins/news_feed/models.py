# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: News Service Data Models
# =============================================================================
# Description:
#   Data structures and models for news articles, user interest profiles,
#   user interactions/feedback, and adaptive scoring entities.
#
# File: models.py
# Project: ai-breadboard
# Package: plugins.news_feed
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Data structures for intelligent news filtering and user learning."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class NewsArticleModel(BaseModel):
    """Normalized news article data model."""

    id: str = Field(description="Unique article hash or identifier")
    title: str = Field(description="Headline of the article")
    summary: str = Field(default="", description="Short body or description")
    ai_summary: Optional[str] = Field(default=None, description="Concise AI-generated TL;DR")
    link: str = Field(description="Direct URL to original source")
    source_name: str = Field(description="Name of RSS or news source")
    source_url: Optional[str] = Field(default=None, description="Base source website or feed URL")
    category: str = Field(default="general", description="Primary article category")
    tags: List[str] = Field(default_factory=list, description="Extracted keywords and tags")
    published_at: str = Field(description="Publication timestamp")
    relevance_score: float = Field(default=0.5, description="Computed relevance score (0.0 to 1.0)")
    user_interaction: Optional[str] = Field(default=None, description="User action: like, dislike, bookmark, read")


class UserFeedbackRequest(BaseModel):
    """Incoming feedback from user on a specific article."""

    article_id: str = Field(description="Article identifier")
    action: str = Field(description="Action type: like, dislike, bookmark, read, hide")
    article_title: Optional[str] = Field(default="", description="Title for context extraction")
    article_tags: Optional[List[str]] = Field(default_factory=list, description="Tags for context learning")
    category: Optional[str] = Field(default="general", description="Category of the article")


class UserPreferencesUpdate(BaseModel):
    """User preferences payload for manual customisation."""

    preferred_topics: Optional[List[str]] = Field(default=None, description="List of preferred topics/keywords")
    ignored_topics: Optional[List[str]] = Field(default=None, description="List of negative keywords to penalize")
    custom_sources: Optional[List[Dict[str, str]]] = Field(default=None, description="Custom RSS feeds")
    min_relevance_threshold: Optional[float] = Field(default=0.3, description="Minimum relevance score to show")
    auto_ai_summary: Optional[bool] = Field(default=True, description="Whether to generate AI summaries")


@dataclass
class UserInterestProfile:
    """Adaptive learning profile representing user interests and weights."""

    user_id: str
    topic_weights: Dict[str, float] = field(default_factory=dict)
    negative_keywords: List[str] = field(default_factory=list)
    source_weights: Dict[str, float] = field(default_factory=dict)
    custom_sources: List[Dict[str, str]] = field(default_factory=list)
    min_relevance_threshold: float = 0.3
    interaction_count: int = 0
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to serializable dictionary."""
        return {
            "user_id": self.user_id,
            "topic_weights": self.topic_weights,
            "negative_keywords": self.negative_keywords,
            "source_weights": self.source_weights,
            "custom_sources": self.custom_sources,
            "min_relevance_threshold": self.min_relevance_threshold,
            "interaction_count": self.interaction_count,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> UserInterestProfile:
        """Create profile instance from dictionary."""
        return cls(
            user_id=data.get("user_id", "default"),
            topic_weights=data.get("topic_weights", {}),
            negative_keywords=data.get("negative_keywords", []),
            source_weights=data.get("source_weights", {}),
            custom_sources=data.get("custom_sources", []),
            min_relevance_threshold=float(data.get("min_relevance_threshold", 0.3)),
            interaction_count=int(data.get("interaction_count", 0)),
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat()),
        )
