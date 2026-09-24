# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Tests for Windows System Administrator FastAPI Router
# =============================================================================
# Description:
#   Unit tests for FastAPI endpoints in apps/windows_sysadmin/router.py.
#   Tests status, users, events, AD connectivity endpoints.
#
# File: test_router_windows_sysadmin.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Unit tests for Windows System Administrator FastAPI router."""

import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from apps.windows.sysadmin.router import init_router


class TestWindowsSysadminRouter(unittest.TestCase):
    """Test suite for Windows System Administrator router endpoints."""

    def test_get_status(self):
        """Test /api/sysadmin/status endpoint."""
        app = FastAPI()
        app.include_router(init_router())
        test_client = TestClient(app)
        response = test_client.get("/api/sysadmin/status")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("hostname", data)
        self.assertIn("domain", data)
        self.assertIn("ad_connected", data)
        self.assertIn("user_count", data)

    def test_get_users(self):
        """Test /api/sysadmin/users endpoint."""
        app = FastAPI()
        app.include_router(init_router())
        test_client = TestClient(app)
        response = test_client.get("/api/sysadmin/users")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("users", data)
        self.assertIsInstance(data["users"], list)

    def test_get_events(self):
        """Test /api/sysadmin/events endpoint."""
        app = FastAPI()
        app.include_router(init_router())
        test_client = TestClient(app)
        response = test_client.get("/api/sysadmin/events")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("events", data)
        self.assertIsInstance(data["events"], list)

    def test_get_user_not_found(self):
        """Test /api/sysadmin/users/{username} for non-existent user."""
        app = FastAPI()
        app.include_router(init_router())
        test_client = TestClient(app)
        response = test_client.get("/api/sysadmin/users/nonexistent")

        self.assertEqual(response.status_code, 404)

    def test_get_ad_status(self):
        """Test /api/sysadmin/ad/status endpoint."""
        app = FastAPI()
        app.include_router(init_router())
        test_client = TestClient(app)
        response = test_client.get("/api/sysadmin/ad/status")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("hostname", data)
        self.assertIn("domain", data)

    def test_init_router(self):
        """Test init_router function returns valid router."""
        router = init_router()
        self.assertIsNotNone(router)
        self.assertEqual(router.prefix, "/api/sysadmin")


if __name__ == "__main__":
    unittest.main()
