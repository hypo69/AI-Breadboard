# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Tests for Network Terminal FastAPI Router
# =============================================================================
# Description:
#   Unit tests for FastAPI endpoints in apps/windows/network/router.py.
#   Tests status, interfaces, connections, telemetry, packets, stats, security,
#   start/stop capture, and PCAP analysis endpoints.
#
# File: test_router_network_terminal.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Unit tests for Network Terminal FastAPI router."""

import unittest
from io import BytesIO
from unittest.mock import patch

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from apps.windows.network.router import init_router


class TestNetworkTerminalRouter(unittest.TestCase):
    """Test suite for Network Terminal router endpoints."""

    def setUp(self):
        """Set up FastAPI test client."""
        self.app = FastAPI()
        self.app.include_router(init_router())
        self.client = TestClient(self.app)

    def test_get_status(self):
        """Test /api/network/status endpoint."""
        response = self.client.get("/api/network/status")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("interface", data)
        self.assertIn("total_packets", data)
        self.assertIn("total_bytes", data)
        self.assertIn("total_adapters", data)
        self.assertIn("active_connections_count", data)
        self.assertIn("listening_ports_count", data)
        self.assertTrue(data.get("available"))

    def test_get_interfaces(self):
        """Test /api/network/interfaces endpoint."""
        response = self.client.get("/api/network/interfaces")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        if len(data) > 0:
            first = data[0]
            self.assertIn("name", first)
            self.assertIn("status", first)
            self.assertIn("ipv4", first)
            self.assertIn("mac", first)

    def test_get_connections(self):
        """Test /api/network/connections endpoint."""
        response = self.client.get("/api/network/connections?limit=10")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("connections", data)
        self.assertIn("listening_ports", data)
        self.assertIsInstance(data["connections"], list)
        self.assertIsInstance(data["listening_ports"], list)

    def test_get_telemetry(self):
        """Test /api/network/telemetry endpoint."""
        response = self.client.get("/api/network/telemetry")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("sensors", data)
        self.assertIsInstance(data["sensors"], list)

    def test_get_packets(self):
        """Test /api/network/packets endpoint."""
        response = self.client.get("/api/network/packets?limit=10")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("packets", data)
        self.assertIsInstance(data["packets"], list)

    def test_get_stats(self):
        """Test /api/network/stats endpoint."""
        response = self.client.get("/api/network/stats")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("total_packets", data)
        self.assertIn("avg_pps", data)

    def test_get_security(self):
        """Test /api/network/security endpoint."""
        response = self.client.get("/api/network/security")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("heuristics", data)

    def test_start_and_stop_capture(self):
        """Test /api/network/start-capture and stop-capture endpoints."""
        with patch("apps.windows.network.router.require_admin_user", side_effect=HTTPException(status_code=403, detail="Admin required")):
            response = self.client.post(
                "/api/network/start-capture?interface=1&display_filter=tcp"
            )
            self.assertEqual(response.status_code, 403)

        with patch("apps.windows.network.router.require_admin_user", return_value=None):
            # Start capture
            response = self.client.post(
                "/api/network/start-capture?interface=1&display_filter=tcp"
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json().get("success"))

            # Stop capture
            stop_resp = self.client.post("/api/network/stop-capture")
            self.assertEqual(stop_resp.status_code, 200)
            self.assertTrue(stop_resp.json().get("success"))

    def test_analyze_pcap(self):
        """Test /api/network/analyze/pcap endpoint."""
        dummy_pcap = BytesIO(b"\xd4\xc3\xb2\xa1\x02\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\x00\x00\x01\x00\x00\x00")
        files = {"file": ("test.pcap", dummy_pcap, "application/vnd.tcpdump.pcap")}
        response = self.client.post("/api/network/analyze/pcap", files=files)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("stats", data)
        self.assertIn("heuristics", data)

    def test_speedtest_latest_no_data(self):
        """Test /api/network/speedtest/latest when no test run yet."""
        response = self.client.get("/api/network/speedtest/latest")
        self.assertEqual(response.status_code, 200)

    def test_speedtest_ping(self):
        """Test /api/network/speedtest/ping endpoint."""
        response = self.client.get("/api/network/speedtest/ping")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("meta", data)
        self.assertIn("servers", data)
        self.assertIsInstance(data["servers"], list)

    def test_init_router(self):
        """Test init_router function returns valid router."""
        router = init_router()
        self.assertIsNotNone(router)
        self.assertEqual(router.prefix, "/api/network")


if __name__ == "__main__":
    unittest.main()
