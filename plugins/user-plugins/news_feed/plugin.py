# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Smart News Feed Plugin
# =============================================================================
# Description:
#   Modular plugin exposing intelligent news feed aggregation, personalized
#   ranking, user feedback loops, and LLM tools to AI agents.
#
# File: plugin.py
# Project: ai-breadboard
# Package: plugins.news_feed
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Smart News Feed and Personalization Plugin."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

from plugins.base import BasePlugin
from src.logger import logger
from plugins.news_feed.models import UserFeedbackRequest
from plugins.news_feed.news_engine import NewsEngine


class NewsFeedPlugin(BasePlugin):
    """Modular plugin providing smart relevant news, user learning, and AI digest tools."""

    name: str = "news_feed"
    title: str = "Smart News Feed"
    title_i18n: Dict[str, str] = {
        "ru": "Умная лента новостей",
        "en": "Smart News Feed",
        "he": "עדכון חדשות חכם",
    }
    version: str = "1.0.0"
    description: str = "Intelligent relevant news filtering with personalized learning and AI summarization."
    description_i18n: Dict[str, str] = {
        "ru": "Интеллектуальный сервис персонализированных новостей с самообучением и ИИ-дайджестом.",
        "en": "Intelligent relevant news filtering with personalized learning and AI summarization.",
        "he": "סינון חדשות מותאם אישית חכם עם למידה מותאמת אישית ותקציר AI.",
    }
    icon: str = "📰"
    category: str = "information"
    enabled: bool = True
    is_system: bool = False
    scope: str = "user"

    def __init__(self, ai_model: Any = None, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize Smart News Feed plugin."""
        defaults = self._load_default_config()
        if config:
            defaults.update(config)
        super().__init__(ai_model=ai_model, config=defaults)
        self.engine = NewsEngine(ai_model=ai_model)

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default config from config.json."""
        cfg_file = Path(__file__).parent / "config.json"
        if cfg_file.exists():
            try:
                return json.loads(cfg_file.read_text(encoding="utf-8"))
            except Exception as e:
                logger.error(f"NewsFeedPlugin: error loading config: {e}")
        return {
            "refresh_interval_minutes": 30,
            "default_min_relevance": 0.3,
            "enable_ai_summary": True,
        }

    def get_tools(self) -> List[Dict[str, Any]]:
        """Return function calling tools available to LLM agents."""
        return [
            {
                "name": "get_smart_news",
                "description": "Get top relevant news tailored to the user profile and interests.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of articles to retrieve (default: 5)",
                        },
                        "user_id": {
                            "type": "string",
                            "description": "User identifier",
                        }
                    },
                },
            },
            {
                "name": "generate_news_digest",
                "description": "Generate an AI summary digest of recent relevant news for the user.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User identifier",
                        }
                    },
                },
            },
        ]

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute agent tool invocation."""
        user_id = arguments.get("user_id", "default")
        if tool_name == "get_smart_news":
            limit = int(arguments.get("limit", 5))
            feed = self.engine.get_personalized_feed(user_id=user_id, limit=limit)
            return [a.model_dump() for a in feed]
        elif tool_name == "generate_news_digest":
            return await self.engine.generate_user_digest(user_id=user_id)
        raise ValueError(f"Unknown tool: {tool_name}")

    def get_actions(self) -> List[Dict[str, Any]]:
        """Return admin and user UI actions for plugin settings tab."""
        return [
            {
                "id": "refresh_feeds",
                "title": "Обновить ленту новостей",
                "title_en": "Refresh News Feeds",
                "description": "Принудительно загрузить свежие статьи из всех RSS источников.",
                "icon": "bi-arrow-repeat",
                "variant": "primary",
            },
            {
                "id": "generate_digest",
                "title": "Сгенерировать дайджест дня",
                "title_en": "Generate Daily Digest",
                "description": "Сформировать сводный ИИ-отчет по актуальным новостям.",
                "icon": "bi-cpu",
                "variant": "success",
            },
            {
                "id": "reset_learning_profile",
                "title": "Сбросить веса обучения",
                "title_en": "Reset Learning Profile",
                "description": "Очистить накопленные веса интересов и вернуть профиль по умолчанию.",
                "icon": "bi-arrow-counterclockwise",
                "variant": "outline-danger",
            },
        ]

    async def execute_action(self, action_id: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute plugin UI action."""
        user_id = (payload or {}).get("user_id", "default")
        if action_id == "refresh_feeds":
            arts = self.engine.refresh_news()
            return {"status": "ok", "message": f"Лента обновлена. Загружено {len(arts)} новостей."}
        elif action_id == "generate_digest":
            digest = await self.engine.generate_user_digest(user_id=user_id)
            return {"status": "ok", "digest": digest}
        elif action_id == "reset_learning_profile":
            new_profile = self.engine.learner._create_default_profile(user_id=user_id)
            self.engine.learner.save_profile(new_profile)
            return {"status": "ok", "message": "Профиль обучения успешно сброшен к базовым настройкам."}
        return {"status": "error", "message": f"Action '{action_id}' not found."}

    async def handle(
        self, message: str, **kwargs: Any
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle incoming request or message stream for news queries and digests.

        Args:
            message (str): Incoming query or request text.
            **kwargs (Any): Additional parameters (e.g. user_id, limit).

        Yields:
            Dict[str, Any]: Streamed output events and result chunks.
        """
        user_id = kwargs.get("user_id", "default")
        limit = kwargs.get("limit", 5)

        yield {"status": "started", "text": "Fetching relevant personalized news feed..."}

        lower_msg = message.lower()
        if "digest" in lower_msg or "дайджест" in lower_msg or "summary" in lower_msg:
            digest = await self.engine.generate_user_digest(user_id=user_id)
            yield {
                "status": "complete",
                "text": digest,
                "type": "digest",
            }
            return

        articles = self.engine.get_personalized_feed(user_id=user_id, limit=limit)
        feed_data = [a.model_dump() for a in articles]

        if not articles:
            yield {
                "status": "complete",
                "text": "No news articles found matching your interests at this time.",
                "articles": [],
            }
            return

        lines = [f"### 📰 Top News ({len(articles)} articles)\n"]
        for idx, art in enumerate(articles, 1):
            score_pct = int(art.relevance_score * 100)
            lines.append(f"{idx}. **[{art.title}]({art.link})** ({score_pct}% match)")
            if art.summary:
                lines.append(f"   > {art.summary}")
            elif art.content:
                lines.append(f"   > {art.content[:150]}...")
            lines.append("")

        yield {
            "status": "complete",
            "text": "\n".join(lines).strip(),
            "articles": feed_data,
        }


def plugin(ai_model: Any = None, config: Optional[Dict[str, Any]] = None) -> NewsFeedPlugin:
    """Plugin factory function."""
    return NewsFeedPlugin(ai_model=ai_model, config=config)
