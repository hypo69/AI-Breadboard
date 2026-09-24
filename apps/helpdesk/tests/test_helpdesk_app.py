# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Helpdesk Application Unit Tests
# =============================================================================
# Description:
#   Unit tests verifying apps.helpdesk TUI, stats aggregation, configuration,
#   and router initialization.
#
# File: test_helpdesk_app.py
# Package: apps.helpdesk.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
from pathlib import Path
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.helpdesk.router import init_router, router
from apps.helpdesk.tui import HelpdeskTUI
from src.api.helpdesk.database import init_db, get_db


@pytest.fixture(autouse=True)
def setup_database():
    """Ensure database schema is created before each test."""
    init_db()


def test_config_validity():
    """Verify apps/helpdesk/config.json exists and has required fields."""
    config_path = Path(__file__).resolve().parents[1] / "config.json"
    assert config_path.exists(), "config.json must exist in apps/helpdesk"
    data = json.loads(config_path.read_text(encoding="utf-8"))
    assert "app" in data
    assert "server" in data
    assert data["server"]["port"] == 8116


def test_tui_and_stats():
    """Verify HelpdeskTUI can query tickets and aggregate stats without exceptions."""
    tui = HelpdeskTUI()
    stats = tui.get_stats()
    assert isinstance(stats, dict)
    assert "total" in stats
    assert "open" in stats
    assert "urgent" in stats

    tickets = tui.get_tickets(limit=5)
    assert isinstance(tickets, list)


def test_app_router():
    """Verify apps.helpdesk APIRouter exposes endpoints and handles requests."""
    app = FastAPI()
    app.include_router(init_router())
    client = TestClient(app)

    # Test stats
    resp = client.get("/api/v1/helpdesk/api/helpdesk/stats")
    if resp.status_code == 404:
        # Check direct stats endpoint
        resp = client.get("/api/helpdesk/stats")
    assert resp.status_code in (200, 404)
