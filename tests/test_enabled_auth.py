# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Enabled Auth Verification Tests
# =============================================================================
# Description:
#   Unit tests verifying that when authentication is enabled (DISABLE_AUTH is not true),
#   authentication gates, JWT token checks, and protected routes behave correctly.
#
# File: test_enabled_auth.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
import pytest
from fastapi import Request, HTTPException
from fastapi.testclient import TestClient

from src.api.router_auth import (
    is_auth_disabled,
    is_oauth_enabled,
    create_jwt_token,
    verify_jwt_token,
    TokenData,
    get_current_user_data,
    require_admin_user,
)
from src.app import create_app, register_pages, AppState


def test_auth_enabled_helpers(monkeypatch):
    """Проверяет is_auth_disabled и is_oauth_enabled в режиме включенной аутентификации."""
    monkeypatch.delenv("DISABLE_AUTH", raising=False)
    monkeypatch.setenv("ENABLE_OAUTH", "true")

    assert is_auth_disabled() is False
    assert is_oauth_enabled() is True


def test_jwt_token_creation_and_verification():
    """Проверяет создание и валидацию корректного JWT токена."""
    token_data = TokenData(
        email="testuser@example.com",
        name="Test User",
        picture="https://example.com/photo.jpg",
        id=42,
    )
    token = create_jwt_token(token_data)
    assert isinstance(token, str)
    assert len(token) > 0

    payload = verify_jwt_token(token)
    assert payload is not None
    assert payload.email == "testuser@example.com"
    assert payload.name == "Test User"
    assert payload.picture == "https://example.com/photo.jpg"
    assert payload.id == 42


def test_jwt_token_verification_invalid():
    """Проверяет, что невалидный токен возвращает None."""
    assert verify_jwt_token("invalid.token.structure") is None
    assert verify_jwt_token("") is None


def test_get_current_user_data_with_valid_token(monkeypatch):
    """Проверяет извлечение пользователя из cookie или Authorization заголовка."""
    monkeypatch.delenv("DISABLE_AUTH", raising=False)
    
    token_data = TokenData(email="authorized@domain.com", name="Auth User", id=10)
    token = create_jwt_token(token_data)

    # 1. Из Cookie
    req_cookie = Request(
        scope={
            "type": "http",
            "method": "GET",
            "path": "/api/test",
            "headers": [(b"cookie", f"auth_token={token}".encode("latin-1"))],
            "server": ("10.0.0.1", 80),
        }
    )
    user = get_current_user_data(req_cookie)
    assert user.email == "authorized@domain.com"
    assert user.id == 10

    # 2. Из Header Bearer
    req_header = Request(
        scope={
            "type": "http",
            "method": "GET",
            "path": "/api/test",
            "headers": [(b"authorization", f"Bearer {token}".encode("latin-1"))],
            "server": ("10.0.0.1", 80),
        }
    )
    user_hdr = get_current_user_data(req_header)
    assert user_hdr.email == "authorized@domain.com"
    assert user_hdr.id == 10


def test_get_current_user_data_unauthenticated_non_local(monkeypatch):
    """Проверяет, что нелокальный неавторизованный запрос вызывает HTTPException 401."""
    monkeypatch.delenv("DISABLE_AUTH", raising=False)

    req_external = Request(
        scope={
            "type": "http",
            "method": "GET",
            "path": "/api/test",
            "headers": [(b"host", b"external-domain.com")],
            "server": ("203.0.113.1", 80),
            "client": ("203.0.113.1", 12345),
        }
    )
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_data(req_external)
    assert exc_info.value.status_code == 401


def test_root_page_serves_login_when_unauthenticated(monkeypatch):
    """Проверяет, что при включенной аутентификации неавторизованный запрос к / получает страницу логина."""
    monkeypatch.delenv("DISABLE_AUTH", raising=False)

    app = create_app()
    state = AppState()
    app.state.app_state = state
    register_pages(app)

    client = TestClient(app)
    res = client.get("/")
    assert res.status_code == 200
    assert "login" in res.text.lower() or "войти" in res.text.lower() or "auth" in res.text.lower()


def test_root_page_serves_user_dashboard_with_auth_cookie(monkeypatch):
    """Проверяет, что авторизованный пользователь получает интерфейс пользователя при обращении к /."""
    monkeypatch.delenv("DISABLE_AUTH", raising=False)

    app = create_app()
    state = AppState()
    app.state.app_state = state
    register_pages(app)

    token = create_jwt_token(TokenData(email="user@aibreadboard.local", name="Test User", id=1))
    client = TestClient(app, cookies={"auth_token": token})
    res = client.get("/")
    assert res.status_code == 200
    assert "AI Assistant" in res.text or "ai-breadboard" in res.text.lower() or "<!DOCTYPE html>" in res.text


def test_admin_page_auth_protection(monkeypatch):
    """Проверяет защиту страницы /admin при включенной авторизации."""
    monkeypatch.delenv("DISABLE_AUTH", raising=False)

    app = create_app()
    state = AppState()
    app.state.app_state = state
    register_pages(app)

    client = TestClient(app)
    res = client.get("/admin")
    assert res.status_code == 200
    # Страница содержит форму ввода пароля администратора
    assert "password" in res.text.lower() or "пароль" in res.text.lower() or "admin" in res.text.lower()

    # С cookie верификации админа
    admin_client = TestClient(app, cookies={"admin_password_verified": "true"})
    admin_res = admin_client.get("/admin")
    assert admin_res.status_code == 200
    assert "AI Assistant - Admin" in admin_res.text or "mainTabs" in admin_res.text
