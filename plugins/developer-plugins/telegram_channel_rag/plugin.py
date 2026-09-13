# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Telegram Multi-Channel RAG Plugin Controller
# =============================================================================
# Description:
#   Main plugin implementation for Telegram multi-channel RAG ingestion,
#   shared channel pool management, user subscriptions, and fast federated search.
#
# File: plugin.py
# Project: ai-breadboard
# Package: plugins.telegram_channel_rag
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Telegram Multi-Channel RAG & Fast Search Plugin Module.

Integrates Telegram channel message collection (via web preview or export file),
channel pool reuse, user subscriptions, and fast search returning exact Telegram message links.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

from header import __root__
from src.logger import logger
from plugins.base import BasePlugin
from plugins.telegram_channel_rag.collector import TelegramMessageCollector
from plugins.telegram_channel_rag.indexer import TelegramChannelIndexer
from plugins.telegram_channel_rag.channel_manager import ChannelManager


class TelegramChannelRagPlugin(BasePlugin):
    """Modular plugin for multi-channel Telegram knowledge retrieval and user subscriptions.

    Attributes:
        name (str): 'telegram_channel_rag'.
        title (str): 'Telegram Channel RAG & Fast Search'.
        version (str): '2.0.0'.
        description (str): Functional summary.
        icon (str): '💬'.
        category (str): 'tools'.
    """

    name: str = "telegram_channel_rag"
    title: str = "Telegram Channel RAG & Fast Search"
    title_i18n: Dict[str, str] = {
        "en": "Telegram Channel RAG & Fast Search",
        "ru": "RAG и быстрый поиск по Telegram каналам",
    }
    version: str = "2.0.0"
    description: str = "Monitors Telegram channels/groups, manages user channel subscriptions, reuses existing RAG pools, and searches with direct message URLs."
    description_i18n: Dict[str, str] = {
        "en": "Monitors Telegram channels/groups, manages user channel subscriptions, reuses existing RAG pools, and searches with direct message URLs.",
        "ru": "Мониторит каналы Telegram, подключает пользователей к существующим RAG-базам без повторного парсинга и ищет сообщения со ссылками.",
    }
    icon: str = "💬"
    category: str = "tools"
    enabled: bool = True
    is_system: bool = False
    scope: str = "general"

    def __init__(self, ai_model: Any = None, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the Telegram Channel RAG plugin.

        Args:
            ai_model (Any): Optional AI model instance.
            config (Optional[Dict[str, Any]]): Initial configuration dictionary.
        """
        defaults = self._load_default_config()
        if config:
            defaults.update(config)

        super().__init__(ai_model=ai_model, config=defaults)

        storage_rel = self.config.get("storage_dir", "data/telegram_rag")
        self.storage_dir: Path = __root__ / storage_rel
        self.channel_manager = ChannelManager(base_storage_dir=self.storage_dir)

        # Default fallback channel
        self.default_channel: str = str(self.config.get("target_channel", "canozrimb")).strip()

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration from config.json.

        Returns:
            Dict[str, Any]: Default configuration dictionary.
        """
        cfg_file = Path(__file__).parent / "config.json"
        if cfg_file.exists():
            try:
                return json.loads(cfg_file.read_text(encoding="utf-8"))
            except Exception as exc:
                logger.error(f"Error reading telegram_channel_rag config.json: {exc}")
        return {
            "target_channel": "canozrimb",
            "max_messages": 5000,
            "index_name": "canozrimb",
            "storage_dir": "data/telegram_rag",
            "similarity_top_k": 5,
        }

    def get_config_fields(self) -> List[Dict[str, Any]]:
        """Return configurable form fields for web UI."""
        return [
            {
                "key": "target_channel",
                "label": "Default Telegram Channel",
                "type": "text",
                "default": "canozrimb",
                "description": "Default Telegram username or link (e.g., canozrimb or https://t.me/canozrimb)",
                "required": True,
            },
            {
                "key": "max_messages",
                "label": "Max Messages to Fetch",
                "type": "number",
                "default": 5000,
                "description": "Maximum messages limit when indexing a new channel",
                "required": False,
            },
            {
                "key": "similarity_top_k",
                "label": "Top Results Count",
                "type": "number",
                "default": 5,
                "description": "Default number of search results to return",
                "required": False,
            },
        ]

    def get_actions(self) -> List[Dict[str, Any]]:
        """Return administrative actions exposed to UI."""
        return [
            {
                "id": "list_channels",
                "name": "List Available Channels & Subscriptions",
                "description": "Lists all indexed Telegram channel RAG pools and active user subscriptions.",
                "icon": "📋",
                "parameters": [
                    {
                        "name": "user_id",
                        "type": "str",
                        "required": False,
                        "description": "User ID to filter subscriptions (default: 'default_user')",
                    }
                ],
            },
            {
                "id": "subscribe_channel",
                "name": "Subscribe User to Channel",
                "description": "Attaches user to a channel. If channel RAG exists, reuses it immediately; otherwise indexes it first.",
                "icon": "➕",
                "parameters": [
                    {
                        "name": "channel",
                        "type": "str",
                        "required": True,
                        "description": "Channel username or link (e.g. canozrimb)",
                    },
                    {
                        "name": "user_id",
                        "type": "str",
                        "required": False,
                        "description": "User ID (default: 'default_user')",
                    },
                    {
                        "name": "max_messages",
                        "type": "int",
                        "required": False,
                        "description": "Max messages if new indexing is needed",
                    },
                ],
            },
            {
                "id": "unsubscribe_channel",
                "name": "Unsubscribe User from Channel",
                "description": "Detaches a channel from user's monitored list.",
                "icon": "➖",
                "parameters": [
                    {
                        "name": "channel",
                        "type": "str",
                        "required": True,
                        "description": "Channel to detach",
                    },
                    {
                        "name": "user_id",
                        "type": "str",
                        "required": False,
                        "description": "User ID",
                    },
                ],
            },
            {
                "id": "fetch_and_index",
                "name": "Force Re-index Channel",
                "description": "Scrapes and rebuilds/refreshes the RAG index for a specific channel.",
                "icon": "🔄",
                "parameters": [
                    {
                        "name": "channel",
                        "type": "str",
                        "required": True,
                        "description": "Channel username to index",
                    },
                    {
                        "name": "max_messages",
                        "type": "int",
                        "required": False,
                        "description": "Max messages limit (default: 500)",
                    },
                ],
            },
            {
                "id": "search",
                "name": "Search Channel Messages",
                "description": "Performs fast RAG search across user's subscribed channels or all channels.",
                "icon": "🔍",
                "parameters": [
                    {
                        "name": "query",
                        "type": "str",
                        "required": True,
                        "description": "Search query text",
                    },
                    {
                        "name": "user_id",
                        "type": "str",
                        "required": False,
                        "description": "User ID whose subscriptions to search",
                    },
                    {
                        "name": "channel",
                        "type": "str",
                        "required": False,
                        "description": "Specific channel filter (optional)",
                    },
                    {
                        "name": "top_k",
                        "type": "int",
                        "required": False,
                        "description": "Number of top results (default: 5)",
                    },
                ],
            },
        ]

    def get_tools(self) -> List[Dict[str, Any]]:
        """Return LLM function calling tool definitions."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_telegram_channels",
                    "description": (
                        "Search messages across monitored Telegram channels (e.g. canozrimb) "
                        "for relevant discussions, news, links, and solutions. Returns snippets and direct message URLs."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query, topic, or question to look up in Telegram messages.",
                            },
                            "user_id": {
                                "type": "string",
                                "description": "Optional user ID to search their subscribed channels.",
                            },
                            "channel": {
                                "type": "string",
                                "description": "Optional specific channel username to filter the search.",
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Maximum number of relevant messages to return (default: 5).",
                            },
                        },
                        "required": ["query"],
                    },
                },
            }
        ]

    async def execute_action(self, action_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute admin action."""
        params = params or {}
        user_id = str(params.get("user_id") or "default_user")

        if action_id == "list_channels":
            available = self.channel_manager.list_available_channels()
            user_subs = self.channel_manager.get_user_channels(user_id=user_id)
            return {
                "status": "success",
                "user_id": user_id,
                "user_subscriptions": user_subs,
                "available_channels_in_pool": available,
            }

        elif action_id == "subscribe_channel":
            channel = str(params.get("channel") or self.default_channel).strip()
            max_msgs = int(params.get("max_messages") or self.config.get("max_messages", 500))
            return self.channel_manager.subscribe_user(
                channel_input=channel,
                user_id=user_id,
                max_messages=max_msgs
            )

        elif action_id == "unsubscribe_channel":
            channel = str(params.get("channel", "")).strip()
            return self.channel_manager.unsubscribe_user(channel_input=channel, user_id=user_id)

        elif action_id == "fetch_and_index":
            channel = str(params.get("channel") or self.default_channel).strip()
            max_msgs = int(params.get("max_messages") or self.config.get("max_messages", 500))

            indexer, newly_created = self.channel_manager.ensure_channel_indexed(
                channel_input=channel,
                max_messages=max_msgs,
                force_refresh=True
            )
            return {
                "status": "success",
                "channel": channel,
                "indexed_messages": len(indexer.messages),
                "message": f"Channel @{channel} indexed with {len(indexer.messages)} messages.",
            }

        elif action_id == "search":
            query = params.get("query", "").strip()
            top_k = int(params.get("top_k") or self.config.get("similarity_top_k", 5))
            specific_channel = params.get("channel")
            channels_override = [specific_channel] if specific_channel else None

            results = self.channel_manager.search_user_channels(
                query=query,
                user_id=user_id,
                channels_override=channels_override,
                top_k=top_k,
            )
            return {
                "status": "success",
                "query": query,
                "user_id": user_id,
                "results_count": len(results),
                "results": results,
            }

        return {"status": "error", "message": f"Unknown action '{action_id}'"}

    def search(
        self,
        query: str,
        user_id: str | int = "default_user",
        channel: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Perform search across user's channels.

        Args:
            query (str): Search text.
            user_id (str | int): User identifier.
            channel (Optional[str]): Specific channel override.
            top_k (int): Result limit.

        Returns:
            List[Dict[str, Any]]: Formatted results list.
        """
        channels_override = [channel] if channel else None
        return self.channel_manager.search_user_channels(
            query=query,
            user_id=user_id,
            channels_override=channels_override,
            top_k=top_k,
        )

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute LLM function call."""
        if tool_name in ("search_telegram_channels", "search_telegram_channel"):
            query = arguments.get("query", "")
            user_id = arguments.get("user_id", "default_user")
            channel = arguments.get("channel")
            top_k = int(arguments.get("top_k", 5))

            results = self.search(query=query, user_id=user_id, channel=channel, top_k=top_k)
            if not results:
                return f"No relevant messages found in Telegram channels for query '{query}'."

            lines = [f"Found {len(results)} relevant Telegram messages:"]
            for r in results:
                lines.append(
                    f"- [@{r['channel']} | {r['author']} at {r['date']}] ({r['url']}):\n  {r['snippet']}\n"
                )
            return "\n".join(lines)
        return f"Unknown tool '{tool_name}'"

    async def handle(self, message: str, **kwargs: Any) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle conversational query or direct prompt.

        Args:
            message (str): Incoming search query.
            **kwargs (Any): Additional context parameters (user_id, channel, top_k).

        Yields:
            Dict[str, Any]: Search result chunks and direct answer links.
        """
        user_id = kwargs.get("user_id", "default_user")
        channel = kwargs.get("channel")
        top_k = kwargs.get("top_k", self.config.get("similarity_top_k", 5))

        results = self.search(query=message, user_id=user_id, channel=channel, top_k=int(top_k))

        if not results:
            yield {
                "status": "complete",
                "text": f"No relevant messages found for '{message}'.",
                "results": [],
            }
            return

        yield {
            "status": "complete",
            "text": f"Found {len(results)} relevant Telegram messages across monitored channels.",
            "results": results,
        }
