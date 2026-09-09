# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit tests for Google Workspace Accounts Pool Router
# =============================================================================
# Description:
#   Validates REST endpoints for Google Workspace account CRUD, file uploads,
#   default account selection, status resets, and connection testing.
#
# File: test_router_google_accounts.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import io
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from main import app
from src.ai.google_accounts_state import save_google_account


@pytest.fixture(autouse=True)
def isolate_google_accounts(tmp_path, monkeypatch):
    """Isolate accounts storage and tokens dir to temporary directory."""
    temp_secrets = tmp_path / "secrets"
    temp_tokens = temp_secrets / "tokens"
    temp_accounts = temp_secrets / "google_accounts.json"
    temp_secrets.mkdir(parents=True, exist_ok=True)
    temp_tokens.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("src.ai.google_accounts_state._SECRETS_DIR", temp_secrets)
    monkeypatch.setattr("src.ai.google_accounts_state._TOKENS_DIR", temp_tokens)
    monkeypatch.setattr("src.ai.google_accounts_state._ACCOUNTS_FILE", temp_accounts)

    monkeypatch.setattr("src.fastapi.router_google_accounts._TOKENS_DIR", temp_tokens)


@pytest.fixture
def client():
    """Create test client with mock admin authentication."""
    with patch("src.fastapi.router_auth.require_admin_user", return_value={"id": 1, "username": "admin", "role": "admin"}):
        yield TestClient(app)


class TestGoogleAccountsRouter:
    """Test suite for /api/admin/google-accounts endpoints."""

    def test_list_empty_accounts(self, client):
        response = client.get("/api/admin/google-accounts")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["accounts"] == []

    def test_create_account_json(self, client):
        payload = {
            "account_name": "primary_work",
            "account_type": "oauth2",
            "email": "work@example.com",
            "credentials_dict": {"installed": {"client_id": "cid-123", "client_secret": "csec-123"}},
            "set_as_default": True
        }
        response = client.post("/api/admin/google-accounts", json=payload)
        assert response.status_code == 200
        assert response.json()["status"] == "success"

        # Verify listed
        list_res = client.get("/api/admin/google-accounts")
        assert list_res.status_code == 200
        data = list_res.json()
        assert data["total"] == 1
        acc = data["accounts"][0]
        assert acc["name"] == "primary_work"
        assert acc["is_default"] is True
        assert acc["email"] == "work@example.com"
        assert acc["type"] == "oauth2"

    def test_upload_credentials_file(self, client):
        creds_content = json.dumps({
            "type": "service_account",
            "project_id": "test-proj",
            "client_email": "sa@test-proj.iam.gserviceaccount.com"
        }).encode("utf-8")

        files = {
            "file": ("service_account.json", io.BytesIO(creds_content), "application/json")
        }
        data = {
            "account_name": "sa_account",
            "account_type": "service_account",
            "set_as_default": False
        }

        response = client.post("/api/admin/google-accounts/upload", data=data, files=files)
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert response.json()["type"] == "service_account"

        # Verify details
        detail_res = client.get("/api/admin/google-accounts/sa_account")
        assert detail_res.status_code == 200
        assert detail_res.json()["name"] == "sa_account"
        assert detail_res.json()["type"] == "service_account"

    def test_set_default_account(self, client):
        client.post("/api/admin/google-accounts", json={
            "account_name": "acc_a",
            "credentials_dict": {"installed": {"client_id": "a"}},
            "set_as_default": True
        })
        client.post("/api/admin/google-accounts", json={
            "account_name": "acc_b",
            "credentials_dict": {"installed": {"client_id": "b"}},
            "set_as_default": False
        })

        # Switch default to acc_b
        res = client.post("/api/admin/google-accounts/acc_b/default")
        assert res.status_code == 200

        list_data = client.get("/api/admin/google-accounts").json()["accounts"]
        b = next(a for a in list_data if a["name"] == "acc_b")
        a = next(a for a in list_data if a["name"] == "acc_a")
        assert b["is_default"] is True
        assert a["is_default"] is False

    def test_reset_status(self, client):
        client.post("/api/admin/google-accounts", json={
            "account_name": "acc_quota",
            "credentials_dict": {"installed": {"client_id": "q"}}
        })

        from src.ai.google_accounts_state import mark_account_exhausted
        mark_account_exhausted("acc_quota")

        # Check status is exhausted
        info = client.get("/api/admin/google-accounts/acc_quota").json()
        assert info["status"] == "exhausted"

        # Reset status
        res = client.post("/api/admin/google-accounts/acc_quota/reset-status")
        assert res.status_code == 200

        info_after = client.get("/api/admin/google-accounts/acc_quota").json()
        assert info_after["status"] == "active"

    def test_test_account_connectivity(self, client):
        client.post("/api/admin/google-accounts", json={
            "account_name": "acc_test",
            "credentials_dict": {"installed": {"client_id": "t"}}
        })

        with patch("src.fastapi.router_google_accounts.load_account_credentials") as mock_load:
            mock_creds = MagicMock()
            mock_creds.valid = True
            mock_creds.expired = False
            mock_creds.scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
            mock_load.return_value = mock_creds

            res = client.post("/api/admin/google-accounts/acc_test/test")
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "success"
            assert data["valid"] is True
            assert "https://www.googleapis.com/auth/gmail.readonly" in data["scopes"]

    def test_delete_account(self, client):
        client.post("/api/admin/google-accounts", json={
            "account_name": "acc_del",
            "credentials_dict": {"installed": {"client_id": "del"}}
        })
        assert client.get("/api/admin/google-accounts").json()["total"] == 1

        del_res = client.delete("/api/admin/google-accounts/acc_del")
        assert del_res.status_code == 200
        assert client.get("/api/admin/google-accounts").json()["total"] == 0
