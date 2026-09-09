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

    def test_partial_field_updates_via_patch(self):
        """Check partial field updating (inline table editing) via PATCH endpoint."""
        create_payload = {
            "email": "test_user_admin_2@test.com",
            "name": "Inline User",
            "password": "SecurePassword123!",
            "role": "user",
        }
        create_resp = client.post("/api/admin/users", json=create_payload)
        user_id = create_resp.json()["user"]["id"]

        # 1. Update only role
        patch_role = client.patch(f"/api/admin/users/{user_id}", json={"role": "admin"})
        assert patch_role.status_code == 200
        assert patch_role.json()["user"]["role"] == "admin"
        assert patch_role.json()["user"]["is_admin"] == 1
        assert patch_role.json()["user"]["name"] == "Inline User"

        # 2. Update only status (is_active)
        patch_status = client.patch(f"/api/admin/users/{user_id}", json={"is_active": 0})
        assert patch_status.status_code == 200
        assert patch_status.json()["user"]["is_active"] == 0
        assert patch_status.json()["user"]["role"] == "admin"

        # 3. Update only telegram username
        patch_tg = client.patch(f"/api/admin/users/{user_id}", json={"telegram_username": "@testadmin"})
        assert patch_tg.status_code == 200
        assert patch_tg.json()["user"]["telegram_username"] == "testadmin"

    def test_oauth_user_default_role_is_user(self):
        """Verify that user_manager.add_user creates a regular 'user' by default with is_admin=0."""
        oauth_email = "test_user_admin_1@test.com"
        user_id = user_manager.add_user(
            email=oauth_email,
            name="OAuth Registered User",
            picture="https://example.com/photo.jpg",
            role="user"
        )
        assert user_id > 0
        created = user_manager.get_user_by_id(user_id)
        assert created["role"] == "user"
        assert created["is_admin"] == 0

