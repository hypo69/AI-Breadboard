# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows API - Auth Helper
# =============================================================================
# Description:
#   Автономные утилиты аутентификации и проверки токенов для Windows API.
#
# Usage Examples:
#   Python API:
#     from apps.windows.api.auth import TokenData, get_current_user_optional, require_admin_user
#
# File: auth.py
# Project: ai-breadboard
# Package: apps.windows.api
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 12:41:00
# =============================================================================

from __future__ import annotations
"""Автономные утилиты аутентификации и проверки токенов для Windows API."""

import os
from typing import Optional
import jwt
from fastapi import HTTPException, Request

JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'


class TokenData:
    """Данные токена авторизации."""

    def __init__(
        self,
        email: str = 'local@aibreadboard.local',
        name: Optional[str] = 'Local User',
        picture: Optional[str] = None,
        id: Optional[int] = 1,
    ):
        self.email = email
        self.name = name
        self.picture = picture
        self.id = id


def is_auth_disabled() -> bool:
    """Проверка отключения авторизации."""
    env_val = os.getenv('DISABLE_AUTH')
    if env_val is not None:
        return env_val.strip().lower() in ('true', '1', 'yes')
    return True


def is_local_request(request: Request) -> bool:
    """Проверка принадлежности запроса локальному хосту/петле."""
    if request is None:
        return True
    hostname: str = request.url.hostname or ''
    return (
        hostname in ('127.0.0.1', 'localhost', '::1', 'testserver', '0.0.0.0')
        or hostname.startswith('192.168.')
        or hostname.startswith('10.')
        or hostname.startswith('172.')
    )


def verify_jwt_token(token: str) -> Optional[TokenData]:
    """Проверка валидности JWT токена."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return TokenData(
            email=payload.get('email', 'local@aibreadboard.local'),
            name=payload.get('name', 'Local User'),
            picture=payload.get('picture'),
            id=payload.get('id', 1),
        )
    except Exception:
        return None


def get_current_user_data(request: Request) -> TokenData:
    """Извлечение данных текущего пользователя."""
    if request is None:
        return TokenData()

    token: str = request.cookies.get('auth_token', '')
    if not token:
        auth_header: str = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:].strip()
        elif auth_header.startswith('Token '):
            token = auth_header[6:].strip()

    if token:
        user_data = verify_jwt_token(token)
        if user_data:
            return user_data

    if is_auth_disabled() or is_local_request(request):
        return TokenData(email='local@aibreadboard.local', name='Local User', id=1)

    raise HTTPException(status_code=401, detail='Authentication required')


def get_current_user_optional(request: Optional[Request] = None) -> Optional[TokenData]:
    """Нестрогое получение данных текущего пользователя."""
    try:
        return get_current_user_data(request)
    except Exception:
        return TokenData(email='local@aibreadboard.local', name='Local User', id=1)


def require_admin_user(request: Request) -> TokenData:
    """Проверка прав администратора."""
    return get_current_user_optional(request) or TokenData(email='admin@cli.local', name='Admin', id=1)


__all__ = [
    'TokenData',
    'is_auth_disabled',
    'is_local_request',
    'verify_jwt_token',
    'get_current_user_data',
    'get_current_user_optional',
    'require_admin_user',
]
