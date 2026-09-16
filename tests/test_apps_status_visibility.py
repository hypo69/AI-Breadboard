# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit Tests for Apps Status and UI Visibility
# =============================================================================
# Description:
#   Verifies that /api/apps/status and /api/admin/apps/status return accurate
#   application status based on config.json / config_tc.json, and tests
#   dynamic visibility handling for apps interface and admin navigation.
#
# File: test_apps_status_visibility.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Unit tests for /apps status and visibility filtering based on configuration."""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from header import __root__
from main import app
from src.api.router_admin import get_apps_status, APPS_REGISTRY

client = TestClient(app)


class TestAppsStatusVisibility:
    """Test suite verifying apps configuration parsing and UI visibility controls."""

    def test_get_apps_status_returns_all_registered_apps(self):
        """get_apps_status should return all 10 registered apps with their keys and tabs."""
        status = get_apps_status()
        assert status["status"] == "ok"
        assert "apps" in status
        assert "config_file" in status

        apps = status["apps"]
        assert len(apps) == len(APPS_REGISTRY)

        # Check key apps exist
        assert "chat" in apps
        assert "trading_terminal" in apps
        assert "network_terminal" in apps
        assert "system_inspector" in apps
        assert "windows_sysadmin" in apps
        assert "cloudflared_monitor" in apps
        assert "gcloud_monitor" in apps
        assert "website_monitor" in apps
        assert "user_assistant" in apps
        assert "system_control_center" in apps
        assert "system_log_viewer" in apps

        for app_id, app_info in apps.items():
            assert "enabled" in app_info
            assert isinstance(app_info["enabled"], bool)
            assert "tab" in app_info
            assert app_info["tab"].startswith("tab-")
            assert "key" in app_info
            assert app_info["key"].startswith("enable_")

    def test_apps_status_endpoint_public_and_admin(self):
        """Both /api/apps/status and /api/admin/apps/status should be accessible and return valid json."""
        res_public = client.get("/api/apps/status")
        assert res_public.status_code == 200
        data_public = res_public.json()
        assert data_public["status"] == "ok"
        assert "apps" in data_public

        res_admin = client.get("/api/admin/apps/status")
        assert res_admin.status_code == 200
        data_admin = res_admin.json()
        assert data_admin["status"] == "ok"
        assert "apps" in data_admin
        assert data_public["apps"] == data_admin["apps"]

    def test_config_tc_behavior(self, monkeypatch, tmp_path):
        """Simulate running with config_tc.json where cloudflared is disabled and enable_all is false."""
        tc_cfg = {
            "apps": {
                "enable_all": False,
                "enable_windows_admin": True,
                "enable_system_inspector": True,
                "enable_system_control_center": True,
                "enable_system_log_viewer": True,
                "enable_network_terminal": True,
                "enable_trading_terminal": True,
                "enable_user_assistant": True,
                "enable_gcloud_monitor": True,
                "enable_website_monitor": True,
                "enable_cloudflared_monitor": False,
            }
        }
        cfg_file = tmp_path / "config_tc_test.json"
        cfg_file.write_text(json.dumps(tc_cfg), encoding="utf-8")

        monkeypatch.setenv("CONFIG_FILE", str(cfg_file))
        status = get_apps_status()

        assert status["config_file"] == "config_tc_test.json"
        assert status["enable_all"] is False
        assert status["apps"]["cloudflared_monitor"]["enabled"] is False
        assert status["apps"]["trading_terminal"]["enabled"] is True
        assert status["apps"]["windows_sysadmin"]["enabled"] is True

    def test_all_disabled_behavior(self, monkeypatch, tmp_path):
        """When enable_all is false and no specific app enabled, all apps must be disabled."""
        disabled_cfg = {
            "apps": {
                "enable_all": False
            }
        }
        cfg_file = tmp_path / "disabled_config.json"
        cfg_file.write_text(json.dumps(disabled_cfg), encoding="utf-8")

        monkeypatch.setenv("CONFIG_FILE", str(cfg_file))
        status = get_apps_status()

        assert status["enable_all"] is False
        for app_id, app_info in status["apps"].items():
            assert app_info["enabled"] is False

    def test_apps_hub_js_contains_filtering_logic(self):
        """apps/main.js must contain status fetching, visibility toggling, and fallback handling."""
        hub_js = __root__ / "src" / "api" / "webgui" / "apps" / "main.js"
        if not hub_js.exists():
            hub_js = __root__ / "src" / "api" / "webinterface" / "apps" / "main.js"
        assert hub_js.exists()
        content = hub_js.read_text(encoding="utf-8")

        assert "fetchAppsStatus" in content
        assert "/api/apps/status" in content
        assert "appsMap" in content
        assert "d-none" in content
        assert "tab-network" in content
        assert "tab-windows-admin" in content

    def test_admin_main_js_contains_apps_sync_logic(self):
        """admin/main.js must contain syncAppsTabsVisibility logic for hiding disabled dropdown items."""
        admin_js = __root__ / "src" / "api" / "webgui" / "admin" / "main.js"
        if not admin_js.exists():
            admin_js = __root__ / "src" / "api" / "webinterface" / "admin" / "main.js"
        assert admin_js.exists()
        content = admin_js.read_text(encoding="utf-8")

        assert "syncAppsTabsVisibility" in content
        assert "/api/apps/status" in content
        assert "appsTabsDropdown" in content

    def test_config_tc_array_format_behavior(self, monkeypatch, tmp_path):
        """When apps is a list of app names (config_tc.json format), only those apps must be enabled."""
        tc_array_cfg = {
            "apps": [
                "windows_admin",
                "system_inspector",
                "system_control_center",
                "system_log_viewer",
                "network_terminal"
            ]
        }
        cfg_file = tmp_path / "config_tc_array.json"
        cfg_file.write_text(json.dumps(tc_array_cfg), encoding="utf-8")

        monkeypatch.setenv("CONFIG_FILE", str(cfg_file))
        status = get_apps_status()

        assert status["config_file"] == "config_tc_array.json"
        assert status["enable_all"] is False

        # Verify exactly the 5 specified apps are enabled
        assert status["apps"]["windows_sysadmin"]["enabled"] is True
        assert status["apps"]["system_inspector"]["enabled"] is True
        assert status["apps"]["system_control_center"]["enabled"] is True
        assert status["apps"]["system_log_viewer"]["enabled"] is True
        assert status["apps"]["network_terminal"]["enabled"] is True

        # Verify the other apps are disabled
        assert status["apps"]["chat"]["enabled"] is False
        assert status["apps"]["trading_terminal"]["enabled"] is False
        assert status["apps"]["user_assistant"]["enabled"] is False
        assert status["apps"]["gcloud_monitor"]["enabled"] is False
        assert status["apps"]["website_monitor"]["enabled"] is False
        assert status["apps"]["cloudflared_monitor"]["enabled"] is False

    def test_enabled_and_disabled_lists_format(self, monkeypatch, tmp_path):
        """When apps dict defines enabled and disabled lists, prioritize disabled over enabled."""
        new_format_cfg = {
            "apps": {
                "enabled": [
                    "enable_windows_admin",
                    "enable_system_inspector",
                    "enable_trading_terminal",
                    "enable_cloudflared_monitor",
                ],
                "disabled": [
                    "enable_cloudflared_monitor",
                ],
            }
        }
        cfg_file = tmp_path / "config_enabled_disabled.json"
        cfg_file.write_text(json.dumps(new_format_cfg), encoding="utf-8")

        monkeypatch.setenv("CONFIG_FILE", str(cfg_file))
        status = get_apps_status()

        assert status["config_file"] == "config_enabled_disabled.json"
        assert status["enable_all"] is False

        # windows_admin, system_inspector, trading_terminal must be enabled
        assert status["apps"]["windows_sysadmin"]["enabled"] is True
        assert status["apps"]["system_inspector"]["enabled"] is True
        assert status["apps"]["trading_terminal"]["enabled"] is True

        # cloudflared_monitor is in disabled -> must be False even if listed in enabled
        assert status["apps"]["cloudflared_monitor"]["enabled"] is False

        # network_terminal is not in enabled -> must be False
        assert status["apps"]["network_terminal"]["enabled"] is False

    def test_disabled_list_only_format(self, monkeypatch, tmp_path):
        """When only disabled list is provided without enabled list, other apps default to enabled."""
        disabled_only_cfg = {
            "apps": {
                "disabled": [
                    "trading_terminal",
                    "gcloud_monitor",
                ]
            }
        }
        cfg_file = tmp_path / "config_disabled_only.json"
        cfg_file.write_text(json.dumps(disabled_only_cfg), encoding="utf-8")

        monkeypatch.setenv("CONFIG_FILE", str(cfg_file))
        status = get_apps_status()

        assert status["config_file"] == "config_disabled_only.json"
        assert status["apps"]["trading_terminal"]["enabled"] is False
        assert status["apps"]["gcloud_monitor"]["enabled"] is False
        assert status["apps"]["windows_sysadmin"]["enabled"] is True
        assert status["apps"]["system_inspector"]["enabled"] is True

    def test_config_tc_json_has_chat_enabled(self, monkeypatch):
        """When actual config_tc.json is active, chat and test computer apps should be enabled."""
        tc_path = __root__ / "config_tc.json"
        if tc_path.exists():
            monkeypatch.setenv("CONFIG_FILE", "config_tc.json")
            status = get_apps_status()
            assert status["status"] == "ok"
            assert status["apps"]["chat"]["enabled"] is True
            assert status["apps"]["windows_sysadmin"]["enabled"] is True



