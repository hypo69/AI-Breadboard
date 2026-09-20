# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: User Assistant FastAPI Router
# =============================================================================
# Description:
#   FastAPI REST API router for user assistant services: daily agenda, email triage,
#   calendar scheduling, and personal document search.
#
# File: router.py
# Package: apps.user_assistant
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from apps.user_assistant.engine import UserAssistantEngine
from src.logger import logger
from apps.common.csv_logger import AppCsvLogger

router = APIRouter(prefix="/api/v1/assistant", tags=["User Assistant"])
csv_logger = AppCsvLogger("user_assistant")


class DraftRequest(BaseModel):
    to: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body content")


class EventCreateRequest(BaseModel):
    summary: str = Field(..., description="Event title")
    start_time: str = Field(..., description="ISO datetime string")
    end_time: str = Field(..., description="ISO datetime string")
    description: Optional[str] = Field("", description="Event notes")
    location: Optional[str] = Field("", description="Location")


def _get_engine(request: Request) -> UserAssistantEngine:
    """Retrieve engine for current request user."""
    from src.api.router_auth import get_current_user_optional
    user = get_current_user_optional(request)
    user_id = getattr(user, "id", 1) if user else 1
    return UserAssistantEngine(user_id=user_id)


@router.get("/agenda")
async def get_agenda(request: Request) -> Dict[str, Any]:
    """Retrieve daily agenda overview (events, unread emails, recent files)."""
    engine = _get_engine(request)
    agenda = engine.get_daily_agenda()
    csv_logger.log_poll(
        poll_type="agenda",
        metric_name="agenda_events_count",
        value=len(agenda.get("events", [])),
        unit="count",
        status="ok",
        details=f"unread_mail={len(agenda.get('unread_emails', []))}",
        filename="user_assistant_polls.csv",
    )
    return agenda


@router.get("/mail")
async def list_mail(
    request: Request,
    query: str = Query("is:unread", description="Search query filter"),
    limit: int = Query(10, ge=1, le=50, description="Max messages"),
) -> Dict[str, Any]:
    """Search and retrieve user email messages."""
    engine = _get_engine(request)
    messages = engine.mail.list_messages(query=query, max_results=limit)
    csv_logger.log_poll(
        poll_type="mail",
        metric_name="messages_count",
        value=len(messages),
        unit="count",
        status="ok",
        details=f"query={query},limit={limit}",
        filename="user_assistant_polls.csv",
    )
    return {"status": "ok", "count": len(messages), "messages": messages}


@router.post("/mail/draft")
async def create_mail_draft(request: Request, body: DraftRequest) -> Dict[str, Any]:
    """Create a new email draft."""
    engine = _get_engine(request)
    res = engine.mail.create_draft(to=body.to, subject=body.subject, body=body.body)
    csv_logger.log_event(
        event_type="mail_draft_created",
        status="success" if res.get("status") == "ok" else "error",
        details=f"to={body.to},subject={body.subject}",
        filename="user_assistant_events.csv",
    )
    return res


@router.get("/calendar")
async def list_calendar_events(
    request: Request,
    days: int = Query(7, ge=1, le=30, description="Days forward to search"),
) -> Dict[str, Any]:
    """List upcoming calendar events."""
    engine = _get_engine(request)
    events = engine.calendar.list_upcoming_events(days_ahead=days)
    csv_logger.log_poll(
        poll_type="calendar",
        metric_name="upcoming_events_count",
        value=len(events),
        unit="count",
        status="ok",
        details=f"days_ahead={days}",
        filename="user_assistant_polls.csv",
    )
    return {"status": "ok", "count": len(events), "events": events}


@router.post("/calendar/event")
async def create_calendar_event(request: Request, body: EventCreateRequest) -> Dict[str, Any]:
    """Create a new calendar event."""
    engine = _get_engine(request)
    res = engine.calendar.create_event(
        summary=body.summary,
        start_time=body.start_time,
        end_time=body.end_time,
        description=body.description or "",
        location=body.location or "",
    )
    csv_logger.log_event(
        event_type="calendar_event_created",
        status="success" if res.get("status") == "ok" else "error",
        details=f"summary={body.summary},start={body.start_time}",
        filename="user_assistant_events.csv",
    )
    return res


@router.get("/documents")
async def list_documents(
    request: Request,
    subfolder: str = Query("files", description="User subfolder"),
) -> Dict[str, Any]:
    """List user personal document files."""
    engine = _get_engine(request)
    files = engine.docs.list_user_files(subfolder=subfolder)
    csv_logger.log_poll(
        poll_type="documents",
        metric_name="files_count",
        value=len(files),
        unit="count",
        status="ok",
        details=f"subfolder={subfolder}",
        filename="user_assistant_polls.csv",
    )
    return {"status": "ok", "count": len(files), "files": files}


def init_router() -> APIRouter:
    """Initialize and return User Assistant APIRouter instance."""
    return router
