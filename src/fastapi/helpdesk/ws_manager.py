# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Helpdesk Real-Time WebSocket Hub and Dispatcher
# =============================================================================
# Description:
#   Maintains persistent WebSocket connections for support operators and clients,
#   broadcasts real-time chat messages, ticket status changes, and operator alerts.
#
# File: ws_manager.py
# Project: ai-breadboard
# Package: src.fastapi.helpdesk
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
import asyncio
from typing import Dict, Set, Optional, Any
from fastapi import WebSocket

from src.logger import logger
from .database import get_db


class HelpdeskConnectionHub:
    """Manages active WebSocket connections and message routing for Helpdesk."""

    def __init__(self) -> None:
        # Maps client_id -> set of active WebSockets
        self.client_sockets: Dict[str, Set[WebSocket]] = {}
        # Maps ticket_id -> set of client_ids actively viewing the ticket
        self.ticket_viewers: Dict[str, Set[str]] = {}
        # Set of active operator client_ids (for global ticket notifications)
        self.operators: Set[str] = set()
        self._lock = asyncio.Lock()

    async def connect(self, client_id: str, websocket: WebSocket, is_operator: bool = False) -> None:
        """Register a new active WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            if client_id not in self.client_sockets:
                self.client_sockets[client_id] = set()
            self.client_sockets[client_id].add(websocket)
            if is_operator:
                self.operators.add(client_id)

        self._update_operator_presence(client_id, is_online=True)
        logger.info(f"Helpdesk WebSocket client connected: client_id={client_id}, is_operator={is_operator}")

    async def disconnect(self, client_id: str, websocket: WebSocket) -> None:
        """Unregister a WebSocket connection."""
        async with self._lock:
            if client_id in self.client_sockets:
                self.client_sockets[client_id].discard(websocket)
                if not self.client_sockets[client_id]:
                    del self.client_sockets[client_id]
                    self.operators.discard(client_id)
                    self._update_operator_presence(client_id, is_online=False)

            for ticket_id, viewers in list(self.ticket_viewers.items()):
                viewers.discard(client_id)

        logger.info(f"Helpdesk WebSocket client disconnected: client_id={client_id}")

    def subscribe_ticket(self, ticket_id: str, client_id: str) -> None:
        """Subscribe client to ticket live events."""
        if ticket_id not in self.ticket_viewers:
            self.ticket_viewers[ticket_id] = set()
        self.ticket_viewers[ticket_id].add(client_id)

    def unsubscribe_ticket(self, ticket_id: str, client_id: str) -> None:
        """Unsubscribe client from ticket live events."""
        if ticket_id in self.ticket_viewers:
            self.ticket_viewers[ticket_id].discard(client_id)

    async def broadcast_to_ticket(self, ticket_id: str, payload: Dict[str, Any]) -> None:
        """Send a message to all clients viewing the ticket and all active operators."""
        recipients = set(self.ticket_viewers.get(ticket_id, set())) | set(self.operators)
        msg_json = json.dumps(payload, ensure_ascii=False)

        async with self._lock:
            for cid in recipients:
                sockets = self.client_sockets.get(cid, set())
                dead_sockets = set()
                for ws in sockets:
                    try:
                        await ws.send_text(msg_json)
                    except Exception as e:
                        logger.warning(f"Failed to send ticket event to {cid}: {e}")
                        dead_sockets.add(ws)
                sockets.difference_update(dead_sockets)

    async def broadcast_to_operators(self, payload: Dict[str, Any]) -> None:
        """Broadcast an administrative or new-ticket notification to all online operators."""
        msg_json = json.dumps(payload, ensure_ascii=False)
        async with self._lock:
            for op_id in self.operators:
                sockets = self.client_sockets.get(op_id, set())
                dead_sockets = set()
                for ws in sockets:
                    try:
                        await ws.send_text(msg_json)
                    except Exception as e:
                        logger.warning(f"Failed to send operator alert to {op_id}: {e}")
                        dead_sockets.add(ws)
                sockets.difference_update(dead_sockets)

    def _update_operator_presence(self, user_id: str, is_online: bool) -> None:
        """Record operator presence in database."""
        try:
            with get_db() as conn:
                conn.execute("""
                    UPDATE helpdesk_operators
                    SET is_online = ?, last_active = CURRENT_TIMESTAMP
                    WHERE user_id = ?;
                """, (1 if is_online else 0, user_id))
        except Exception as e:
            logger.debug(f"Operator presence update skipped: {e}")


hub = HelpdeskConnectionHub()
