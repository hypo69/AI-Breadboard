# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: API Key State and Quota Management
# =============================================================================
# Description:
#   Manages Google Gemini and AI provider API keys, rotation pools,
#   quota exhaustion cooldowns, and runtime state persistence.
#
# File: api_key_state.py
# Project: ai-breadboard
# Package: core.secrets
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from header import __root__
from core.logger.logger import logger

_SECRETS_DIR: Path = __root__ / 'core' / 'secrets'
_KEYS_FILE: Path = _SECRETS_DIR / 'gemini_keys.json'
_LEGACY_SECRETS_FILE: Path = __root__ / 'core' / 'ai' / 'gemini' / 'secrets.json'
_ENV_FILE: Path = __root__ / '.env'
_DAY_SECONDS: float = 86400.0


def _ensure_secrets_dir() -> None:
    """Ensure that the secrets directory exists on the filesystem."""
    try:
        _SECRETS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as ex:
        logger.error(f'Failed to create secrets directory: {ex}')


def _now_iso() -> str:
    """Get current UTC timestamp in ISO 8601 string format.

    Returns:
        str: ISO formatted UTC datetime.
    """
    return datetime.now(timezone.utc).isoformat()


def _now_ts() -> float:
    """Get current UTC timestamp as Unix epoch float.

    Returns:
        float: Unix timestamp in seconds.
    """
    return datetime.now(timezone.utc).timestamp()


def _iso_to_ts(iso_str: str) -> float:
    """Convert ISO formatted string into Unix timestamp.

    Args:
        iso_str (str): Datetime string in ISO 8601 format.

    Returns:
        float: Unix epoch timestamp or 0.0 on parsing error.
    """
    if not iso_str:
        return 0.0
    try:
        cleaned = iso_str.replace('Z', '+00:00')
        return datetime.fromisoformat(cleaned).timestamp()
    except Exception:
        return 0.0


def _load_json_file(file_path: Path) -> Dict[str, Any]:
    """Safely load JSON object from file path.

    Args:
        file_path (Path): Path to JSON file.

    Returns:
        Dict[str, Any]: Parsed JSON dictionary or empty dictionary.
    """
    if not file_path.exists():
        return {}
    try:
        content = file_path.read_text(encoding='utf-8').strip()
        if not content:
            return {}
        data = json.loads(content)
        if isinstance(data, dict):
            return data
    except Exception as ex:
        logger.warning(f'Error reading JSON file {file_path}: {ex}')
    return {}


def _save_json_file(file_path: Path, data: Dict[str, Any]) -> bool:
    """Safely save dictionary as formatted JSON to file.

    Args:
        file_path (Path): Target file destination.
        data (Dict[str, Any]): Dictionary to serialize.

    Returns:
        bool: True on success, False on error.
    """
    try:
        _ensure_secrets_dir()
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
        return True
    except Exception as ex:
        logger.error(f'Failed to save JSON to {file_path}: {ex}')
        return False


def _read_env_keys() -> Dict[str, str]:
    """Read API keys defined in environment variables and .env file.

    Returns:
        Dict[str, str]: Mapping of key names/identifiers to API key strings.
    """
    keys_found: Dict[str, str] = {}

    # Check process environment
    env_gemini = os.getenv('GEMINI_API_KEY', '').strip()
    if env_gemini:
        keys_found['GEMINI_API_KEY'] = env_gemini

    env_google = os.getenv('GOOGLE_API_KEY', '').strip()
    if env_google and env_google != env_gemini:
        keys_found['GOOGLE_API_KEY'] = env_google

    env_agy = os.getenv('AGY_API_KEY', '').strip()
    if env_agy:
        keys_found['AGY_API_KEY'] = env_agy

    # Multiple comma-separated keys in GEMINI_API_KEYS
    multi_keys = os.getenv('GEMINI_API_KEYS', '').strip()
    if multi_keys:
        for idx, k in enumerate(multi_keys.split(','), start=1):
            cleaned = k.strip()
            if cleaned:
                keys_found[f'gemini_env_{idx}'] = cleaned

    # Parse .env directly if file exists
    if _ENV_FILE.exists():
        try:
            lines = _ENV_FILE.read_text(encoding='utf-8').splitlines()
            for line in lines:
                trimmed = line.strip()
                if not trimmed or trimmed.startswith('#') or '=' not in trimmed:
                    continue
                k, v = trimmed.split('=', 1)
                k_clean = k.strip()
                v_clean = v.strip().strip('"').strip("'")
                if k_clean in ('GEMINI_API_KEY', 'GOOGLE_API_KEY', 'AGY_API_KEY') and v_clean:
                    if k_clean not in keys_found:
                        keys_found[k_clean] = v_clean
        except Exception as ex:
            logger.warning(f'Could not read .env file for keys: {ex}')

    return keys_found


def _get_merged_keys_data() -> Dict[str, Dict[str, Any]]:
    """Load and merge keys from all storage locations and environment.

    Returns:
        Dict[str, Dict[str, Any]]: Unified dictionary of keys with metadata.
    """
    merged: Dict[str, Dict[str, Any]] = {}

    # 1. Load from gemini_keys.json
    primary_data = _load_json_file(_KEYS_FILE)
    for name, entry in primary_data.items():
        if isinstance(entry, dict):
            api_key = str(entry.get('api_key', '')).strip()
            merged[name] = {
                'api_key': api_key,
                'status': str(entry.get('status', 'active')),
                'last_run': entry.get('last_run', ''),
                'exhausted_at': entry.get('exhausted_at', ''),
            }
        elif isinstance(entry, str) and entry.strip():
            merged[name] = {
                'api_key': entry.strip(),
                'status': 'active',
                'last_run': '',
                'exhausted_at': '',
            }

    # 2. Load from legacy secrets.json
    legacy_data = _load_json_file(_LEGACY_SECRETS_FILE)
    for name, entry in legacy_data.items():
        if name not in merged:
            if isinstance(entry, dict):
                api_key = str(entry.get('api_key', '')).strip()
                merged[name] = {
                    'api_key': api_key,
                    'status': str(entry.get('status', 'active')),
                    'last_run': entry.get('last_run', ''),
                    'exhausted_at': entry.get('exhausted_at', ''),
                }
            elif isinstance(entry, str) and entry.strip():
                merged[name] = {
                    'api_key': entry.strip(),
                    'status': 'active',
                    'last_run': '',
                    'exhausted_at': '',
                }

    # 3. Load from environment variables
    env_keys = _read_env_keys()
    for name, key_val in env_keys.items():
        if name not in merged and key_val:
            merged[name] = {
                'api_key': key_val,
                'status': 'active',
                'last_run': '',
                'exhausted_at': '',
            }

    return merged


def load_api_keys(
    names: Optional[List[str]] = [],
    skip_exhausted: bool = True,
) -> Tuple[List[str], List[str], List[Any]]:
    """Load API keys filtered by active status and optional name criteria.

    Args:
        names (Optional[List[str]]): Specific key names to load, or empty/None for all.
        skip_exhausted (bool): Whether to skip keys in 24h exhaustion cooldown.

    Returns:
        Tuple[List[str], List[str], List[Any]]:
            - list of valid API key strings
            - list of corresponding key names
            - list of key status/metadata objects
    """
    keys_data = _get_merged_keys_data()
    now = _now_ts()

    # Determine desired names if specified
    filter_names: List[str] = []
    if names:
        if isinstance(names, str):
            filter_names = [n.strip() for n in str(names).split(',') if n.strip()]
        elif isinstance(names, (list, tuple, set)):
            filter_names = [str(n).strip() for n in names if str(n).strip()]

    # Also check GEMINI_API_KEY_NAMES if no names explicitly provided
    if not filter_names:
        env_names_str = os.getenv('GEMINI_API_KEY_NAMES', '').strip()
        if env_names_str and env_names_str != '*':
            filter_names = [n.strip() for n in env_names_str.split(',') if n.strip()]

    result_keys: List[str] = []
    result_names: List[str] = []
    result_states: List[Any] = []
    updated_needed: bool = False

    for name, data in keys_data.items():
        api_key = data.get('api_key', '').strip()
        if not api_key:
            continue

        # Filter by name if criteria active
        if filter_names and name not in filter_names and api_key not in filter_names:
            continue

        exhausted_at = data.get('exhausted_at', '')
        is_exhausted = False

        if exhausted_at:
            exhausted_ts = _iso_to_ts(exhausted_at)
            elapsed = now - exhausted_ts
            if 0 <= elapsed < _DAY_SECONDS:
                is_exhausted = True
            else:
                # 24h period expired, auto-reset exhaustion status
                data['exhausted_at'] = ''
                data['status'] = 'active'
                updated_needed = True

        if skip_exhausted and is_exhausted:
            continue

        if data.get('status') == 'disabled':
            continue

        result_keys.append(api_key)
        result_names.append(name)
        result_states.append(data)

    if updated_needed:
        _save_json_file(_KEYS_FILE, keys_data)

    # Fallback to direct raw key in filter_names if nothing matched in storage
    if not result_keys and filter_names:
        for item in filter_names:
            if item.startswith('AIza') or len(item) >= 20:
                result_keys.append(item)
                result_names.append('direct_key')
                result_states.append({'api_key': item, 'status': 'active'})

    return result_keys, result_names, result_states


def mark_exhausted(key_name: str) -> None:
    """Mark an API key as quota exhausted and start 24h cooldown timer.

    Args:
        key_name (str): The identifier or raw value of the key to mark.
    """
    if not key_name:
        return

    keys_data = _get_merged_keys_data()
    target_name = key_name

    # If key_name is not direct dict key, search by api_key value
    if target_name not in keys_data:
        for name, data in keys_data.items():
            if data.get('api_key') == key_name:
                target_name = name
                break

    if target_name not in keys_data:
        keys_data[target_name] = {
            'api_key': key_name if key_name.startswith('AIza') else '',
            'status': 'exhausted',
            'last_run': '',
            'exhausted_at': _now_iso(),
        }
    else:
        keys_data[target_name]['exhausted_at'] = _now_iso()
        keys_data[target_name]['status'] = 'exhausted'

    _save_json_file(_KEYS_FILE, keys_data)
    logger.warning(f'API key "{target_name}" marked as exhausted (24h cooldown initiated).')


def update_last_run(key_name: str) -> None:
    """Update last executed timestamp for specified API key.

    Args:
        key_name (str): Identifier of the key that was executed.
    """
    if not key_name:
        return

    keys_data = _get_merged_keys_data()
    target_name = key_name

    if target_name not in keys_data:
        for name, data in keys_data.items():
            if data.get('api_key') == key_name:
                target_name = name
                break

    if target_name in keys_data:
        keys_data[target_name]['last_run'] = _now_iso()
        _save_json_file(_KEYS_FILE, keys_data)


def next_available_in() -> float:
    """Calculate remaining seconds until the earliest exhausted key becomes available.

    Returns:
        float: Seconds remaining until reset, or 0.0 if any keys are already available.
    """
    keys_data = _get_merged_keys_data()
    if not keys_data:
        return 0.0

    now = _now_ts()
    min_wait: float = _DAY_SECONDS
    found_exhausted = False

    for name, data in keys_data.items():
        if data.get('status') == 'disabled':
            continue
        exhausted_at = data.get('exhausted_at', '')
        if not exhausted_at:
            return 0.0  # At least one key is active and ready
        exhausted_ts = _iso_to_ts(exhausted_at)
        elapsed = now - exhausted_ts
        if elapsed >= _DAY_SECONDS:
            return 0.0  # Expired cooldown, ready now
        found_exhausted = True
        remaining = _DAY_SECONDS - elapsed
        if remaining < min_wait:
            min_wait = remaining

    return min_wait if found_exhausted else 0.0


def get_status(names: Optional[List[str]] = []) -> Dict[str, Any]:
    """Retrieve detailed runtime status for all or selected keys.

    Args:
        names (Optional[List[str]]): List of key names to filter, or empty for all.

    Returns:
        Dict[str, Any]: Dictionary mapping key names to status descriptors.
    """
    keys_data = _get_merged_keys_data()
    now = _now_ts()
    statuses: Dict[str, Any] = {}

    for name, data in keys_data.items():
        if names and name not in names:
            continue
        exhausted_at = data.get('exhausted_at', '')
        is_exhausted = False
        remaining_sec = 0.0

        if exhausted_at:
            elapsed = now - _iso_to_ts(exhausted_at)
            if 0 <= elapsed < _DAY_SECONDS:
                is_exhausted = True
                remaining_sec = _DAY_SECONDS - elapsed

        statuses[name] = {
            'status': data.get('status', 'active'),
            'last_run': data.get('last_run', ''),
            'exhausted_at': exhausted_at,
            'is_exhausted': is_exhausted,
            'reset_in_seconds': int(remaining_sec) if is_exhausted else 0,
        }

    return statuses


def save_api_key(name: str, api_key: str, status: str = 'active') -> bool:
    """Save or update an API key in persistent storage.

    Args:
        name (str): Unique name identifier for the key.
        api_key (str): The raw secret API key string.
        status (str): Initial key status ('active' or 'disabled').

    Returns:
        bool: True if key was successfully saved.
    """
    if not name or not api_key:
        return False

    keys_data = _get_merged_keys_data()
    keys_data[name] = {
        'api_key': api_key.strip(),
        'status': status,
        'last_run': keys_data.get(name, {}).get('last_run', ''),
        'exhausted_at': keys_data.get(name, {}).get('exhausted_at', ''),
    }

    success = _save_json_file(_KEYS_FILE, keys_data)
    if success:
        logger.info(f'API key "{name}" saved successfully to {_KEYS_FILE}.')
    return success
