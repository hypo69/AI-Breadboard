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
def client():
    """Create TestClient instance."""
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
    """Test that localhost can access /admin (returns 200 login page or admin panel)."""
    # TestClient by default simulates testserver on localhost
    response = client.get("/admin", headers={"host": "localhost:8000"})
    # Either returns login form (200) or redirects to auth (303/200)
    assert response.status_code in (200, 303)


def test_admin_access_redirects_for_user_domain(client):
    """Test that requests from user domain to /admin are silently redirected to root /."""
    response = client.get("/admin", headers={"host": "kino.davidka.net"}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/"


def test_admin_post_redirects_for_user_domain(client):
    """Test that POST /admin from user domain is silently redirected to root /."""
    response = client.post("/admin", data={"password": "onela"}, headers={"host": "kino.davidka.net"}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/"
