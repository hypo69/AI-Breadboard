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

client = TestClient(app, cookies={"admin_password_verified": "true"})



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

    def test_news_tab_in_admin_and_user_html(self) -> None:
        """Verify tab-news presence in admin and user interfaces."""
        webinterface_dir = __root__ / "src" / "api" / "webgui"
        admin_html = (webinterface_dir / "admin" / "index.html").read_text(encoding="utf-8")
        user_html = (webinterface_dir / "user" / "index.html").read_text(encoding="utf-8")
        main_html = (webinterface_dir / "index.html").read_text(encoding="utf-8")

        assert 'id="tab-news"' in admin_html
        assert 'id="tab-news"' in user_html
        assert 'id="tab-news"' in main_html

    def test_dropdown_navigation_supports_data_plugin(self) -> None:
        """Verify that dropdown setup in main.js files handles data-plugin attribute."""
        webinterface_dir = __root__ / "src" / "api" / "webgui"
        main_js = (webinterface_dir / "js" / "main.js").read_text(encoding="utf-8")
        admin_js = (webinterface_dir / "admin" / "main.js").read_text(encoding="utf-8")
        user_js = (webinterface_dir / "user" / "main.js").read_text(encoding="utf-8")
        plugins_tab_js = (webinterface_dir / "plugins_tab" / "main.js").read_text(encoding="utf-8")

        assert "data-plugin" in main_js
        assert "data-plugin" in admin_js
        assert "data-plugin" in user_js
        assert "data-plugin" in plugins_tab_js
        assert "openPluginFromDropdown" in plugins_tab_js

