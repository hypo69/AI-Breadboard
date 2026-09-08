# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Loading Gemini API keys from unified environment storage
# =============================================================================
# Description:
#   Loads and manages Google Gemini API authentication keys from .env.
#   Provides backwards-compatible functions to retrieve all keys, get keys by name,
#   and load active keys with proper filtering by status and quota restrictions.
#
# File: secrets_loader.py
# Project: ai-breadboard
# Package: src.ai.gemini
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from src.secrets.api_key_state import (
    _get_merged_keys_data,
    _read_env_keys,
    load_api_keys as state_load_api_keys,
)


def load_secrets() -> Dict[str, str]:
    """Load API keys mapping from environment storage.

    Returns:
        Dict[str, str]: Dictionary mapping key names to API keys.
    """
    return _read_env_keys()


def get_all_keys() -> List[str]:
    """Returns list of all API keys.

    Returns:
        List[str]: List of API key values.
    """
    secrets = load_secrets()
    return list(secrets.values())


def get_all_key_names() -> List[str]:
    """Returns list of all key names.

    Returns:
        List[str]: List of key identifiers.
    """
    secrets = load_secrets()
    return list(secrets.keys())


def get_key_by_name(name: str) -> Optional[str]:
    """Returns API key by name.

    Args:
        name (str): Key identifier.

    Returns:
        Optional[str]: API key value or None if not found.
    """
    secrets = load_secrets()
    return secrets.get(name)


def load_api_keys(
    names: Optional[List[str]] = [],
    skip_exhausted: bool = True,
) -> Tuple[List[str], List[str], List[Any]]:
    """Load active API keys.

    Args:
        names (Optional[List[str]]): Optional list of key names.
        skip_exhausted (bool): Whether to skip quota-exhausted keys.

    Returns:
        Tuple[List[str], List[str], List[Any]]: (api_keys, key_names, key_states)
    """
    return state_load_api_keys(names=names, skip_exhausted=skip_exhausted)
