# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit Tests for Admin Panel Apps Tabs Integration
# =============================================================================
# Description:
#   Verifies that the admin interface properly serves the /apps application tabs
#   (Trading Terminal, Network Terminal, System Inspector) and their static files.
#
# File: test_admin_apps_tabs.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Unit tests for /apps tabs in Admin Panel."""

import json
from pathlib import Path
from fastapi.testclient import TestClient
from header import __root__
from main import app

client = TestClient(app)


class TestAdminAppsTabs:
    """Test suite verifying presence and integrity of /apps tabs in admin panel."""

    def test_admin_html_contains_apps_tabs(self):
        """Admin HTML should contain navigation entries and tab panes for /apps."""
        admin_html_path = __root__ / "src" / "api" / "webinterface" / "admin" / "index.html"
        assert admin_html_path.exists(), "Admin index.html must exist"
        content = admin_html_path.read_text(encoding="utf-8")

        assert 'id="appsTabsDropdown"' in content
        assert 'data-tab="tab-trading"' in content
        assert 'data-tab="tab-network"' in content
        assert 'data-tab="tab-system-inspector"' in content

        assert 'id="tab-trading"' in content
        assert 'id="tab-network"' in content
        assert 'id="tab-system-inspector"' in content

    def test_admin_main_js_loads_apps_tabs(self):
        """Admin main.js should register and load /apps tabs."""
        admin_js_path = __root__ / "src" / "api" / "webinterface" / "admin" / "main.js"
        assert admin_js_path.exists(), "Admin main.js must exist"
        content = admin_js_path.read_text(encoding="utf-8")

        assert "initTradingTab" in content
        assert "initNetworkTab" in content
        assert "initSystemInspectorTab" in content
        assert "trading_tab" in content
        assert "network_tab" in content
        assert "system_inspector_tab" in content

    def test_apps_tab_static_files_exist(self):
        """Static index.html and main.js files must exist for each app tab."""
        webinterface_dir = __root__ / "src" / "api" / "webinterface"

        for tab in ["trading_tab", "network_tab", "system_inspector_tab"]:
            tab_dir = webinterface_dir / tab
            assert tab_dir.exists(), f"Tab directory {tab} must exist"
            assert (tab_dir / "index.html").exists(), f"{tab}/index.html must exist"
            assert (tab_dir / "main.js").exists(), f"{tab}/main.js must exist"
            assert (tab_dir / "README.md").exists(), f"{tab}/README.md must exist"

    def test_locales_contain_apps_tab_keys(self):
        """Localization JSON files should contain translations for apps tabs."""
        locales_dir = __root__ / "src" / "api" / "webinterface" / "locales"

        for lang_file in ["ru.json", "en.json", "he.json"]:
            path = locales_dir / lang_file
            assert path.exists(), f"{lang_file} must exist"
            data = json.loads(path.read_text(encoding="utf-8"))
            tabs = data.get("tabs", {})

            assert "groupApps" in tabs, f"groupApps missing in {lang_file}"
            assert "trading" in tabs, f"trading missing in {lang_file}"
            assert "network" in tabs, f"network missing in {lang_file}"
            assert "systemInspector" in tabs, f"systemInspector missing in {lang_file}"

