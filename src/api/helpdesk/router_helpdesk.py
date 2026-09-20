# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Helpdesk REST and WebSocket Router
# =============================================================================
# Description:
#   Provides API endpoints for creating, managing, prioritizing, and replying
#   to support tickets, operator assignment, statistics, and live WebSocket sync.
#
# File: router_helpdesk.py
# Project: ai-breadboard
# Package: src.api.helpdesk
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import uuid
import json
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    HTTPException,
    Request,
    Depends,
    Query,
    Header,
)
from fastapi.responses import JSONResponse

from src.logger import logger
from apps.common.csv_logger import AppCsvLogger
from .database import get_db, init_db, get_next_ticket_number
from .models import (
    HelpdeskUser,
    CreateTicketRequest,
    SendTicketMessageRequest,
    UpdateTicketStatusRequest,
    HelpdeskTicketItem,
    TicketMessageItem,
    HelpdeskStats,
)
from .ws_manager import hub

router = APIRouter(prefix="/api/helpdesk", tags=["helpdesk"])
_csv_logger = AppCsvLogger("helpdesk")


def get_current_helpdesk_user(
    request: Request,
    authorization: Optional[str] = Header(None),
) -> HelpdeskUser:
    """Resolve current user for helpdesk from auth cookies or bearer headers."""
    user_id: Optional[str] = None
    email: Optional[str] = None
    display_name: Optional[str] = None
    role: str = "user"

    # 1. Check Auth Cookie
    cookie_token = request.cookies.get("auth_token")
    if cookie_token:
        from src.api.router_auth import verify_jwt_token
        decoded = verify_jwt_token(cookie_token)
        if decoded:
            user_id = str(getattr(decoded, 'id', None) or "1")
            email = getattr(decoded, 'email', "user@breadboard.local")
            display_name = getattr(decoded, 'name', "User")
            role = getattr(decoded, 'role', 'user')

    # 2. Check Bearer Authorization Header
    if not user_id and authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            from src.api.messenger.sync_bridge import verify_sso_token
            decoded_sso = verify_sso_token(token)
            if decoded_sso:
                user_id = str(decoded_sso.get("sub") or decoded_sso.get("id"))
                email = decoded_sso.get("email")
                display_name = decoded_sso.get("name")
        except Exception:
            pass

    # Fallback to local default session if not authenticated
    if not user_id:
        user_id = "local_user"
        display_name = "Guest User"
        email = "guest@breadboard.local"

    return HelpdeskUser(
        id=user_id,
        username=user_id,
        display_name=display_name or user_id,
        email=email,
        role=role,
    )


@router.get("/tickets", response_model=Dict[str, Any])
async def list_tickets(
    status: Optional[str] = Query(None, description="Filter by status: open, in_progress, resolved, closed"),
    priority: Optional[str] = Query(None, description="Filter by priority: low, normal, high, urgent"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    search: Optional[str] = Query(None, description="Search term in subject or user name"),
    current_user: HelpdeskUser = Depends(get_current_helpdesk_user),
) -> Dict[str, Any]:
    """Retrieve list of helpdesk tickets with optional filtering."""
    init_db()
    with get_db() as conn:
        query = "SELECT * FROM helpdesk_tickets WHERE 1=1"
        params: List[Any] = []

        if status and status != "all":
            query += " AND status = ?"
            params.append(status)

        if priority:
            query += " AND priority = ?"
            params.append(priority)

        # If regular user (not admin/operator), allow filtering or restrict to their own tickets if requested
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        if search:
            query += " AND (subject LIKE ? OR user_name LIKE ? OR CAST(ticket_number AS TEXT) LIKE ?)"
            term = f"%{search}%"
            params.extend([term, term, term])

        query += " ORDER BY CASE priority WHEN 'urgent' THEN 1 WHEN 'high' THEN 2 WHEN 'normal' THEN 3 ELSE 4 END, updated_at DESC"

        rows = conn.execute(query, params).fetchall()
        tickets = []
        for r in rows:
            t_id = r["id"]
            # Get last message and count
            msg_count_row = conn.execute("SELECT COUNT(*) as c FROM helpdesk_messages WHERE ticket_id = ?", (t_id,)).fetchone()
            msg_count = msg_count_row["c"] if msg_count_row else 0

            last_msg_row = conn.execute("SELECT * FROM helpdesk_messages WHERE ticket_id = ? ORDER BY created_at DESC LIMIT 1", (t_id,)).fetchone()
            last_msg = dict(last_msg_row) if last_msg_row else None

            ticket_dict = dict(r)
            ticket_dict["messages_count"] = msg_count
            ticket_dict["last_message"] = last_msg
            tickets.append(ticket_dict)

    _csv_logger.log_poll(
        poll_type="tickets",
        metric_name="tickets_count",
        value=len(tickets),
        unit="count",
        status="ok",
        details=f"status_filter={status},priority_filter={priority}",
        filename="helpdesk_polls.csv",
    )

    return {"status": "success", "tickets": tickets, "count": len(tickets)}


@router.post("/tickets", response_model=Dict[str, Any])
async def create_ticket(
    payload: CreateTicketRequest,
    current_user: HelpdeskUser = Depends(get_current_helpdesk_user),
) -> Dict[str, Any]:
    """Create a new support ticket and send initial message."""
    init_db()
    ticket_id = f"ticket_{uuid.uuid4().hex[:12]}"
    ticket_num = get_next_ticket_number()
    now_str = datetime.utcnow().isoformat()

    user_name = payload.user_name or current_user.display_name or "Anonymous User"
    user_email = payload.user_email or current_user.email

    with get_db() as conn:
        conn.execute("""
            INSERT INTO helpdesk_tickets (
                id, ticket_number, user_id, user_name, user_email,
                subject, category, status, priority, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'open', ?, ?, ?);
        """, (
            ticket_id, ticket_num, current_user.id, user_name, user_email,
            payload.subject, payload.category or "general", payload.priority or "normal",
            now_str, now_str,
        ))

        # Insert initial message
        msg_id = f"msg_{uuid.uuid4().hex[:12]}"
        conn.execute("""
            INSERT INTO helpdesk_messages (
                id, ticket_id, sender_id, sender_name, sender_type, message_type, content, is_internal_note, created_at
            ) VALUES (?, ?, ?, ?, 'user', 'text', ?, 0, ?);
        """, (msg_id, ticket_id, current_user.id, user_name, payload.message, now_str))

    ticket_data = {
        "id": ticket_id,
        "ticket_number": ticket_num,
        "user_id": current_user.id,
        "user_name": user_name,
        "user_email": user_email,
        "subject": payload.subject,
        "category": payload.category or "general",
        "status": "open",
        "priority": payload.priority or "normal",
        "created_at": now_str,
        "updated_at": now_str,
    }

    _csv_logger.log_event(
        event_type="ticket_created",
        status="success",
        details=f"ticket_id={ticket_id},number={ticket_num},subject={payload.subject},priority={payload.priority}",
        filename="helpdesk_events.csv",
    )

    # Broadcast notification to all online operators
    asyncio.create_task(hub.broadcast_to_operators({
        "type": "new_ticket_alert",
        "ticket": ticket_data,
        "message": {
            "id": msg_id,
            "ticket_id": ticket_id,
            "sender_name": user_name,
            "content": payload.message,
            "created_at": now_str,
        }
    }))

    return {"status": "success", "ticket": ticket_data, "message_id": msg_id}


@router.get("/tickets/{ticket_id}", response_model=Dict[str, Any])
async def get_ticket_details(
    ticket_id: str,
    current_user: HelpdeskUser = Depends(get_current_helpdesk_user),
) -> Dict[str, Any]:
    """Retrieve detailed information and full conversation stream for a ticket."""
    init_db()
    with get_db() as conn:
        t_row = conn.execute("SELECT * FROM helpdesk_tickets WHERE id = ?", (ticket_id,)).fetchone()
        if not t_row:
            raise HTTPException(status_code=404, detail="Ticket not found")

        msg_rows = conn.execute("""
            SELECT * FROM helpdesk_messages
            WHERE ticket_id = ?
            ORDER BY created_at ASC
        """, (ticket_id,)).fetchall()

        messages = [dict(m) for m in msg_rows]

    return {
        "status": "success",
        "ticket": dict(t_row),
        "messages": messages,
    }


@router.post("/tickets/{ticket_id}/messages", response_model=Dict[str, Any])
async def send_ticket_message(
    ticket_id: str,
    payload: SendTicketMessageRequest,
    current_user: HelpdeskUser = Depends(get_current_helpdesk_user),
) -> Dict[str, Any]:
    """Send a reply, operator response, or internal note to a ticket."""
    init_db()
    now_str = datetime.utcnow().isoformat()
    msg_id = f"msg_{uuid.uuid4().hex[:12]}"

    with get_db() as conn:
        t_row = conn.execute("SELECT * FROM helpdesk_tickets WHERE id = ?", (ticket_id,)).fetchone()
        if not t_row:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # Determine sender type and display name
        sender_type = payload.sender_type or ("operator" if current_user.role == "admin" else "user")
        sender_name = current_user.display_name or "Support"

        conn.execute("""
            INSERT INTO helpdesk_messages (
                id, ticket_id, sender_id, sender_name, sender_type, message_type, content, is_internal_note, created_at
            ) VALUES (?, ?, ?, ?, ?, 'text', ?, ?, ?);
        """, (
            msg_id, ticket_id, current_user.id, sender_name,
            sender_type, payload.content, 1 if payload.is_internal_note else 0, now_str,
        ))

        # Update ticket updated_at
        new_status = t_row["status"]
        if sender_type == "operator" and new_status == "open":
            new_status = "in_progress"

        conn.execute("""
            UPDATE helpdesk_tickets
            SET updated_at = ?, status = ?
            WHERE id = ?;
        """, (now_str, new_status, ticket_id))

    msg_data = {
        "id": msg_id,
        "ticket_id": ticket_id,
        "sender_id": current_user.id,
        "sender_name": sender_name,
        "sender_type": sender_type,
        "message_type": "text",
        "content": payload.content,
        "is_internal_note": bool(payload.is_internal_note),
        "created_at": now_str,
    }

    _csv_logger.log_event(
        event_type="ticket_message_sent",
        status="success",
        details=f"ticket_id={ticket_id},sender_type={sender_type},msg_id={msg_id}",
        filename="helpdesk_events.csv",
    )

    # Broadcast message to ticket subscribers and operators
    asyncio.create_task(hub.broadcast_to_ticket(ticket_id, {
        "type": "new_ticket_message",
        "message": msg_data,
        "ticket_id": ticket_id,
        "status": new_status,
    }))

    return {"status": "success", "message": msg_data}


@router.patch("/tickets/{ticket_id}", response_model=Dict[str, Any])
@router.put("/tickets/{ticket_id}", response_model=Dict[str, Any])
async def update_ticket(
    ticket_id: str,
    payload: UpdateTicketStatusRequest,
    current_user: HelpdeskUser = Depends(get_current_helpdesk_user),
) -> Dict[str, Any]:
    """Modify ticket status, priority, or operator assignment."""
    init_db()
    now_str = datetime.utcnow().isoformat()

    with get_db() as conn:
        t_row = conn.execute("SELECT * FROM helpdesk_tickets WHERE id = ?", (ticket_id,)).fetchone()
        if not t_row:
            raise HTTPException(status_code=404, detail="Ticket not found")

        updates: List[str] = ["updated_at = ?"]
        params: List[Any] = [now_str]

        if payload.status is not None:
            updates.append("status = ?")
            params.append(payload.status)
            if payload.status in ("resolved", "closed"):
                updates.append("closed_at = ?")
                params.append(now_str)
            else:
                updates.append("closed_at = NULL")

        if payload.priority is not None:
            updates.append("priority = ?")
            params.append(payload.priority)

        if payload.assigned_to is not None:
            updates.append("assigned_to = ?")
            params.append(payload.assigned_to)
            updates.append("assigned_name = ?")
            params.append(payload.assigned_name or current_user.display_name)

        params.append(ticket_id)
        conn.execute(f"UPDATE helpdesk_tickets SET {', '.join(updates)} WHERE id = ?", params)

        updated_row = conn.execute("SELECT * FROM helpdesk_tickets WHERE id = ?", (ticket_id,)).fetchone()

    updated_dict = dict(updated_row)

    if payload.status is not None:
        _csv_logger.log_param_change(
            param_name=f"ticket_{ticket_id}_status",
            old_value=t_row["status"],
            new_value=payload.status,
            status="success",
            details=f"priority={updated_dict.get('priority')}",
            filename="helpdesk_param_changes.csv",
        )

    # Broadcast update event
    asyncio.create_task(hub.broadcast_to_ticket(ticket_id, {
        "type": "ticket_updated",
        "ticket": updated_dict,
    }))

    return {"status": "success", "ticket": updated_dict}


@router.put("/tickets/{ticket_id}/status", response_model=Dict[str, Any])
async def update_ticket_status_direct(
    ticket_id: str,
    payload: UpdateTicketStatusRequest,
    current_user: HelpdeskUser = Depends(get_current_helpdesk_user),
) -> Dict[str, Any]:
    """Direct endpoint to update ticket status."""
    return await update_ticket(ticket_id=ticket_id, payload=payload, current_user=current_user)


@router.put("/tickets/{ticket_id}/priority", response_model=Dict[str, Any])
async def update_ticket_priority_direct(
    ticket_id: str,
    payload: UpdateTicketStatusRequest,
    current_user: HelpdeskUser = Depends(get_current_helpdesk_user),
) -> Dict[str, Any]:
    """Direct endpoint to update ticket priority."""
    return await update_ticket(ticket_id=ticket_id, payload=payload, current_user=current_user)


@router.get("/stats", response_model=Dict[str, Any])
async def get_helpdesk_stats() -> Dict[str, Any]:
    """Retrieve aggregate statistics for helpdesk management dashboard."""
    init_db()
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) as c FROM helpdesk_tickets;").fetchone()["c"]
        open_cnt = conn.execute("SELECT COUNT(*) as c FROM helpdesk_tickets WHERE status = 'open';").fetchone()["c"]
        in_prog = conn.execute("SELECT COUNT(*) as c FROM helpdesk_tickets WHERE status = 'in_progress';").fetchone()["c"]
        resolved = conn.execute("SELECT COUNT(*) as c FROM helpdesk_tickets WHERE status = 'resolved';").fetchone()["c"]
        closed = conn.execute("SELECT COUNT(*) as c FROM helpdesk_tickets WHERE status = 'closed';").fetchone()["c"]
        urgent = conn.execute("SELECT COUNT(*) as c FROM helpdesk_tickets WHERE priority = 'urgent' AND status NOT IN ('resolved', 'closed');").fetchone()["c"]

    stats = HelpdeskStats(
        total_tickets=total,
        open_tickets=open_cnt,
        in_progress_tickets=in_prog,
        resolved_tickets=resolved,
        closed_tickets=closed,
        urgent_tickets=urgent,
    )

    _csv_logger.log_poll(
        poll_type="stats",
        metric_name="total_tickets",
        value=total,
        unit="count",
        status="ok",
        details=f"open={open_cnt},in_prog={in_prog},resolved={resolved},urgent={urgent}",
        filename="helpdesk_polls.csv",
    )

    return {"status": "success", "stats": stats.model_dump()}


@router.websocket("/ws/{client_id}")
async def helpdesk_websocket(
    websocket: WebSocket,
    client_id: str,
    role: Optional[str] = Query("user"),
) -> None:
    """Real-time bidirectional WebSocket connection for Helpdesk clients and operators."""
    is_operator = role in ("admin", "operator")
    await hub.connect(client_id, websocket, is_operator=is_operator)

    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                packet = json.loads(raw_data)
            except Exception:
                continue

            action = packet.get("action") or packet.get("type")

            if action == "subscribe_ticket":
                ticket_id = packet.get("ticket_id")
                if ticket_id:
                    hub.subscribe_ticket(ticket_id, client_id)

            elif action == "unsubscribe_ticket":
                ticket_id = packet.get("ticket_id")
                if ticket_id:
                    hub.unsubscribe_ticket(ticket_id, client_id)

            elif action == "typing_start":
                ticket_id = packet.get("ticket_id")
                if ticket_id:
                    await hub.broadcast_to_ticket(ticket_id, {
                        "type": "typing_start",
                        "ticket_id": ticket_id,
                        "client_id": client_id,
                        "name": packet.get("name", "Support Operator"),
                    })

            elif action == "typing_stop":
                ticket_id = packet.get("ticket_id")
                if ticket_id:
                    await hub.broadcast_to_ticket(ticket_id, {
                        "type": "typing_stop",
                        "ticket_id": ticket_id,
                        "client_id": client_id,
                    })

    except WebSocketDisconnect:
        await hub.disconnect(client_id, websocket)
    except Exception as e:
        logger.error(f"Helpdesk WebSocket error for {client_id}: {e}")
        await hub.disconnect(client_id, websocket)


def init_router() -> APIRouter:
    """Initialize and export Helpdesk router instance."""
    init_db()
    return router
