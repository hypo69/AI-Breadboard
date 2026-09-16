# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit tests for BackgroundScheduler
# =============================================================================
# Description:
#   Tests background scheduler lifecycle, periodic job triggers, and status diagnostics.
#
# File: test_scheduler.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from src.utils.scheduler import BackgroundScheduler


@pytest.mark.asyncio
async def test_scheduler_lifecycle():
    """Verify scheduler starts, reports active status, and stops cleanly."""
    scheduler = BackgroundScheduler()
    scheduler._rag_interval_seconds = 1000
    scheduler._email_interval_seconds = 1000

    assert scheduler.is_running is False
    await scheduler.start()
    assert scheduler.is_running is True

    status = scheduler.status
    assert status["running"] is True
    assert status["rag_interval_hours"] == 1000 / 3600.0

    await scheduler.stop()
    assert scheduler.is_running is False


@pytest.mark.asyncio
async def test_scheduler_recheck_and_update_all_rags():
    """Verify recheck_and_update_all_rags scans users and triggers build_collection."""
    scheduler = BackgroundScheduler()

    mock_users = [{"id": 1, "name": "Admin"}]
    mock_collections = [{"id": "test_rag", "provider": "local_tfidf"}]

    with patch("src.user_manager.user_manager.get_all_users", return_value=mock_users), \
         patch("src.rag.user_workspace_rag.user_workspace_rag_manager.list_collections", return_value=mock_collections), \
         patch("src.rag.user_workspace_rag.user_workspace_rag_manager.build_collection", return_value={"status": "ok", "chunks_count": 5}):

        summary = await scheduler.recheck_and_update_all_rags()
        assert summary["updated_count"] == 1
        assert len(summary["details"]) == 1
        assert summary["details"][0]["chunks_count"] == 5


@pytest.mark.asyncio
async def test_scheduler_check_emails():
    """Verify check_emails calls GmailManager and caches unread emails."""
    scheduler = BackgroundScheduler()

    mock_emails = [
        {"id": "msg1", "subject": "Test Email", "from": "sender@test.com", "snippet": "Hello world"}
    ]

    mock_gmail_manager_cls = MagicMock()
    mock_instance = MagicMock()
    mock_instance.service = True
    mock_instance.search_messages.return_value = mock_emails
    mock_gmail_manager_cls.return_value = mock_instance

    with patch.dict("sys.modules", {"gmail_manager": MagicMock(GmailManager=mock_gmail_manager_cls)}):
        results = await scheduler.check_emails()
        assert len(results) == 1
        assert results[0]["subject"] == "Test Email"
        assert len(scheduler.status["latest_unread_emails"]) == 1


@pytest.mark.asyncio
async def test_scheduler_check_emails_real_import():
    """Verify check_emails finds gmail_manager module from user-skills path without raising ModuleNotFoundError."""
    scheduler = BackgroundScheduler()
    # When credentials are not set or auth fails, it returns empty list instead of failing with ModuleNotFoundError
    results = await scheduler.check_emails()
    assert isinstance(results, list)

