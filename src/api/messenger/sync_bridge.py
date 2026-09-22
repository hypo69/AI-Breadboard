# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: WordPress Synchronization Bridge and SSO Manager
# =============================================================================
# Description:
#   Synchronizes WordPress user accounts, membership roles, and avatar profiles
#   into the Messenger database, verifying HMAC webhooks and signed SSO tokens.
#
# File: sync_bridge.py
# Project: ai-breadboard
# Package: src.api.messenger
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import hmac
import hashlib
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import jwt
from header import __root__
from logger import logger
from .database import get_db
from .models import UserSyncPayload


def get_sync_secret() -> str:
    """Retrieve shared synchronization secret key from environment or default."""
    return os.getenv("MESSENGER_SYNC_SECRET", "breadboard_messenger_secret_key_2026")


def verify_wp_signature(payload_bytes: bytes, signature_header: str) -> bool:
    """Validate incoming WordPress HMAC-SHA256 webhook signature.

    Args:
        payload_bytes (bytes): Raw request body.
        signature_header (str): Value of 'X-WP-Signature' header.

    Returns:
        bool: True if signature matches secret, False otherwise.
    """
    if not signature_header:
        return False
    secret = get_sync_secret().encode("utf-8")
    expected = hmac.new(secret, payload_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def upsert_user(payload: UserSyncPayload) -> Dict[str, Any]:
    """Insert or update a user account in the messenger database.

    Args:
        payload (UserSyncPayload): Validated user data from WordPress or native auth.

    Returns:
        Dict[str, Any]: Persisted user record dictionary.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        user_id = str(payload.id)
        display_name = payload.display_name or payload.username

        cursor.execute("""
            INSERT INTO messenger_users (id, email, username, display_name, avatar_url, source, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                email = excluded.email,
                username = excluded.username,
                display_name = excluded.display_name,
                avatar_url = excluded.avatar_url,
                source = excluded.source,
                last_seen = excluded.last_seen;
        """, (
            user_id,
            payload.email,
            payload.username,
            display_name,
            payload.avatar_url,
            payload.source,
            datetime.utcnow().isoformat()
        ))

        row = cursor.execute("SELECT * FROM messenger_users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else {}


def create_sso_token(user_id: str, email: str, display_name: str, expiry_hours: int = 72) -> str:
    """Generate a signed JWT SSO token for authenticating in the messenger.

    Args:
        user_id (str): User identifier.
        email (str): User email.
        display_name (str): Full display name.
        expiry_hours (int): Token lifetime in hours.

    Returns:
        str: Encoded JWT string.
    """
    payload = {
        "sub": str(user_id),
        "email": email,
        "name": display_name,
        "iss": "ai-breadboard-messenger",
        "exp": datetime.utcnow() + timedelta(hours=expiry_hours),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, get_sync_secret(), algorithm="HS256")


def verify_sso_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a signed SSO JWT token.

    Args:
        token (str): JWT string.

    Returns:
        Optional[Dict[str, Any]]: Decoded payload if valid, None otherwise.
    """
    try:
        return jwt.decode(token, get_sync_secret(), algorithms=["HS256"])
    except Exception as e:
        logger.warning(f"SSO token validation failed: {e}")
        return None
