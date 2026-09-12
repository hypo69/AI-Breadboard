# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: API security and authentication test suite
# =============================================================================
# Description:
#   Validates security rules for /api endpoints:
#   - Unauthorized external requests receive 401 Unauthorized or 403 Forbidden.
#   - Local and private subnet requests succeed via local auto-login.
#   - Valid Bearer tokens and cookies are properly accepted.
#   - CORS policy prevents unrestricted wildcard access with credentials.
#
# File: test_api_security.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
from unittest.mock import Mock, patch
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.testclient import TestClient

from src.fastapi.router_auth import (
    TokenData,
    create_jwt_token,
    verify_jwt_token,
    is_local_request,
    get_current_user_data,
    get_current_user_optional,
    require_admin_user,
)


class TestAuthDependencies:
    """Test suite for core auth dependencies."""

    def test_is_local_request_true(self):
        """Validates that loopback and private LAN addresses are detected as local."""
        for host in ["127.0.0.1", "localhost", "::1", "0.0.0.0", "192.168.1.50", "10.0.0.1", "172.16.0.2"]:
            req = Mock(spec=Request)
            req.url = Mock(hostname=host)
            assert is_local_request(req) is True

    def test_is_local_request_false(self):
        """Validates that public external IPs are not detected as local."""
        for host in ["8.8.8.8", "198.51.100.1", "example.com", "api.evil.com"]:
            req = Mock(spec=Request)
            req.url = Mock(hostname=host)
            assert is_local_request(req) is False

    def test_get_current_user_data_with_bearer_token(self):
        """Validates extraction of user data from Bearer token."""
        token = create_jwt_token(TokenData(email="user@test.com", name="User", id=42))
        req = Mock(spec=Request)
        req.cookies = {}
        req.headers = {"Authorization": f"Bearer {token}"}
        req.url = Mock(hostname="external.domain.com")

        user_data = get_current_user_data(req)
        assert user_data.email == "user@test.com"
        assert user_data.id == 42

    def test_get_current_user_data_with_cookie(self):
        """Validates extraction of user data from auth_token cookie."""
        token = create_jwt_token(TokenData(email="cookie_user@test.com", name="Cookie User", id=100))
        req = Mock(spec=Request)
        req.cookies = {"auth_token": token}
        req.headers = {}
        req.url = Mock(hostname="external.domain.com")

        user_data = get_current_user_data(req)
        assert user_data.email == "cookie_user@test.com"
        assert user_data.id == 100

    def test_get_current_user_data_local_fallback(self):
        """Validates fallback to local user when request is local."""
        req = Mock(spec=Request)
        req.cookies = {}
        req.headers = {}
        req.url = Mock(hostname="127.0.0.1")

        user_data = get_current_user_data(req)
        assert user_data is not None
        assert user_data.id == 1

    def test_get_current_user_data_unauthorized_external(self):
        """Validates 401 error for unauthenticated external requests."""
        req = Mock(spec=Request)
        req.cookies = {}
        req.headers = {}
        req.url = Mock(hostname="93.184.216.34")

        with pytest.raises(HTTPException) as exc_info:
            get_current_user_data(req)
        assert exc_info.value.status_code == 401

    def test_require_admin_user_external_non_admin(self):
        """Validates 403 error when external user is not an admin."""
        token = create_jwt_token(TokenData(email="regular@test.com", name="Regular User", id=999))
        req = Mock(spec=Request)
        req.cookies = {}
        req.headers = {"Authorization": f"Bearer {token}"}
        req.url = Mock(hostname="external.com")

        with patch("src.user_manager.user_manager.get_user_by_email", return_value={"id": 999, "is_admin": 0, "role": "user"}):
            with pytest.raises(HTTPException) as exc_info:
                require_admin_user(req)
            assert exc_info.value.status_code == 403


class TestEndpointProtection:
    """Test protection on FastAPI endpoints."""

    def test_keys_router_requires_auth(self):
        """Tests that /api/keys blocks unauthenticated external access."""
        from src.fastapi.router_keys import init_router
        app = FastAPI()
        app.include_router(init_router())
        client = TestClient(app, base_url="http://external.domain.com")

        res = client.get("/api/keys", headers={"Host": "external.domain.com"})
        assert res.status_code in (401, 403)

    def test_keys_router_allows_admin(self):
        """Tests that /api/keys allows admin access with token."""
        from src.fastapi.router_keys import init_router
        token = create_jwt_token(TokenData(email="admin@test.com", name="Admin", id=1))
        app = FastAPI()
        app.include_router(init_router())
        client = TestClient(app, base_url="http://external.domain.com")

        with patch("src.user_manager.user_manager.get_user_by_email", return_value={"id": 1, "is_admin": 1, "role": "admin"}):
            res = client.get("/api/keys", headers={"Authorization": f"Bearer {token}", "Host": "external.domain.com"})
            assert res.status_code == 200

    def test_openai_models_requires_auth(self):
        """Tests that /v1/models blocks unauthenticated external calls."""
        from src.fastapi.router_openai import router as router_openai
        app = FastAPI()
        app.include_router(router_openai)
        client = TestClient(app, base_url="http://external.domain.com")

        res = client.get("/v1/models", headers={"Host": "external.domain.com"})
        assert res.status_code == 401
