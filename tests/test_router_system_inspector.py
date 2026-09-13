# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Tests for System Inspector FastAPI Router
# =============================================================================
# Description:
#   Unit tests for FastAPI endpoints in apps/system_inspector/router.py.
#   Tests status, processes, hardware, diagnostic endpoints.
#
# File: test_router_system_inspector.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Unit tests for System Inspector FastAPI router."""

import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from apps.system_inspector.router import init_router


class TestSystemInspectorRouter(unittest.TestCase):
    """Test suite for System Inspector router endpoints."""

    def test_get_status(self):
        """Test /api/system/status endpoint."""
        app = FastAPI()
        app.include_router(init_router())
        test_client = TestClient(app)
        response = test_client.get("/api/system/status")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("hostname", data)
        self.assertIn("process_count", data)

    def test_get_processes(self):
        """Test /api/system/processes endpoint."""
        app = FastAPI()
        app.include_router(init_router())
        test_client = TestClient(app)
        response = test_client.get("/api/system/processes?limit=10&sort_by=cpu")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("processes", data)
        self.assertIsInstance(data["processes"], list)

    def test_get_hardware(self):
        """Test /api/system/hardware endpoint."""
        app = FastAPI()
        app.include_router(init_router())
        test_client = TestClient(app)
        response = test_client.get("/api/system/hardware")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("hardware", data)
        self.assertIn("sensors", data)

    def test_get_diagnostic(self):
        """Test /api/system/diagnostic endpoint."""
        app = FastAPI()
        app.include_router(init_router())
        test_client = TestClient(app)
        response = test_client.get("/api/system/diagnostic?process_limit=15")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("health_score", data)
        self.assertIn("anomalies", data)

    def test_get_hardware_tree(self):
        """Test /api/system/hardware/tree endpoint."""
        app = FastAPI()
        app.include_router(init_router())
        test_client = TestClient(app)
        response = test_client.get("/api/system/hardware/tree")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("tree", data)

    def test_get_hardware_sensors(self):
        """Test /api/system/hardware/sensors endpoint."""
        app = FastAPI()
        app.include_router(init_router())
        test_client = TestClient(app)
        response = test_client.get("/api/system/hardware/sensors")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("sensors", data)

    def test_trigger_diagnostic(self):
        """Test /api/system/trigger-diagnostic endpoint (admin required)."""
        app = FastAPI()
        app.include_router(init_router())
        test_client = TestClient(app)
        response = test_client.post("/api/system/trigger-diagnostic")

        # Should return 401 or 403 since admin auth is required
        self.assertIn(response.status_code, [401, 403])

    def test_init_router(self):
        """Test init_router function returns valid router."""
        router = init_router()
        self.assertIsNotNone(router)
        self.assertEqual(router.prefix, "/api/system")


if __name__ == "__main__":
    unittest.main()
