# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Google Drive Sync Plugin Main Controller
# =============================================================================
# Description:
#   Main plugin adapter for Google Drive synchronization, managing scheduled
#   and manual backups of system databases, RAG indices, configs, and user files.
#
# File: plugin.py
# Project: ai-breadboard
# Package: plugins.gdrive_sync
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

from typing import Any, AsyncGenerator, Dict, List, Optional
from fastapi import APIRouter

from plugins.base import BasePlugin
from logger import logger


class GDriveSyncPlugin(BasePlugin):
    """Modular plugin providing Google Drive cloud synchronization and backup.

    Attributes:
        name (str): 'gdrive_sync'.
        title (str): 'Google Drive Sync'.
        version (str): '1.0.0'.
        description (str): Functional summary.
        icon (str): '🔄'.
        category (str): 'cloud'.
    """

    name: str = "gdrive_sync"
    title: str = "Google Drive Sync"
    title_i18n: Dict[str, str] = {
        "en": "Google Drive Sync & Backup",
        "ru": "Синхронизация и бэкап в Google Drive",
    }
    version: str = "1.0.0"
    description: str = "Automated and manual synchronization of databases, configs, RAG indices, and files to Google Drive."
    description_i18n: Dict[str, str] = {
        "en": "Automated and manual synchronization of databases, configs, RAG indices, and files to Google Drive.",
        "ru": "Автоматическая и ручная синхронизация баз данных, конфигураций, RAG индексов и файлов на Google Drive.",
    }
    icon: str = "🔄"
    category: str = "cloud"
    enabled: bool = True
    is_system: bool = True
    scope: str = "system"

    def __init__(self, ai_model: Any = None, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the Google Drive Sync plugin."""
        super().__init__(ai_model=ai_model, config=config)

    def get_router(self) -> Optional[APIRouter]:
        """Return the Google Drive Sync FastAPI router."""
        try:
            from src.api.router_sync import router
            return router
        except Exception as ex:
            logger.warning(f"Could not load Sync router for plugin: {ex}")
            return None

    def get_actions(self) -> List[Dict[str, Any]]:
        """Return admin actions for Google Drive sync."""
        return [
            {
                "id": "manual_sync",
                "label": "Run Manual Sync",
                "description": "Trigger immediate synchronization of all modified files to Google Drive.",
                "params": [
                    {"name": "sync_type", "type": "string", "default": "all", "label": "Sync Type (all, data, logs, configs)"}
                ],
            },
            {
                "id": "sync_status",
                "label": "Check Sync Status",
                "description": "Retrieve current sync scheduler status and last run timestamps.",
                "params": [],
            },
        ]

    async def execute_action(self, action_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute sync admin actions."""
        params = params or {}
        try:
            from src.integrations.sync_scheduler import get_scheduler
            scheduler = get_scheduler()
            if action_id == "sync_status":
                return {
                    "success": True,
                    "is_running": scheduler.is_running if scheduler else False,
                    "last_sync": str(getattr(scheduler, "last_sync_time", None)),
                }
            if action_id == "manual_sync":
                sync_type = params.get("sync_type", "all")
                if scheduler:
                    res = await scheduler.manual_sync(sync_type=sync_type)
                    return {"success": True, "result": res}
                return {"success": False, "error": "Sync scheduler not initialized"}
        except Exception as ex:
            return {"success": False, "error": str(ex)}

        return await super().execute_action(action_id, params)

    async def handle(self, message: str, **kwargs: Any) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle conversational queries about Google Drive sync."""
        yield {
            "status": "complete",
            "text": "Google Drive Sync plugin is active. Scheduled backups are managed automatically.",
        }
