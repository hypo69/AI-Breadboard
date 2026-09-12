# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Background Periodic Scheduler for AI Breadboard
# =============================================================================
# Description:
#   Provides an asynchronous background scheduler running periodic maintenance
#   tasks: RAG index verification and re-indexing every 24 hours, and Gmail email
#   verification every 5 minutes.
#
# File: scheduler.py
# Project: ai-breadboard
# Package: src.utils
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from header import __root__
from src.logger import logger
from src.user_manager import user_manager
from src.rag.user_workspace_rag import user_workspace_rag_manager


class BackgroundScheduler:
    """Async background periodic job scheduler."""

    def __init__(self) -> None:
        """Initialize the background scheduler."""
        self._running: bool = False
        self._tasks: List[asyncio.Task] = []
        self._rag_interval_seconds: float = 24 * 3600.0  # 24 hours
        self._email_interval_seconds: float = 5 * 60.0    # 5 minutes
        self._last_rag_run: Optional[datetime] = None
        self._last_email_run: Optional[datetime] = None
        self._latest_unread_emails: List[Dict[str, Any]] = []

    @property
    def is_running(self) -> bool:
        """Return True if background scheduler is active."""
        return self._running

    @property
    def status(self) -> Dict[str, Any]:
        """Return diagnostic status of scheduled jobs."""
        return {
            "running": self._running,
            "rag_interval_hours": self._rag_interval_seconds / 3600.0,
            "email_interval_minutes": self._email_interval_seconds / 60.0,
            "last_rag_run": self._last_rag_run.isoformat() if self._last_rag_run else None,
            "last_email_run": self._last_email_run.isoformat() if self._last_email_run else None,
            "unread_emails_count": len(self._latest_unread_emails),
            "latest_unread_emails": self._latest_unread_emails[:5],
        }

    async def start(self) -> None:
        """Start periodic background tasks."""
        if self._running:
            return

        self._running = True
        logger.info("Starting BackgroundScheduler (24h RAG recheck, 5m Gmail check)...")
        
        self._tasks.append(asyncio.create_task(self._run_rag_periodically()))
        self._tasks.append(asyncio.create_task(self._run_email_check_periodically()))

    async def stop(self) -> None:
        """Stop all running background tasks gracefully."""
        self._running = False
        for task in self._tasks:
            task.cancel()
        
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        logger.info("BackgroundScheduler stopped.")

    async def _run_rag_periodically(self) -> None:
        """Execute RAG index verification and re-indexing every 24 hours."""
        while self._running:
            try:
                await self.recheck_and_update_all_rags()
                self._last_rag_run = datetime.now(timezone.utc)
            except asyncio.CancelledError:
                break
            except Exception as ex:
                logger.error(f"[Scheduler] Error during periodic RAG update: {ex}")

            try:
                await asyncio.sleep(self._rag_interval_seconds)
            except asyncio.CancelledError:
                break

    async def _run_email_check_periodically(self) -> None:
        """Execute Gmail unread email verification every 5 minutes."""
        while self._running:
            try:
                await self.check_emails()
                self._last_email_run = datetime.now(timezone.utc)
            except asyncio.CancelledError:
                break
            except Exception as ex:
                logger.error(f"[Scheduler] Error during periodic Email check: {ex}")

            try:
                await asyncio.sleep(self._email_interval_seconds)
            except asyncio.CancelledError:
                break

    async def recheck_and_update_all_rags(self) -> Dict[str, Any]:
        """Scan all user RAG collections and rebuild/update outdated indexes.

        Returns:
            Dict[str, Any]: Summary of re-indexed collections.
        """
        logger.info("[Scheduler] Starting 24h RAG index verification & update...")
        users = await asyncio.to_thread(user_manager.get_all_users)
        updated_count = 0
        details = []

        for user in users:
            user_id = user.get("id")
            if not user_id:
                continue

            try:
                collections = await asyncio.to_thread(user_workspace_rag_manager.list_collections, user_id)
                for col in collections:
                    rag_id = col.get("id")
                    if not rag_id:
                        continue
                    
                    # Rebuild collection
                    logger.info(f"[Scheduler] Refreshing RAG collection '{rag_id}' for user {user_id}")
                    res = await asyncio.to_thread(
                        user_workspace_rag_manager.build_collection,
                        user_id=user_id,
                        rag_id=rag_id,
                        provider=col.get("provider", "local_tfidf")
                    )
                    updated_count += 1
                    details.append({
                        "user_id": user_id,
                        "rag_id": rag_id,
                        "status": res.get("status", "ok"),
                        "chunks_count": res.get("chunks_count", 0)
                    })
            except Exception as ex:
                logger.error(f"[Scheduler] Failed to update RAG for user {user_id}: {ex}")

        logger.info(f"[Scheduler] Finished 24h RAG re-indexing. Updated {updated_count} collection(s).")
        return {"updated_count": updated_count, "details": details}

    async def check_emails(self, account_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Check for unread emails in Gmail via google-workspace manager.

        Args:
            account_name (Optional[str]): Optional specific account name from pool.

        Returns:
            List[Dict[str, Any]]: List of unread message summaries.
        """
        scripts_dir = __root__ / ".agents" / "skills" / "google-workspace" / "scripts"
        import sys
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))

        def _fetch_messages():
            try:
                from gmail_manager import GmailManager
                manager = GmailManager(account_name=account_name)
                if not manager.service:
                    return []
                return manager.search_messages(query="is:unread", max_results=10)
            except Exception as ex:
                logger.warning(f"[Scheduler] Email check skipped or failed: {ex}")
                return []

        messages = await asyncio.to_thread(_fetch_messages)
        if messages:
            self._latest_unread_emails = messages
            logger.info(f"[Scheduler] Found {len(messages)} unread email(s) in Gmail.")
        return messages


# Global singleton instance
scheduler = BackgroundScheduler()
