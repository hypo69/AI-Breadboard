# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Facebook Publisher Plugin Main Controller
# =============================================================================
# Description:
#   Main plugin adapter class for Facebook publishing in AI Breadboard,
#   implementing BasePlugin interface, lifecycle management, LLM function calling
#   tools, admin actions, and conversational streaming.
#
# File: plugin.py
# Project: ai-breadboard
# Package: plugins.facebook
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Facebook publisher plugin implementation module.

Extends BasePlugin to provide Facebook Graph API lifecycle management, UI configuration,
admin actions (test_connection/publish_post/get_page_info), and LLM function calling tools.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

from src.logger import logger
from plugins.base import BasePlugin
from plugins.facebook.client import FacebookGraphClient


class FacebookPlugin(BasePlugin):
    """Modular plugin providing Facebook publishing and Graph API integration.

    Attributes:
        name (str): 'facebook'.
        title (str): 'Facebook Publisher'.
        version (str): '1.0.0'.
        description (str): Functional summary of the plugin.
        icon (str): '📘'.
        category (str): 'communication'.
        client (FacebookGraphClient): Underlying Facebook Graph API client.
    """

    name: str = "facebook"
    title: str = "Facebook Publisher"
    version: str = "1.0.0"
    description: str = "Publish posts, links, and photos to Facebook Pages and user feeds via Graph API."
    icon: str = "📘"
    category: str = "communication"
    enabled: bool = True
    is_system: bool = False
    scope: str = "user"

    def __init__(self, ai_model: Any = None, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the Facebook plugin.

        Args:
            ai_model (Any): Optional AI model instance.
            config (Optional[Dict[str, Any]]): Initial configuration overrides.
        """
        defaults = self._load_default_config()
        if config:
            defaults.update(config)

        # Environment variable overrides
        env_token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "").strip() or os.getenv("FACEBOOK_ACCESS_TOKEN", "").strip()
        env_page_id = os.getenv("FACEBOOK_PAGE_ID", "").strip()

        if not defaults.get("page_access_token") and env_token:
            defaults["page_access_token"] = env_token
        if not defaults.get("page_id") and env_page_id:
            defaults["page_id"] = env_page_id

        super().__init__(ai_model=ai_model, config=defaults)

        token = self.config.get("page_access_token") or self.config.get("user_access_token") or ""
        self.client: FacebookGraphClient = FacebookGraphClient(
            page_id=self.config.get("page_id", ""),
            access_token=token,
            api_version=self.config.get("api_version", "v19.0"),
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
                logger.error(f"FacebookPlugin: Error reading plugin config.json: {exc}")
        return {
            "page_id": "",
            "page_access_token": "",
            "user_access_token": "",
            "api_version": "v19.0",
            "default_target": "page",
        }

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update plugin configuration and refresh client credentials.

        Args:
            new_config (Dict[str, Any]): New configuration dictionary.
        """
        super().update_config(new_config)
        token = self.config.get("page_access_token") or self.config.get("user_access_token") or ""
        self.client.page_id = str(self.config.get("page_id", "")).strip()
        self.client.access_token = token.strip()
        self.client.api_version = str(self.config.get("api_version", "v19.0")).strip()
        self.client.base_url = f"https://graph.facebook.com/{self.client.api_version}"

    def get_tools(self) -> List[Dict[str, Any]]:
        """Return list of LLM function calling tool definitions.

        Returns:
            List[Dict[str, Any]]: Tool declarations adhering to standard tool schemas.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "post_to_facebook",
                    "description": "Publish a message, web link, or photo to a Facebook Page or user feed.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Text content of the post or photo caption.",
                            },
                            "link": {
                                "type": "string",
                                "description": "Optional web URL to attach as a rich link preview.",
                            },
                            "photo_url": {
                                "type": "string",
                                "description": "Optional public URL of an image/photo to upload.",
                            },
                            "page_id": {
                                "type": "string",
                                "description": "Optional target Facebook Page ID override.",
                            },
                        },
                        "required": ["message"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_facebook_page_info",
                    "description": "Retrieve metadata and follower metrics for the configured Facebook Page.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "page_id": {
                                "type": "string",
                                "description": "Optional Page ID to inspect (defaults to configured page_id).",
                            },
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_facebook_accounts",
                    "description": "List all Facebook Pages managed by the current user token.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                },
            },
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
                "description": "Verify Facebook Graph API token and target connectivity.",
            },
            {
                "id": "publish_post",
                "label": "Publish Post",
                "color": "success",
                "description": "Publish a new text/link post to the configured Facebook Page.",
            },
            {
                "id": "get_page_info",
                "label": "Get Page Info",
                "color": "primary",
                "description": "Retrieve information and statistics about the Facebook Page.",
            },
        ]

    def get_config_fields(self) -> List[Dict[str, Any]]:
        """Return UI configuration field specifications.

        Returns:
            List[Dict[str, Any]]: List of field descriptors.
        """
        return [
            {
                "id": "page_id",
                "label": "Facebook Page ID",
                "type": "string",
                "default": "",
                "description": "Target Facebook Page ID (numeric or page username).",
            },
            {
                "id": "page_access_token",
                "label": "Page Access Token",
                "type": "string",
                "default": "",
                "description": "Facebook Page Access Token with 'pages_manage_posts' and 'pages_read_engagement' permissions.",
            },
            {
                "id": "user_access_token",
                "label": "User Access Token (Optional)",
                "type": "string",
                "default": "",
                "description": "Facebook User Access Token for managing pages or personal feed publishing.",
            },
            {
                "id": "api_version",
                "label": "Graph API Version",
                "type": "string",
                "default": "v19.0",
                "description": "Facebook Graph API version tag (e.g. v19.0).",
            },
        ]

    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check and return diagnostic information.

        Returns:
            Dict[str, Any]: Health status dictionary with connection status.
        """
        base_status = await super().health_check()
        base_status.update(
            {
                "configured": self.client.is_configured(),
                "page_id": self.client.page_id,
                "api_version": self.client.api_version,
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
            if not self.client.is_configured():
                return {"success": False, "error": "Facebook Access Token is missing or not configured."}
            return await self.client.test_connection()

        if action_id == "publish_post":
            if not self.client.is_configured():
                return {"success": False, "error": "Facebook Access Token is missing or not configured."}
            message = params.get("message", "").strip()
            if not message:
                return {"success": False, "error": "Parameter 'message' cannot be empty."}

            link = params.get("link")
            photo_url = params.get("photo_url")
            page_id = params.get("page_id")

            if photo_url:
                res = await self.client.publish_photo(caption=message, photo_url=photo_url, page_id=page_id)
            else:
                res = await self.client.publish_post(message=message, link=link, page_id=page_id)

            if res.get("success"):
                return {
                    "success": True,
                    "message": f"Post published successfully (ID: {res.get('id')}).",
                    "id": res.get("id"),
                    "data": res.get("data"),
                }
            return {"success": False, "error": res.get("error", "Unknown publishing error.")}

        if action_id == "get_page_info":
            if not self.client.is_configured():
                return {"success": False, "error": "Facebook Access Token is missing or not configured."}
            target_page_id = params.get("page_id") or self.client.page_id or "me"
            res = await self.client.get_page_info(page_id=target_page_id)
            if res.get("success"):
                return {"success": True, "data": res.get("data")}
            return {"success": False, "error": res.get("error", "Failed to retrieve page info.")}

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
        configured_str = "Yes" if is_configured else "No"
        page_id_str = self.client.page_id or "Not set"

        reply = (
            f"📘 Facebook Publisher Status:\n"
            f"- Configured: {configured_str}\n"
            f"- Target Page ID: {page_id_str}\n"
            f"- Graph API Version: {self.client.api_version}\n"
        )
        yield {
            "status": "complete",
            "text": reply,
            "data": {
                "configured": is_configured,
                "page_id": self.client.page_id,
                "api_version": self.client.api_version,
            },
        }
