# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Base Plugin Interface Definition
# =============================================================================
# Description:
#   Provides the foundational abstract base class for all modular plugins in the
#   AI Breadboard platform, defining lifecycle, metadata, actions, and handling.
#
# File: base.py
# Project: ai-breadboard
# Package: plugins
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Base plugin module for modular extension system.

Defines the BasePlugin abstract interface that all AI Breadboard plugins must
inherit from to ensure seamless lifecycle management, configuration, action
execution, and AI routing.
"""

from __future__ import annotations

import abc
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional

from src.logger import logger


class BasePlugin(abc.ABC):
    """Abstract base class for all system plugins.

    Attributes:
        name (str): Unique machine-readable identifier for the plugin.
        title (str): Human-readable display title.
        version (str): Semantic version string of the plugin.
        description (str): Short summary of the plugin's responsibilities.
        icon (str): Emoji or icon identifier representing the plugin.
        category (str): Functional category (e.g., 'communication', 'media', 'tools').
        enabled (bool): Current active status of the plugin.
        ai_model (Any): Optional AI model instance passed for inference.
        config (Dict[str, Any]): Plugin runtime configuration dictionary.
    """

    name: str = "base_plugin"
    title: str = "Base Plugin"
    version: str = "1.0.0"
    description: str = "Base plugin interface."
    icon: str = "🧩"
    category: str = "general"
    enabled: bool = True

    def __init__(self, ai_model: Any = None, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the plugin instance.

        Args:
            ai_model (Any): Optional language or multimodal AI model instance.
            config (Optional[Dict[str, Any]]): Initial configuration overrides.
        """
        self.ai_model: Any = ai_model
        self.config: Dict[str, Any] = config or {}
        self.is_running: bool = False

    def get_manifest(self) -> Dict[str, Any]:
        """Return the plugin manifest schema and metadata.

        Returns:
            Dict[str, Any]: Dictionary containing plugin metadata, status,
                actions, tools, and configurable fields.
        """
        return {
            "name": self.name,
            "title": self.title,
            "version": self.version,
            "description": self.description,
            "icon": self.icon,
            "category": self.category,
            "enabled": self.enabled,
            "is_running": self.is_running,
            "actions": self.get_actions(),
            "tools": self.get_tools(),
            "fields": self.get_config_fields(),
            "config": self.config,
        }

    def get_tools(self) -> List[Dict[str, Any]]:
        """Return list of LLM function calling tool definitions.

        Returns:
            List[Dict[str, Any]]: Tool declarations adhering to standard tool schemas.
        """
        return []

    def get_actions(self) -> List[Dict[str, Any]]:
        """Return list of executable admin actions exposed to the web UI.

        Returns:
            List[Dict[str, Any]]: Action descriptor dictionaries.
        """
        return []

    def get_config_fields(self) -> List[Dict[str, Any]]:
        """Return UI configuration field specifications.

        Returns:
            List[Dict[str, Any]]: List of field descriptors (id, label, type, default, etc.).
        """
        return []

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update runtime configuration dictionary.

        Args:
            new_config (Dict[str, Any]): Key-value pairs to merge into config.
        """
        self.config.update(new_config)
        logger.info(f"Plugin '{self.name}' configuration updated.")

    async def start(self) -> None:
        """Start the plugin background workers and services.

        Subclasses should override this method to perform initialization logic.
        """
        self.is_running = True
        logger.info(f"Plugin '{self.name}' started.")

    async def stop(self) -> None:
        """Stop running background workers and release resources.

        Subclasses should override this method to perform clean shutdown logic.
        """
        self.is_running = False
        logger.info(f"Plugin '{self.name}' stopped.")

    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check and return diagnostic information.

        Returns:
            Dict[str, Any]: Health status dictionary with timestamps and states.
        """
        return {
            "name": self.name,
            "enabled": self.enabled,
            "is_running": self.is_running,
            "status": "healthy" if self.enabled else "disabled",
            "last_check": datetime.utcnow().isoformat(),
        }

    async def execute_action(self, action_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a declared admin action by identifier.

        Args:
            action_id (str): Unique identifier of the action to execute.
            params (Optional[Dict[str, Any]]): Parameters for the action.

        Returns:
            Dict[str, Any]: Execution result containing status and payload.
        """
        return {
            "success": False,
            "error": f"Action '{action_id}' is not implemented on plugin '{self.name}'.",
        }

    @abc.abstractmethod
    async def handle(self, message: str, **kwargs: Any) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle incoming request or message stream.

        Args:
            message (str): Incoming message or user prompt.
            **kwargs (Any): Additional context parameters.

        Yields:
            Dict[str, Any]: Streamed output events and result chunks.
        """
        yield {"status": "complete", "text": ""}
