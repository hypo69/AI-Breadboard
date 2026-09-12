# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Telegram Multi-Channel RAG & User Subscription Manager
# =============================================================================
# Description:
#   Manages the pool of Telegram channel RAG indexes, handles user channel
#   subscriptions, enables instant reuse of existing channel RAG indexes,
#   and executes multi-channel federated search.
#
# File: channel_manager.py
# Project: ai-breadboard
# Package: plugins.telegram_channel_rag
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Telegram Channel & User Subscription Manager.

Provides centralized management for the global pool of indexed Telegram channels,
persists user subscription profiles, attaches existing channel RAGs without duplicate
scraping, and performs federated search across multiple channels.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from header import __root__
from src.logger import logger
from plugins.telegram_channel_rag.collector import TelegramMessageCollector
from plugins.telegram_channel_rag.indexer import TelegramChannelIndexer


class ChannelManager:
    """Manages channel RAG pool and user channel subscriptions.

    Attributes:
        base_storage_dir (Path): Base directory for storing channel indexes.
        sub_file (Path): JSON file tracking user-channel subscriptions.
        index_cache (Dict[str, TelegramChannelIndexer]): In-memory cache of channel indexers.
    """

    def __init__(self, base_storage_dir: Optional[Path] = None) -> None:
        """Initialize the ChannelManager.

        Args:
            base_storage_dir (Optional[Path]): Directory where channel indexes reside.
        """
        if base_storage_dir is None:
            self.base_storage_dir = __root__ / "data" / "telegram_rag"
        else:
            self.base_storage_dir = Path(base_storage_dir)

        self.base_storage_dir.mkdir(parents=True, exist_ok=True)
        self.sub_file: Path = self.base_storage_dir / "user_subscriptions.json"
        self.index_cache: Dict[str, TelegramChannelIndexer] = {}

    def _sanitize_channel(self, channel_input: str) -> str:
        """Normalize channel name or link into clean username."""
        collector = TelegramMessageCollector(channel_username=channel_input)
        return collector.channel_username

    def _load_subscriptions(self) -> Dict[str, List[str]]:
        """Load user subscriptions dictionary from disk.

        Returns:
            Dict[str, List[str]]: Mapping of user_id to list of subscribed channel names.
        """
        if self.sub_file.exists():
            try:
                data = json.loads(self.sub_file.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    return data
            except Exception as exc:
                logger.error(f"Error loading user subscriptions from {self.sub_file}: {exc}")
        return {}

    def _save_subscriptions(self, data: Dict[str, List[str]]) -> None:
        """Save user subscriptions dictionary to disk.

        Args:
            data (Dict[str, List[str]]): User subscriptions mapping.
        """
        try:
            self.sub_file.parent.mkdir(parents=True, exist_ok=True)
            self.sub_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            logger.error(f"Error saving user subscriptions to {self.sub_file}: {exc}")

    def list_available_channels(self) -> List[Dict[str, Any]]:
        """List all indexed channels present in the system pool.

        Returns:
            List[Dict[str, Any]]: List of channel metadata dictionaries.
        """
        channels = []
        if not self.base_storage_dir.exists():
            return channels

        for item in self.base_storage_dir.iterdir():
            if item.is_dir():
                indexer = self.get_channel_indexer(item.name)
                channels.append({
                    "channel": item.name,
                    "channel_url": f"https://t.me/{item.name}",
                    "messages_count": len(indexer.messages),
                    "vocab_size": len(indexer.vocab),
                    "is_indexed": len(indexer.messages) > 0,
                    "storage_path": str(item),
                })
        return channels

    def get_channel_indexer(self, channel_input: str) -> TelegramChannelIndexer:
        """Get or create cached in-memory TelegramChannelIndexer for channel.

        Args:
            channel_input (str): Target channel name or URL.

        Returns:
            TelegramChannelIndexer: Initialized and loaded indexer instance.
        """
        channel = self._sanitize_channel(channel_input)
        if channel in self.index_cache:
            return self.index_cache[channel]

        channel_dir = self.base_storage_dir / channel
        indexer = TelegramChannelIndexer(index_dir=channel_dir)
        indexer.load()

        self.index_cache[channel] = indexer
        return indexer

    def is_channel_indexed(self, channel_input: str) -> bool:
        """Check if channel RAG index already exists and has messages.

        Args:
            channel_input (str): Target channel name.

        Returns:
            bool: True if index exists and is populated.
        """
        indexer = self.get_channel_indexer(channel_input)
        return len(indexer.messages) > 0

    def ensure_channel_indexed(
        self,
        channel_input: str,
        max_messages: int = 500,
        force_refresh: bool = False
    ) -> Tuple[TelegramChannelIndexer, bool]:
        """Ensure a channel is indexed; scrapes and builds only if needed or forced.

        Args:
            channel_input (str): Channel name or URL.
            max_messages (int): Message limit for scraping if new.
            force_refresh (bool): Force re-scraping even if index exists.

        Returns:
            Tuple[TelegramChannelIndexer, bool]: Indexer instance and flag indicating if newly crawled.
        """
        channel = self._sanitize_channel(channel_input)
        indexer = self.get_channel_indexer(channel)

        if not force_refresh and len(indexer.messages) > 0:
            logger.info(f"Channel @{channel} is already indexed ({len(indexer.messages)} messages). Reusing existing RAG.")
            return indexer, False

        # Scrape and build
        logger.info(f"Indexing channel @{channel} (fetching up to {max_messages} messages)...")
        collector = TelegramMessageCollector(channel_username=channel)
        messages = collector.fetch_from_web_preview(max_messages=max_messages)

        if messages:
            indexer.build_index(messages)
            indexer.save()
            logger.info(f"Successfully indexed and cached @{channel} with {len(messages)} messages.")
            return indexer, True

        return indexer, False

    def get_user_channels(self, user_id: str | int = "default_user") -> List[str]:
        """Get list of subscribed channel names for a user.

        Args:
            user_id (str | int): User identifier.

        Returns:
            List[str]: List of subscribed channel usernames.
        """
        subs = self._load_subscriptions()
        return subs.get(str(user_id), [])

    def subscribe_user(
        self,
        channel_input: str,
        user_id: str | int = "default_user",
        max_messages: int = 500
    ) -> Dict[str, Any]:
        """Subscribe user to channel, reusing existing RAG index or building if new.

        Args:
            channel_input (str): Target channel name or URL.
            user_id (str | int): User identifier.
            max_messages (int): Max messages to crawl if channel is new.

        Returns:
            Dict[str, Any]: Subscription status, whether reused, and channel stats.
        """
        channel = self._sanitize_channel(channel_input)
        if not channel:
            return {"status": "error", "message": "Invalid channel name."}

        was_already_indexed = self.is_channel_indexed(channel)
        indexer, newly_created = self.ensure_channel_indexed(
            channel_input=channel,
            max_messages=max_messages,
            force_refresh=False
        )

        user_key = str(user_id)
        subs = self._load_subscriptions()
        user_list = subs.get(user_key, [])

        if channel not in user_list:
            user_list.append(channel)
            subs[user_key] = user_list
            self._save_subscriptions(subs)

        return {
            "status": "success",
            "user_id": user_key,
            "channel": channel,
            "channel_url": f"https://t.me/{channel}",
            "reused_existing_rag": was_already_indexed,
            "messages_indexed": len(indexer.messages),
            "user_channels": user_list,
            "message": (
                f"Connected user '{user_key}' to existing RAG index of @{channel}."
                if was_already_indexed
                else f"Created new RAG index for @{channel} and connected user '{user_key}'."
            ),
        }

    def unsubscribe_user(self, channel_input: str, user_id: str | int = "default_user") -> Dict[str, Any]:
        """Unsubscribe user from a channel.

        Args:
            channel_input (str): Target channel to detach.
            user_id (str | int): User identifier.

        Returns:
            Dict[str, Any]: Detach operation status.
        """
        channel = self._sanitize_channel(channel_input)
        user_key = str(user_id)
        subs = self._load_subscriptions()
        user_list = subs.get(user_key, [])

        if channel in user_list:
            user_list.remove(channel)
            subs[user_key] = user_list
            self._save_subscriptions(subs)

        return {
            "status": "success",
            "user_id": user_key,
            "channel": channel,
            "user_channels": user_list,
            "message": f"Channel @{channel} disconnected from user '{user_key}'.",
        }

    def search_user_channels(
        self,
        query: str,
        user_id: str | int = "default_user",
        channels_override: Optional[List[str]] = None,
        top_k: int = 5,
        min_score: float = 0.05
    ) -> List[Dict[str, Any]]:
        """Perform search across all subscribed channels of a user or specified list.

        Args:
            query (str): Search term.
            user_id (str | int): User identifier.
            channels_override (Optional[List[str]]): Specific channels filter.
            top_k (int): Maximum combined results to return.
            min_score (float): Score threshold.

        Returns:
            List[Dict[str, Any]]: Aggregated, ranked search results across channels.
        """
        if not query.strip():
            return []

        target_channels = channels_override or self.get_user_channels(user_id=user_id)
        if not target_channels:
            # Fallback: if user has no subscriptions, search all available indexed channels
            target_channels = [c["channel"] for c in self.list_available_channels() if c["is_indexed"]]

        all_matches: List[Dict[str, Any]] = []

        for ch in target_channels:
            indexer = self.get_channel_indexer(ch)
            if not indexer.messages:
                continue

            results = indexer.search(query=query, top_k=top_k, min_score=min_score)
            for r in results:
                all_matches.append({
                    "channel": ch,
                    "message_id": r.get("id"),
                    "author": r.get("author"),
                    "date": r.get("timestamp"),
                    "snippet": r.get("text"),
                    "url": r.get("url"),
                    "score": r.get("score", 0.0),
                })

        # Sort all matched results by score descending
        all_matches.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        return all_matches[:top_k]
