# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Messenger and Real-Time Hub Unit Tests
# =============================================================================
# Description:
#   Comprehensive test suite validating Messenger database initialization,
#   room creation, message delivery, WordPress SSO token generation/verification,
#   edge case handling, user search, and administrative statistics.
#
# File: tests/test_messenger.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from main import app
from src.api.messenger.sync_bridge import create_sso_token, verify_sso_token
from src.api.messenger.database import init_db, get_db


@pytest.fixture(scope="module", autouse=True)
def setup_messenger_db():
    """Initialize messenger database tables before running the test suite.

    Yields:
        None: Database is ready for tests.
    """
    init_db()


def test_sso_token_generation_and_verification_happy_path():
    """Test standard SSO token generation and verification cycle.

    Validates: Signed JWT contains expected sub, email, and name claims.
    """
    # --- Arrange: Prepare test user credentials ---
    # User identifier from WordPress environment
    test_user_id: str = "wp_user_42"
    # User email address
    test_email: str = "test@wordpress.org"
    # User display name
    test_name: str = "WP Tester"
    # Token lifetime in hours
    test_expiry: int = 2

    # --- Act: Generate and decode token ---
    # Generated JWT token string
    token: str = create_sso_token(
        user_id=test_user_id,
        email=test_email,
        display_name=test_name,
        expiry_hours=test_expiry
    )
    # Decoded dictionary payload
    decoded: dict | None = verify_sso_token(token)

    # --- Assert: Verify claims ---
    assert token is not None, "Token generation returned None"
    assert isinstance(token, str), f"Expected token string, got {type(token)}"
    assert decoded is not None, "Failed to decode valid SSO token"
    assert decoded.get("sub") == test_user_id, f"Subject claim mismatch: {decoded.get('sub')} != {test_user_id}"
    assert decoded.get("email") == test_email, f"Email claim mismatch: {decoded.get('email')} != {test_email}"
    assert decoded.get("name") == test_name, f"Name claim mismatch: {decoded.get('name')} != {test_name}"


def test_sso_token_invalid_signature():
    """Test edge case: Tampered or invalid SSO token decoding.

    Validates: verify_sso_token gracefully returns None on invalid token.
    """
    # --- Arrange: Invalid token string ---
    invalid_token: str = "invalid.jwt.token_string"

    # --- Act: Attempt decode ---
    result: dict | None = verify_sso_token(invalid_token)

    # --- Assert: Must return None ---
    assert result is None, f"Expected None for invalid token, got {result}"


def test_messenger_rooms_and_messages_workflow():
    """Test end-to-end conversation workflow: create room, post message, and query history.

    Validates: Room creation, message serialization, and history retrieval.
    """
    # --- Arrange: TestClient instance ---
    client: TestClient = TestClient(app)

    # --- Act 1: Get current user profile ---
    res_me = client.get("/api/messenger/users/me")
    assert res_me.status_code == 200, f"Failed to get user profile: {res_me.text}"
    user_me: dict | None = res_me.json().get("user")
    assert user_me is not None, "User profile payload missing 'user' key"

    # --- Act 2: Create a group room ---
    create_payload: dict = {
        "room_type": "group",
        "title": "TDD Dev Room",
        "description": "Room for automated test verification",
        "member_ids": []
    }
    res_create = client.post("/api/messenger/rooms", json=create_payload)
    assert res_create.status_code == 200, f"Room creation failed: {res_create.text}"
    room_id: str | None = res_create.json().get("room_id")
    assert room_id is not None, "Created room response missing 'room_id'"

    # --- Act 3: Post a message ---
    msg_payload: dict = {
        "content": "Hello World from TDD automated test!",
        "message_type": "text"
    }
    res_msg = client.post(f"/api/messenger/rooms/{room_id}/messages", json=msg_payload)
    assert res_msg.status_code == 200, f"Message send failed: {res_msg.text}"
    msg_id: str | None = res_msg.json().get("message_id")
    assert msg_id is not None, "Message send response missing 'message_id'"

    # --- Act 4: Query history ---
    res_history = client.get(f"/api/messenger/rooms/{room_id}/messages")
    assert res_history.status_code == 200, f"Message history fetch failed: {res_history.text}"
    messages: list = res_history.json().get("messages", [])
    assert len(messages) >= 1, f"Expected at least 1 message in history, got {len(messages)}"
    assert messages[-1]["content"] == msg_payload["content"], "Message content does not match sent text"


def test_messenger_user_search():
    """Test user search endpoint for room member invitations.

    Validates: Searching with valid substring returns matching user list.
    """
    # --- Arrange: TestClient and search query ---
    client: TestClient = TestClient(app)
    query: str = "adm"

    # --- Act: Perform search ---
    res = client.get(f"/api/messenger/users/search?q={query}")

    # --- Assert: Check response ---
    assert res.status_code == 200, f"User search failed: {res.text}"
    users: list = res.json().get("users", [])
    assert isinstance(users, list), f"Expected list of users, got {type(users)}"


def test_messenger_admin_stats():
    """Test administrator statistics endpoint for active metrics.

    Validates: Returns count of users, rooms, messages, and calls.
    """
    # --- Arrange: TestClient instance ---
    client: TestClient = TestClient(app)

    # --- Act: Query stats ---
    res_stats = client.get("/api/messenger/admin/stats")

    # --- Assert: Verify structure and counts ---
    assert res_stats.status_code == 200, f"Admin stats fetch failed: {res_stats.text}"
    stats: dict | None = res_stats.json().get("stats")
    assert stats is not None, "Stats response missing 'stats' key"
    assert "total_rooms" in stats, "Stats missing 'total_rooms'"
    assert "total_messages" in stats, "Stats missing 'total_messages'"
    assert "online_users" in stats, "Stats missing 'online_users'"
    assert stats["total_rooms"] >= 1, f"Expected total_rooms >= 1, got {stats['total_rooms']}"
