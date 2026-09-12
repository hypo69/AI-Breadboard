# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit Tests for Multi-Channel Telegram RAG Plugin
# =============================================================================
# Description:
#   Validates channel pool management, instant RAG reuse on user subscription,
#   multi-channel federated search, permalinks, and plugin lifecycle actions.
#
# File: test_plugin_telegram_channel_rag.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Unit tests for Multi-Channel Telegram RAG & User Subscription Plugin."""

import json
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch

from plugins.telegram_channel_rag.collector import TelegramMessageCollector
from plugins.telegram_channel_rag.indexer import TelegramChannelIndexer
from plugins.telegram_channel_rag.channel_manager import ChannelManager
from plugins.telegram_channel_rag.plugin import TelegramChannelRagPlugin
from plugins.telegram_channel_rag import plugin


def test_telegram_collector_username_cleaner():
    """Test channel username parsing and URL cleaning."""
    col1 = TelegramMessageCollector("canozrimb")
    assert col1.channel_username == "canozrimb"

    col2 = TelegramMessageCollector("https://t.me/canozrimb")
    assert col2.channel_username == "canozrimb"

    col3 = TelegramMessageCollector("https://t.me/s/canozrimb/")
    assert col3.channel_username == "canozrimb"

    col4 = TelegramMessageCollector("@canozrimb")
    assert col4.channel_username == "canozrimb"

    assert col1.build_message_url(1234) == "https://t.me/canozrimb/1234"


def test_telegram_collector_parse_json_export(tmp_path):
    """Test parsing exported Telegram Desktop result.json file."""
    export_data = {
        "messages": [
            {
                "id": 101,
                "type": "message",
                "date": "2026-03-01T12:00:00",
                "from": "Alex",
                "text": "Hello world, check this project out",
            },
            {
                "id": 102,
                "type": "message",
                "date": "2026-03-01T12:05:00",
                "from": "Boris",
                "text": ["Discussion on ", {"type": "link", "text": "https://example.com"}],
            },
        ],
    }
    json_path = tmp_path / "result.json"
    json_path.write_text(json.dumps(export_data), encoding="utf-8")

    collector = TelegramMessageCollector("canozrimb")
    messages = collector.parse_export_json(json_path)

    assert len(messages) == 2
    assert messages[0]["id"] == 101
    assert messages[0]["url"] == "https://t.me/canozrimb/101"
    assert "Hello world" in messages[0]["text"]


def test_channel_manager_subscription_and_reuse(tmp_path):
    """Test user subscription connecting to existing RAG pool without scraping."""
    manager = ChannelManager(base_storage_dir=tmp_path)

    # 1. Pre-populate channel 'canozrimb' RAG index
    canozrimb_dir = tmp_path / "canozrimb"
    idx = TelegramChannelIndexer(index_dir=canozrimb_dir)
    idx.build_index([
        {
            "id": 50,
            "channel": "canozrimb",
            "author": "Alice",
            "timestamp": "2026-01-01",
            "text": "Deep Learning with PyTorch and Transformers",
            "url": "https://t.me/canozrimb/50",
        }
    ])
    idx.save()

    # Verify channel is recognized as existing
    assert manager.is_channel_indexed("canozrimb") is True

    # 2. User 1 subscribes to 'canozrimb' (Should reuse existing index instantly)
    sub_res = manager.subscribe_user(channel_input="https://t.me/canozrimb", user_id="user_1")
    assert sub_res["status"] == "success"
    assert sub_res["reused_existing_rag"] is True
    assert sub_res["messages_indexed"] == 1
    assert "canozrimb" in manager.get_user_channels("user_1")

    # 3. User 2 also subscribes to 'canozrimb' (Also reuses existing index)
    sub_res_2 = manager.subscribe_user(channel_input="canozrimb", user_id="user_2")
    assert sub_res_2["status"] == "success"
    assert sub_res_2["reused_existing_rag"] is True

    # 4. Search for User 1
    results = manager.search_user_channels(query="PyTorch Transformers", user_id="user_1")
    assert len(results) == 1
    assert results[0]["message_id"] == 50
    assert results[0]["url"] == "https://t.me/canozrimb/50"


@pytest.mark.asyncio
async def test_plugin_multi_channel_actions(tmp_path):
    """Test multi-channel actions: list, subscribe, search, unsubscribe."""
    cfg = {
        "storage_dir": str(tmp_path),
        "similarity_top_k": 3,
    }
    p = plugin(config=cfg)
    p.channel_manager = ChannelManager(base_storage_dir=tmp_path)

    # Populate index for 'tech_news'
    tech_dir = tmp_path / "tech_news"
    idx = TelegramChannelIndexer(index_dir=tech_dir)
    idx.build_index([
        {
            "id": 99,
            "channel": "tech_news",
            "author": "Reporter",
            "timestamp": "2026-02-01",
            "text": "New AI models released this week",
            "url": "https://t.me/tech_news/99",
        }
    ])
    idx.save()

    # 1. Action: subscribe_channel
    sub_res = await p.execute_action(
        "subscribe_channel",
        {"channel": "tech_news", "user_id": "alice"}
    )
    assert sub_res["status"] == "success"
    assert sub_res["reused_existing_rag"] is True

    # 2. Action: list_channels
    list_res = await p.execute_action("list_channels", {"user_id": "alice"})
    assert list_res["status"] == "success"
    assert "tech_news" in list_res["user_subscriptions"]

    # 3. Action: search
    search_res = await p.execute_action(
        "search",
        {"query": "AI models", "user_id": "alice"}
    )
    assert search_res["status"] == "success"
    assert search_res["results_count"] == 1
    assert search_res["results"][0]["url"] == "https://t.me/tech_news/99"

    # 4. Tool call
    tool_out = await p.execute_tool(
        "search_telegram_channels",
        {"query": "AI models", "user_id": "alice"}
    )
    assert "https://t.me/tech_news/99" in tool_out

    # 5. Action: unsubscribe_channel
    unsub_res = await p.execute_action(
        "unsubscribe_channel",
        {"channel": "tech_news", "user_id": "alice"}
    )
    assert unsub_res["status"] == "success"
    assert "tech_news" not in p.channel_manager.get_user_channels("alice")
