# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: IFTTT Smart Home Plugin Main Controller
# =============================================================================
# Description:
#   Main plugin adapter class for IFTTT Smart Home automation in AI Breadboard,
#   implementing BasePlugin interface, lifecycle management, LLM function calling
#   tools, admin actions, and conversational streaming.
#
# File: plugin.py
# Project: ai-breadboard
# Package: plugins.ifttt
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

from src.logger import logger
from plugins.base import BasePlugin
from plugins.ifttt.client import IFTTTClient


class IFTTTPlugin(BasePlugin):
    """Modular plugin providing IFTTT Maker Webhooks and Smart Home automation.

    Attributes:
        name (str): 'ifttt'.
        title (str): 'IFTTT Smart Home'.
        version (str): '1.0.0'.
        description (str): Functional summary of the plugin.
        icon (str): '🏠'.
        category (str): 'automation'.
        client (IFTTTClient): Underlying IFTTT Maker Webhooks client.
    """

    name: str = "ifttt"
    title: str = "IFTTT Smart Home"
    title_i18n: Dict[str, str] = {
        "en": "IFTTT Smart Home",
        "ru": "Умный дом IFTTT",
    }
    version: str = "1.0.0"
    description: str = "Automate and control smart home devices, scenes, climate, and alerts via IFTTT Maker Webhooks."
    description_i18n: Dict[str, str] = {
        "en": "Automate and control smart home devices, scenes, climate, and alerts via IFTTT Maker Webhooks.",
        "ru": "Автоматизация и управление устройствами умного дома, сценариями, климатом и оповещениями через IFTTT Maker Webhooks.",
    }
    icon: str = "🏠"
    category: str = "automation"
    enabled: bool = True
    is_system: bool = False
    scope: str = "user"

    def __init__(self, ai_model: Any = None, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the IFTTT plugin.

        Args:
            ai_model (Any): Optional AI model instance.
            config (Optional[Dict[str, Any]]): Initial configuration overrides.
        """
        defaults = self._load_default_config()
        if config:
            defaults.update(config)

        # Check environment variable for key override
        env_key = os.getenv("IFTTT_WEBHOOK_KEY", "").strip() or os.getenv("IFTTT_KEY", "").strip()
        if not defaults.get("webhook_key") and env_key:
            defaults["webhook_key"] = env_key

        super().__init__(ai_model=ai_model, config=defaults)

        timeout = int(self.config.get("timeout_seconds", 10))
        self.client: IFTTTClient = IFTTTClient(
            webhook_key=self.config.get("webhook_key", ""),
            timeout_seconds=timeout,
        )

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
                logger.error(f"IFTTTPlugin: Error reading plugin config.json: {exc}")
        return {
            "webhook_key": "",
            "timeout_seconds": 10,
        }

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update plugin configuration and refresh client key.

        Args:
            new_config (Dict[str, Any]): New configuration dictionary.
        """
        super().update_config(new_config)
        key = str(self.config.get("webhook_key", "")).strip()
        self.client.webhook_key = key
        self.client.timeout_seconds = int(self.config.get("timeout_seconds", 10))

    def get_tools(self) -> List[Dict[str, Any]]:
        """Return list of LLM function calling tool definitions for Smart Home triggers.

        Returns:
            List[Dict[str, Any]]: Tool declarations adhering to standard tool schemas.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "trigger_ifttt_event",
                    "description": "Trigger an IFTTT Webhook event to control smart home devices (lights, climate, scene, vacuum) or send alerts.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "event_name": {
                                "type": "string",
                                "description": "The exact IFTTT Webhook event name (e.g., 'living_room_lights_on', 'ac_cool', 'movie_mode', 'send_alert').",
                            },
                            "value1": {
                                "type": "string",
                                "description": "Optional first parameter value passed to the IFTTT applet.",
                            },
                            "value2": {
                                "type": "string",
                                "description": "Optional second parameter value passed to the IFTTT applet.",
                            },
                            "value3": {
                                "type": "string",
                                "description": "Optional third parameter value passed to the IFTTT applet.",
                            },
                            "json_payload": {
                                "type": "object",
                                "description": "Optional JSON payload object for advanced IFTTT applets.",
                            },
                        },
                        "required": ["event_name"],
                    },
                },
            }
        ]

    def get_actions(self) -> List[Dict[str, Any]]:
        """Return list of executable admin actions exposed to the web UI.

        Returns:
            List[Dict[str, Any]]: Action descriptor dictionaries.
        """
        return [
            {
                "id": "test_connection",
                "label": "Test Connection",
                "color": "info",
                "description": "Verify IFTTT Maker Webhooks key by triggering a ping event.",
            },
            {
                "id": "trigger_event",
                "label": "Trigger Event",
                "color": "success",
                "description": "Trigger a custom IFTTT smart home event directly.",
            },
        ]

    def get_config_fields(self) -> List[Dict[str, Any]]:
        """Return UI configuration field specifications.

        Returns:
            List[Dict[str, Any]]: List of field descriptors.
        """
        return [
            {
                "id": "webhook_key",
                "label": "IFTTT Webhook Maker Key",
                "type": "password",
                "default": "",
                "description": "Your secret IFTTT Webhooks Maker key from ifttt.com/maker_webhooks.",
            },
            {
                "id": "timeout_seconds",
                "label": "Request Timeout (Seconds)",
                "type": "number",
                "default": 10,
                "description": "Maximum seconds to wait for IFTTT webhook HTTP response.",
            },
        ]

    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check and return diagnostic information.

        Returns:
            Dict[str, Any]: Health status dictionary.
        """
        base_status = await super().health_check()
        base_status.update(
            {
                "configured": self.client.is_configured(),
                "base_url": self.client.base_url,
            }
        )
        return base_status

    async def execute_action(self, action_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute declared admin action by identifier.

        Args:
            action_id (str): Unique identifier of the action to execute.
            params (Optional[Dict[str, Any]]): Parameters for the action.

        Returns:
            Dict[str, Any]: Execution result containing status and payload.
        """
        params = params or {}

        if action_id == "test_connection":
            return await self.client.test_connection()

        if action_id == "trigger_event":
            event_name = params.get("event_name", "").strip()
            if not event_name:
                return {"success": False, "error": "Parameter 'event_name' is required."}
            res = await self.client.trigger_event(
                event_name=event_name,
                value1=params.get("value1", ""),
                value2=params.get("value2", ""),
                value3=params.get("value3", ""),
                json_payload=params.get("json_payload", {}),
            )
            if res.get("status") == "success":
                return {"success": True, "message": f"Event '{event_name}' triggered.", "data": res}
            return {"success": False, "error": res.get("error", "Failed to trigger event."), "data": res}

        return await super().execute_action(action_id, params)

    async def handle(self, message: str, **kwargs: Any) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle incoming chat messages or web UI stream.

        Args:
            message (str): Input prompt or command.
            **kwargs (Any): Additional context parameters.

        Yields:
            Dict[str, Any]: Streaming event objects.
        """
        yield {"status": "start", "plugin": self.name}
        is_configured = self.client.is_configured()
        configured_str = "Yes" if is_configured else "No (Set IFTTT_WEBHOOK_KEY in .env or plugin settings)"

        reply = (
            f"🏠 IFTTT Smart Home Plugin Status:\n"
            f"- Configured: {configured_str}\n"
            f"- Endpoint: {self.client.base_url}\n"
            f"- Ready to dispatch smart home events.\n"
        )
        yield {
            "status": "complete",
            "text": reply,
            "data": {
                "configured": is_configured,
                "base_url": self.client.base_url,
            },
        }
