# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Google OAuth System Plugin Main Controller
# =============================================================================
# Description:
#   System plugin providing centralized Google OAuth 2.0 / Service Account
#   token management, account pool discovery, credential refresh, and admin API.
#
# File: plugin.py
# Project: ai-breadboard
# Package: plugins.google_oauth
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

from typing import Any, AsyncGenerator, Dict, List, Optional
from fastapi import APIRouter

from plugins.base import BasePlugin
from logger import logger


class GoogleOAuthPlugin(BasePlugin):
    """Системный плагин управления авторизацией Google OAuth и пулом аккаунтов.

    Attributes:
        name (str): 'google_oauth'.
        title (str): 'Google OAuth & Accounts'.
        version (str): '1.0.0'.
        description (str): Functional summary.
        icon (str): '🔐'.
        category (str): 'auth'.
    """

    name: str = "google_oauth"
    title: str = "Google OAuth & Accounts"
    title_i18n: Dict[str, str] = {
        "en": "Google OAuth & Credentials Manager",
        "ru": "Системный менеджер Google OAuth и аккаунтов",
    }
    version: str = "1.0.0"
    description: str = "Centralized system OAuth 2.0 and Service Account credential manager for Google Workspace."
    description_i18n: Dict[str, str] = {
        "en": "Centralized system OAuth 2.0 and Service Account credential manager for Google Workspace.",
        "ru": "Централизованное управление токенами OAuth 2.0, сервисными аккаунтами и пулом учетных записей Google.",
    }
    icon: str = "🔐"
    category: str = "auth"
    enabled: bool = True
    is_system: bool = True
    scope: str = "system"

    def __init__(self, ai_model: Any = None, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize Google OAuth system plugin."""
        super().__init__(ai_model=ai_model, config=config)

    def get_router(self) -> Optional[APIRouter]:
        """Return the Google Workspace account pool management FastAPI router."""
        try:
            from src.api.router_google_accounts import router
            return router
        except Exception as ex:
            logger.warning(f"Could not load Google accounts router for plugin: {ex}")
            return None

    def get_actions(self) -> List[Dict[str, Any]]:
        """Return admin actions for Google OAuth and accounts."""
        return [
            {
                "id": "list_accounts",
                "label": "List Google Accounts",
                "description": "View all configured OAuth2 and Service Account credentials and token statuses.",
                "params": [],
            },
            {
                "id": "test_credentials",
                "label": "Test Google Credentials",
                "description": "Verify validity and freshness of Google Workspace OAuth tokens.",
                "params": [
                    {"name": "account_name", "type": "string", "default": "", "label": "Account Name (optional)"}
                ],
            },
            {
                "id": "reset_quotas",
                "label": "Reset Account Quotas",
                "description": "Reset cooldown status for all exhausted Google accounts.",
                "params": [],
            },
        ]

    async def execute_action(self, action_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute Google OAuth admin actions."""
        from src.ai.google_accounts_state import list_google_accounts, reset_account_status, load_account_credentials
        params = params or {}

        if action_id == "list_accounts":
            accounts = list_google_accounts()
            return {"success": True, "accounts": accounts, "total": len(accounts)}

        if action_id == "test_credentials":
            acc_name = params.get("account_name", "").strip() or None
            try:
                creds = load_account_credentials(account_name=acc_name)
                valid = bool(creds and getattr(creds, "valid", False))
                return {
                    "success": valid,
                    "valid": valid,
                    "account": acc_name or "default",
                    "message": "Token is valid and active" if valid else "Failed to validate credentials",
                }
            except Exception as ex:
                return {"success": False, "error": str(ex)}

        if action_id == "reset_quotas":
            accounts = list_google_accounts()
            for acc in accounts:
                reset_account_status(acc.get("name", ""))
            return {"success": True, "message": "All Google account quotas reset."}

        return await super().execute_action(action_id, params)

    async def handle(self, message: str, **kwargs: Any) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle conversational queries about Google OAuth."""
        from src.ai.google_accounts_state import list_google_accounts
        accounts = list_google_accounts()
        count = len(accounts)
        yield {
            "status": "complete",
            "text": f"Google OAuth System Plugin is active. {count} account(s) registered in pool.",
            "accounts_count": count,
        }
