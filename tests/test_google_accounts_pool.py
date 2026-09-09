# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit tests for Google Workspace multi-account pool
# =============================================================================
# Description:
#   Validates account pool management, quota exhaustion rotation, and credential loading.
#
# File: test_google_accounts_pool.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from src.ai.google_accounts_state import (
    list_google_accounts,
    get_account_info,
    save_google_account,
    delete_google_account,
    set_default_account,
    mark_account_exhausted,
    reset_account_status,
    load_account_credentials,
)
from src.ai.agents.tools import (
    gmail_search,
    gdrive_list_files,
    gsheets_read,
)


@pytest.fixture(autouse=True)
def mock_accounts_storage(tmp_path, monkeypatch):
    """Isolate accounts JSON and tokens dir to temp directory."""
    temp_secrets = tmp_path / "secrets"
    temp_tokens = temp_secrets / "tokens"
    temp_accounts = temp_secrets / "google_accounts.json"
    temp_secrets.mkdir(parents=True, exist_ok=True)
    temp_tokens.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("src.ai.google_accounts_state._SECRETS_DIR", temp_secrets)
    monkeypatch.setattr("src.ai.google_accounts_state._TOKENS_DIR", temp_tokens)
    monkeypatch.setattr("src.ai.google_accounts_state._ACCOUNTS_FILE", temp_accounts)


class TestGoogleAccountsPoolManagement:
    """Test CRUD operations on Google accounts pool."""

    def test_save_and_list_accounts(self):
        # 1. Save work account
        creds_dummy = {"installed": {"client_id": "work-123.apps.googleusercontent.com", "client_secret": "sec-work"}}
        ok = save_google_account(
            account_name="work",
            credentials_path_or_dict=creds_dummy,
            account_type="oauth2",
            email="work@company.com",
            set_as_default=True,
        )
        assert ok is True

        # 2. Save personal account
        ok2 = save_google_account(
            account_name="personal",
            credentials_path_or_dict=creds_dummy,
            account_type="oauth2",
            email="personal@gmail.com",
            set_as_default=False,
        )
        assert ok2 is True

        # 3. List accounts
        accounts = list_google_accounts()
        assert len(accounts) == 2
        work_acc = next((a for a in accounts if a["name"] == "work"), None)
        assert work_acc is not None
        assert work_acc["is_default"] is True
        assert work_acc["email"] == "work@company.com"

        # 4. Get specific account info
        info = get_account_info("personal")
        assert info is not None
        assert info["email"] == "personal@gmail.com"

    def test_set_default_account(self):
        creds_dummy = {"installed": {"client_id": "dummy"}}
        save_google_account("acc1", creds_dummy, set_as_default=True)
        save_google_account("acc2", creds_dummy, set_as_default=False)

        assert get_account_info()["name"] == "acc1"

        set_default_account("acc2")
        assert get_account_info()["name"] == "acc2"

    def test_quota_exhaustion_and_reset(self):
        creds_dummy = {"installed": {"client_id": "dummy"}}
        save_google_account("primary", creds_dummy, set_as_default=True)

        mark_account_exhausted("primary")
        info = get_account_info("primary")
        assert info["status"] == "exhausted"

        active_accounts = list_google_accounts(skip_exhausted=True)
        assert len(active_accounts) == 0

        reset_account_status("primary")
        info_reset = get_account_info("primary")
        assert info_reset["status"] == "active"

    def test_delete_account(self):
        creds_dummy = {"installed": {"client_id": "dummy"}}
        save_google_account("temp_acc", creds_dummy)
        assert len(list_google_accounts()) == 1

        deleted = delete_google_account("temp_acc")
        assert deleted is True
        assert len(list_google_accounts()) == 0


class TestToolsWithAccountName:
    """Test LangChain tool execution with account_name routing."""

    def test_gmail_search_with_account_name(self):
        with patch("src.ai.agents.tools._get_google_workspace_managers") as mock_get:
            mock_cls = MagicMock()
            mock_inst = MagicMock()
            mock_inst.service = MagicMock()
            mock_inst.search_messages.return_value = [{"id": "m1", "subject": "Work email"}]
            mock_cls.return_value = mock_inst
            mock_get.return_value = (mock_cls, None, None)

            res = gmail_search.invoke({"query": "is:unread", "limit": 5, "account_name": "work"})
            mock_cls.assert_called_once_with(account_name="work")
            data = json.loads(res)
            assert len(data) == 1
            assert data[0]["subject"] == "Work email"

    def test_gsheets_read_with_account_name(self):
        with patch("src.ai.agents.tools._get_google_workspace_managers") as mock_get:
            mock_cls = MagicMock()
            mock_inst = MagicMock()
            mock_inst.service = MagicMock()
            mock_inst.read_range.return_value = [["Col1", "Col2"], ["Val1", "Val2"]]
            mock_cls.return_value = mock_inst
            mock_get.return_value = (None, None, mock_cls)

            res = gsheets_read.invoke({
                "spreadsheet_id": "sheet_xyz",
                "range_name": "Sheet1!A1:B2",
                "account_name": "personal"
            })
            mock_cls.assert_called_once_with(account_name="personal")
            data = json.loads(res)
            assert len(data["rows"]) == 2
