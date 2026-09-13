# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Tests for Cloudflared Monitor FastAPI Router
# =============================================================================
# Description:
#   Unit tests for FastAPI endpoints in apps/cloudflared_monitor/router.py.
#   Tests status, logs, metrics, diagnostic, test-endpoint, and lifecycle control.
#
# File: test_router_cloudflared_monitor.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Unit tests for Cloudflared Monitor FastAPI router."""

import unittest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from apps.cloudflared_monitor.router import get_state, init_router


class TestCloudflaredMonitorRouter(unittest.TestCase):
    """Test suite for Cloudflared Monitor router endpoints."""

    def setUp(self):
        """Set up FastAPI test client."""
        self.app = FastAPI()
        self.app.include_router(init_router())
        self.client = TestClient(self.app)

    def test_init_router(self):
        """Test init_router returns configured APIRouter."""
        router = init_router()
        self.assertIsNotNone(router)
        self.assertEqual(router.prefix, "/api/cloudflared")

    def test_get_status(self):
        """Test GET /api/cloudflared/status endpoint."""
        response = self.client.get("/api/cloudflared/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("is_running", data)
        self.assertIn("has_token", data)
        self.assertIn("public_url", data)
        self.assertIn("health_score", data)

    def test_get_logs(self):
        """Test GET /api/cloudflared/logs endpoint."""
        response = self.client.get("/api/cloudflared/logs?limit=10")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("logs", data)
        self.assertIn("count", data)
        self.assertIsInstance(data["logs"], list)

    def test_get_metrics(self):
        """Test GET /api/cloudflared/metrics endpoint."""
        response = self.client.get("/api/cloudflared/metrics")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("process", data)
        self.assertIn("network", data)
        self.assertIn("log_stats", data)

    def test_get_diagnostic(self):
        """Test GET /api/cloudflared/diagnostic endpoint."""
        response = self.client.get("/api/cloudflared/diagnostic")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("health_score", data)
        self.assertIn("status", data)
        self.assertIn("anomalies", data)
        self.assertIn("recommendations", data)

    def test_test_endpoint(self):
        """Test POST /api/cloudflared/test-endpoint."""
        response = self.client.post("/api/cloudflared/test-endpoint")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("url", data)
        self.assertIn("is_reachable", data)

    def test_lifecycle_admin_auth_forbidden(self):
        """Test POST /start, /stop, /restart when non-admin."""
        with patch("apps.cloudflared_monitor.router.require_admin_user", side_effect=HTTPException(status_code=403, detail="Admin required")):
            res_start = self.client.post("/api/cloudflared/start")
            self.assertEqual(res_start.status_code, 403)

            res_stop = self.client.post("/api/cloudflared/stop")
            self.assertEqual(res_stop.status_code, 403)

            res_restart = self.client.post("/api/cloudflared/restart")
            self.assertEqual(res_restart.status_code, 403)

    def test_lifecycle_authorized_success(self):
        """Test POST /start, /stop, /restart when authorized as admin."""
        state = get_state()
        with patch("apps.cloudflared_monitor.router.require_admin_user", return_value=None):
            with patch.object(state, "start_tunnel", return_value=(True, "Started")):
                res_start = self.client.post("/api/cloudflared/start")
                self.assertEqual(res_start.status_code, 200)
                self.assertTrue(res_start.json()["success"])

            with patch.object(state, "stop_tunnel", return_value=(True, "Stopped")):
                res_stop = self.client.post("/api/cloudflared/stop")
                self.assertEqual(res_stop.status_code, 200)
                self.assertTrue(res_stop.json()["success"])

            with patch.object(state, "restart_tunnel", return_value=(True, "Restarted")):
                res_restart = self.client.post("/api/cloudflared/restart")
                self.assertEqual(res_restart.status_code, 200)
                self.assertTrue(res_restart.json()["success"])


if __name__ == "__main__":
    unittest.main()
