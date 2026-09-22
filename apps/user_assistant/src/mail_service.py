# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: User Assistant Mail Service
# =============================================================================
# Description:
#   Provides email fetching, search, and draft generation via Google Workspace
#   Gmail API and fallback IMAP connectors.
#
# File: mail_service.py
# Package: apps.user_assistant.src
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

from typing import Any, Dict, List, Optional
from logger import logger


class MailService:
    """Manages user email accounts, inbox triage, and draft generation."""

    def __init__(self, account_name: Optional[str] = None) -> None:
        """Initialize mail service."""
        self.account_name = account_name

    def list_messages(self, query: str = "is:unread", max_results: int = 10) -> List[Dict[str, Any]]:
        """Search and retrieve messages from email inbox.

        Args:
            query (str): Search filter query.
            max_results (int): Maximum messages to return.

        Returns:
            List[Dict[str, Any]]: List of email summaries.
        """
        try:
            import sys
            from pathlib import Path
            from header import __root__
            scripts_dir = __root__ / ".agents" / "skills" / "user-skills" / "google-workspace" / "scripts"
            if not scripts_dir.exists():
                scripts_dir = __root__ / ".agents" / "skills" / "google-workspace" / "scripts"
            if scripts_dir.exists() and str(scripts_dir) not in sys.path:
                sys.path.insert(0, str(scripts_dir))

            from gmail_manager import GmailManager
            mgr = GmailManager(account_name=self.account_name)
            return mgr.search_messages(query=query, max_results=max_results)
        except Exception:
            # Fallback direct import or mock
            try:
                from src.ai.google_accounts_state import list_google_accounts
                accounts = list_google_accounts()
                if not accounts:
                    return []
            except Exception as ex:
                logger.debug(f"Mail service status probe: {ex}")
            return []

    def create_draft(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """Create an email draft.

        Args:
            to (str): Recipient email address.
            subject (str): Email subject.
            body (str): Email body text.

        Returns:
            Dict[str, Any]: Creation status and draft metadata.
        """
        try:
            import sys
            from pathlib import Path
            from header import __root__
            scripts_dir = __root__ / ".agents" / "skills" / "user-skills" / "google-workspace" / "scripts"
            if not scripts_dir.exists():
                scripts_dir = __root__ / ".agents" / "skills" / "google-workspace" / "scripts"
            if scripts_dir.exists() and str(scripts_dir) not in sys.path:
                sys.path.insert(0, str(scripts_dir))

            from gmail_manager import GmailManager
            mgr = GmailManager(account_name=self.account_name)
            return mgr.create_draft(to=to, subject=subject, body=body)
        except Exception as ex:
            logger.warning(f"Failed to create draft: {ex}")
            return {"success": False, "error": str(ex), "draft_id": None}
