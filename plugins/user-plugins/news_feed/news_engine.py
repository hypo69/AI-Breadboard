# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: News Engine Aggregator and AI Summarizer
# =============================================================================
# Description:
#   Collects, deduplicates, and parses RSS/Atom feeds and search news,
#   performs LLM-powered summarization and TL;DR extraction, and serves
#   personalized smart feeds.
#
# File: news_engine.py
# Project: ai-breadboard
# Package: plugins.news_feed
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Aggregator and AI summarization engine for smart news feed."""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from header import __root__
from logger import logger
from plugins.news_feed.models import NewsArticleModel, UserFeedbackRequest, UserInterestProfile
from plugins.news_feed.user_learner import UserNewsLearner


# Default reliable public RSS feeds across diverse tech/science/world categories
DEFAULT_RSS_FEEDS = [
    {
        "name": "Habr (AI & IT)",
        "url": "https://habr.com/ru/rss/hubs/artificial_intelligence/all/",
        "category": "ai"
    },
    {
        "name": "Habr (Разработка)",
        "url": "https://habr.com/ru/rss/hubs/develop/all/",
        "category": "dev"
    },
    {
        "name": "TechCrunch (AI)",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "category": "ai"
    },
    {
        "name": "Hacker News Top",
        "url": "https://news.ycombinator.com/rss",
        "category": "tech"
    },
    {
        "name": "BBC World News",
        "url": "https://feeds.bbci.co.uk/news/world/rss.xml",
        "category": "world"
    },
    {
        "name": "N+1 Наука",
        "url": "https://nplus1.ru/rss",
        "category": "science"
    }
]


def _clean_html(html_text: str) -> str:
    """Strip HTML tags and unescape common entities."""
    if not html_text:
        return ""
    clean = re.sub(r"<[^>]+>", " ", html_text)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


class NewsEngine:
    """Core news aggregator, cache manager, and AI summarizer."""

    def __init__(
        self,
        ai_model: Any = None,
        learner: Optional[UserNewsLearner] = None,
        cache_ttl_seconds: int = 1800
    ) -> None:
        """Initialize NewsEngine.

        Args:
            ai_model (Any): Optional UnifiedChatModel instance.
            learner (Optional[UserNewsLearner]): Learner instance.
            cache_ttl_seconds (int): RSS in-memory cache TTL (30 min default).
        """
        self.ai_model = ai_model
        self.learner = learner or UserNewsLearner()
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cached_articles: List[NewsArticleModel] = []
        self._last_fetch_time: float = 0.0

    def fetch_rss_feed(self, feed_meta: Dict[str, str]) -> List[NewsArticleModel]:
        """Fetch and parse single RSS/Atom feed.

        Args:
            feed_meta (Dict[str, str]): Feed name, url, category.

        Returns:
            List[NewsArticleModel]: Parsed articles.
        """
        url = feed_meta.get("url", "")
        name = feed_meta.get("name", "RSS")
        category = feed_meta.get("category", "general")
        articles: List[NewsArticleModel] = []

        if not url:
            return articles

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AI-Breadboard-News/1.0"}
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                content = resp.read()

            root = ET.fromstring(content)

            # RSS 2.0 channel/item check
            channel = root.find("channel")
            items = channel.findall("item") if channel is not None else []
            
            # Atom check if no RSS items
            if not items and root.tag.endswith("feed"):
                items = root.findall("{http://www.w3.org/2005/Atom}entry") or root.findall("entry")

            for item in items[:15]:
                title = ""
                link = ""
                desc = ""
                pub_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

                # Parse RSS 2.0 tags
                t_elem = item.find("title")
                if t_elem is not None and t_elem.text:
                    title = _clean_html(t_elem.text)

                l_elem = item.find("link")
                if l_elem is not None:
                    link = (l_elem.text or l_elem.attrib.get("href", "")).strip()

                d_elem = item.find("description")
                if d_elem is None:
                    d_elem = item.find("summary")
                if d_elem is None:
                    d_elem = item.find("{http://www.w3.org/2005/Atom}summary")
                if d_elem is not None and d_elem.text:
                    desc = _clean_html(d_elem.text)

                date_elem = item.find("pubDate")
                if date_elem is None:
                    date_elem = item.find("published")
                if date_elem is None:
                    date_elem = item.find("updated")
                if date_elem is not None and date_elem.text:
                    pub_date = date_elem.text.strip()

                if not title or not link:
                    continue

                # Compute unique ID
                art_id = hashlib.md5(f"{link}_{title}".encode("utf-8")).hexdigest()[:16]

                # Extract basic tags
                tags = [category]
                for cat_elem in item.findall("category"):
                    if cat_elem.text and len(cat_elem.text) < 30:
                        tags.append(cat_elem.text.strip().lower())

                art = NewsArticleModel(
                    id=art_id,
                    title=title,
                    summary=desc[:400] + ("..." if len(desc) > 400 else ""),
                    link=link,
                    source_name=name,
                    source_url=url,
                    category=category,
                    tags=list(set(tags)),
                    published_at=pub_date,
                    relevance_score=0.5
                )
                articles.append(art)

        except Exception as e:
            logger.debug(f"Failed to fetch RSS from {name} ({url}): {e}")

        return articles

    def refresh_news(self, custom_sources: Optional[List[Dict[str, str]]] = None) -> List[NewsArticleModel]:
        """Fetch all news from default and custom RSS sources with deduplication.

        Args:
            custom_sources (Optional[List[Dict[str, str]]]): Extra user feeds.

        Returns:
            List[NewsArticleModel]: Aggregated fresh articles.
        """
        now = time.time()
        if self._cached_articles and (now - self._last_fetch_time < self.cache_ttl_seconds) and not custom_sources:
            return self._cached_articles

        sources_to_fetch = list(DEFAULT_RSS_FEEDS)
        if custom_sources:
            sources_to_fetch.extend(custom_sources)

        all_articles: List[NewsArticleModel] = []
        seen_hashes = set()

        for src in sources_to_fetch:
            arts = self.fetch_rss_feed(src)
            for a in arts:
                if a.id not in seen_hashes:
                    seen_hashes.add(a.id)
                    all_articles.append(a)

        self._cached_articles = all_articles
        self._last_fetch_time = now
        logger.info(f"NewsEngine refreshed: {len(all_articles)} articles collected from {len(sources_to_fetch)} sources.")
        return all_articles

    def get_personalized_feed(
        self,
        user_id: str = "default",
        force_refresh: bool = False,
        limit: int = 30
    ) -> List[NewsArticleModel]:
        """Get intelligent ranked and filtered news feed for specific user.

        Args:
            user_id (str): User identifier.
            force_refresh (bool): Skip cache.
            limit (int): Maximum items to return.

        Returns:
            List[NewsArticleModel]: Ranked articles tailored for user.
        """
        profile = self.learner.get_profile(user_id)
        if force_refresh:
            self._last_fetch_time = 0.0

        raw_articles = self.refresh_news(profile.custom_sources)
        ranked = self.learner.rank_and_filter(raw_articles, user_id=user_id)
        return ranked[:limit]

    async def generate_ai_summary(self, article: NewsArticleModel) -> str:
        """Generate a crisp, 2-sentence summary/takeaway of an article using AI.

        Args:
            article (NewsArticleModel): Target article.

        Returns:
            str: AI summary text.
        """
        if not self.ai_model:
            return article.summary

        prompt = (
            f"Сделай краткую, емкую выжимку новости (1-2 предложения) с сутью и выводами на русском языке:\n\n"
            f"Заголовок: {article.title}\n"
            f"Текст: {article.summary}"
        )
        try:
            if hasattr(self.ai_model, "ask_async"):
                res = await self.ai_model.ask_async(prompt)
                return str(res).strip()
            elif hasattr(self.ai_model, "ask"):
                res = self.ai_model.ask(prompt)
                return str(res).strip()
        except Exception as e:
            logger.error(f"AI news summarization error: {e}")

        return article.summary

    async def generate_user_digest(self, user_id: str = "default") -> Dict[str, Any]:
        """Generate full morning/evening personalized AI news digest.

        Args:
            user_id (str): User identifier.

        Returns:
            Dict[str, Any]: Structured digest with AI narrative and key links.
        """
        feed = self.get_personalized_feed(user_id=user_id, limit=6)
        if not feed:
            return {
                "title": "Персональный дайджест новостей",
                "summary": "На данный момент нет новых релевантных новостей по вашим интересам.",
                "top_articles": []
            }

        articles_text = "\n\n".join([
            f"- [{a.source_name}] {a.title}: {a.summary}" for a in feed
        ])

        prompt = (
            "Ты — персональный информационный ассистент. Ниже представлены наиболее важные и релевантные "
            "новости для пользователя на основе его профиля интересов. "
            "Составь структурированный утренний дайджест: выдели 3-4 главных тренда, сделай краткие выводы "
            "и порекомендуй, на что обратить внимание. Пиши живо, емко и профессионально на русском языке.\n\n"
            f"Новости:\n{articles_text}"
        )

        digest_text = ""
        if self.ai_model:
            try:
                if hasattr(self.ai_model, "ask_async"):
                    res = await self.ai_model.ask_async(prompt)
                    digest_text = str(res).strip()
                elif hasattr(self.ai_model, "ask"):
                    res = self.ai_model.ask(prompt)
                    digest_text = str(res).strip()
            except Exception as e:
                logger.error(f"Error generating AI digest: {e}")
                digest_text = "Не удалось сгенерировать ИИ-выжимку. Ознакомьтесь со списком главных новостей ниже."
        else:
            digest_text = "Главные персонализированные новости на сегодня:"

        return {
            "title": f"Персональный ИИ-дайджест ({datetime.now().strftime('%d.%m.%Y')})",
            "digest_text": digest_text,
            "articles": [a.model_dump() for a in feed]
        }
