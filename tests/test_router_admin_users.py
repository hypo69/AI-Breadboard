# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Testing user management endpoints in admin panel
# =============================================================================
# Description:
#   Module contains tests for REST API endpoints /api/admin/users/*
#
# File: test_router_admin_users.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
from fastapi.testclient import TestClient
from main import app
from src.user_manager import user_manager

client = TestClient(app)

class TestAdminUsersAPI:
    """Testing user management endpoints in admin panel."""

    @pytest.fixture(autouse=True)
    def setup_cleanup(self):
        """Create test users and cleanup after tests."""
        self.test_emails = [
            "test_user_admin_1@test.com",
            "test_user_admin_2@test.com",
            "searchable_unique@test.com"
        ]
        # Cleanup before test
        for email in self.test_emails:
            u = user_manager.get_user_by_email(email)
            if u:
                user_manager.delete_user(u["id"])

        yield

        # Cleanup after test
        for email in self.test_emails:
            u = user_manager.get_user_by_email(email)
            if u:
                user_manager.delete_user(u["id"])

    def test_list_users_and_stats(self):
        """Check retrieval of users list and statistics."""
        response = client.get("/api/admin/users")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data["users"], list)
        assert "stats" in data

        # Verify statistics contain expected keys
        assert "total" in data["stats"]
        assert "active" in data["stats"]
        assert "suspended" in data["stats"]
        assert "telegram" in data["stats"]

        # Passwords should not be in open form or hashed
        for u in data["users"]:
            assert "password_hash" not in u

    def test_create_user(self):
        """Check creation of new user via API."""
        payload = {
            "email": "test_user_admin_1@test.com",
            "name": "Test User",
            "password": "SecurePassword123!",
            "role": "user",
        }
        response = client.post("/api/admin/users", json=payload)
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

        data = response.json()
        created = data["user"]
        assert created["email"] == "test_user_admin_1@test.com"
        assert created["name"] == "Test User"

    def test_update_user(self):
        """Check user update via API."""
        # Create user first
        create_payload = {
            "email": "test_user_admin_2@test.com",
            "name": "Original Name",
            "password": "SecurePassword123!",
            "role": "user",
        }
        create_resp = client.post("/api/admin/users", json=create_payload)
        user_id = create_resp.json()["user"]["id"]

        # Update user
        update_payload = {
            "name": "Updated Name",
            "role": "moderator",
        }
        response = client.put(f"/api/admin/users/{user_id}", json=update_payload)
        assert response.status_code == 200

        data = response.json()
        updated = data["user"]
        assert updated["name"] == "Updated Name"
        assert updated["role"] == "moderator"

    def test_search_users(self):
        """Check user search functionality."""
        # Create test user
        create_payload = {
            "email": "searchable_unique@test.com",
            "name": "Searchable User",
            "password": "SecurePassword123!",
            "role": "user",
        }
        client.post("/api/admin/users", json=create_payload)

        # Search by email
        response = client.get("/api/admin/users?q=searchable_unique")
        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) > 0
        assert any(u["email"] == "searchable_unique@test.com" for u in data["users"])
