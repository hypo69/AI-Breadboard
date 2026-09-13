# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Google Workspace Plugin Main Controller
# =============================================================================
# Description:
#   Main plugin adapter for Google Workspace integration (Gmail, Drive, Sheets, Docs),
#   providing account pool lifecycle, tools, admin actions, and FastAPI router.
#
# File: plugin.py
# Project: ai-breadboard
# Package: plugins.google_workspace
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

from typing import Any, AsyncGenerator, Dict, List, Optional
from fastapi import APIRouter

from plugins.base import BasePlugin
from src.logger import logger


class GoogleWorkspacePlugin(BasePlugin):
    """Modular plugin managing Google Workspace accounts, credentials, and tools.

    Attributes:
        name (str): 'google_workspace'.
        title (str): 'Google Workspace'.
        version (str): '1.0.0'.
        description (str): Functional summary.
        icon (str): '📁'.
        category (str): 'cloud'.
    """

    name: str = "google_workspace"
    title: str = "Google Workspace"
    title_i18n: Dict[str, str] = {
        "en": "Google Workspace & Accounts",
        "ru": "Google Workspace и аккаунты",
    }
    version: str = "1.0.0"
    description: str = "Multi-account OAuth2/Service Account manager for Gmail, Drive, Sheets, and Docs."
    description_i18n: Dict[str, str] = {
        "en": "Multi-account OAuth2/Service Account manager for Gmail, Drive, Sheets, and Docs.",
        "ru": "Управление пулом OAuth2 и сервисных аккаунтов Google (Gmail, Drive, Sheets, Docs).",
    }
    icon: str = "📁"
    category: str = "cloud"
    enabled: bool = True
    is_system: bool = True
    scope: str = "system"

    def __init__(self, ai_model: Any = None, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the Google Workspace plugin."""
        super().__init__(ai_model=ai_model, config=config)

    def get_router(self) -> Optional[APIRouter]:
        """Return the Google Workspace account pool management router."""
        try:
            from src.api.router_google_accounts import router
            return router
        except Exception as ex:
            logger.warning(f"Could not load Google accounts router for plugin: {ex}")
            return None

    def get_actions(self) -> List[Dict[str, Any]]:
        """Return admin actions for Google accounts."""
        return [
            {
                "id": "list_accounts",
                "label": "List Google Accounts",
                "description": "View all configured OAuth2 and Service Account credentials.",
                "params": [],
            },
            {
                "id": "reset_quotas",
                "label": "Reset Account Quotas",
                "description": "Reset cooldown status for all exhausted Google accounts.",
                "params": [],
            },
        ]

    async def execute_action(self, action_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute Google Workspace admin actions."""
        from src.ai.google_accounts_state import list_google_accounts, reset_account_status
        if action_id == "list_accounts":
            accounts = list_google_accounts()
            return {"success": True, "accounts": accounts, "total": len(accounts)}
        if action_id == "reset_quotas":
            accounts = list_google_accounts()
            for acc in accounts:
                reset_account_status(acc.get("account_name", ""))
            return {"success": True, "message": "All Google account quotas reset."}
        return await super().execute_action(action_id, params)

    async def handle(self, message: str, **kwargs: Any) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle conversational queries about Google Workspace."""
        from src.ai.google_accounts_state import list_google_accounts
        accounts = list_google_accounts()
        count = len(accounts)
        yield {
            "status": "complete",
            "text": f"Google Workspace plugin active. {count} account(s) registered in pool.",
            "accounts_count": count,
        }
