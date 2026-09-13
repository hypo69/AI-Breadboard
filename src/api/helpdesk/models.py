# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Helpdesk Data Models and Schemas
# =============================================================================
# Description:
#   Pydantic data validation schemas for support tickets, replies, status
#   updates, priority configuration, and operator metadata.
#
# File: models.py
# Project: ai-breadboard
# Package: src.api.helpdesk
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


class HelpdeskUser(BaseModel):
    """User context within the helpdesk subsystem."""
    id: str
    username: str
    display_name: str
    email: Optional[str] = None
    role: str = "user"  # 'user', 'operator', 'admin'


class CreateTicketRequest(BaseModel):
    """Payload schema for creating a new support ticket."""
    subject: str = Field(..., min_length=2, max_length=200, description="Short summary of the issue")
    message: str = Field(..., min_length=2, description="Detailed problem description or question")
    category: Optional[str] = Field("general", description="Category: general, technical, billing, bug, ai_query")
    priority: Optional[Literal["low", "normal", "high", "urgent"]] = Field("normal", description="Initial priority")
    user_name: Optional[str] = None
    user_email: Optional[str] = None


class SendTicketMessageRequest(BaseModel):
    """Payload schema for adding a response or note to a ticket."""
    content: str = Field(..., min_length=1, description="Message text or reply")
    is_internal_note: Optional[bool] = Field(False, description="Whether this message is visible only to operators")
    sender_type: Optional[Literal["user", "operator", "system", "ai"]] = "user"


class UpdateTicketStatusRequest(BaseModel):
    """Payload schema for modifying ticket status, priority, or operator assignment."""
    status: Optional[Literal["open", "in_progress", "pending", "resolved", "closed"]] = None
    priority: Optional[Literal["low", "normal", "high", "urgent"]] = None
    assigned_to: Optional[str] = None
    assigned_name: Optional[str] = None


class TicketMessageItem(BaseModel):
    """Schema representing an individual message inside a ticket conversation."""
    id: str
    ticket_id: str
    sender_id: str
    sender_name: str
    sender_type: str
    message_type: str
    content: str
    is_internal_note: bool
    created_at: str


class HelpdeskTicketItem(BaseModel):
    """Detailed summary of a Helpdesk support ticket."""
    id: str
    ticket_number: int
    user_id: str
    user_name: str
    user_email: Optional[str] = None
    subject: str
    category: str
    status: str
    priority: str
    assigned_to: Optional[str] = None
    assigned_name: Optional[str] = None
    created_at: str
    updated_at: str
    closed_at: Optional[str] = None
    messages_count: Optional[int] = 0
    last_message: Optional[TicketMessageItem] = None


class HelpdeskStats(BaseModel):
    """Aggregate statistics for Helpdesk overview."""
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    closed_tickets: int
    urgent_tickets: int
