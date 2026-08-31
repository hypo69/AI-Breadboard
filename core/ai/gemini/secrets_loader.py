# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Loading Gemini API keys from secrets.json file
# =============================================================================
# Description:
#   Loads and manages Google Gemini API authentication keys from local secrets.json.
#   Provides functions to retrieve all keys, get keys by name, and load active keys
#   with proper filtering by status and quota restrictions.
#
# File: secrets_loader.py
# Project: ai-breadboard
# Package: core.ai.gemini
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
from pathlib import Path
from typing import Dict, List, Tuple

# Path to secrets.json file relative to module directory
_SECRETS_FILE = Path(__file__).parent / 'secrets.json'

def load_secrets() -> Dict[str, str]:
    """
    Loading API keys from secrets.json file.

    Returns:
        Dict[str, str]: Dictionary mapping email addresses to API keys.
    """
    if not _SECRETS_FILE.exists():
        return {}
    
    try:
        content = _SECRETS_FILE.read_text(encoding='utf-8')
        return json.loads(content)
    except Exception as ex:
        print(f"Error loading secrets.json: {ex}")
        return {}

def get_all_keys() -> List[str]:
    """
    Returns list of all API keys.

    Returns:
        List[str]: List of API key values.
    """
    secrets = load_secrets()
    return list(secrets.values())

def get_all_key_names() -> List[str]:
    """
    Returns list of all key names (email addresses).

    Returns:
        List[str]: List of key identifiers (email addresses).
    """
    secrets = load_secrets()
    return list(secrets.keys())

def get_key_by_name(name: str) -> str | None:
    """
    Returns API key by name.

    Args:
        name: Key identifier (email address).

    Returns:
        str | None: API key value or None if not found.
    """
    secrets = load_secrets()
    return secrets.get(name)

def load_api_keys(names: List[str] = []) -> Tuple[List[str], List[str], List[str]]:
    """
    Loading API keys sorted by last_run timestamp.
    Filters keys: only active status and not banned (daily quota).

    Args:
        names: Optional list of key names; if empty, loads all from file.

    Returns:
        Tuple[List[str], List[str], List[str]]: (api_keys, key_names, key_names)
    """
    from core.secrets.api_key_state import load_api_keys as state_load_api_keys
    
    # Using existing function with names from secrets.json
    all_names = get_all_key_names()
    
    if names:
        # Filter only names that exist in secrets.json
        names = [n for n in names if n in all_names]
    
    return state_load_api_keys(names)
