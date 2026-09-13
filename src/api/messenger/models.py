# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Messenger Data Models and Validation Schemas
# =============================================================================
# Description:
#   Pydantic models and serialization contracts for chat rooms, real-time messages,
#   typing indicators, read receipts, WebRTC signaling events, and user profiles.
#
# File: models.py
# Project: ai-breadboard
# Package: src.api.messenger
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class MessengerUser(BaseModel):
    """User profile representation in the messenger domain."""
    id: str
    email: Optional[str] = None
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    source: str = "native"
    is_online: bool = False
    last_seen: Optional[datetime] = None
    created_at: Optional[datetime] = None


class AttachmentInfo(BaseModel):
    """Metadata for uploaded files, voice notes, and media attachments."""
    id: str
    message_id: Optional[str] = None
    file_name: str
    file_path: str
    file_type: str
    file_size: int = 0
    duration_sec: float = 0.0
    created_at: Optional[datetime] = None


class MessageItem(BaseModel):
    """Single message entity with sender info, status, and attachments."""
    id: str
    room_id: str
    sender_id: str
    sender_name: Optional[str] = None
    sender_avatar: Optional[str] = None
    message_type: str = "text"  # text, image, audio, video, file, system
    content: Optional[str] = ""
    reply_to_id: Optional[str] = None
    forward_from_id: Optional[str] = None
    status: str = "sent"  # sent, delivered, read
    is_edited: bool = False
    is_deleted: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    attachments: List[AttachmentInfo] = []


class ChatRoomSummary(BaseModel):
    """Chat room summary representation for sidebar dialogue listing."""
    id: str
    room_type: str  # direct, group, channel, meeting
    title: str
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    unread_count: int = 0
    last_message: Optional[MessageItem] = None
    members_count: int = 0
    is_online: Optional[bool] = False  # for direct chats


class CreateRoomRequest(BaseModel):
    """Payload for creating a new direct, group, or meeting room."""
    room_type: str = "direct"  # direct, group, channel, meeting
    title: Optional[str] = None
    description: Optional[str] = None
    member_ids: List[str] = Field(default_factory=list)


class SendMessageRequest(BaseModel):
    """Payload for posting a message via REST endpoint."""
    content: str
    message_type: str = "text"
    reply_to_id: Optional[str] = None
    attachment_ids: List[str] = Field(default_factory=list)


class UserSyncPayload(BaseModel):
    """Synchronization payload received from WordPress or external auth bridges."""
    id: str
    email: Optional[str] = None
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
    source: str = "wordpress"


class WebRTCSignal(BaseModel):
    """WebRTC signaling packet for peer-to-peer or conference sessions."""
    action: str  # 'join_room', 'leave_room', 'offer', 'answer', 'ice_candidate', 'call_user', 'reject_call'
    room_id: str
    sender_id: Optional[str] = None
    target_id: Optional[str] = None
    sdp: Optional[str] = None
    candidate: Optional[dict] = None
    call_type: str = "video"  # audio, video, screen
