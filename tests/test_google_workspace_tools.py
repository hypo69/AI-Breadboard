# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit tests for Google Workspace agent tools
# =============================================================================
# Description:
#   Validates functionality and error handling of Google Workspace LangChain tools.
#
# File: test_google_workspace_tools.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
from unittest.mock import MagicMock, patch
import pytest

from src.ai.agents.tools import (
    gmail_search,
    gmail_create_draft,
    gdrive_list_files,
    gdrive_download_file,
    gsheets_info,
    gsheets_read,
    gsheets_search,
    gsheets_append,
)


class TestGoogleWorkspaceToolsNoAuth:
    """Test behavior when Google Workspace credentials are not configured."""

    def test_gmail_search_no_auth(self):
        with patch("src.ai.agents.tools._get_google_workspace_managers") as mock_get:
            mock_manager_cls = MagicMock()
            mock_manager_inst = MagicMock()
            mock_manager_inst.service = None
            mock_manager_cls.return_value = mock_manager_inst
            mock_get.return_value = (mock_manager_cls, None, None)

            res = gmail_search.invoke({"query": "is:unread", "limit": 5})
            data = json.loads(res)
            assert "error" in data
            assert "authentication failed" in data["error"]

    def test_gmail_create_draft_no_auth(self):
        with patch("src.ai.agents.tools._get_google_workspace_managers") as mock_get:
            mock_manager_cls = MagicMock()
            mock_manager_inst = MagicMock()
            mock_manager_inst.service = None
            mock_manager_cls.return_value = mock_manager_inst
            mock_get.return_value = (mock_manager_cls, None, None)

            res = gmail_create_draft.invoke({"to": "test@example.com", "subject": "Hello", "body": "Test body"})
            data = json.loads(res)
            assert "error" in data
            assert "authentication failed" in data["error"]

    def test_gdrive_list_files_no_auth(self):
        with patch("src.ai.agents.tools._get_google_workspace_managers") as mock_get:
            mock_manager_cls = MagicMock()
            mock_manager_inst = MagicMock()
            mock_manager_inst.service = None
            mock_manager_cls.return_value = mock_manager_inst
            mock_get.return_value = (None, mock_manager_cls, None)

            res = gdrive_list_files.invoke({"query": "", "limit": 5})
            data = json.loads(res)
            assert "error" in data
            assert "authentication failed" in data["error"]

    def test_gsheets_read_no_auth(self):
        with patch("src.ai.agents.tools._get_google_workspace_managers") as mock_get:
            mock_manager_cls = MagicMock()
            mock_manager_inst = MagicMock()
            mock_manager_inst.service = None
            mock_manager_cls.return_value = mock_manager_inst
            mock_get.return_value = (None, None, mock_manager_cls)

            res = gsheets_read.invoke({"spreadsheet_id": "test_id", "range_name": "A1:B10"})
            data = json.loads(res)
            assert "error" in data
            assert "authentication failed" in data["error"]


class TestGoogleWorkspaceToolsSuccess:
    """Test behavior when Google Workspace API calls succeed."""

    def test_gmail_search_success(self):
        with patch("src.ai.agents.tools._get_google_workspace_managers") as mock_get:
            mock_manager_cls = MagicMock()
            mock_manager_inst = MagicMock()
            mock_manager_inst.service = MagicMock()
            mock_manager_inst.search_messages.return_value = [
                {"id": "msg1", "subject": "Test Email", "from": "sender@test.com", "snippet": "Hello world"}
            ]
            mock_manager_cls.return_value = mock_manager_inst
            mock_get.return_value = (mock_manager_cls, None, None)

            res = gmail_search.invoke({"query": "is:unread", "limit": 5})
            data = json.loads(res)
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["subject"] == "Test Email"

    def test_gmail_create_draft_success(self):
        with patch("src.ai.agents.tools._get_google_workspace_managers") as mock_get:
            mock_manager_cls = MagicMock()
            mock_manager_inst = MagicMock()
            mock_manager_inst.service = MagicMock()
            mock_manager_inst.create_draft.return_value = {"id": "draft_123"}
            mock_manager_cls.return_value = mock_manager_inst
            mock_get.return_value = (mock_manager_cls, None, None)

            res = gmail_create_draft.invoke({"to": "test@example.com", "subject": "Hello", "body": "Content"})
            data = json.loads(res)
            assert data.get("status") == "ok"
            assert data.get("draft_id") == "draft_123"

    def test_gdrive_list_files_success(self):
        with patch("src.ai.agents.tools._get_google_workspace_managers") as mock_get:
            mock_manager_cls = MagicMock()
            mock_manager_inst = MagicMock()
            mock_manager_inst.service = MagicMock()
            mock_manager_inst.list_files.return_value = [
                {"id": "file1", "name": "Report.docx", "mimeType": "application/vnd.google-apps.document"}
            ]
            mock_manager_cls.return_value = mock_manager_inst
            mock_get.return_value = (None, mock_manager_cls, None)

            res = gdrive_list_files.invoke({"query": "name contains 'Report'", "limit": 10})
            data = json.loads(res)
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["name"] == "Report.docx"

    def test_gsheets_info_success(self):
        with patch("src.ai.agents.tools._get_google_workspace_managers") as mock_get:
            mock_manager_cls = MagicMock()
            mock_manager_inst = MagicMock()
            mock_manager_inst.service = MagicMock()
            mock_manager_inst.get_spreadsheet_info.return_value = {
                "spreadsheet_id": "sheet_123",
                "title": "Budget 2026",
                "sheets": [{"sheet_id": 0, "title": "Sheet1", "row_count": 100, "column_count": 20}]
            }
            mock_manager_cls.return_value = mock_manager_inst
            mock_get.return_value = (None, None, mock_manager_cls)

            res = gsheets_info.invoke({"spreadsheet_id": "sheet_123"})
            data = json.loads(res)
            assert data.get("title") == "Budget 2026"
            assert len(data.get("sheets", [])) == 1

    def test_gsheets_read_success(self):
        with patch("src.ai.agents.tools._get_google_workspace_managers") as mock_get:
            mock_manager_cls = MagicMock()
            mock_manager_inst = MagicMock()
            mock_manager_inst.service = MagicMock()
            mock_manager_inst.read_range.return_value = [["Name", "Score"], ["Alice", "95"]]
            mock_manager_cls.return_value = mock_manager_inst
            mock_get.return_value = (None, None, mock_manager_cls)

            res = gsheets_read.invoke({"spreadsheet_id": "sheet_123", "range_name": "A1:B2"})
            data = json.loads(res)
            assert data.get("range") == "A1:B2"
            assert len(data.get("rows", [])) == 2

    def test_gsheets_search_success(self):
        with patch("src.ai.agents.tools._get_google_workspace_managers") as mock_get:
            mock_manager_cls = MagicMock()
            mock_manager_inst = MagicMock()
            mock_manager_inst.service = MagicMock()
            mock_manager_inst.search.return_value = [{"row_index": 2, "values": ["Alice", "95"]}]
            mock_manager_cls.return_value = mock_manager_inst
            mock_get.return_value = (None, None, mock_manager_cls)

            res = gsheets_search.invoke({"spreadsheet_id": "sheet_123", "query": "Alice"})
            data = json.loads(res)
            assert data.get("query") == "Alice"
            assert len(data.get("matches", [])) == 1

    def test_gsheets_append_success(self):
        with patch("src.ai.agents.tools._get_google_workspace_managers") as mock_get:
            mock_manager_cls = MagicMock()
            mock_manager_inst = MagicMock()
            mock_manager_inst.service = MagicMock()
            mock_manager_inst.append_rows.return_value = {
                "updates": {"updatedRange": "Sheet1!A3:B3"}
            }
            mock_manager_cls.return_value = mock_manager_inst
            mock_get.return_value = (None, None, mock_manager_cls)

            res = gsheets_append.invoke({
                "spreadsheet_id": "sheet_123",
                "range_name": "Sheet1!A1",
                "values_json": '["Bob", "88"]'
            })
            data = json.loads(res)
            assert data.get("status") == "ok"
            assert data.get("updated_range") == "Sheet1!A3:B3"
