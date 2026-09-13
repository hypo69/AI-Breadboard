# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Tests for Network Terminal FastAPI Router
# =============================================================================
# Description:
#   Unit tests for FastAPI endpoints in apps/network_terminal/router.py.
#   Tests status, packets, stats, security endpoints.
#
# File: test_router_network_terminal.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Unit tests for Network Terminal FastAPI router."""

import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from apps.network_terminal.router import init_router


class TestNetworkTerminalRouter(unittest.TestCase):
    """Test suite for Network Terminal router endpoints."""

    def test_get_status(self):
        """Test /api/network/status endpoint."""
        app = FastAPI()
        app.include_router(init_router())
        test_client = TestClient(app)
        response = test_client.get("/api/network/status")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("interface", data)
        self.assertIn("total_packets", data)
        self.assertIn("total_bytes", data)

    def test_get_packets(self):
        """Test /api/network/packets endpoint."""
        app = FastAPI()
        app.include_router(init_router())
        test_client = TestClient(app)
        response = test_client.get("/api/network/packets?limit=10")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("packets", data)
        self.assertIsInstance(data["packets"], list)

    def test_get_stats(self):
        """Test /api/network/stats endpoint."""
        app = FastAPI()
        app.include_router(init_router())
        test_client = TestClient(app)
        response = test_client.get("/api/network/stats")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("total_packets", data)
        self.assertIn("avg_pps", data)

    def test_get_security(self):
        """Test /api/network/security endpoint."""
        app = FastAPI()
        app.include_router(init_router())
        test_client = TestClient(app)
        response = test_client.get("/api/network/security")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("heuristics", data)

    def test_start_capture(self):
        """Test /api/network/start-capture endpoint (admin required)."""
        app = FastAPI()
        app.include_router(init_router())
        test_client = TestClient(app)
        response = test_client.post(
            "/api/network/start-capture?interface=1&display_filter=tcp"
        )

        # Should return 401 or 403 since admin auth is required
        self.assertIn(response.status_code, [401, 403])

    def test_init_router(self):
        """Test init_router function returns valid router."""
        router = init_router()
        self.assertIsNotNone(router)
        self.assertEqual(router.prefix, "/api/network")


if __name__ == "__main__":
    unittest.main()
