# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: IFTTT FastApi Router and Webhook Endpoints
# =============================================================================
# Description:
#   Provides FastAPI endpoints for triggering outbound IFTTT Webhook events,
#   checking configuration status, and receiving incoming triggers from IFTTT applets.
#
# Examples:
#   >>> from fastapi import FastAPI
#   >>> from src.fastapi.router_ifttt import init_router
#   >>> app = FastAPI()
#   >>> app.include_router(init_router())
#
# File: router_ifttt.py
# Project: ai-breadboard
# Package: src.fastapi
# Module: src.fastapi.router_ifttt
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from plugins.ifttt.client import IFTTTClient
from src.logger import logger


class IFTTTTriggerRequest(BaseModel):
    """Schema for triggering an outbound IFTTT webhook."""
    value1: str = Field(default="", description="First value parameter")
    value2: str = Field(default="", description="Second value parameter")
    value3: str = Field(default="", description="Third value parameter")
    payload: Dict[str, Any] = Field(default={}, description="Arbitrary JSON payload for /json endpoint")
    webhook_key: str = Field(default="", description="Optional custom IFTTT Webhooks Maker key")


class IFTTTInboundResponse(BaseModel):
    """Schema for responding to inbound webhook events."""
    status: str = "received"
    event: str
    message: str = "Event accepted by AI Breadboard"


def init_router() -> APIRouter:
    """Initialize and return the IFTTT FastAPI router.

    Returns:
        APIRouter: Configured router with IFTTT endpoints.

    Examples:
        >>> router = init_router()
        >>> router.prefix
        '/api/ifttt'
    """
    router = APIRouter(prefix="/api/ifttt", tags=["IFTTT & Smart Home"])

    @router.get("/status")
    async def get_ifttt_status() -> Dict[str, Any]:
        """Get the current configuration and operational status of IFTTT integration."""
        client = IFTTTClient()
        return client.get_status()

    @router.post("/trigger/{event_name}")
    async def trigger_event(event_name: str, body: Optional[IFTTTTriggerRequest] = None) -> Dict[str, Any]:
        """Trigger an outbound IFTTT event with optional parameters.

        Args:
            event_name: Name of the IFTTT Maker Webhook event.
            body: Optional trigger parameters.
        """
        req = body or IFTTTTriggerRequest()
        client = IFTTTClient(webhook_key=req.webhook_key)
        result = await client.trigger_event(
            event_name=event_name,
            value1=req.value1,
            value2=req.value2,
            value3=req.value3,
            json_payload=req.payload,
            webhook_key=req.webhook_key,
        )
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("error", "Trigger failed"))
        return result

    @router.post("/webhook/{event_name}")
    async def receive_inbound_webhook(event_name: str, request: Request) -> IFTTTInboundResponse:
        """Receive an inbound webhook trigger from an external IFTTT applet.

        Args:
            event_name: Event identifier sent by the IFTTT applet.
            request: Raw request containing JSON or form data.
        """
        try:
            data = await request.json()
        except Exception:
            data = {}

        logger.info(f"[router_ifttt] Inbound IFTTT webhook received for event '{event_name}': {data}")

        # Optional processing hook: notify assistants or log events
        return IFTTTInboundResponse(
            status="received",
            event=event_name,
            message=f"Event '{event_name}' received successfully with {len(data)} fields",
        )

    return router
