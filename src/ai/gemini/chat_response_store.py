# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Store user-approved model responses to JSON files
# =============================================================================
# Description:
#   Stores model responses explicitly approved by user to JSON files.
#   Manages persistence of chat and voice text responses with metadata
#   including timestamps, user IDs, and unique identifiers for auditing.
#
# File: chat_response_store.py
# Project: ai-breadboard
# Package: src.ai.gemini
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import uuid
from datetime import datetime
from pathlib import Path

from src.logger import logger

# Directory for storing approved responses
_STORE_DIR = Path(__file__).parent.parent.parent / 'plugins' / 'media_organizer' / 'data' / 'chat_responses'
_STORE_DIR.mkdir(parents=True, exist_ok=True)

def save_approved_response(user_id: str, query: str, chat_text: str, voice_text: str = '') -> bool:
    """Save user-approved model response to JSON file.

    Args:
        user_id: User identifier (database ID or anon_<ip>).
        query: Original user query.
        chat_text: Model response text for chat.
        voice_text: Model response text for voice narrator (optional).

    Returns:
        True if save successful, otherwise False.
    """
    try:
        entry = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': str(user_id),
            'query': query,
            'chat_text': chat_text,
            'voice_text': voice_text,
        }
        filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{entry['id'][:8]}.json"
        filepath = _STORE_DIR / filename
        filepath.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding='utf-8')
        logger.info(f"[ChatResponseStore] Approved response saved: {filename}")
        return True
    except Exception as ex:
        logger.error('[ChatResponseStore] Error saving response', ex)
        return False

def list_responses(user_id: str = '') -> list[dict]:
    """Return list of all stored approved responses (optionally filtered by user_id).

    Args:
        user_id: If provided — return only records for this user.

    Returns:
        List of dictionaries with response data.
    """
    results = []
    for fp in sorted(_STORE_DIR.glob('*.json')):
        try:
            entry = json.loads(fp.read_text(encoding='utf-8'))
            if user_id and entry.get('user_id') != str(user_id):
                continue
            results.append(entry)
        except Exception as ex:
            logger.error(f'[ChatResponseStore] Error reading file {fp.name}', ex)
    return results

def update_response(doc_id: str, query: str, chat_text: str, voice_text: str = '') -> bool:
    """Update saved dialog content on disk by its ID.

    Args:
        doc_id: Document ID.
        query: New request text.
        chat_text: New model response.
        voice_text: New narrator text.

    Returns:
        True on success, otherwise False.
    """
    try:
        for fp in _STORE_DIR.glob('*.json'):
            try:
                entry = json.loads(fp.read_text(encoding='utf-8'))
                if entry.get('id') == doc_id:
                    entry['query'] = query
                    entry['chat_text'] = chat_text
                    entry['voice_text'] = voice_text
                    fp.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding='utf-8')
                    logger.info(f"[ChatResponseStore] RAG response updated: {fp.name}")
                    return True
            except Exception as ex:
                logger.error(f"[ChatResponseStore] Error parsing during update {fp.name}", ex)
        return False
    except Exception as ex:
        logger.error('[ChatResponseStore] Error updating response', ex)
        return False

def delete_response(doc_id: str) -> bool:
    """Delete saved dialog file from disk by its ID.

    Args:
        doc_id: Document ID.

    Returns:
        True on success, otherwise False.
    """
    try:
        for fp in _STORE_DIR.glob('*.json'):
            try:
                entry = json.loads(fp.read_text(encoding='utf-8'))
                if entry.get('id') == doc_id:
                    fp.unlink()
                    logger.info(f"[ChatResponseStore] RAG response deleted: {fp.name}")
                    return True
            except Exception as ex:
                logger.error(f"[ChatResponseStore] Error parsing during delete {fp.name}", ex)
        return False
    except Exception as ex:
        logger.error('[ChatResponseStore] Error deleting response', ex)
        return False
