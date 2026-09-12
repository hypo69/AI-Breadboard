# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit and integration tests for chat sessions management
# =============================================================================
# Description:
#   Validates SQLite persistence, CRUD operations, bulk synchronization, and
#   FastAPI REST endpoints for chat sessions and conversational history.
#
# File: test_chat_sessions.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.fastapi import chat_sessions_db
from src.fastapi.router_chat import init_router as init_chat_router


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path: Path):
    """Fixture ensuring chat sessions db uses an isolated temporary path during tests."""
    temp_db = tmp_path / "test_chat_sessions.db"
    with patch.object(chat_sessions_db, "DB_PATH", temp_db):
        chat_sessions_db.init_db()
        yield temp_db


@pytest.fixture
def chat_api_client():
    """Create test client with initialized chat router."""
    app = FastAPI()
    mock_chat_model = Mock()
    mock_chat_model.api_key = "test-key"
    mock_narrator_model = Mock()
    router = init_chat_router(mock_chat_model, mock_narrator_model)
    app.include_router(router)
    return TestClient(app)


class TestChatSessionsDB:
    """Unit tests for chat_sessions_db SQLite persistence module."""

    def test_save_and_get_session(self):
        """Test creating and retrieving a chat session."""
        session_data = {
            "id": "session_test_1",
            "userId": "user_1",
            "title": "Discussion about Python",
            "isCustomTitle": True,
            "createdAt": 1700000000000,
            "updatedAt": 1700000001000,
            "messages": [{"sender": "user", "text": "Hello!"}],
            "chatHistory": [{"role": "user", "parts": ["Hello!"]}]
        }
        saved = chat_sessions_db.save_session(session_data, user_id="user_1")
        assert saved["id"] == "session_test_1"
        assert saved["title"] == "Discussion about Python"

        fetched = chat_sessions_db.get_session("session_test_1", user_id="user_1")
        assert fetched["id"] == "session_test_1"
        assert fetched["userId"] == "user_1"
        assert len(fetched["messages"]) == 1
        assert fetched["messages"][0]["text"] == "Hello!"

    def test_list_and_delete_sessions(self):
        """Test listing and deleting sessions."""
        chat_sessions_db.save_session({"id": "s1", "title": "Session 1", "createdAt": 1000, "updatedAt": 1000}, user_id="u1")
        chat_sessions_db.save_session({"id": "s2", "title": "Session 2", "createdAt": 2000, "updatedAt": 2000}, user_id="u1")

        sessions = chat_sessions_db.list_sessions("u1")
        assert len(sessions) == 2
        assert sessions[0]["id"] == "s2"  # ordered by updatedAt DESC

        deleted = chat_sessions_db.delete_session("s1", user_id="u1")
        assert deleted is True

        sessions_after = chat_sessions_db.list_sessions("u1")
        assert len(sessions_after) == 1
        assert sessions_after[0]["id"] == "s2"

    def test_bulk_sync_sessions(self):
        """Test syncing multiple sessions and updating existing ones."""
        initial_session = {
            "id": "s_sync_1",
            "title": "Initial",
            "createdAt": 1000,
            "updatedAt": 1000,
            "messages": []
        }
        chat_sessions_db.save_session(initial_session, user_id="u1")

        client_batch = [
            {
                "id": "s_sync_1",
                "title": "Updated by Client",
                "createdAt": 1000,
                "updatedAt": 3000,
                "messages": [{"sender": "user", "text": "Synced"}]
            },
            {
                "id": "s_sync_2",
                "title": "New Session from Client",
                "createdAt": 2000,
                "updatedAt": 2000,
                "messages": []
            }
        ]
        synced = chat_sessions_db.bulk_sync_sessions(client_batch, user_id="u1")
        assert len(synced) == 2
        updated_s1 = chat_sessions_db.get_session("s_sync_1", user_id="u1")
        assert updated_s1["title"] == "Updated by Client"
        assert len(updated_s1["messages"]) == 1


class TestChatSessionsEndpoints:
    """Integration tests for FastAPI chat session REST endpoints."""

    def test_get_and_post_sessions(self, chat_api_client: TestClient):
        """Test GET /api/chat/sessions and POST /api/chat/sessions."""
        # Get empty list
        resp = chat_api_client.get("/api/chat/sessions")
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"
        assert resp.json()["sessions"] == []

        # Create session
        payload = {
            "id": "session_api_1",
            "title": "API Session",
            "isCustomTitle": False,
            "createdAt": 1700000000000,
            "updatedAt": 1700000000000,
            "messages": [{"sender": "user", "text": "Testing API"}],
            "chatHistory": []
        }
        post_resp = chat_api_client.post("/api/chat/sessions", json=payload)
        assert post_resp.status_code == 200
        assert post_resp.json()["session"]["id"] == "session_api_1"

        # Get single session
        get_single = chat_api_client.get("/api/chat/sessions/session_api_1")
        assert get_single.status_code == 200
        assert get_single.json()["session"]["title"] == "API Session"

    def test_sync_and_delete_endpoints(self, chat_api_client: TestClient):
        """Test POST /api/chat/sessions/sync and DELETE /api/chat/sessions/{id}."""
        sync_payload = {
            "sessions": [
                {"id": "sync_1", "title": "Chat 1", "createdAt": 100, "updatedAt": 100, "messages": []},
                {"id": "sync_2", "title": "Chat 2", "createdAt": 200, "updatedAt": 200, "messages": []}
            ]
        }
        sync_resp = chat_api_client.post("/api/chat/sessions/sync", json=sync_payload)
        assert sync_resp.status_code == 200
        assert len(sync_resp.json()["sessions"]) == 2

        # Delete single
        del_resp = chat_api_client.delete("/api/chat/sessions/sync_1")
        assert del_resp.status_code == 200
        assert del_resp.json()["deleted"] is True

        # Verify 1 remains
        list_resp = chat_api_client.get("/api/chat/sessions")
        assert len(list_resp.json()["sessions"]) == 1
        assert list_resp.json()["sessions"][0]["id"] == "sync_2"

        # Clear all
        clear_resp = chat_api_client.delete("/api/chat/sessions")
        assert clear_resp.status_code == 200
        assert clear_resp.json()["cleared"] is True

        list_after_clear = chat_api_client.get("/api/chat/sessions")
        assert len(list_after_clear.json()["sessions"]) == 0
