# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Update access_token using refresh_token
# =============================================================================
# Description:
#   Module for Google API interaction with OAuth token management.
#
# File: google_services.py
# Project: ai-breadboard
# Package: core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, List

import requests

from core.logger import logger
from core.user_manager import user_manager

def refresh_google_access_token(user_id: int) -> str:
    """Update access_token с использованием refresh_token.

    Args:
        user_id (int): Идентификатор пользователя.

    Returns:
        str: Новый access_token или пустая string при ошибке.
    """
    token_record = user_manager.get_google_tokens(user_id)
    refresh_token = token_record.get('refresh_token', '')
    if not refresh_token:
        logger.warning(f'Refresh token отсутствует для user_id={user_id}')
        return ''

    from core.fastapi.router_auth import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        logger.error('Google OAuth Client ID или Secret не настроены')
        return ''

    token_url = 'https://oauth2.googleapis.com/token'
    data = {
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token',
    }

    try:
        response = requests.post(token_url, data=data, timeout=10)
        response.raise_for_status()
        token_data = response.json()
        new_access_token = token_data.get('access_token', '')
        expires_in = token_data.get('expires_in', 3600)
        scope = token_data.get('scope', token_record.get('scope', ''))

        if new_access_token:
            user_manager.save_google_tokens(
                user_id=user_id,
                access_token=new_access_token,
                refresh_token=refresh_token,
                expires_in=int(expires_in),
                scope=scope
            )
            logger.info(f'Successfully обновлен access_token для user_id={user_id}')
            return new_access_token
        return ''
    except Exception as ex:
        logger.error(f'Error обновления Google access token для user_id={user_id}:', ex, False)
        return ''

def get_valid_google_access_token(user_id: int) -> str:
    """Получение действующего access_token с проверкой срока жизни.

    Args:
        user_id (int): Идентификатор пользователя.

    Returns:
        str: Valid access_token или пустая string.
    """
    token_record = user_manager.get_google_tokens(user_id)
    if not token_record:
        return ''

    access_token = token_record.get('access_token', '')
    expires_at_str = token_record.get('expires_at', '')

    if not access_token:
        return ''

    if expires_at_str:
        try:
            expires_at = datetime.fromisoformat(expires_at_str)
            now = datetime.utcnow()
            # Если токен истекает менее чем через 60 секунд — обновляем
            if (expires_at - now).total_seconds() < 60:
                logger.info(f'Срок действия токена истекает, запуск обновления для user_id={user_id}')
                refreshed = refresh_google_access_token(user_id)
                if refreshed:
                    return refreshed
        except Exception:
            pass

    return access_token

def get_google_headers(user_id: int) -> Dict[str, str]:
    """Formation заголовков авторизации для Google API.

    Args:
        user_id (int): Идентификатор пользователя.

    Returns:
        Dict[str, str]: Заголовки HTTP запроса.
    """
    token = get_valid_google_access_token(user_id)
    if not token:
        return {}
    return {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json',
    }

# =============================================================================
# Google Calendar API
# =============================================================================

def get_google_calendar_events(user_id: int, time_min: str = '', max_results: int = 20) -> List[Dict[str, Any]]:
    """Получение событий из основного календаря Google.

    Args:
        user_id (int): Идентификатор пользователя.
        time_min (str): Минимальное время (ISO 8601). По умолчанию текущее время.
        max_results (int): Максимальное количество событий.

    Returns:
        List[Dict[str, Any]]: List событий.
    """
    headers = get_google_headers(user_id)
    if not headers:
        return []

    if not time_min:
        time_min = datetime.utcnow().isoformat() + 'Z'

    url = 'https://www.googleapis.com/calendar/v3/calendars/primary/events'
    params = {
        'timeMin': time_min,
        'singleEvents': 'true',
        'orderBy': 'startTime',
        'maxResults': max_results,
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json().get('items', [])
    except Exception as ex:
        logger.error(f'Error получения событий Google Calendar для user_id={user_id}:', ex, False)
        return []

# =============================================================================
# Google Contacts API (People API)
# =============================================================================

def get_google_contacts(user_id: int, page_size: int = 50) -> List[Dict[str, Any]]:
    """Получение списка контактов Google пользователя.

    Args:
        user_id (int): Идентификатор пользователя.
        page_size (int): Количество контактов на страницу.

    Returns:
        List[Dict[str, Any]]: List контактов.
    """
    headers = get_google_headers(user_id)
    if not headers:
        return []

    url = 'https://people.googleapis.com/v1/people/me/connections'
    params = {
        'personFields': 'names,emailAddresses,phoneNumbers,photos',
        'pageSize': page_size,
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json().get('connections', [])
    except Exception as ex:
        logger.error(f'Error получения контактов Google для user_id={user_id}:', ex, False)
        return []

# =============================================================================
# Google Drive & Docs API
# =============================================================================

def list_google_documents(user_id: int, page_size: int = 20) -> List[Dict[str, Any]]:
    """Получение списка Google Документов пользователя.

    Args:
        user_id (int): Идентификатор пользователя.
        page_size (int): Количество документов.

    Returns:
        List[Dict[str, Any]]: List файлов Google Docs.
    """
    headers = get_google_headers(user_id)
    if not headers:
        return []

    url = 'https://www.googleapis.com/drive/v3/files'
    params = {
        'q': "mimeType='application/vnd.google-apps.document' and trashed=false",
        'fields': 'files(id, name, createdTime, modifiedTime, webViewLink)',
        'pageSize': page_size,
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json().get('files', [])
    except Exception as ex:
        logger.error(f'Error получения списка Google Docs для user_id={user_id}:', ex, False)
        return []

def get_google_document_content(user_id: int, document_id: str) -> Dict[str, Any]:
    """Получение содержимого конкретного Google Документа.

    Args:
        user_id (int): Идентификатор пользователя.
        document_id (str): Идентификатор документа Google Docs.

    Returns:
        Dict[str, Any]: Структура документа или empty dictionary.
    """
    headers = get_google_headers(user_id)
    if not headers:
        return {}

    url = f'https://docs.googleapis.com/v1/documents/{document_id}'
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as ex:
        logger.error(f'Error чтения Google Document {document_id}:', ex, False)
        return {}
