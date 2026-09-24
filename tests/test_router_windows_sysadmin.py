# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Tests for Windows System Administrator FastAPI Router
# =============================================================================
# Description:
#   Unit tests for FastAPI endpoints in apps/windows_sysadmin/router.py.
#   Tests status, users, accounts, hidden users detection, telemetry and metrics.
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

    def setUp(self):
        """Setup test FastAPI app and client."""
        self.app = FastAPI()
        self.app.include_router(init_router())
        self.client = TestClient(self.app)

    def test_get_status(self):
        """Test /api/sysadmin/status endpoint with account breakdown."""
        response = self.client.get("/api/sysadmin/status")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("hostname", data)
        self.assertIn("domain", data)
        self.assertIn("ad_connected", data)
        self.assertIn("user_count", data)
        self.assertIn("total_accounts", data)
        self.assertIn("active_users", data)
        self.assertIn("hidden_users", data)

    def test_get_users(self):
        """Test /api/sysadmin/users endpoint."""
        response = self.client.get("/api/sysadmin/users")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("users", data)
        self.assertIsInstance(data["users"], list)

    def test_get_accounts_all(self):
        """Test /api/sysadmin/accounts endpoint with all filters."""
        response = self.client.get("/api/sysadmin/accounts")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("accounts", data)
        self.assertIn("total", data)
        self.assertIn("filtered_count", data)
        self.assertIsInstance(data["accounts"], list)
        self.assertGreater(len(data["accounts"]), 0)

        # Проверяем структуру первой учетной записи
        first_acc = data["accounts"][0]
        self.assertIn("name", first_acc)
        self.assertIn("is_hidden", first_acc)
        self.assertIn("is_admin", first_acc)
        self.assertIn("groups", first_acc)

    def test_get_accounts_filters(self):
        """Test /api/sysadmin/accounts with different filter_type parameters."""
        for flt in ["active", "hidden", "admins", "disabled"]:
            response = self.client.get(f"/api/sysadmin/accounts?filter_type={flt}")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["filter"], flt)
            self.assertIsInstance(data["accounts"], list)

    def test_get_account_details(self):
        """Test /api/sysadmin/accounts/{username} for existing and non-existing accounts."""
        # Получаем список, берем первое имя
        acc_resp = self.client.get("/api/sysadmin/accounts")
        accounts = acc_resp.json().get("accounts", [])
        self.assertTrue(len(accounts) > 0)
        
        target_name = accounts[0]["name"]
        detail_resp = self.client.get(f"/api/sysadmin/accounts/{target_name}")
        self.assertEqual(detail_resp.status_code, 200)
        self.assertEqual(detail_resp.json()["name"].lower(), target_name.lower())

        # Несуществующий пользователь
        not_found_resp = self.client.get("/api/sysadmin/accounts/non_existent_user_xyz")
        self.assertEqual(not_found_resp.status_code, 404)

    def test_get_account_metrics(self):
        """Test /api/sysadmin/accounts/{username}/metrics endpoint."""
        acc_resp = self.client.get("/api/sysadmin/accounts")
        accounts = acc_resp.json().get("accounts", [])
        target_name = accounts[0]["name"]

        metrics_resp = self.client.get(f"/api/sysadmin/accounts/{target_name}/metrics")
        self.assertEqual(metrics_resp.status_code, 200)
        metrics = metrics_resp.json()
        self.assertIn("username", metrics)
        self.assertIn("total_processes", metrics)
        self.assertIn("total_memory_rss_mb", metrics)
        self.assertIn("top_processes", metrics)

    def test_get_events(self):
        """Test /api/sysadmin/events endpoint."""
        response = self.client.get("/api/sysadmin/events")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("events", data)
        self.assertIsInstance(data["events"], list)

    def test_get_user_not_found(self):
        """Test /api/sysadmin/users/{username} for non-existent user."""
        response = self.client.get("/api/sysadmin/users/nonexistent")
        self.assertEqual(response.status_code, 404)

    def test_get_ad_status(self):
        """Test /api/sysadmin/ad/status endpoint."""
        response = self.client.get("/api/sysadmin/ad/status")

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
