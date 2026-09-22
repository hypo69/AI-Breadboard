# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: IFTTT Maker Webhook Connector and Dispatcher
# =============================================================================
# Description:
#   Provides an asynchronous client to trigger smart home events via the IFTTT Webhooks
#   Maker service with custom parameters and JSON payloads.
#
# Examples:
#   >>> client = IFTTTClient()
#   >>> result = await client.trigger_event("living_room_lights_on", value1="warm_white")
#   >>> print(result["status"])
#
# File: client.py
# Project: ai-breadboard
# Package: plugins.ifttt
# Module: plugins.ifttt.client
# Class: IFTTTClient
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

import aiohttp

from header import __root__
from logger import logger
from src.utils.jjson import j_loads_ns


class IFTTTClient:
    """Asynchronous client for interacting with the IFTTT Webhook Maker Channel.

    Attributes:
        webhook_key (str): Default IFTTT Webhooks Maker key.
        base_url (str): Base URL for IFTTT Maker Webhooks.
        timeout_seconds (int): Network request timeout in seconds.
    """

    def __init__(
        self,
        webhook_key: str = "",
        config_path: Path = Path("config.json"),
        timeout_seconds: int = 10,
    ) -> None:
        """Initialization of IFTTTClient with key and configuration parameters.

        Args:
            webhook_key (str): Optional override for the IFTTT Webhooks API key.
            config_path (Path): Path to configuration file. Defaults to 'config.json'.
            timeout_seconds (int): Maximum HTTP timeout in seconds. Defaults to 10.
        """
        self.timeout_seconds: int = timeout_seconds
        self.base_url: str = "https://maker.ifttt.com/trigger"

        # Load key from environment or configuration
        env_key = os.environ.get("IFTTT_WEBHOOK_KEY", "") or os.environ.get("IFTTT_KEY", "")
        if webhook_key:
            self.webhook_key: str = webhook_key
        elif env_key:
            self.webhook_key = env_key
        else:
            cfg = j_loads_ns(__root__ / config_path)
            ifttt_cfg = getattr(cfg, "ifttt", object())
            self.webhook_key = getattr(ifttt_cfg, "webhook_key", "")

        logger.debug(f"[IFTTTClient] Initialized with key configured: {bool(self.webhook_key)}")

    def is_configured(self) -> bool:
        """Return True if IFTTT webhook key is set."""
        return bool(self.webhook_key)

    def get_status(self) -> Dict[str, Any]:
        """Check status and readiness of IFTTT client.

        Returns:
            Dict[str, Any]: Status summary dictionary.

        Examples:
            >>> client = IFTTTClient()
            >>> status = client.get_status()
            >>> status["configured"]
            True
        """
        configured: bool = self.is_configured()
        return {
            "configured": configured,
            "masked_key": f"{self.webhook_key[:4]}...{self.webhook_key[-4:]}" if len(self.webhook_key) >= 8 else ("configured" if configured else "not_configured"),
            "base_url": self.base_url,
        }

    async def test_connection(self) -> Dict[str, Any]:
        """Test connectivity and key validity by sending a ping event.

        Returns:
            Dict[str, Any]: Connection test result.
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "IFTTT_WEBHOOK_KEY is missing or not configured in .env or plugin config.",
            }
        result = await self.trigger_event(event_name="ping", value1="AI-Breadboard Connection Test")
        if result.get("status") == "success":
            return {
                "success": True,
                "message": f"Connection to IFTTT Maker Webhooks verified (HTTP {result.get('http_code')}).",
                "data": result,
            }
        return {
            "success": False,
            "error": result.get("error", "Failed to contact IFTTT Maker Webhooks"),
            "data": result,
        }

    async def trigger_event(
        self,
        event_name: str,
        value1: str = "",
        value2: str = "",
        value3: str = "",
        json_payload: Dict[str, Any] = {},
        webhook_key: str = "",
    ) -> Dict[str, Any]:
        """Trigger an IFTTT Webhook event with values or structured JSON payload.

        Args:
            event_name (str): The name of the IFTTT Webhook event to trigger.
            value1 (str): Optional first value passed to the applet.
            value2 (str): Optional second value passed to the applet.
            value3 (str): Optional third value passed to the applet.
            json_payload (Dict[str, Any]): Optional arbitrary JSON payload sent to /json endpoint.
            webhook_key (str): Optional override key for this specific call.

        Returns:
            Dict[str, Any]: Execution result containing 'status', 'event', 'response', or 'error'.

        Examples:
            >>> client = IFTTTClient(webhook_key="test_key")
            >>> res = await client.trigger_event("turn_light_on", value1="bedroom")
            >>> res["status"]
            'success'
        """
        if not event_name:
            logger.warning("[IFTTTClient] Attempted to trigger event with empty event_name.")
            return {
                "status": "error",
                "error": "event_name cannot be empty",
                "event": "",
            }

        active_key = webhook_key or self.webhook_key
        if not active_key:
            logger.error("[IFTTTClient] IFTTT Webhook key is not configured.")
            return {
                "status": "error",
                "error": "IFTTT_WEBHOOK_KEY is not set. Please set it in .env or config.json.",
                "event": event_name,
            }

        # Select endpoint format
        if json_payload:
            endpoint = f"{self.base_url}/{event_name}/json/with/key/{active_key}"
            payload_data = json_payload
        else:
            endpoint = f"{self.base_url}/{event_name}/with/key/{active_key}"
            payload_data = {}
            if value1:
                payload_data["value1"] = value1
            if value2:
                payload_data["value2"] = value2
            if value3:
                payload_data["value3"] = value3

        logger.info(f"[IFTTTClient] Dispatching event '{event_name}' to IFTTT Maker Webhooks.")

        timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    endpoint,
                    json=payload_data,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    resp_text = await response.text()
                    if response.status == 200:
                        logger.info(f"[IFTTTClient] Event '{event_name}' triggered successfully: {resp_text.strip()}")
                        return {
                            "status": "success",
                            "event": event_name,
                            "http_code": response.status,
                            "message": resp_text.strip(),
                        }
                    else:
                        logger.error(f"[IFTTTClient] Event '{event_name}' failed with status {response.status}: {resp_text}")
                        return {
                            "status": "error",
                            "event": event_name,
                            "http_code": response.status,
                            "error": resp_text.strip(),
                        }
        except Exception as e:
            logger.error(f"[IFTTTClient] Exception while triggering event '{event_name}': {e}")
            return {
                "status": "error",
                "event": event_name,
                "error": str(e),
            }


async def send_ifttt_event(
    event_name: str,
    value1: str = "",
    value2: str = "",
    value3: str = "",
    json_payload: Dict[str, Any] = {},
    webhook_key: str = "",
) -> Dict[str, Any]:
    """Convenience helper function to trigger an IFTTT event.

    Args:
        event_name (str): IFTTT Maker event name.
        value1 (str): First value parameter.
        value2 (str): Second value parameter.
        value3 (str): Third value parameter.
        json_payload (Dict[str, Any]): Arbitrary JSON data payload.
        webhook_key (str): Optional override key.

    Returns:
        Dict[str, Any]: Result dictionary.

    Examples:
        >>> result = await send_ifttt_event("air_conditioner_cool", value1="22C")
        >>> result["status"]
        'success'
    """
    client = IFTTTClient(webhook_key=webhook_key)
    return await client.trigger_event(
        event_name=event_name,
        value1=value1,
        value2=value2,
        value3=value3,
        json_payload=json_payload,
    )
