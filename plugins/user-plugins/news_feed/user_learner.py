# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: User News Adaptive Learner
# =============================================================================
# Description:
#   Maintains and trains individual user interest models based on feedback loops,
#   calculates personalized relevance scores, and manages profile persistence.
#
# File: user_learner.py
# Project: ai-breadboard
# Package: plugins.news_feed
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Adaptive learning engine for personalizing user news feeds."""

from __future__ import annotations

import json
import math
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from header import __root__
from src.logger import logger
from plugins.news_feed.models import NewsArticleModel, UserFeedbackRequest, UserInterestProfile


_STOP_WORDS_RU = {
    "и", "в", "во", "не", "что", "он", "на", "я", "с", "со", "как", "а", "то", "все", "она",
    "так", "его", "но", "да", "ты", "к", "у", "же", "вы", "за", "бы", "по", "только", "ее",
    "мне", "было", "вот", "от", "меня", "еще", "нет", "о", "из", "ему", "теперь", "когда",
    "даже", "ну", "вдруг", "ли", "если", "уже", "или", "ни", "быть", "был", "него", "до",
    "вас", "нибудь", "опять", "уж", "вам", "ведь", "там", "потом", "себя", "ничего", "ей",
    "может", "они", "тут", "где", "есть", "надо", "ней", "для", "мы", "тебя", "их", "чем",
    "была", "сам", "чтоб", "без", "будто", "чего", "раз", "тоже", "себе", "под", "будет",
    "ж", "тогда", "кто", "этот", "того", "потому", "этого", "какой", "совсем", "ним", "здесь",
    "этом", "один", "почти", "мой", "тем", "чтобы", "нее", "сейчас", "были", "куда", "зачем",
    "всех", "никогда", "можно", "при", "наконец", "два", "об", "другой", "хоть", "после",
    "над", "больше", "тот", "через", "эти", "нас", "про", "всего", "них", "какая", "много",
    "разве", "три", "эту", "моя", "впрочем", "хорошо", "свою", "этой", "перед", "иногда",
    "лучше", "чуть", "том", "нельзя", "такой", "им", "более", "всегда", "конечно", "всю", "между"
}

_STOP_WORDS_EN = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but",
    "by", "could", "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him",
    "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just",
    "me", "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once",
    "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same",
    "she", "should", "so", "some", "such", "than", "that", "the", "their", "theirs", "them",
    "themselves", "then", "there", "these", "they", "this", "those", "through", "to", "too",
    "under", "until", "up", "very", "was", "we", "were", "what", "when", "where", "which",
    "while", "who", "whom", "why", "with", "would", "you", "your", "yours", "yourself", "yourselves"
}

ALL_STOP_WORDS = _STOP_WORDS_RU | _STOP_WORDS_EN


def extract_keywords(text: str, tags: Optional[List[str]] = None) -> List[str]:
    """Extract clean lemmatized/normalized keywords from title, summary, and tags.

    Args:
        text (str): Source text.
        tags (Optional[List[str]]): Additional explicit tags.

    Returns:
        List[str]: Clean distinct keyword tokens.
    """
    if not text and not tags:
        return []

    tokens: List[str] = []
    if tags:
        for tag in tags:
            clean_tag = tag.strip().lower()
            if len(clean_tag) >= 2 and clean_tag not in ALL_STOP_WORDS:
                tokens.append(clean_tag)

    if text:
        words = re.findall(r"[a-zA-Zа-яА-ЯёЁ0-9_\-\+#]{2,}", text.lower())
        for w in words:
            w_clean = w.strip("-_#+")
            if len(w_clean) >= 3 and w_clean not in ALL_STOP_WORDS and not w_clean.isdigit():
                tokens.append(w_clean)

    return list(dict.fromkeys(tokens))


class UserNewsLearner:
    """Manages adaptive interest vectors, feedback training, and scoring."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        """Initialize learner with SQLite storage.

        Args:
            db_path (Optional[Path]): Path to database.
        """
        if db_path is None:
            db_path = __root__ / "data" / "news_service.db"
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._profiles_cache: Dict[str, UserInterestProfile] = {}
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Create a sqlite connection."""
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initialize user news preferences and feedback tables."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_news_profiles (
                    user_id TEXT PRIMARY KEY,
                    topic_weights TEXT NOT NULL,
                    negative_keywords TEXT NOT NULL,
                    source_weights TEXT NOT NULL,
                    custom_sources TEXT NOT NULL,
                    min_relevance_threshold REAL DEFAULT 0.3,
                    interaction_count INTEGER DEFAULT 0,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_news_feedback_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    article_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    article_title TEXT,
                    article_tags TEXT,
                    category TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def get_profile(self, user_id: str = "default") -> UserInterestProfile:
        """Load or create the learned interest profile for a given user.

        Args:
            user_id (str): User identifier.

        Returns:
            UserInterestProfile: Active profile instance.
        """
        if user_id in self._profiles_cache:
            return self._profiles_cache[user_id]

        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM user_news_profiles WHERE user_id = ?",
                (user_id,)
            ).fetchone()

            if row:
                try:
                    profile = UserInterestProfile(
                        user_id=row["user_id"],
                        topic_weights=json.loads(row["topic_weights"] or "{}"),
                        negative_keywords=json.loads(row["negative_keywords"] or "[]"),
                        source_weights=json.loads(row["source_weights"] or "{}"),
                        custom_sources=json.loads(row["custom_sources"] or "[]"),
                        min_relevance_threshold=float(row["min_relevance_threshold"] or 0.3),
                        interaction_count=int(row["interaction_count"] or 0),
                        updated_at=row["updated_at"]
                    )
                except Exception as e:
                    logger.error(f"Error parsing news profile for {user_id}: {e}")
                    profile = self._create_default_profile(user_id)
            else:
                profile = self._create_default_profile(user_id)
                self.save_profile(profile)

        self._profiles_cache[user_id] = profile
        return profile

    def _create_default_profile(self, user_id: str) -> UserInterestProfile:
        """Create baseline default profile with balanced seed weights."""
        default_topics = {
            "ai": 1.5, "ии": 1.5, "нейросети": 1.5, "python": 1.2,
            "технологии": 1.0, "наука": 1.0, "разработка": 1.0,
            "llm": 1.4, "gemini": 1.3, "breadboard": 1.3
        }
        return UserInterestProfile(
            user_id=user_id,
            topic_weights=default_topics,
            negative_keywords=[],
            source_weights={},
            custom_sources=[],
            min_relevance_threshold=0.25,
            interaction_count=0,
            updated_at=datetime.now(timezone.utc).isoformat()
        )

    def save_profile(self, profile: UserInterestProfile) -> None:
        """Persist user profile to SQLite database and update cache."""
        profile.updated_at = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO user_news_profiles (
                    user_id, topic_weights, negative_keywords, source_weights,
                    custom_sources, min_relevance_threshold, interaction_count, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    topic_weights=excluded.topic_weights,
                    negative_keywords=excluded.negative_keywords,
                    source_weights=excluded.source_weights,
                    custom_sources=excluded.custom_sources,
                    min_relevance_threshold=excluded.min_relevance_threshold,
                    interaction_count=excluded.interaction_count,
                    updated_at=excluded.updated_at
            """, (
                profile.user_id,
                json.dumps(profile.topic_weights, ensure_ascii=False),
                json.dumps(profile.negative_keywords, ensure_ascii=False),
                json.dumps(profile.source_weights, ensure_ascii=False),
                json.dumps(profile.custom_sources, ensure_ascii=False),
                profile.min_relevance_threshold,
                profile.interaction_count,
                profile.updated_at
            ))
            conn.commit()

        self._profiles_cache[profile.user_id] = profile

    def apply_feedback(self, user_id: str, feedback: UserFeedbackRequest) -> UserInterestProfile:
        """Update user model based on positive or negative feedback.

        Learning Dynamics:
        - 'like': boosts keyword weights (+0.4) and category (+0.3).
        - 'bookmark': strong boost (+0.6).
        - 'dislike': penalizes keywords (-0.5). If weight drops below 0, keyword is moved to negative list.
        - 'hide': heavy penalty (-0.8).
        - 'read': subtle boost (+0.1).

        Args:
            user_id (str): User identifier.
            feedback (UserFeedbackRequest): User interaction info.

        Returns:
            UserInterestProfile: Updated interest profile.
        """
        profile = self.get_profile(user_id)
        keywords = extract_keywords(feedback.article_title or "", feedback.article_tags)
        action = (feedback.action or "").lower()

        # Log action to history
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO user_news_feedback_history (
                    user_id, article_id, action, article_title, article_tags, category, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                feedback.article_id,
                action,
                feedback.article_title,
                json.dumps(feedback.article_tags or [], ensure_ascii=False),
                feedback.category,
                datetime.now(timezone.utc).isoformat()
            ))
            conn.commit()

        delta = 0.0
        if action == "like":
            delta = 0.45
        elif action == "bookmark":
            delta = 0.65
        elif action == "read":
            delta = 0.15
        elif action == "dislike":
            delta = -0.5
        elif action == "hide":
            delta = -0.8

        if delta != 0.0:
            for kw in keywords:
                current = profile.topic_weights.get(kw, 0.5)
                new_weight = current + delta
                
                if new_weight < 0.1 and delta < 0:
                    # Move to negative keywords if severely disliked
                    if kw not in profile.negative_keywords:
                        profile.negative_keywords.append(kw)
                    if kw in profile.topic_weights:
                        del profile.topic_weights[kw]
                else:
                    # Bound maximum weight to avoid unbounded drift
                    profile.topic_weights[kw] = round(min(max(new_weight, 0.1), 5.0), 3)
                    # If previously negative and now liked, remove from negative
                    if delta > 0 and kw in profile.negative_keywords:
                        profile.negative_keywords.remove(kw)

            # Category adaptation
            if feedback.category:
                cat_key = feedback.category.strip().lower()
                cat_curr = profile.topic_weights.get(cat_key, 0.5)
                profile.topic_weights[cat_key] = round(min(max(cat_curr + (delta * 0.5), 0.1), 4.0), 3)

            profile.interaction_count += 1
            self.save_profile(profile)
            logger.info(f"Updated news profile for {user_id}: action={action}, keywords={keywords[:5]}")

        return profile

    def score_article(self, article: NewsArticleModel, profile: UserInterestProfile) -> float:
        """Compute personalized relevance score (0.0 to 1.0) for an article.

        Formula combines:
        1. Learned topic weight overlap (weighted intersection).
        2. Negative keyword penalty (direct disqualification or steep penalty).
        3. Source reputation/weight multiplier.
        4. Recency bonus.

        Args:
            article (NewsArticleModel): Article to score.
            profile (UserInterestProfile): User interest profile.

        Returns:
            float: Normalized score between 0.0 and 1.0.
        """
        keywords = extract_keywords(f"{article.title} {article.summary}", article.tags)
        
        # Check negative keywords first
        for neg in profile.negative_keywords:
            if neg in keywords or neg in article.title.lower():
                return 0.05  # Highly penalized

        matched_weight = 0.0
        total_checks = 0

        for kw in keywords:
            total_checks += 1
            if kw in profile.topic_weights:
                matched_weight += profile.topic_weights[kw]
            else:
                matched_weight += 0.3  # Baseline prior

        if total_checks == 0:
            base_score = 0.4
        else:
            avg_weight = matched_weight / total_checks
            # Map average weight (0.1 .. 3.0) to sigmoid-like 0.0 .. 1.0
            base_score = 1.0 / (1.0 + math.exp(-1.5 * (avg_weight - 1.0)))

        # Category boost
        if article.category and article.category.lower() in profile.topic_weights:
            cat_multiplier = profile.topic_weights[article.category.lower()]
            base_score *= (0.8 + 0.2 * min(cat_multiplier, 2.0))

        # Source multiplier
        if article.source_name and article.source_name in profile.source_weights:
            src_mult = profile.source_weights[article.source_name]
            base_score *= src_mult

        return round(min(max(base_score, 0.0), 1.0), 3)

    def rank_and_filter(
        self,
        articles: List[NewsArticleModel],
        user_id: str = "default",
        apply_min_threshold: bool = True
    ) -> List[NewsArticleModel]:
        """Score, filter, and sort articles in descending order of relevance.

        Args:
            articles (List[NewsArticleModel]): Raw articles.
            user_id (str): User identifier.
            apply_min_threshold (bool): Whether to discard low-scoring news.

        Returns:
            List[NewsArticleModel]: Ranked articles.
        """
        profile = self.get_profile(user_id)
        
        # Get user past interactions to tag articles
        interactions: Dict[str, str] = {}
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT article_id, action FROM user_news_feedback_history WHERE user_id = ?",
                (user_id,)
            ).fetchall()
            for r in rows:
                interactions[r["article_id"]] = r["action"]

        ranked: List[NewsArticleModel] = []
        for art in articles:
            score = self.score_article(art, profile)
            art.relevance_score = score
            art.user_interaction = interactions.get(art.id, None)

            if apply_min_threshold and score < profile.min_relevance_threshold:
                # Skip irrelevant news unless already bookmarked
                if art.user_interaction != "bookmark":
                    continue

            # Don't show hidden news
            if art.user_interaction == "hide":
                continue

            ranked.append(art)

        ranked.sort(key=lambda x: x.relevance_score, reverse=True)
        return ranked
