# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Disabled Auth Verification Tests
# =============================================================================
# Description:
#   Unit tests verifying that when DISABLE_AUTH=true is set (such as when launching
#   via ts.ps1 / tc.ps1), authentication and OAuth are bypassed.
#
# File: test_disabled_auth.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from src.api.router_auth import is_auth_disabled, is_oauth_enabled, get_current_user_data
from src.app import create_app, register_pages, AppState


def test_auth_disabled_helpers(monkeypatch):
    """Verifies is_auth_disabled and is_oauth_enabled under DISABLE_AUTH=true."""
    monkeypatch.setenv("DISABLE_AUTH", "true")
    monkeypatch.setenv("ENABLE_OAUTH", "true")

    assert is_auth_disabled() is True
    # When auth is disabled, OAuth is automatically disabled
    assert is_oauth_enabled() is False


def test_get_current_user_data_when_auth_disabled(monkeypatch):
    """Verifies get_current_user_data returns local fallback user without requiring auth token."""
    monkeypatch.setenv("DISABLE_AUTH", "true")
    req = Request(scope={"type": "http", "method": "GET", "path": "/apps", "headers": []})

    user = get_current_user_data(req)
    assert user is not None
    assert user.id == 1
    assert user.email == "local@aibreadboard.local"


def test_apps_endpoint_accessible_without_auth():
    """Verifies that /apps is accessible without requiring cookies or OAuth."""
    app = create_app()
    state = AppState()
    app.state.app_state = state
    register_pages(app)

    client = TestClient(app)
    res = client.get("/apps")
    assert res.status_code == 200
    assert "AI Breadboard Apps" in res.text or "apps-interface" in res.text


def test_pages_accessible_when_auth_disabled(monkeypatch):
    """Verifies root / and /admin are accessible directly when DISABLE_AUTH is true."""
    monkeypatch.setenv("DISABLE_AUTH", "true")

    app = create_app()
    state = AppState()
    app.state.app_state = state
    register_pages(app)

    client = TestClient(app)
    res = client.get("/")
    assert res.status_code == 200

    admin_res = client.get("/admin")
    assert admin_res.status_code == 200
    assert "AI Assistant - Admin" in admin_res.text or "mainTabs" in admin_res.text


def test_ts_launcher_exists():
    """Verifies ts.ps1 launcher file exists in project root with valid synopsis."""
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    ts_file = root / "ts.ps1"
    assert ts_file.is_file(), "ts.ps1 must exist in project root"

    content = ts_file.read_text(encoding="utf-8")
    assert ".SYNOPSIS" in content
    assert "tc.ps1" in content
    assert "DISABLE_AUTH" in content


def test_oauth_disabled_by_default_in_configs():
    """Проверяет, что enable_oauth установлен в false в config.json и config_tc.json."""
    import json
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent

    config_json_path = root / "config.json"
    if config_json_path.is_file():
        data = json.loads(config_json_path.read_text(encoding="utf-8"))
        assert data.get("server", {}).get("enable_oauth") is False, "config.json server.enable_oauth must be false"

    config_tc_path = root / "config_tc.json"
    if config_tc_path.is_file():
        tc_data = json.loads(config_tc_path.read_text(encoding="utf-8"))
        assert tc_data.get("server", {}).get("enable_oauth") is False, "config_tc.json server.enable_oauth must be false"


def test_oauth_enabled_toggle(monkeypatch):
    """Проверяет переключение OAuth флага через переменную окружения ENABLE_OAUTH."""
    monkeypatch.delenv("DISABLE_AUTH", raising=False)
    monkeypatch.setenv("ENABLE_OAUTH", "false")
    assert is_oauth_enabled() is False

    monkeypatch.setenv("ENABLE_OAUTH", "true")
    assert is_oauth_enabled() is True

