# -*- coding: utf-8 -*-
"""Unified WebSocket connection hub.

All real-time connections go through /ws/{channel}.
Channels: chat, stream, voice, metrics, admin, events.

Usage from a route:
    hub: WSHub = request.app.state.ws_hub
    await hub.broadcast("metrics", {"type": "update", "data": {...}})
"""
from __future__ import annotations

import asyncio
import json
import time
from collections import defaultdict
from typing import Dict, Optional, Set

from fastapi import WebSocket

from src.logger import logger

VALID_CHANNELS: Set[str] = {"chat", "stream", "voice", "metrics", "admin", "events"}


class WSHub:
    """Manages all active WebSocket connections grouped by channel."""

    def __init__(self) -> None:
        self._connections: Dict[str, Set[WebSocket]] = defaultdict(set)
        self._user_map: Dict[WebSocket, Optional[int]] = {}
        self._last_pong: Dict[WebSocket, float] = {}
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._shutdown = False

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def connect(self, ws: WebSocket, channel: str, user_id: Optional[int] = None) -> None:
        await ws.accept()
        self._connections[channel].add(ws)
        self._user_map[ws] = user_id
        self._last_pong[ws] = time.time()
        logger.info(f"[WSHub] connect channel={channel} user_id={user_id} total={self.active_connections_count}")

    def disconnect(self, ws: WebSocket, channel: str) -> None:
        self._connections[channel].discard(ws)
        self._user_map.pop(ws, None)
        self._last_pong.pop(ws, None)
        logger.info(f"[WSHub] disconnect channel={channel} total={self.active_connections_count}")

    # ------------------------------------------------------------------
    # Messaging
    # ------------------------------------------------------------------

    async def broadcast(self, channel: str, data: dict) -> int:
        """Broadcast JSON to all connections in *channel*. Returns send count."""
        payload = json.dumps(data, ensure_ascii=False)
        dead: list[WebSocket] = []
        sent = 0
        for ws in list(self._connections.get(channel, [])):
            try:
                await ws.send_text(payload)
                sent += 1
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, channel)
        return sent

    async def send_personal(self, user_id: int, data: dict) -> int:
        """Send JSON to all connections of a specific user. Returns send count."""
        payload = json.dumps(data, ensure_ascii=False)
        dead: list[tuple[WebSocket, str]] = []
        sent = 0
        for channel, connections in self._connections.items():
            for ws in list(connections):
                if self._user_map.get(ws) == user_id:
                    try:
                        await ws.send_text(payload)
                        sent += 1
                    except Exception:
                        dead.append((ws, channel))
        for ws, channel in dead:
            self.disconnect(ws, channel)
        return sent

    # ------------------------------------------------------------------
    # Heartbeat
    # ------------------------------------------------------------------

    async def start_heartbeat(self, interval: int = 30, timeout: int = 90) -> None:
        if self._heartbeat_task and not self._heartbeat_task.done():
            return
        self._heartbeat_task = asyncio.create_task(
            self._heartbeat_loop(interval, timeout), name="ws_hub_heartbeat"
        )
        logger.info(f"[WSHub] heartbeat started interval={interval}s")

    async def _heartbeat_loop(self, interval: int, timeout: int) -> None:
        while not self._shutdown:
            await asyncio.sleep(interval)
            now = time.time()
            dead: list[tuple[WebSocket, str]] = []
            for channel, connections in self._connections.items():
                for ws in list(connections):
                    if now - self._last_pong.get(ws, now) > timeout:
                        dead.append((ws, channel))
                    else:
                        try:
                            await ws.send_text('{"type":"ping"}')
                        except Exception:
                            dead.append((ws, channel))
            for ws, channel in dead:
                try:
                    await ws.close()
                except Exception:
                    pass
                self.disconnect(ws, channel)

    def record_pong(self, ws: WebSocket) -> None:
        self._last_pong[ws] = time.time()

    # ------------------------------------------------------------------
    # Stats & shutdown
    # ------------------------------------------------------------------

    @property
    def active_connections_count(self) -> int:
        return sum(len(v) for v in self._connections.values())

    def channel_stats(self) -> dict:
        return {ch: len(c) for ch, c in self._connections.items() if c}

    async def stop(self) -> None:
        self._shutdown = True
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        for connections in self._connections.values():
            for ws in list(connections):
                try:
                    await ws.close()
                except Exception:
                    pass
        self._connections.clear()
        self._user_map.clear()
        self._last_pong.clear()
        logger.info("[WSHub] stopped")
