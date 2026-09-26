# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Tests for App Server Mode (shared/dedicated)
# =============================================================================
# Description:
#   Unit tests verifying that all microservices under /apps declare the
#   {server: {mode: "dedicated"|"shared"}} option in config.json, that
#   _get_server_mode correctly parses server modes, and that app routers
#   can be initialized for shared server routing.
#
# File: test_apps_server_mode.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Tests for app server configuration and shared/dedicated mode resolution."""

import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from fastapi import FastAPI

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APPS_DIR = PROJECT_ROOT / "apps"

ALL_APPS = [
    ("windows/sysadmin", 8100),
    ("windows/network", 8101),
    ("system_inspector", 8102),
    ("trading_terminal", 8103),
    ("cloudflared_monitor", 8104),
    ("user_assistant", 8105),
    ("gcloud_monitor", 8106),
    ("website_monitor", 8107),
    ("windows", 8108),
    ("windows/system_control_center", 8109),
]


class TestAppConfigs:
    """Test app config.json declarations and server mode options."""

    @pytest.mark.parametrize("app_name, expected_port", ALL_APPS)
    def test_app_config_exists_and_has_server_mode(self, app_name: str, expected_port: int) -> None:
        """Each app must have config.json declaring server with port and dedicated boolean or mode."""
        config_path = APPS_DIR / app_name / "config.json"
        assert config_path.is_file(), f"config.json missing for app {app_name}"

        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "server" in data, f"Key 'server' missing in {config_path}"
        server = data["server"]

        if isinstance(server, dict):
            if "dedicated" in server:
                assert isinstance(server["dedicated"], bool), f"'dedicated' must be boolean in {app_name}"
            elif "mode" in server or "type" in server:
                mode = server.get("mode") or server.get("type")
                assert mode in ("dedicated", "shared"), f"Invalid server mode '{mode}' in {app_name}"
            assert server.get("port") == expected_port, f"Expected port {expected_port} for {app_name}, got {server.get('port')}"
        elif isinstance(server, str):
            assert server in ("dedicated", "shared"), f"Invalid server string '{server}' in {app_name}"


class TestServerModeHelper:
    """Test _get_server_mode parser across all apps."""

    def test_windows_sysadmin_get_server_mode(self) -> None:
        from apps.windows.sysadmin.__main__ import _get_server_mode

        assert _get_server_mode(SimpleNamespace(server=SimpleNamespace(dedicated=True))) == "dedicated"
        assert _get_server_mode(SimpleNamespace(server=SimpleNamespace(dedicated=False))) == "shared"
        assert _get_server_mode(SimpleNamespace(server={"dedicated": True})) == "dedicated"
        assert _get_server_mode(SimpleNamespace(server={"dedicated": False})) == "shared"
        assert _get_server_mode(SimpleNamespace(server=SimpleNamespace(mode="dedicated"))) == "dedicated"
        assert _get_server_mode(SimpleNamespace(server=SimpleNamespace(mode="shared"))) == "shared"
        assert _get_server_mode(SimpleNamespace(server="dedicated")) == "dedicated"
        assert _get_server_mode(SimpleNamespace(server="shared")) == "shared"
        assert _get_server_mode(SimpleNamespace()) == "dedicated"

    def test_network_terminal_get_server_mode(self) -> None:
        from apps.windows.network.__main__ import _get_server_mode

        assert _get_server_mode(SimpleNamespace(server=SimpleNamespace(dedicated=True))) == "dedicated"
        assert _get_server_mode(SimpleNamespace(server=SimpleNamespace(dedicated=False))) == "shared"
        assert _get_server_mode(SimpleNamespace(server={"dedicated": True})) == "dedicated"
        assert _get_server_mode(SimpleNamespace(server={"dedicated": False})) == "shared"
        assert _get_server_mode(SimpleNamespace(server=SimpleNamespace(mode="dedicated"))) == "dedicated"
        assert _get_server_mode(SimpleNamespace(server=SimpleNamespace(mode="shared"))) == "shared"

    def test_system_inspector_get_server_mode(self) -> None:
        from apps.system_inspector.__main__ import _get_server_mode

        assert _get_server_mode(SimpleNamespace(server=SimpleNamespace(dedicated=True))) == "dedicated"
        assert _get_server_mode(SimpleNamespace(server=SimpleNamespace(dedicated=False))) == "shared"
        assert _get_server_mode(SimpleNamespace(server={"dedicated": True})) == "dedicated"
        assert _get_server_mode(SimpleNamespace(server={"dedicated": False})) == "shared"
        assert _get_server_mode(SimpleNamespace(server=SimpleNamespace(mode="dedicated"))) == "dedicated"
        assert _get_server_mode(SimpleNamespace(server=SimpleNamespace(mode="shared"))) == "shared"

    def test_trading_terminal_get_server_mode(self) -> None:
        from apps.trading_terminal.__main__ import _get_server_mode

        assert _get_server_mode(SimpleNamespace(server=SimpleNamespace(dedicated=True))) == "dedicated"
        assert _get_server_mode(SimpleNamespace(server=SimpleNamespace(dedicated=False))) == "shared"
        assert _get_server_mode(SimpleNamespace(server={"dedicated": True})) == "dedicated"
        assert _get_server_mode(SimpleNamespace(server={"dedicated": False})) == "shared"
        assert _get_server_mode(SimpleNamespace(server=SimpleNamespace(mode="dedicated"))) == "dedicated"
        assert _get_server_mode(SimpleNamespace(server=SimpleNamespace(mode="shared"))) == "shared"

    def test_cloudflared_monitor_get_server_mode(self) -> None:
        from apps.cloudflared_monitor.__main__ import _get_server_mode

        assert _get_server_mode(SimpleNamespace(server=SimpleNamespace(dedicated=True))) == "dedicated"
        assert _get_server_mode(SimpleNamespace(server=SimpleNamespace(dedicated=False))) == "shared"
        assert _get_server_mode(SimpleNamespace(server={"dedicated": True})) == "dedicated"
        assert _get_server_mode(SimpleNamespace(server={"dedicated": False})) == "shared"
        assert _get_server_mode(SimpleNamespace(server=SimpleNamespace(mode="dedicated"))) == "dedicated"
        assert _get_server_mode(SimpleNamespace(server=SimpleNamespace(mode="shared"))) == "shared"


class TestAppRoutersInSharedServer:
    """Test that all app routers can be initialized in a FastAPI app."""

    def test_include_all_app_routers(self) -> None:
        """Verify all app routers can be added to a FastAPI instance for shared mode."""
        app = FastAPI()

        from apps.trading_terminal import init_router as init_trading
        from apps.cloudflared_monitor.router import init_router as init_cloudflared
        from apps.windows.sysadmin.router import init_router as init_sysadmin
        from apps.windows.network.router import init_router as init_network
        from apps.system_inspector.router import init_router as init_inspector

        routers = [
            init_trading(),
            init_cloudflared(),
            init_sysadmin(),
            init_network(),
            init_inspector(),
        ]
        for r in routers:
            app.include_router(r)

        routes = [route.path for r in routers for route in r.routes]
        assert any(p.startswith("/api/v1/trading") or p.startswith("/api/trading") for p in routes)
        assert any(p.startswith("/api/cloudflared") for p in routes)
        assert any(p.startswith("/api/sysadmin") for p in routes)
        assert any(p.startswith("/api/network") for p in routes)
        assert any(p.startswith("/api/system") for p in routes)
