# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit tests for Telegram Channel RAG API endpoints
# =============================================================================
# Description:
#   Integration and unit tests for /api/telegram_rag router endpoints (channels list,
#   subscribe, unsubscribe, reindex, search).
#
# File: test_router_telegram_rag.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Unit tests for /api/telegram_rag router."""

import shutil
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from main import app
from plugins.telegram_channel_rag.channel_manager import ChannelManager
from plugins.telegram_channel_rag.indexer import TelegramChannelIndexer

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_telegram_channel_manager(monkeypatch):
    """Provide an isolated ChannelManager instance for each test."""
    temp_dir = Path(tempfile.mkdtemp())
    isolated_mgr = ChannelManager(base_storage_dir=temp_dir)

    # Populate a sample indexed channel 'sample_channel'
    sample_dir = temp_dir / "sample_channel"
    idx = TelegramChannelIndexer(index_dir=sample_dir)
    idx.build_index([
        {
            "id": 1,
            "channel": "sample_channel",
            "author": "Alice",
            "timestamp": "2026-03-01",
            "text": "Latest breakthroughs in quantum computing and AI",
            "url": "https://t.me/sample_channel/1",
        },
        {
            "id": 2,
            "channel": "sample_channel",
            "author": "Bob",
            "timestamp": "2026-03-02",
            "text": "Python 3.14 release details and performance improvements",
            "url": "https://t.me/sample_channel/2",
        },
    ])
    idx.save()

    # Pre-subscribe user 'test_user'
    isolated_mgr._save_subscriptions({"test_user": ["sample_channel"]})

    monkeypatch.setattr("src.api.router_telegram_rag._channel_manager", isolated_mgr)

    yield isolated_mgr

    shutil.rmtree(temp_dir, ignore_errors=True)


class TestRouterTelegramRAG:
    """Test suite for /api/telegram_rag endpoints."""

    def test_list_channels(self):
        """Test GET /api/telegram_rag/channels."""
        resp = client.get("/api/telegram_rag/channels?user_id=test_user")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "sample_channel" in data["user_subscriptions"]
        assert len(data["available_channels"]) >= 1
        ch = data["available_channels"][0]
        assert ch["channel"] == "sample_channel"
        assert ch["messages_count"] == 2

    def test_search_telegram_rag_unified(self):
        """Test POST /api/telegram_rag/search."""
        resp = client.post(
            "/api/telegram_rag/search",
            json={
                "query": "quantum computing",
                "user_id": "test_user",
                "channel": "sample_channel",
                "search_mode": "unified",
                "top_k": 5,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["results_count"] == 1
        assert "https://t.me/sample_channel/1" in data["results"][0]["url"]

    def test_subscribe_and_unsubscribe(self):
        """Test POST /api/telegram_rag/subscribe and /api/telegram_rag/unsubscribe."""
        # 1. Subscribe existing channel to new user 'user2'
        resp_sub = client.post(
            "/api/telegram_rag/subscribe",
            json={"channel": "sample_channel", "user_id": "user2", "max_messages": 100},
        )
        assert resp_sub.status_code == 200
        data_sub = resp_sub.json()
        assert data_sub["status"] == "success"
        assert data_sub["reused_existing_rag"] is True

        # Verify subscribed
        resp_list = client.get("/api/telegram_rag/channels?user_id=user2")
        assert "sample_channel" in resp_list.json()["user_subscriptions"]

        # 2. Unsubscribe
        resp_unsub = client.post(
            "/api/telegram_rag/unsubscribe",
            json={"channel": "sample_channel", "user_id": "user2"},
        )
        assert resp_unsub.status_code == 200
        assert resp_unsub.json()["status"] == "success"

        # Verify no longer subscribed
        resp_list2 = client.get("/api/telegram_rag/channels?user_id=user2")
        assert "sample_channel" not in resp_list2.json()["user_subscriptions"]
