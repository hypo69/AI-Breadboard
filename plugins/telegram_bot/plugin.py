# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Telegram Bot Plugin Main Controller
# =============================================================================
# Description:
#   Main plugin adapter class for Telegram bot integration in AI Breadboard,
#   implementing BasePlugin interface, lifecycle commands, and admin actions.
#
# File: plugin.py
# Project: ai-breadboard
# Package: plugins.telegram_bot
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Telegram bot plugin implementation module.

Extends BasePlugin to provide Telegram bot lifecycle management, UI configuration,
admin actions (start/stop/status/test_message), and conversational AI streaming.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

from header import __root__
from src.logger import logger
from plugins.base import BasePlugin
from plugins.telegram_bot.bot import TelegramBotEngine


class TelegramBotPlugin(BasePlugin):
    """Modular plugin providing full Telegram bot integration.

    Attributes:
        name (str): 'telegram_bot'.
        title (str): 'Telegram Bot & Mini App'.
        version (str): '1.0.0'.
        description (str): Functional summary of the plugin.
        icon (str): '🤖'.
        category (str): 'communication'.
        bot_engine (TelegramBotEngine): Underlying bot service engine.
    """

    name: str = "telegram_bot"
    title: str = "Telegram Bot & Mini App"
    version: str = "1.0.0"
    description: str = "Remote control, voice narration, notifications, and AI chat via Telegram."
    icon: str = "🤖"
    category: str = "communication"
    enabled: bool = True

    def __init__(self, ai_model: Any = None, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the Telegram bot plugin.

        Args:
            ai_model (Any): Optional AI model instance.
            config (Optional[Dict[str, Any]]): Initial configuration overrides.
        """
        # Load defaults from config.json in plugin directory
        defaults = self._load_default_config()
        if config:
            defaults.update(config)

        # Fallback token from environment variable if not in config
        env_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        if not defaults.get("token") and env_token:
            defaults["token"] = env_token

        super().__init__(ai_model=ai_model, config=defaults)

        # Parse admin IDs
        admin_ids = self._parse_admin_ids(self.config.get("admin_ids", []))

        # Instantiate engine
        self.bot_engine: TelegramBotEngine = TelegramBotEngine(
            token=self.config.get("token", ""),
            admin_ids=admin_ids,
            ai_model=self.ai_model,
            config=self.config,
        )
        self.plugins_registry: Dict[str, Any] = {}

    def set_plugins(self, plugins: Dict[str, Any]) -> None:
        """Store reference to all loaded plugins in system.

        Args:
            plugins (Dict[str, Any]): Dictionary of loaded plugins.
        """
        self.plugins_registry = plugins

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration from plugin config.json.

        Returns:
            Dict[str, Any]: Default configuration dictionary.
        """
        cfg_file = Path(__file__).parent / "config.json"
        if cfg_file.exists():
            try:
                return json.loads(cfg_file.read_text(encoding="utf-8"))
            except Exception as exc:
                logger.error(f"Error reading plugin config.json: {exc}")
        return {
            "token": "",
            "admin_ids": [],
            "notifications_enabled": True,
            "webhook_url": "",
            "api_base_url": "http://127.0.0.1:8000",
        }

    def _parse_admin_ids(self, raw_val: Any) -> List[int]:
        """Normalize admin IDs into list of integers.

        Args:
            raw_val (Any): Raw list or comma-separated string of IDs.

        Returns:
            List[int]: Parsed list of integer IDs.
        """
        if isinstance(raw_val, list):
            result = []
            for item in raw_val:
                try:
                    result.append(int(item))
                except (ValueError, TypeError):
                    pass
            return result
        if isinstance(raw_val, str):
            result = []
            for item in raw_val.replace(",", " ").split():
                try:
                    result.append(int(item))
                except (ValueError, TypeError):
                    pass
            return result
        return []

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update plugin configuration and propagate to bot engine.

        Args:
            new_config (Dict[str, Any]): New configuration dictionary.
        """
        super().update_config(new_config)
        token = self.config.get("token") or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.bot_engine.token = token.strip()
        self.bot_engine.admin_ids = self._parse_admin_ids(self.config.get("admin_ids", []))
        self.bot_engine.config = self.config

    def get_tools(self) -> List[Dict[str, Any]]:
        """Return function calling tools for AI routing."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "send_telegram_notification",
                    "description": "Send a notification or alert message to configured Telegram administrators.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Text message to deliver via Telegram.",
                            },
                        },
                        "required": ["message"],
                    },
                },
            }
        ]

    def get_actions(self) -> List[Dict[str, Any]]:
        """Return actions exposed to Admin Web Interface."""
        return [
            {
                "id": "start_bot",
                "label": "Start Bot",
                "color": "success",
                "description": "Start Telegram bot service polling loop.",
            },
            {
                "id": "stop_bot",
                "label": "Stop Bot",
                "color": "danger",
                "description": "Stop running Telegram bot service.",
            },
            {
                "id": "get_status",
                "label": "Check Status",
                "color": "info",
                "description": "Inspect live bot connection and status.",
            },
            {
                "id": "test_message",
                "label": "Test Message",
                "color": "warning",
                "description": "Send a test ping message to the first configured admin ID.",
            },
        ]

    def get_config_fields(self) -> List[Dict[str, Any]]:
        """Return schema of settings for Admin Web Interface."""
        return [
            {
                "id": "token",
                "label": "Telegram Bot Token",
                "type": "string",
                "default": "",
                "description": "API token obtained from @BotFather in Telegram.",
            },
            {
                "id": "admin_ids",
                "label": "Admin User IDs",
                "type": "list_string",
                "default": "",
                "description": "List of Telegram user IDs with administrative privileges (comma-separated).",
            },
            {
                "id": "notifications_enabled",
                "label": "Enable Notifications",
                "type": "boolean",
                "default": True,
                "description": "Allow system alerts and download notifications to be routed to Telegram.",
            },
            {
                "id": "api_base_url",
                "label": "FastAPI Base URL",
                "type": "string",
                "default": "http://127.0.0.1:8000",
                "description": "Base address for the local server used in Mini App URLs and TTS synthesis.",
            },
        ]

    async def start(self) -> None:
        """Start the plugin and underlying Telegram bot engine."""
        await super().start()
        if not self.bot_engine.is_configured():
            logger.warning(
                "TelegramBotPlugin: TELEGRAM_BOT_TOKEN is not set or invalid. Bot polling not started."
            )
            return

        try:
            await self.bot_engine.start()
        except Exception as exc:
            logger.error(f"TelegramBotPlugin: Failed to start bot engine: {exc}")

    async def stop(self) -> None:
        """Stop running Telegram bot engine and cleanup resources."""
        await self.bot_engine.stop()
        await super().stop()

    async def health_check(self) -> Dict[str, Any]:
        """Return health status of Telegram bot plugin."""
        base_status = await super().health_check()
        info = self.bot_engine.get_info()
        base_status.update(
            {
                "configured": info["configured"],
                "bot_running": info["running"],
                "bot_info": info["bot_info"],
            }
        )
        return base_status

    async def execute_action(self, action_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute admin action by ID.

        Args:
            action_id (str): ID of action.
            params (Optional[Dict[str, Any]]): Action arguments.

        Returns:
            Dict[str, Any]: Execution result dictionary.
        """
        params = params or {}

        if action_id == "start_bot":
            if self.bot_engine.is_running:
                return {"success": True, "message": "Bot is already running."}
            if not self.bot_engine.is_configured():
                return {"success": False, "error": "Bot token is missing or not configured."}
            try:
                await self.bot_engine.start()
                return {"success": True, "message": "Telegram bot started successfully."}
            except Exception as exc:
                return {"success": False, "error": str(exc)}

        if action_id == "stop_bot":
            if not self.bot_engine.is_running:
                return {"success": True, "message": "Bot is already stopped."}
            await self.bot_engine.stop()
            return {"success": True, "message": "Telegram bot stopped cleanly."}

        if action_id == "get_status":
            return {"success": True, "data": self.bot_engine.get_info()}

        if action_id == "test_message":
            if not self.bot_engine.is_configured():
                return {"success": False, "error": "Bot token not configured."}
            if not self.bot_engine.admin_ids:
                return {"success": False, "error": "No admin user IDs configured to receive test message."}

            target_id = self.bot_engine.admin_ids[0]
            try:
                if not self.bot_engine.app:
                    await self.bot_engine.initialize()
                if self.bot_engine.app:
                    await self.bot_engine.app.bot.send_message(
                        chat_id=target_id,
                        text="🔔 *AI Breadboard Test Ping*\nThis is a test notification from your server.",
                        parse_mode="Markdown",
                    )
                    return {"success": True, "message": f"Test message sent to Telegram ID {target_id}."}
                return {"success": False, "error": "Bot application could not be initialized."}
            except Exception as exc:
                return {"success": False, "error": f"Failed to send test message: {exc}"}

        return await super().execute_action(action_id, params)

    async def handle(self, message: str, **kwargs: Any) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle incoming chat messages or web UI stream.

        Args:
            message (str): Input prompt.
            **kwargs (Any): Extra context.

        Yields:
            Dict[str, Any]: Streaming event objects.
        """
        yield {"status": "start", "plugin": self.name}
        status_info = self.bot_engine.get_info()
        running_str = "Running" if status_info["running"] else "Stopped"
        configured_str = "Yes" if status_info["configured"] else "No"
        reply = (
            f"Telegram Bot Plugin Status:\n"
            f"- Configured: {configured_str}\n"
            f"- Status: {running_str}\n"
            f"- Admins: {status_info['admin_count']}\n"
        )
        yield {
            "status": "complete",
            "text": reply,
            "data": status_info,
        }
