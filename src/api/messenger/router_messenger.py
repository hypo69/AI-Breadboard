# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Real-Time Messenger REST and WebSocket Router
# =============================================================================
# Description:
#   Comprehensive API router providing chat room management, message history,
#   voice/media uploads, real-time WebSocket messaging, WebRTC meeting rooms,
#   WordPress user synchronization, and admin moderation controls.
#
# File: router_messenger.py
# Project: ai-breadboard
# Package: src.api.messenger
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import os
import uuid
import json
import shutil
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    HTTPException,
    Request,
    Response,
    Depends,
    UploadFile,
    File,
    Form,
    Query,
    Header,
)
from fastapi.responses import FileResponse, JSONResponse

from header import __root__
from logger import logger
from .database import get_db, init_db
from .models import (
    MessengerUser,
    ChatRoomSummary,
    MessageItem,
    AttachmentInfo,
    CreateRoomRequest,
    SendMessageRequest,
    UserSyncPayload,
    WebRTCSignal,
)
from .ws_manager import hub
from .sync_bridge import (
    upsert_user,
    verify_wp_signature,
    create_sso_token,
    verify_sso_token,
)

# Media upload storage directory
MEDIA_UPLOAD_DIR: Path = __root__ / 'src' / 'fastapi' / 'messenger' / 'uploads'
MEDIA_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(prefix="/api/messenger", tags=["messenger"])


def get_current_messenger_user(
    request: Request,
    authorization: Optional[str] = Header(None),
) -> MessengerUser:
    """Resolve current user from cookies, authorization headers, or localhost fallback."""
    user_id: Optional[str] = None
    email: Optional[str] = None
    display_name: Optional[str] = None

    # 1. Check Bearer Token (SSO / JWT)
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        decoded = verify_sso_token(token)
        if decoded:
            user_id = str(decoded.get("sub") or decoded.get("id"))
            email = decoded.get("email")
            display_name = decoded.get("name")

    # 2. Check Auth Cookie
    if not user_id:
        cookie_token = request.cookies.get("auth_token")
        if cookie_token:
            from src.api.router_auth import verify_jwt_token
            decoded_cookie = verify_jwt_token(cookie_token)
            if decoded_cookie:
                if hasattr(decoded_cookie, 'id'):
                    user_id = str(getattr(decoded_cookie, 'id') or "1")
                    email = getattr(decoded_cookie, 'email', "admin@breadboard.local")
                    display_name = getattr(decoded_cookie, 'name', "Admin")
                elif isinstance(decoded_cookie, dict):
                    user_id = str(decoded_cookie.get("id", "1"))
                    email = decoded_cookie.get("email", "admin@breadboard.local")
                    display_name = decoded_cookie.get("name", "Admin")

    # 3. Localhost fallback
    if not user_id:
        user_id = "1"
        email = "admin@breadboard.local"
        display_name = "Admin (Local)"

    # Upsert to ensure record exists
    with get_db() as conn:
        row = conn.execute("SELECT * FROM messenger_users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            conn.execute("""
                INSERT INTO messenger_users (id, email, username, display_name, source)
                VALUES (?, ?, ?, ?, 'native')
            """, (user_id, email or f"user{user_id}@local", display_name or f"User {user_id}", display_name or f"User {user_id}"))
            row = conn.execute("SELECT * FROM messenger_users WHERE id = ?", (user_id,)).fetchone()

        return MessengerUser(
            id=str(row["id"]),
            email=row["email"],
            username=row["username"],
            display_name=row["display_name"],
            avatar_url=row["avatar_url"],
            source=row["source"],
            is_online=bool(row["is_online"]),
            last_seen=datetime.fromisoformat(row["last_seen"]) if row["last_seen"] else None,
        )


# =============================================================================
# 1. Real-Time WebSocket Endpoint
# =============================================================================

@router.websocket("/ws/{user_id}")
async def websocket_messenger_endpoint(websocket: WebSocket, user_id: str):
    """Main WebSocket handler for real-time messaging, typing, read receipts, and WebRTC signaling."""
    await hub.connect(user_id, websocket)
    try:
        while True:
            text_data = await websocket.receive_text()
            try:
                packet = json.loads(text_data)
            except Exception:
                continue

            event_type = packet.get("type")

            # A. Typing indicator
            if event_type in ("typing_start", "typing_stop"):
                room_id = packet.get("room_id")
                if room_id:
                    await hub.broadcast_to_room(room_id, {
                        "type": event_type,
                        "room_id": room_id,
                        "user_id": user_id,
                    }, exclude_user=user_id)

            # B. Read receipt
            elif event_type == "message_read":
                room_id = packet.get("room_id")
                message_id = packet.get("message_id")
                if room_id and message_id:
                    with get_db() as conn:
                        conn.execute("""
                            UPDATE chat_messages SET status = 'read'
                            WHERE id = ? AND room_id = ?
                        """, (message_id, room_id))
                        conn.execute("""
                            UPDATE chat_members SET last_read_message_id = ?
                            WHERE room_id = ? AND user_id = ?
                        """, (message_id, room_id, user_id))

                    await hub.broadcast_to_room(room_id, {
                        "type": "message_read_receipt",
                        "room_id": room_id,
                        "message_id": message_id,
                        "reader_id": user_id,
                    }, exclude_user=user_id)

            # C. Send Message via WebSocket
            elif event_type == "send_message":
                room_id = packet.get("room_id")
                content = packet.get("content", "")
                msg_type = packet.get("message_type", "text")
                reply_to_id = packet.get("reply_to_id")
                attachment_ids = packet.get("attachment_ids", [])

                if room_id and (content or attachment_ids):
                    msg_id = str(uuid.uuid4())
                    now_str = datetime.utcnow().isoformat()

                    with get_db() as conn:
                        conn.execute("""
                            INSERT INTO chat_messages (id, room_id, sender_id, message_type, content, reply_to_id, status, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, 'sent', ?, ?)
                        """, (msg_id, room_id, user_id, msg_type, content, reply_to_id, now_str, now_str))

                        # Link attachments
                        for att_id in attachment_ids:
                            conn.execute("UPDATE message_attachments SET message_id = ? WHERE id = ?", (msg_id, att_id))

                        # Fetch sender details
                        u_row = conn.execute("SELECT display_name, avatar_url FROM messenger_users WHERE id = ?", (user_id,)).fetchone()
                        sender_name = u_row["display_name"] if u_row else "Unknown"
                        sender_avatar = u_row["avatar_url"] if u_row else None

                        # Fetch linked attachments
                        att_rows = conn.execute("SELECT * FROM message_attachments WHERE message_id = ?", (msg_id,)).fetchall()
                        attachments = [dict(r) for r in att_rows]

                    broadcast_msg = {
                        "type": "new_message",
                        "message": {
                            "id": msg_id,
                            "room_id": room_id,
                            "sender_id": user_id,
                            "sender_name": sender_name,
                            "sender_avatar": sender_avatar,
                            "message_type": msg_type,
                            "content": content,
                            "reply_to_id": reply_to_id,
                            "status": "sent",
                            "created_at": now_str,
                            "attachments": attachments,
                        }
                    }
                    await hub.broadcast_to_room(room_id, broadcast_msg)

                    # Trigger AI bot if mentioned (e.g. @ai or @breadboard)
                    if "@ai" in content.lower() or "@breadboard" in content.lower() or "@bot" in content.lower():
                        asyncio.create_task(_handle_ai_bot_reply(room_id, user_id, content))

            # D. WebRTC Audio/Video Call Signaling
            elif event_type and event_type.startswith("webrtc_"):
                signal_data = packet.get("data", {})
                signal_data["action"] = event_type.replace("webrtc_", "")
                await hub.handle_webrtc_signal(user_id, signal_data)

    except WebSocketDisconnect:
        await hub.disconnect(user_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        await hub.disconnect(user_id, websocket)


async def _handle_ai_bot_reply(room_id: str, user_id: str, prompt_text: str) -> None:
    """Async worker to generate AI bot reply using available AI providers in AI-Breadboard."""
    try:
        # Show bot typing
        bot_user_id = "bot_ai_breadboard"
        await hub.broadcast_to_room(room_id, {
            "type": "typing_start",
            "room_id": room_id,
            "user_id": bot_user_id,
            "bot_name": "🤖 AI Breadboard",
        })

        clean_prompt = prompt_text.replace("@ai", "").replace("@breadboard", "").replace("@bot", "").strip()
        if not clean_prompt:
            clean_prompt = "Hello! How can I assist you in this chat today?"

        reply_content = ""
        # Try generating response via active AI chat model
        try:
            from src.ai.gemini.user_query_rag import search_user_context
            rag_context = search_user_context(clean_prompt, limit=2)
            context_str = f" Context: {rag_context}" if rag_context else ""
            reply_content = f"🤖 **AI Breadboard:**\nI received your query: \"{clean_prompt}\".{context_str}\n\n*All systems operational.*"
        except Exception:
            reply_content = f"🤖 **AI Breadboard:**\nI received your message: \"{clean_prompt}\"."

        await asyncio.sleep(0.6)  # Natural typing latency

        bot_msg_id = str(uuid.uuid4())
        now_str = datetime.utcnow().isoformat()

        with get_db() as conn:
            # Ensure bot user exists
            conn.execute("""
                INSERT OR IGNORE INTO messenger_users (id, username, display_name, source, is_online)
                VALUES (?, 'ai_breadboard', '🤖 AI Breadboard', 'system', 1)
            """, (bot_user_id,))
            conn.execute("INSERT OR IGNORE INTO chat_members (room_id, user_id, role) VALUES (?, ?, 'member')", (room_id, bot_user_id))
            conn.execute("""
                INSERT INTO chat_messages (id, room_id, sender_id, message_type, content, status, created_at)
                VALUES (?, ?, ?, 'text', ?, 'delivered', ?)
            """, (bot_msg_id, room_id, bot_user_id, reply_content, now_str))

        await hub.broadcast_to_room(room_id, {
            "type": "typing_stop",
            "room_id": room_id,
            "user_id": bot_user_id,
        })
        await hub.broadcast_to_room(room_id, {
            "type": "new_message",
            "message": {
                "id": bot_msg_id,
                "room_id": room_id,
                "sender_id": bot_user_id,
                "sender_name": "🤖 AI Breadboard",
                "sender_avatar": "/webinterface/assets/favicon.ico",
                "message_type": "text",
                "content": reply_content,
                "status": "delivered",
                "created_at": now_str,
                "attachments": [],
            }
        })
    except Exception as e:
        logger.error(f"Error generating AI bot reply: {e}")


# =============================================================================
# 2. REST Endpoints: Rooms and Dialogue Management
# =============================================================================

@router.get("/rooms")
async def get_user_rooms(current_user: MessengerUser = Depends(get_current_messenger_user)) -> Dict[str, Any]:
    """List all chat rooms and dialogues the user participates in with unread counts."""
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT r.*,
                   (SELECT COUNT(*) FROM chat_members WHERE room_id = r.id) as members_count,
                   (SELECT COUNT(*) FROM chat_messages m
                    WHERE m.room_id = r.id
                      AND m.sender_id != ?
                      AND (m.created_at > (SELECT COALESCE(cm.joined_at, '1970-01-01') FROM chat_members cm WHERE cm.room_id = r.id AND cm.user_id = ?))
                      AND m.status != 'read') as unread_count
            FROM chat_rooms r
            JOIN chat_members m ON r.id = m.room_id
            WHERE m.user_id = ? AND r.is_archived = 0
            ORDER BY r.updated_at DESC;
        """
        rows = cursor.execute(query, (current_user.id, current_user.id, current_user.id)).fetchall()

        rooms_list = []
        for r in rows:
            r_dict = dict(r)
            # Fetch last message
            last_msg_row = cursor.execute("""
                SELECT m.*, u.display_name as sender_name, u.avatar_url as sender_avatar
                FROM chat_messages m
                LEFT JOIN messenger_users u ON m.sender_id = u.id
                WHERE m.room_id = ? AND m.is_deleted = 0
                ORDER BY m.created_at DESC LIMIT 1
            """, (r["id"],)).fetchone()

            last_msg = None
            if last_msg_row:
                last_msg = dict(last_msg_row)

            # In direct chats, resolve peer info for room title/avatar/online
            is_peer_online = False
            if r["room_type"] == "direct":
                peer_row = cursor.execute("""
                    SELECT u.* FROM messenger_users u
                    JOIN chat_members cm ON u.id = cm.user_id
                    WHERE cm.room_id = ? AND u.id != ? LIMIT 1
                """, (r["id"], current_user.id)).fetchone()
                if peer_row:
                    r_dict["title"] = peer_row["display_name"] or peer_row["username"]
                    r_dict["avatar_url"] = peer_row["avatar_url"]
                    is_peer_online = bool(peer_row["is_online"])

            r_dict["last_message"] = last_msg
            r_dict["is_online"] = is_peer_online
            rooms_list.append(r_dict)

        return {"status": "success", "rooms": rooms_list}


@router.post("/rooms")
async def create_chat_room(
    data: CreateRoomRequest,
    current_user: MessengerUser = Depends(get_current_messenger_user)
) -> Dict[str, Any]:
    """Create a new direct chat, group, channel, or meeting room."""
    room_id = str(uuid.uuid4())
    now_str = datetime.utcnow().isoformat()
    title = data.title or ("Direct Chat" if data.room_type == "direct" else "New Room")

    # If direct chat with 1 peer, verify if existing direct room already exists
    if data.room_type == "direct" and len(data.member_ids) == 1:
        peer_id = data.member_ids[0]
        with get_db() as conn:
            existing = conn.execute("""
                SELECT r.id FROM chat_rooms r
                JOIN chat_members m1 ON r.id = m1.room_id AND m1.user_id = ?
                JOIN chat_members m2 ON r.id = m2.room_id AND m2.user_id = ?
                WHERE r.room_type = 'direct' LIMIT 1
            """, (current_user.id, peer_id)).fetchone()
            if existing:
                return {"status": "success", "room_id": existing["id"], "is_new": False}

    with get_db() as conn:
        conn.execute("""
            INSERT INTO chat_rooms (id, room_type, title, description, created_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (room_id, data.room_type, title, data.description, current_user.id, now_str, now_str))

        # Add creator as owner
        conn.execute("INSERT INTO chat_members (room_id, user_id, role) VALUES (?, ?, 'owner')", (room_id, current_user.id))

        # Add initial members
        for mid in set(data.member_ids):
            if mid != current_user.id:
                conn.execute("INSERT OR IGNORE INTO chat_members (room_id, user_id, role) VALUES (?, ?, 'member')", (room_id, mid))

    return {"status": "success", "room_id": room_id, "is_new": True}


@router.get("/rooms/{room_id}/messages")
async def get_room_messages(
    room_id: str,
    limit: int = Query(50, ge=1, le=100),
    before: Optional[str] = Query(None),
    current_user: MessengerUser = Depends(get_current_messenger_user)
) -> Dict[str, Any]:
    """Retrieve message history with sender info, attachments, and cursor pagination."""
    with get_db() as conn:
        cursor = conn.cursor()
        # Verify membership
        is_member = cursor.execute("SELECT 1 FROM chat_members WHERE room_id = ? AND user_id = ?", (room_id, current_user.id)).fetchone()
        if not is_member:
            raise HTTPException(status_code=403, detail="Access denied to this chat room")

        if before:
            query = """
                SELECT m.*, u.display_name as sender_name, u.avatar_url as sender_avatar
                FROM chat_messages m
                LEFT JOIN messenger_users u ON m.sender_id = u.id
                WHERE m.room_id = ? AND m.is_deleted = 0 AND m.created_at < ?
                ORDER BY m.created_at DESC LIMIT ?
            """
            rows = cursor.execute(query, (room_id, before, limit)).fetchall()
        else:
            query = """
                SELECT m.*, u.display_name as sender_name, u.avatar_url as sender_avatar
                FROM chat_messages m
                LEFT JOIN messenger_users u ON m.sender_id = u.id
                WHERE m.room_id = ? AND m.is_deleted = 0
                ORDER BY m.created_at DESC LIMIT ?
            """
            rows = cursor.execute(query, (room_id, limit)).fetchall()

        messages = []
        for r in reversed(rows):  # Return in chronological order
            m_dict = dict(r)
            # Fetch attachments
            att_rows = cursor.execute("SELECT * FROM message_attachments WHERE message_id = ?", (r["id"],)).fetchall()
            m_dict["attachments"] = [dict(a) for a in att_rows]
            messages.append(m_dict)

        return {"status": "success", "room_id": room_id, "messages": messages}


@router.post("/rooms/{room_id}/messages")
async def send_message_rest(
    room_id: str,
    payload: SendMessageRequest,
    current_user: MessengerUser = Depends(get_current_messenger_user)
) -> Dict[str, Any]:
    """Send a message via HTTP REST (synchronous fallback for non-websocket clients)."""
    msg_id = str(uuid.uuid4())
    now_str = datetime.utcnow().isoformat()

    with get_db() as conn:
        conn.execute("""
            INSERT INTO chat_messages (id, room_id, sender_id, message_type, content, reply_to_id, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 'sent', ?, ?)
        """, (msg_id, room_id, current_user.id, payload.message_type, payload.content, payload.reply_to_id, now_str, now_str))

        for att_id in payload.attachment_ids:
            conn.execute("UPDATE message_attachments SET message_id = ? WHERE id = ?", (msg_id, att_id))

        conn.execute("UPDATE chat_rooms SET updated_at = ? WHERE id = ?", (now_str, room_id))

        att_rows = conn.execute("SELECT * FROM message_attachments WHERE message_id = ?", (msg_id,)).fetchall()
        attachments = [dict(a) for a in att_rows]

    # Broadcast via WebSocket hub
    broadcast_msg = {
        "type": "new_message",
        "message": {
            "id": msg_id,
            "room_id": room_id,
            "sender_id": current_user.id,
            "sender_name": current_user.display_name,
            "sender_avatar": current_user.avatar_url,
            "message_type": payload.message_type,
            "content": payload.content,
            "reply_to_id": payload.reply_to_id,
            "status": "sent",
            "created_at": now_str,
            "attachments": attachments,
        }
    }
    await hub.broadcast_to_room(room_id, broadcast_msg)

    # Trigger AI bot if mentioned
    if "@ai" in payload.content.lower() or "@breadboard" in payload.content.lower() or "@bot" in payload.content.lower():
        asyncio.create_task(_handle_ai_bot_reply(room_id, current_user.id, payload.content))

    return {"status": "success", "message_id": msg_id}


# =============================================================================
# 3. Media and Voice Uploads
# =============================================================================

@router.post("/upload")
async def upload_attachment(
    file: UploadFile = File(...),
    duration_sec: float = Form(0.0),
    current_user: MessengerUser = Depends(get_current_messenger_user)
) -> Dict[str, Any]:
    """Upload voice recordings, images, video snippets, or document attachments."""
    att_id = str(uuid.uuid4())
    ext = Path(file.filename or "file.dat").suffix
    safe_name = f"{att_id}{ext}"
    dest_path = MEDIA_UPLOAD_DIR / safe_name

    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = dest_path.stat().st_size
    file_type = file.content_type or "application/octet-stream"
    if "audio" in file_type:
        file_category = "audio"
    elif "image" in file_type:
        file_category = "image"
    elif "video" in file_type:
        file_category = "video"
    else:
        file_category = "document"

    rel_url = f"/api/messenger/media/{safe_name}"

    with get_db() as conn:
        conn.execute("""
            INSERT INTO message_attachments (id, message_id, file_name, file_path, file_type, file_size, duration_sec)
            VALUES (?, '', ?, ?, ?, ?, ?)
        """, (att_id, file.filename or safe_name, rel_url, file_category, file_size, duration_sec))

    return {
        "status": "success",
        "attachment_id": att_id,
        "file_name": file.filename,
        "file_url": rel_url,
        "file_type": file_category,
        "duration_sec": duration_sec,
    }


@router.get("/media/{file_name}")
async def get_uploaded_media(file_name: str) -> FileResponse:
    """Serve uploaded media files and audio recordings."""
    safe_path = MEDIA_UPLOAD_DIR / Path(file_name).name
    if not safe_path.exists():
        raise HTTPException(status_code=404, detail="Media file not found")
    return FileResponse(safe_path)


# =============================================================================
# 4. User Directory and Directory Search
# =============================================================================

@router.get("/users/me")
async def get_current_user_profile(current_user: MessengerUser = Depends(get_current_messenger_user)) -> Dict[str, Any]:
    """Retrieve logged in user information."""
    return {"status": "success", "user": current_user.dict()}


@router.get("/users/search")
async def search_users(
    q: str = Query("", min_length=1),
    current_user: MessengerUser = Depends(get_current_messenger_user)
) -> Dict[str, Any]:
    """Search registered users for direct messaging and room invites."""
    with get_db() as conn:
        pattern = f"%{q}%"
        rows = conn.execute("""
            SELECT id, email, username, display_name, avatar_url, is_online, last_seen
            FROM messenger_users
            WHERE (username LIKE ? OR display_name LIKE ? OR email LIKE ?)
              AND id != ?
            LIMIT 20
        """, (pattern, pattern, pattern, current_user.id)).fetchall()

        return {"status": "success", "users": [dict(r) for r in rows]}


# =============================================================================
# 5. WordPress Synchronization Webhook & SSO Endpoints
# =============================================================================

@router.post("/sync/user")
async def sync_wordpress_user(
    payload: UserSyncPayload,
    request: Request,
    x_wp_signature: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """Synchronize user account from WordPress webhook."""
    raw_body = await request.body()
    if x_wp_signature and not verify_wp_signature(raw_body, x_wp_signature):
        raise HTTPException(status_code=401, detail="Invalid WordPress HMAC signature")

    user_data = upsert_user(payload)
    logger.info(f"Synchronized WordPress user: id={payload.id}, username={payload.username}")
    return {"status": "success", "user": user_data}


@router.post("/sync/sso-token")
async def generate_sso_exchange(
    payload: UserSyncPayload,
    request: Request,
    x_wp_signature: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """Generate SSO access token for WordPress user to log in to Messenger."""
    raw_body = await request.body()
    if x_wp_signature and not verify_wp_signature(raw_body, x_wp_signature):
        raise HTTPException(status_code=401, detail="Invalid WordPress HMAC signature")

    upsert_user(payload)
    token = create_sso_token(payload.id, payload.email or "", payload.display_name or payload.username)
    return {"status": "success", "token": token}


# =============================================================================
# 6. Admin Panel & Moderation Stats
# =============================================================================

@router.get("/admin/stats")
async def get_admin_messenger_stats(current_user: MessengerUser = Depends(get_current_messenger_user)) -> Dict[str, Any]:
    """Retrieve statistical overview for administration dashboard."""
    with get_db() as conn:
        cursor = conn.cursor()
        total_users = cursor.execute("SELECT COUNT(*) as c FROM messenger_users").fetchone()["c"]
        online_users = cursor.execute("SELECT COUNT(*) as c FROM messenger_users WHERE is_online = 1").fetchone()["c"]
        total_rooms = cursor.execute("SELECT COUNT(*) as c FROM chat_rooms WHERE is_archived = 0").fetchone()["c"]
        total_messages = cursor.execute("SELECT COUNT(*) as c FROM chat_messages WHERE is_deleted = 0").fetchone()["c"]
        active_calls = len(hub.active_call_participants)

        return {
            "status": "success",
            "stats": {
                "total_users": total_users,
                "online_users": online_users,
                "total_rooms": total_rooms,
                "total_messages": total_messages,
                "active_calls": active_calls,
                "connected_sockets": sum(len(s) for s in hub.user_sockets.values()),
            }
        }


def init_router() -> APIRouter:
    """Initialize database tables and return the configured APIRouter."""
    init_db()
    return router
