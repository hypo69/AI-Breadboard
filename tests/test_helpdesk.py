# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Helpdesk Subsystem Unit and Integration Tests
# =============================================================================
# Description:
#   Test suite covering ticket creation, message posting, status updating,
#   priority management, filtering, and helpdesk statistics endpoints.
#
# File: test_helpdesk.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
from fastapi.testclient import TestClient

from main import app
from src.fastapi.helpdesk.database import init_db, get_db


@pytest.fixture(autouse=True)
def setup_helpdesk_db():
    """Ensure clean test environment for helpdesk tables."""
    init_db()
    with get_db() as conn:
        conn.execute("DELETE FROM helpdesk_messages;")
        conn.execute("DELETE FROM helpdesk_tickets;")
    yield


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


def test_create_and_get_ticket(client: TestClient):
    """Test creating a new helpdesk ticket and retrieving it."""
    payload = {
        "subject": "Need help with ONNX DirectML model",
        "message": "The ONNX DirectML model fails to load with error 1005.",
        "category": "technical",
        "priority": "high",
        "user_name": "Test User",
        "user_email": "test@example.com"
    }
    res_create = client.post("/api/helpdesk/tickets", json=payload)
    assert res_create.status_code == 200
    data_create = res_create.json()
    assert data_create["status"] == "success"
    assert "ticket" in data_create
    ticket_id = data_create["ticket"]["id"]
    assert data_create["ticket"]["subject"] == payload["subject"]
    assert data_create["ticket"]["priority"] == "high"
    assert data_create["ticket"]["status"] == "open"

    # Fetch details
    res_get = client.get(f"/api/helpdesk/tickets/{ticket_id}")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["ticket"]["id"] == ticket_id
    assert len(data_get["messages"]) == 1
    assert data_get["messages"][0]["content"] == payload["message"]


def test_send_ticket_message(client: TestClient):
    """Test sending an operator reply and internal note to a ticket."""
    # 1. Create ticket
    payload = {
        "subject": "Billing inquiry",
        "message": "How do I upgrade my quota?",
    }
    t_id = client.post("/api/helpdesk/tickets", json=payload).json()["ticket"]["id"]

    # 2. Operator message
    reply_payload = {
        "content": "You can configure additional API keys in Settings.",
        "is_internal_note": False,
        "sender_type": "operator"
    }
    res_msg = client.post(f"/api/helpdesk/tickets/{t_id}/messages", json=reply_payload)
    assert res_msg.status_code == 200
    assert res_msg.json()["message"]["content"] == reply_payload["content"]

    # 3. Internal note
    note_payload = {
        "content": "Operator note: User verified.",
        "is_internal_note": True,
        "sender_type": "operator"
    }
    res_note = client.post(f"/api/helpdesk/tickets/{t_id}/messages", json=note_payload)
    assert res_note.status_code == 200
    assert res_note.json()["message"]["is_internal_note"] is True

    # 4. Check conversation history
    res_get = client.get(f"/api/helpdesk/tickets/{t_id}")
    assert len(res_get.json()["messages"]) == 3  # Initial + Reply + Note


def test_update_ticket_status_and_priority(client: TestClient):
    """Test changing ticket status and priority using PATCH and PUT routes."""
    # 1. Arrange: Create base ticket
    t_id = client.post("/api/helpdesk/tickets", json={"subject": "Bug", "message": "Crash"}).json()["ticket"]["id"]

    # 2. Act & Assert: PATCH status and priority
    patch_payload = {
        "status": "in_progress",
        "priority": "urgent"
    }
    res_patch = client.patch(f"/api/helpdesk/tickets/{t_id}", json=patch_payload)
    assert res_patch.status_code == 200, f"PATCH failed: {res_patch.text}"
    updated = res_patch.json()["ticket"]
    assert updated["status"] == "in_progress", "Expected status to be updated to in_progress"
    assert updated["priority"] == "urgent", "Expected priority to be updated to urgent"

    # 3. Act & Assert: Direct PUT status endpoint
    res_put_status = client.put(f"/api/helpdesk/tickets/{t_id}/status", json={"status": "resolved"})
    assert res_put_status.status_code == 200, f"PUT status failed: {res_put_status.text}"
    assert res_put_status.json()["ticket"]["status"] == "resolved", "Expected status to be updated to resolved"

    # 4. Act & Assert: Direct PUT priority endpoint
    res_put_prio = client.put(f"/api/helpdesk/tickets/{t_id}/priority", json={"priority": "low"})
    assert res_put_prio.status_code == 200, f"PUT priority failed: {res_put_prio.text}"
    assert res_put_prio.json()["ticket"]["priority"] == "low", "Expected priority to be updated to low"


def test_helpdesk_stats_and_filtering(client: TestClient):
    """Test helpdesk statistics aggregation and query filtering."""
    client.post("/api/helpdesk/tickets", json={"subject": "Issue 1", "message": "Msg 1", "priority": "normal"})
    client.post("/api/helpdesk/tickets", json={"subject": "Issue 2", "message": "Msg 2", "priority": "urgent"})

    res_stats = client.get("/api/helpdesk/stats")
    assert res_stats.status_code == 200
    stats = res_stats.json()["stats"]
    assert stats["total_tickets"] == 2
    assert stats["open_tickets"] == 2
    assert stats["urgent_tickets"] == 1

    # Filter tickets
    res_filter = client.get("/api/helpdesk/tickets?priority=urgent")
    assert res_filter.status_code == 200
    assert len(res_filter.json()["tickets"]) == 1


def test_helpdesk_ui_routes(client: TestClient):
    """Test that /helpdesk web interface routes and admin helpdesk_tab assets are accessible."""
    res_page = client.get("/helpdesk")
    assert res_page.status_code == 200
    assert "Helpdesk" in res_page.text

    res_css = client.get("/helpdesk/style.css")
    assert res_css.status_code == 200
    assert "helpdesk" in res_css.text.lower()

    # Verify admin helpdesk_tab files are served via static /html
    res_tab_html = client.get("/html/helpdesk_tab/index.html")
    assert res_tab_html.status_code == 200, f"helpdesk_tab/index.html not found: {res_tab_html.status_code}"
    assert "Helpdesk" in res_tab_html.text

    res_tab_js = client.get("/html/helpdesk_tab/main.js")
    assert res_tab_js.status_code == 200, f"helpdesk_tab/main.js not found: {res_tab_js.status_code}"
    assert "initHelpdeskTab" in res_tab_js.text

