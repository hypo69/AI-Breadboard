# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Routing and access control tests
# =============================================================================
# Description:
#   Validates localhost restriction for /admin endpoints and proper serving
#   of the user interface (Chat, RAG, TTS, Voice tabs) on the user domain / root.
#
# File: tests/test_routing_access.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
from fastapi.testclient import TestClient
from main import app, is_localhost, get_request_hostname


@pytest.fixture
def client(monkeypatch):
    """Create TestClient instance with test environment variables."""
    monkeypatch.setenv("ADMIN_PASSWORD", "test_admin_secret_123")
    return TestClient(app)


def test_is_localhost_helper():
    """Verify is_localhost detection logic."""
    from starlette.requests import Request
    
    # Mock localhost scope
    scope_local = {
        "type": "http",
        "client": ("127.0.0.1", 12345),
        "headers": [(b"host", b"localhost:8000")],
    }
    req_local = Request(scope_local)
    assert is_localhost(req_local) is True
    assert get_request_hostname(req_local) == "localhost"

    # Mock remote scope
    scope_remote = {
        "type": "http",
        "client": ("198.51.100.25", 12345),
        "headers": [(b"host", b"kino.davidka.net")],
    }
    req_remote = Request(scope_remote)
    assert is_localhost(req_remote) is False
    assert get_request_hostname(req_remote) == "kino.davidka.net"


def test_root_serves_user_interface(client):
    """Test that root endpoint serves User Interface with the 4 tabs."""
    response = client.get("/", headers={"host": "kino.davidka.net"})
    assert response.status_code == 200
    html = response.text
    # Check that the 4 tabs exist in User Interface
    assert 'id="tab-chat"' in html
    assert 'id="tab-rag"' in html
    assert 'id="tab-tts"' in html
    assert 'id="tab-voice"' in html


def test_user_endpoint_serves_user_interface(client):
    """Test that /user endpoint redirects to root / and serves User Interface."""
    response = client.get("/user", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/"

    response_followed = client.get("/user", follow_redirects=True)
    assert response_followed.status_code == 200
    html = response_followed.text
    assert 'id="tab-chat"' in html
    assert 'id="tab-rag"' in html
    assert 'id="tab-tts"' in html
    assert 'id="tab-voice"' in html


def test_admin_access_allowed_for_localhost(client):
    """Test that localhost can access /admin (returns 200 login page)."""
    response = client.get("/admin", headers={"host": "localhost:8000"})
    assert response.status_code == 200
    assert 'name="password"' in response.text


def test_admin_access_allowed_for_user_domain(client):
    """Test that requests from user domain to /admin return the password login page."""
    response = client.get("/admin", headers={"host": "kino.davidka.net"}, follow_redirects=False)
    assert response.status_code == 200
    assert 'name="password"' in response.text


def test_admin_post_password_login(client):
    """Test that POST /admin with correct password sets cookie and redirects to /admin."""
    response = client.post("/admin", data={"password": "test_admin_secret_123"}, headers={"host": "kino.davidka.net"}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/admin"
    assert "admin_password_verified=true" in response.headers.get("set-cookie", "")

    # Access /admin with the verified cookie
    client.cookies.set("admin_password_verified", "true")
    admin_page = client.get("/admin", headers={"host": "kino.davidka.net"})
    assert admin_page.status_code == 200
    assert "Панель управления" in admin_page.text or "admin" in admin_page.text.lower()


def test_docs_endpoints_allowed_for_localhost(client):
    """Test that localhost can access /docs, /redoc, and /openapi.json."""
    resp_docs = client.get("/docs", headers={"host": "localhost:8000"})
    assert resp_docs.status_code == 200
    assert "swagger-ui" in resp_docs.text.lower() or "html" in resp_docs.text.lower()

    resp_redoc = client.get("/redoc", headers={"host": "localhost:8000"})
    assert resp_redoc.status_code == 200
    assert "redoc" in resp_redoc.text.lower()

    resp_openapi = client.get("/openapi.json", headers={"host": "localhost:8000"})
    assert resp_openapi.status_code == 200
    assert "openapi" in resp_openapi.json()


def test_docs_endpoints_return_404_for_user_domain(client):
    """Test that requests from user domain to /docs, /redoc, and /openapi.json return 404."""
    resp_docs = client.get("/docs", headers={"host": "kino.davidka.net"})
    assert resp_docs.status_code == 404

    resp_redoc = client.get("/redoc", headers={"host": "kino.davidka.net"})
    assert resp_redoc.status_code == 404

    resp_openapi = client.get("/openapi.json", headers={"host": "kino.davidka.net"})
    assert resp_openapi.status_code == 404

