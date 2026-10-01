# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Apps User Assistant
# =============================================================================
# Description:
#   Test UserAssistantEngine agenda aggregation.
#
# Usage Examples:
#   Python API:
#     from tests.test_apps_user_assistant import test_user_assistant_engine_agenda
#
#     res = test_user_assistant_engine_agenda()
#
# File: test_apps_user_assistant.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

from __future__ import annotations
"""Test UserAssistantEngine agenda aggregation."""

import pytest
from fastapi.testclient import TestClient
from apps.user_assistant.engine import UserAssistantEngine
from apps.user_assistant.routers.router import init_router
from main import app

def test_user_assistant_engine_agenda():
    """Test UserAssistantEngine agenda aggregation."""
    engine = UserAssistantEngine(user_id=1)
    agenda = engine.get_daily_agenda()
    assert 'user_id' in agenda
    assert agenda['user_id'] == 1
    assert 'upcoming_events_count' in agenda
    assert 'unread_emails_count' in agenda
    assert 'recent_files_count' in agenda
    assert isinstance(agenda['events'], list)
    assert isinstance(agenda['emails'], list)
    assert isinstance(agenda['files'], list)

def test_user_assistant_router_agenda():
    """Test /api/v1/assistant/agenda endpoint."""
    client = TestClient(app)
    response = client.get('/api/v1/assistant/agenda')
    assert response.status_code == 200
    data = response.json()
    assert 'user_id' in data
    assert 'upcoming_events_count' in data

def test_user_assistant_router_mail():
    """Test /api/v1/assistant/mail endpoint."""
    client = TestClient(app)
    response = client.get('/api/v1/assistant/mail?limit=5')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'ok'
    assert 'messages' in data

def test_user_assistant_router_calendar():
    """Test /api/v1/assistant/calendar endpoint."""
    client = TestClient(app)
    response = client.get('/api/v1/assistant/calendar?days=3')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'ok'
    assert 'events' in data

def test_user_assistant_router_documents():
    """Test /api/v1/assistant/documents endpoint."""
    client = TestClient(app)
    response = client.get('/api/v1/assistant/documents')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'ok'
    assert 'files' in data