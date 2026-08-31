# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: WebSocket remote control and player synchronization router
# =============================================================================
# Description:
#   Manages WebSocket connections and REST endpoints for synchronized remote control,
#   media player state broadcasts, and device pairing rooms.
#
# File: router_control.py
# Project: ai-breadboard
# Package: core.fastapi
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
from typing import Dict, List, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Request, HTTPException
from core.logger import logger
from core.fastapi.router_auth import verify_jwt_token

class ControlConnectionManager:
    """Менеджер WebSocket соединений для пульта и плеера."""

    def __init__(self):
        # Хранение активных подключений: room_id -> {"player": [ws...], "remote": [ws...]}
        self.rooms: Dict[str, Dict[str, List[WebSocket]]] = {}
        # Хранение последнего известного состояния плеера: room_id -> dict
        self.room_states: Dict[str, dict] = {}
        # Хранение плейлиста плеера: room_id -> list
        self.room_playlists: Dict[str, list] = {}

    async def connect(self, websocket: WebSocket, room_id: str, role: str):
        """Connection клиента с ролью 'player' или 'remote' в комнату."""
        await websocket.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = {"player": [], "remote": []}
        
        if role not in ("player", "remote"):
            role = "remote"

        self.rooms[room_id][role].append(websocket)
        logger.info(f"WebSocket connected: room={room_id}, role={role}")

        # Если подключается remote и у нас есть сохраненное state, сразу отправляем его
        if role == "remote":
            if room_id in self.room_states:
                try:
                    await websocket.send_json(self.room_states[room_id])
                except Exception as e:
                    logger.warning(f"Error sending state on connect to remote: {e}")
            if room_id in self.room_playlists:
                try:
                    await websocket.send_json({
                        "event": "playlist_update",
                        "files": self.room_playlists[room_id]
                    })
                except Exception as e:
                    logger.warning(f"Error sending playlist on connect to remote: {e}")

    def disconnect(self, websocket: WebSocket, room_id: str, role: str):
        """Disconnection клиента из комнаты."""
        if room_id in self.rooms and role in self.rooms[room_id]:
            if websocket in self.rooms[room_id][role]:
                self.rooms[room_id][role].remove(websocket)
            # Если комната пуста, очищаем её
            if not self.rooms[room_id]["player"] and not self.rooms[room_id]["remote"]:
                self.rooms.pop(room_id, None)
                self.room_states.pop(room_id, None)
                self.room_playlists.pop(room_id, None)
        logger.info(f"WebSocket disconnected: room={room_id}, role={role}")

    async def broadcast_to_role(self, room_id: str, target_role: str, data: dict):
        """Пересылает сообщение всем клиентам с целевой ролью в комнате."""
        if room_id not in self.rooms:
            return

        targets = self.rooms[room_id].get(target_role, [])
        disconnected = []

        for ws in targets:
            try:
                await ws.send_json(data)
            except Exception as e:
                logger.warning(f"Failed to send to {target_role} in room {room_id}: {e}")
                disconnected.append(ws)

        for ws in disconnected:
            self.disconnect(ws, room_id, target_role)

manager = ControlConnectionManager()
router = APIRouter(prefix="/api/control", tags=["control"])

def get_room_id(token: Optional[str], room: Optional[str]) -> str:
    """Определение идентификатора комнаты на основе JWT токена или параметров."""
    if room and room.strip():
        return room.strip().lower()
    if token:
        token_data = verify_jwt_token(token)
        if token_data and token_data.email:
            return token_data.email.strip().lower()
    return "default"

@router.websocket("/ws")
async def websocket_control_endpoint(
    websocket: WebSocket,
    role: str = Query("remote"),
    token: Optional[str] = Query(None),
    room: Optional[str] = Query(None)
):
    """WebSocket эндпоинт для управления плеером в реальном времени."""
    cookie_token = websocket.cookies.get("auth_token")
    logger.info(f"WS connection request: role={role}, query_token={'present' if token else 'None'}, query_room={room}")
    if cookie_token and not token:
        token = cookie_token
        
    room_id = get_room_id(token, room)
    logger.info(f"WS room resolved: role={role}, room_id={room_id}")
    await manager.connect(websocket, room_id, role)

    try:
        while True:
            text_data = await websocket.receive_text()
            try:
                data = json.loads(text_data)
            except json.JSONDecodeError:
                continue

            if role == "remote":
                # Пульт sends команды плееру
                await manager.broadcast_to_role(room_id, "player", data)
            elif role == "player":
                # Плеер обновляет свой status или плейлист для пульта
                event_type = data.get("event")
                if event_type == "status_update":
                    manager.room_states[room_id] = data
                elif event_type == "playlist_update":
                    manager.room_playlists[room_id] = data.get("files", [])

                await manager.broadcast_to_role(room_id, "remote", data)

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id, role)
    except Exception as e:
        logger.error(f"WebSocket error in room {room_id}: {e}")
        manager.disconnect(websocket, room_id, role)

@router.get("/status")
async def get_control_status(request: Request, token: Optional[str] = None, room: Optional[str] = None):
    """Получить текущее state комнаты по HTTP."""
    cookie_token = request.cookies.get("auth_token")
    if cookie_token and not token:
        token = cookie_token
        
    room_id = get_room_id(token, room)
    return {
        "room_id": room_id,
        "has_player": len(manager.rooms.get(room_id, {}).get("player", [])) > 0,
        "remotes_count": len(manager.rooms.get(room_id, {}).get("remote", [])),
        "state": manager.room_states.get(room_id, None),
        "playlist_count": len(manager.room_playlists.get(room_id, []))
    }

@router.get("/active_players")
async def get_active_players(request: Request):
    """Получить list комнат с активными плеерами."""
    token = request.cookies.get("auth_token")
    user_email = None
    if token:
        token_data = verify_jwt_token(token)
        if token_data and token_data.email:
            user_email = token_data.email.strip().lower()

    active = []
    for room_id, roles in manager.rooms.items():
        if len(roles.get("player", [])) > 0:
            active.append(room_id)
            
    logger.info(f"active_players endpoint called: token={token}, user_email={user_email}, active_rooms={active}")
    return {"players": active, "user_email": user_email}

@router.get("/rescan")
async def rescan_storage(request: Request):
    """Принудительное пересканирование доступных хранилищ."""
    # Check прав администратора
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=403)
        
    from core.fastapi.router_auth import verify_jwt_token
    user_data = verify_jwt_token(token)
    if not user_data:
        raise HTTPException(status_code=403)
    
    from core.user_manager import user_manager
    db_user = user_manager.get_user_by_email(user_data.email)
    if not db_user or (not db_user.get('is_admin', 0) and db_user.get('role') != 'admin'):
        raise HTTPException(status_code=403)

    import psutil
    drives = []
    drives_details = []
    for d in psutil.disk_partitions():
        drives.append(d.device)
        try:
            usage = psutil.disk_usage(d.mountpoint)
            total_gb = round(usage.total / (1024 ** 3), 1)
            used_gb = round(usage.used / (1024 ** 3), 1)
            free_gb = round(usage.free / (1024 ** 3), 1)
            percent = usage.percent
            drives_details.append({
                "device": d.device,
                "mountpoint": d.mountpoint,
                "fstype": d.fstype,
                "total_gb": total_gb,
                "used_gb": used_gb,
                "free_gb": free_gb,
                "percent": percent
            })
        except Exception:
            drives_details.append({
                "device": d.device,
                "mountpoint": d.mountpoint,
                "fstype": d.fstype,
                "total_gb": 0.0,
                "used_gb": 0.0,
                "free_gb": 0.0,
                "percent": 0.0
            })
    return {"status": "success", "drives": drives, "details": drives_details}

def init_router() -> APIRouter:
    """Initialization роутера управления.
    Returns:
        APIRouter: Настроенный роутер FastAPI.
    """
    return router

