# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Telemetry and Ngrok tunnel system tests
# =============================================================================
# Description:
#   Unit and integration tests for user activity telemetry tracking,
#   tab navigation dwell timing, click event batching, and Ngrok tunnel forwarding.
#
# File: test_telemetry.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.user_manager import user_manager
from apps.windows.telemetry.ngrok_tunnel import NgrokTunnelManager, ngrok_manager
from src.api.router_telemetry import init_router as init_telemetry_router
from src.api.router_auth import create_jwt_token, TokenData


@pytest.fixture
def telemetry_client():
    """Create a FastAPI test client with telemetry router."""
    app = FastAPI()
    app.include_router(init_telemetry_router())
    return TestClient(app)


class TestUserManagerTelemetry:
    """Tests for UserManager telemetry batch storage and statistics."""

    def test_log_telemetry_batch_and_stats(self):
        """Test inserting a batch of telemetry events and reading aggregated stats."""
        # Ensure test user exists
        user_id = 1
        events = [
            {
                "action": "Entered tab tab-chat",
                "event_type": "tab_view",
                "tab_name": "tab-chat",
                "target_element": "tab:tab-chat",
                "duration_ms": 0,
                "details": {"source": "test"}
            },
            {
                "action": "Left tab tab-chat",
                "event_type": "tab_view",
                "tab_name": "tab-chat",
                "target_element": "tab:tab-chat",
                "duration_ms": 15400,
                "details": {"transition_to": "tab-rag"}
            },
            {
                "action": "Click: Send Message",
                "event_type": "click",
                "tab_name": "tab-chat",
                "target_element": "button#send-button",
                "duration_ms": 0,
                "details": {"label": "Send Message"}
            }
        ]

        inserted = user_manager.log_telemetry_batch(
            user_id=user_id,
            events=events,
            ip_address="127.0.0.1",
            user_agent="PyTestClient"
        )
        assert inserted == 3

        stats = user_manager.get_telemetry_stats(days=30, user_id=user_id)
        assert stats["total_events"] >= 3
        assert "tab-chat" in stats["tab_views"]
        assert stats["tab_views"]["tab-chat"]["count"] >= 2
        assert "button#send-button" in stats["top_clicks"]
        assert len(stats["recent_events"]) > 0


class TestTelemetryRouter:
    """Tests for FastAPI telemetry API endpoints."""

    def test_track_events_authenticated_user(self, telemetry_client):
        """Test POST /api/telemetry/events for registered authenticated user."""
        token_data = TokenData(email="admin@localhost", name="Admin", id=1)
        jwt_token = create_jwt_token(token_data)

        payload = {
            "events": [
                {
                    "action": "Entered tab tab-rag",
                    "event_type": "tab_view",
                    "tab_name": "tab-rag",
                    "target_element": "tab:tab-rag",
                    "duration_ms": 0,
                },
                {
                    "action": "Click: Search RAG",
                    "event_type": "click",
                    "tab_name": "tab-rag",
                    "target_element": "button#btn-rag-search",
                    "duration_ms": 0,
                }
            ],
            "session_id": "test_session_123"
        }

        response = telemetry_client.post(
            "/api/telemetry/events",
            json=payload,
            cookies={"auth_token": jwt_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["inserted"] == 2
        assert data["user_id"] == 1

    def test_track_events_unauthenticated_ignored(self, telemetry_client):
        """Test that unauthenticated requests from non-local hosts are ignored."""
        payload = {
            "events": [
                {
                    "action": "Click: Guest Button",
                    "event_type": "click"
                }
            ]
        }

        # Patch _get_authenticated_user_id to simulate unauthenticated guest
        with patch("src.api.router_telemetry._get_authenticated_user_id", return_value=None):
            response = telemetry_client.post(
                "/api/telemetry/events",
                json=payload
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ignored"
            assert data["reason"] == "unauthenticated_user"
            assert data["inserted"] == 0

    def test_get_telemetry_stats(self, telemetry_client):
        """Test GET /api/telemetry/stats endpoint."""
        token_data = TokenData(email="admin@localhost", name="Admin", id=1)
        jwt_token = create_jwt_token(token_data)

        response = telemetry_client.get(
            "/api/telemetry/stats?days=7",
            cookies={"auth_token": jwt_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_events" in data
        assert "tab_views" in data
        assert "top_clicks" in data
        assert "tunnel_status" in data

    def test_get_tunnel_status(self, telemetry_client):
        """Test GET /api/telemetry/tunnel-status endpoint."""
        response = telemetry_client.get("/api/telemetry/tunnel-status")
        assert response.status_code == 200
        data = response.json()
        assert "is_active" in data
        assert "local_port" in data


class TestNgrokTunnelManager:
    """Tests for NgrokTunnelManager."""

    def test_authtoken_property(self):
        """Test authtoken retrieval with fallback."""
        mgr = NgrokTunnelManager(local_port=8000)
        with patch.dict("os.environ", {"NGROK_AUTHTOKEN": "test_token_123"}):
            assert mgr.authtoken == "test_token_123"

        with patch.dict("os.environ", {"NGROK_AUTHTOKEN": "", "NGROCK_AUTOTOKEN": "fallback_token"}):
            assert mgr.authtoken == "fallback_token"

    def test_get_active_tunnel_url_from_api(self):
        """Test querying active URL from mock ngrok inspector API."""
        mgr = NgrokTunnelManager(local_port=8000)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "tunnels": [
                {
                    "name": "command_line",
                    "public_url": "https://abc123xyz.ngrok-free.app",
                    "proto": "https"
                }
            ]
        }

        with patch("requests.get", return_value=mock_resp):
            url = mgr.get_active_tunnel_url()
            assert url == "https://abc123xyz.ngrok-free.app"

    def test_get_status(self):
        """Test get_status report dictionary."""
        mgr = NgrokTunnelManager(local_port=8000)
        with patch.object(mgr, "get_active_tunnel_url", return_value="https://my-tunnel.ngrok-free.app"):
            status = mgr.get_status()
            assert status["is_active"] is True
            assert status["public_url"] == "https://my-tunnel.ngrok-free.app"
            assert status["local_port"] == 8000
