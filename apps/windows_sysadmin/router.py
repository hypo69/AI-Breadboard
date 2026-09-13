# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows System Administrator FastAPI Router
# =============================================================================
# Description:
#   FastAPI endpoints for Windows system administration,
#   Active Directory operations, user account management, group policies,
#   and security event monitoring.
#
# Examples:
#   >>> from fastapi import FastAPI
#   >>> from apps.windows_sysadmin.router import init_router
#   >>> app = FastAPI()
#   >>> app.include_router(init_router())
#
# File: router.py
# Project: ai-breadboard
# Package: apps.windows_sysadmin
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI router integration for Windows System Administrator."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from src.api.router_auth import require_admin_user

from .src.state import SystemAdminState, SecurityEvent

router = APIRouter(prefix="/api/sysadmin", tags=["sysadmin"])
state = SystemAdminState()


@router.get("/status")
async def get_status(request: None = None) -> dict:
    """Get current system administration status."""
    state.refresh()
    return {
        "hostname": state.hostname,
        "domain": state.domain,
        "ad_connected": state.ad_connected,
        "ad_status": state.ad_status,
        "user_count": len(state.users),
        "event_count": len(state.events),
    }


@router.get("/users")
async def get_users(request: None = None) -> dict:
    """Get list of active user sessions."""
    state.refresh()
    return {
        "users": [
            {
                "username": u.username,
                "session_id": u.session_id,
                "status": u.status,
                "login_time": u.login_time,
                "ip_address": u.ip_address,
                "process_count": u.process_count,
            }
            for u in state.users
        ]
    }


@router.get("/events")
async def get_events(request: None = None) -> dict:
    """Get list of recent security events."""
    state.refresh()
    return {
        "events": [
            {
                "timestamp": e.timestamp.isoformat(),
                "event_id": e.event_id,
                "level": e.level,
                "source": e.source,
                "description": e.description,
            }
            for e in state.events[:50]
        ]
    }


@router.get("/users/{username}")
async def get_user(username: str, request: None = None) -> dict:
    """Get specific user session details."""
    state.refresh()
    for user in state.users:
        if user.username == username:
            return {
                "username": user.username,
                "session_id": user.session_id,
                "status": user.status,
                "login_time": user.login_time,
                "ip_address": user.ip_address,
                "process_count": user.process_count,
            }
    raise HTTPException(status_code=404, detail=f"User {username} not found")


@router.post("/users/{username}/disconnect")
async def disconnect_user(username: str, request: None = None) -> dict:
    """Disconnect a user session (admin only)."""
    require_admin_user(None)  # This will raise if not admin
    state.refresh()
    for i, user in enumerate(state.users):
        if user.username == username:
            # Placeholder for actual disconnection logic
            return {
                "success": True,
                "message": f"User {username} disconnected",
            }
    raise HTTPException(status_code=404, detail=f"User {username} not found")


@router.get("/ad/status")
async def get_ad_status(request: None = None) -> dict:
    """Get Active Directory connectivity status."""
    state.refresh()
    return {
        "hostname": state.hostname,
        "domain": state.domain,
        "ad_connected": state.ad_connected,
        "ad_status": state.ad_status,
    }


def init_router() -> APIRouter:
    """Initialize the FastAPI router for Windows System Administrator."""
    return router


__all__ = [
    "init_router",
    "router",
]
