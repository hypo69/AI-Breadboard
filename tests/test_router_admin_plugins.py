# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Testing Plugin Management Endpoints and Scope Filtering
# =============================================================================
# Description:
#   Module contains tests for REST API endpoints /api/admin/plugins and /api/plugins,
#   verifying that system plugins are excluded from user-facing interfaces.
#
# File: test_router_admin_plugins.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
from fastapi.testclient import TestClient
from header import __root__
from main import app

client = TestClient(app)


class TestPluginsAPI:
    """Testing plugin management endpoints and scope visibility rules."""

    def test_list_all_plugins_admin(self) -> None:
        """Verify that admin plugins route returns all registered plugins."""
        response = client.get("/api/admin/plugins")
        assert response.status_code == 200

        data = response.json()
        assert "plugins" in data
        assert isinstance(data["plugins"], list)
        assert data["count"] == len(data["plugins"])
        assert data["count"] >= 1

        plugin_names = [p["name"] for p in data["plugins"]]
        # System plugins must be present in full admin list
        assert "telegram_bot" in plugin_names or "generate_rag_from_codebase" in plugin_names

    def test_list_plugins_user_scope_query(self) -> None:
        """Verify that ?scope=user excludes system plugins."""
        response = client.get("/api/admin/plugins?scope=user")
        assert response.status_code == 200

        data = response.json()
        assert "plugins" in data
        assert isinstance(data["plugins"], list)

        for plugin in data["plugins"]:
            assert plugin.get("is_system") is False
            assert plugin.get("scope") != "system"

    def test_list_plugins_user_endpoint(self) -> None:
        """Verify that /api/plugins route returns only user-facing plugins for non-system scope."""
        response = client.get("/api/plugins?scope=user")
        assert response.status_code == 200

        data = response.json()
        assert "plugins" in data
        assert isinstance(data["plugins"], list)

        for plugin in data["plugins"]:
            assert plugin.get("is_system") is False
            assert plugin.get("scope") != "system"

    def test_system_plugins_have_correct_flags(self) -> None:
        """Verify that system plugins declare is_system=True."""
        response = client.get("/api/admin/plugins")
        assert response.status_code == 200
        plugins = response.json()["plugins"]

        system_plugins = [p for p in plugins if p.get("is_system") is True]
        assert len(system_plugins) > 0

        system_names = [p["name"] for p in system_plugins]
        assert "telegram_bot" in system_names or "generate_rag_from_codebase" in system_names

    def test_user_plugins_have_correct_flags(self) -> None:
        """Verify that user plugins (e.g. rag_cleaner) declare is_system=False and scope=user."""
        response = client.get("/api/admin/plugins")
        assert response.status_code == 200
        plugins = response.json()["plugins"]

        rag_cleaner = next((p for p in plugins if p["name"] == "rag_cleaner"), None)
        if rag_cleaner:
            assert rag_cleaner.get("is_system") is False
            assert rag_cleaner.get("scope") == "user"
