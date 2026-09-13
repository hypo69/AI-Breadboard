# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: User telemetry and activity tracking router
# =============================================================================
# Description:
#   Collects, batches, and forwards user activity telemetry (tab navigation,
#   UI interaction clicks, and dwell duration) strictly for registered users.
#   Supports asynchronous forwarding to central machine over Ngrok tunnels.
#
# File: router_telemetry.py
# Project: ai-breadboard
# Package: src.api
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from pydantic import BaseModel, Field

from src.logger import logger
from src.system.ngrok_tunnel import ngrok_manager
from src.user_manager import user_manager

router = APIRouter(prefix='/api/telemetry', tags=['telemetry'])


class TelemetryEvent(BaseModel):
    """Model representing an individual UI interaction or telemetry event."""
    action: str = Field(..., description="Action title or event descriptor")
    event_type: str = Field(default="action", description="Event category: tab_view, click, action, navigation")
    tab_name: Optional[str] = Field(default="", description="Tab identifier or URL segment")
    target_element: Optional[str] = Field(default="", description="Interacted element selector or text")
    duration_ms: Optional[int] = Field(default=0, description="Dwell time or action duration in milliseconds")
    details: Optional[Any] = Field(default=None, description="Arbitrary metadata dictionary or string")
    timestamp: Optional[str] = Field(default=None, description="Client-side ISO timestamp")


class TelemetryBatchRequest(BaseModel):
    """Batch container for incoming telemetry events."""
    events: List[TelemetryEvent] = Field(..., description="List of telemetry events")
    session_id: Optional[str] = Field(default="", description="Client session identifier")
    user_id: Optional[int] = Field(default=None, description="Client asserted user ID")


def _get_authenticated_user_id(request: Request) -> Optional[int]:
    """Retrieve authenticated registered user ID or None.

    Args:
        request (Request): FastAPI request object.

    Returns:
        Optional[int]: Registered user ID or None if anonymous/unauthenticated.
    """
    from src.api.router_auth import verify_jwt_token

    # Check auth cookie
    token = request.cookies.get('auth_token', '')
    if not token:
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:].strip()

    if token:
        user_data = verify_jwt_token(token)
        if user_data:
            if user_data.id:
                return user_data.id
            db_user = user_manager.get_user_by_email(user_data.email)
            if db_user and 'id' in db_user:
                return db_user['id']

    # Local development auto-authenticated user (ID: 1)
    hostname = request.url.hostname or ''
    is_local = (
        hostname in ('127.0.0.1', 'localhost', '::1', 'testserver', '0.0.0.0')
        or hostname.startswith('192.168.')
        or hostname.startswith('10.')
        or hostname.startswith('172.')
    )
    if is_local:
        # Check if local user 1 exists
        user1 = user_manager.get_user_by_id(1)
        if user1 and user1.get('is_active', 1):
            return 1

    return None


def _forward_events_to_central_collector(
    central_url: str,
    payload: Dict[str, Any],
    client_ip: str,
    user_agent: str
) -> None:
    """Asynchronously forward telemetry events to a remote central collector over Ngrok/HTTPS.

    Args:
        central_url (str): Remote central endpoint base URL.
        payload (Dict[str, Any]): Telemetry payload.
        client_ip (str): Originating client IP.
        user_agent (str): Originating User-Agent.
    """
    endpoint = central_url.rstrip('/') + '/api/telemetry/events'
    headers = {
        'User-Agent': user_agent,
        'X-Forwarded-For': client_ip,
        'X-AI-Breadboard-Forward': 'true',
        'Content-Type': 'application/json'
    }
    try:
        resp = requests.post(endpoint, json=payload, headers=headers, timeout=5.0)
        if resp.status_code >= 400:
            logger.warning(f"Failed to forward telemetry to {endpoint}: status {resp.status_code}")
    except Exception as ex:
        logger.debug(f"Telemetry forwarding failed to {endpoint}: {ex}")


@router.post('/events')
async def track_telemetry_events(
    request: Request,
    batch: TelemetryBatchRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Ingest a batch of user activity events strictly for registered users.

    Args:
        request (Request): FastAPI request object.
        batch (TelemetryBatchRequest): Telemetry batch payload.
        background_tasks (BackgroundTasks): Background worker for remote forwarding.

    Returns:
        Dict[str, Any]: Ingestion status and count of recorded events.
    """
    user_id = _get_authenticated_user_id(request)
    if not user_id:
        # Ignore telemetry from non-registered users
        return {
            "status": "ignored",
            "reason": "unauthenticated_user",
            "inserted": 0
        }

    client_ip = request.client.host if request.client else ""
    user_agent = request.headers.get("user-agent", "")

    events_data = [ev.model_dump() for ev in batch.events]
    inserted_count = user_manager.log_telemetry_batch(
        user_id=user_id,
        events=events_data,
        ip_address=client_ip,
        user_agent=user_agent
    )

    # Check if this local node is configured to forward telemetry to central machine
    forward_url = (
        os.getenv("CENTRAL_TELEMETRY_URL")
        or os.getenv("NGROK_TUNNEL_URL")
        or os.getenv("REMOTE_TELEMETRY_URL")
    )
    is_forwarded_call = request.headers.get("X-AI-Breadboard-Forward") == "true"

    if forward_url and forward_url.startswith("http") and not is_forwarded_call:
        payload = batch.model_dump()
        payload["user_id"] = user_id
        background_tasks.add_task(
            _forward_events_to_central_collector,
            forward_url,
            payload,
            client_ip,
            user_agent
        )

    return {
        "status": "ok",
        "user_id": user_id,
        "inserted": inserted_count
    }


@router.get('/stats')
async def get_telemetry_statistics(
    request: Request,
    days: int = Query(default=30, ge=1, le=365, description="Number of previous days to aggregate"),
    user_id: Optional[int] = Query(default=None, description="Optional user ID filter")
) -> Dict[str, Any]:
    """Retrieve aggregated user telemetry statistics.

    Args:
        request (Request): FastAPI request object.
        days (int): Number of days to aggregate.
        user_id (Optional[int]): Optional user ID filter.

    Returns:
        Dict[str, Any]: Telemetry statistics report.
    """
    caller_id = _get_authenticated_user_id(request)
    if not caller_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    # If non-admin requests stats, restrict to their own user ID
    if not user_manager.is_admin(caller_id):
        user_id = caller_id

    stats = user_manager.get_telemetry_stats(days=days, user_id=user_id)
    tunnel_status = ngrok_manager.get_status()
    stats["tunnel_status"] = tunnel_status
    return stats


@router.get('/tunnel-status')
async def get_tunnel_status() -> Dict[str, Any]:
    """Query current Ngrok tunnel and forwarding status.

    Returns:
        Dict[str, Any]: Ngrok tunnel active status, public URL, and port.
    """
    return ngrok_manager.get_status()


def init_router() -> APIRouter:
    """Factory creating telemetry router instance.

    Returns:
        APIRouter: Configured telemetry APIRouter.
    """
    return router
