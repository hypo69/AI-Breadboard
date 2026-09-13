# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Messenger Real-Time WebSocket Hub and Signaling Manager
# =============================================================================
# Description:
#   Maintains persistent WebSocket client connections, manages presence tracking,
#   broadcasts messages across chat rooms, handles typing events, and routes
#   WebRTC peer-to-peer audio/video signaling packets.
#
# File: ws_manager.py
# Project: ai-breadboard
# Package: src.api.messenger
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
import asyncio
from datetime import datetime
from typing import Dict, List, Set, Optional, Any
from fastapi import WebSocket

from src.logger import logger
from .database import get_db


class ConnectionHub:
    """Manages active WebSocket connections, presence states, and room routing."""

    def __init__(self) -> None:
        # Maps user_id -> set of active WebSockets (supports multiple tabs/devices)
        self.user_sockets: Dict[str, Set[WebSocket]] = {}
        # Maps room_id -> set of user_ids active in that room
        self.room_subscribers: Dict[str, Set[str]] = {}
        # Maps room_id -> set of user_ids in active WebRTC call
        self.active_call_participants: Dict[str, Set[str]] = {}
        # Lock for thread safety during connection updates
        self._lock = asyncio.Lock()

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        """Register a new active WebSocket connection for a user."""
        await websocket.accept()
        async with self._lock:
            if user_id not in self.user_sockets:
                self.user_sockets[user_id] = set()
            self.user_sockets[user_id].add(websocket)

        # Update presence to online
        self._set_user_presence(user_id, is_online=True)
        # Broadcast presence change to contacts
        await self.broadcast_presence(user_id, is_online=True)
        logger.info(f"WebSocket client connected: user_id={user_id}")

    async def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        """Unregister a WebSocket connection and update presence if no active connections remain."""
        async with self._lock:
            if user_id in self.user_sockets:
                self.user_sockets[user_id].discard(websocket)
                if not self.user_sockets[user_id]:
                    del self.user_sockets[user_id]
                    self._set_user_presence(user_id, is_online=False)
                    asyncio.create_task(self.broadcast_presence(user_id, is_online=False))

            # Clean up active call participation if any
            for room_id, participants in list(self.active_call_participants.items()):
                if user_id in participants:
                    participants.discard(user_id)
                    asyncio.create_task(self.broadcast_to_room(room_id, {
                        "type": "call_participant_left",
                        "room_id": room_id,
                        "user_id": user_id,
                    }))

        logger.info(f"WebSocket client disconnected: user_id={user_id}")

    def _set_user_presence(self, user_id: str, is_online: bool) -> None:
        """Update user online state and last_seen timestamp in database."""
        try:
            with get_db() as conn:
                conn.execute(
                    "UPDATE messenger_users SET is_online = ?, last_seen = ? WHERE id = ?",
                    (1 if is_online else 0, datetime.utcnow().isoformat(), user_id)
                )
        except Exception as e:
            logger.error(f"Failed to update user presence for {user_id}: {e}")

    async def broadcast_presence(self, user_id: str, is_online: bool) -> None:
        """Notify all connected clients about a user's presence change."""
        payload = {
            "type": "presence_update",
            "user_id": user_id,
            "is_online": is_online,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast_global(payload)

    async def send_to_user(self, user_id: str, message: dict) -> None:
        """Send a JSON payload to all active WebSocket connections of a specific user."""
        sockets = self.user_sockets.get(user_id, set()).copy()
        for ws in sockets:
            try:
                await ws.send_text(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                logger.warning(f"Error sending message to user {user_id}: {e}")

    async def broadcast_to_room(self, room_id: str, message: dict, exclude_user: Optional[str] = None) -> None:
        """Broadcast a message to all members of a room."""
        # Query room members from DB
        member_ids: List[str] = []
        try:
            with get_db() as conn:
                rows = conn.execute("SELECT user_id FROM chat_members WHERE room_id = ?", (room_id,)).fetchall()
                member_ids = [row["user_id"] for row in rows]
        except Exception as e:
            logger.error(f"Error fetching room members for broadcast in {room_id}: {e}")

        tasks = []
        for uid in member_ids:
            if exclude_user and uid == exclude_user:
                continue
            if uid in self.user_sockets:
                tasks.append(self.send_to_user(uid, message))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def broadcast_global(self, message: dict) -> None:
        """Send a message to every connected client."""
        tasks = [self.send_to_user(uid, message) for uid in self.user_sockets.keys()]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def handle_webrtc_signal(self, sender_id: str, data: dict) -> None:
        """Route WebRTC signaling messages between callers and room participants."""
        action = data.get("action")
        room_id = data.get("room_id")
        target_id = data.get("target_id")

        if not room_id:
            return

        if action in ("join_call", "start_call"):
            if room_id not in self.active_call_participants:
                self.active_call_participants[room_id] = set()
            self.active_call_participants[room_id].add(sender_id)

            # Notify room members that a call is active or user joined
            await self.broadcast_to_room(room_id, {
                "type": "call_participant_joined",
                "room_id": room_id,
                "user_id": sender_id,
                "call_type": data.get("call_type", "video"),
                "participants": list(self.active_call_participants[room_id]),
            }, exclude_user=sender_id)

        elif action == "leave_call":
            if room_id in self.active_call_participants:
                self.active_call_participants[room_id].discard(sender_id)
            await self.broadcast_to_room(room_id, {
                "type": "call_participant_left",
                "room_id": room_id,
                "user_id": sender_id,
            })

        elif action in ("offer", "answer", "ice_candidate"):
            # Direct peer-to-peer signaling packet forwarding
            forward_packet = {
                "type": f"webrtc_{action}",
                "room_id": room_id,
                "sender_id": sender_id,
                "sdp": data.get("sdp"),
                "candidate": data.get("candidate"),
                "call_type": data.get("call_type", "video"),
            }
            if target_id:
                await self.send_to_user(target_id, forward_packet)
            else:
                await self.broadcast_to_room(room_id, forward_packet, exclude_user=sender_id)


# Global Hub Instance
hub = ConnectionHub()
