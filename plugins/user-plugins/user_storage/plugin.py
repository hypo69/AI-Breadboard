# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: User Storage Plugin Main Controller
# =============================================================================
# Description:
#   Main plugin adapter for User Personal Storage, managing sandboxed documents,
#   user uploads, RAG document preprocessing, and storage metrics.
#
# File: plugin.py
# Project: ai-breadboard
# Package: plugins.user_storage
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

from typing import Any, AsyncGenerator, Dict, List, Optional
from fastapi import APIRouter

from plugins.base import BasePlugin
from src.logger import logger


class UserStoragePlugin(BasePlugin):
    """Modular plugin managing user personal document files, quotas, and RAG ingestion.

    Attributes:
        name (str): 'user_storage'.
        title (str): 'User Personal Storage'.
        version (str): '1.0.0'.
        description (str): Functional summary.
        icon (str): '📦'.
        category (str): 'storage'.
    """

    name: str = "user_storage"
    title: str = "User Personal Storage"
    title_i18n: Dict[str, str] = {
        "en": "User Storage & Documents",
        "ru": "Хранилище документов пользователя",
    }
    version: str = "1.0.0"
    description: str = "Isolated per-user document storage, file upload/download, quotas, and RAG attachments."
    description_i18n: Dict[str, str] = {
        "en": "Isolated per-user document storage, file upload/download, quotas, and RAG attachments.",
        "ru": "Изолированное хранилище документов пользователей, загрузка/скачивание, квоты и RAG.",
    }
    icon: str = "📦"
    category: str = "storage"
    enabled: bool = True
    is_system: bool = False
    scope: str = "user"

    def __init__(self, ai_model: Any = None, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the User Storage plugin."""
        super().__init__(ai_model=ai_model, config=config)

    def get_router(self) -> Optional[APIRouter]:
        """Return the user personal storage API router."""
        try:
            from src.api.router_user_storage import router
            return router
        except Exception as ex:
            logger.warning(f"Could not load User Storage router for plugin: {ex}")
            return None

    def get_actions(self) -> List[Dict[str, Any]]:
        """Return admin/management actions for user storage."""
        return [
            {
                "id": "storage_stats",
                "label": "Storage Statistics",
                "description": "View disk usage and document quotas across all users.",
                "params": [],
            },
        ]

    async def execute_action(self, action_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute user storage actions."""
        if action_id == "storage_stats":
            from src.user_manager import user_manager
            stats = user_manager.get_total_storage_stats() if hasattr(user_manager, "get_total_storage_stats") else {}
            return {"success": True, "stats": stats}
        return await super().execute_action(action_id, params)

    async def handle(self, message: str, **kwargs: Any) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle conversational queries about user personal storage."""
        yield {
            "status": "complete",
            "text": "User Storage plugin is active. Personal files and documents are sandboxed per user.",
        }
