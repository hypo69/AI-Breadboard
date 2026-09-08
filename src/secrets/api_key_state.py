# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI Provider API Key State and Rotation Pool Manager
# =============================================================================
# Description:
#   Manages Google Gemini and AI provider API keys, rotation pools, and 24h quota
#   exhaustion cooldowns. Keys are stored as {key_name: {value, last_run, status}}
#   in src/secrets/gemini_keys.json and dynamically injected into GEMINI_API_KEY.
#
# File: api_key_state.py
# Project: ai-breadboard
# Package: src.secrets
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
from src.logger.logger import logger

_SECRETS_DIR: Path = __root__ / 'src' / 'secrets'
_KEYS_FILE: Path = _SECRETS_DIR / 'gemini_keys.json'
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
        str: ISO formatted UTC datetime string.
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


def _load_keys_file() -> Dict[str, Dict[str, Any]]:
    """Load keys data dictionary from gemini_keys.json.

    If file does not exist, attempts initial migration from .env.

    Returns:
        Dict[str, Dict[str, Any]]: Mapping of key_name to key item dict.
    """
    if _KEYS_FILE.exists():
        try:
            content = _KEYS_FILE.read_text(encoding='utf-8').strip()
            if content:
                data = json.loads(content)
                if isinstance(data, dict):
                    # Normalize structure ensuring value, last_run, status fields
                    normalized: Dict[str, Dict[str, Any]] = {}
                    for k, v in data.items():
                        if isinstance(v, dict):
                            val = v.get('value') or v.get('api_key') or ''
                            normalized[k] = {
                                'value': str(val),
                                'last_run': str(v.get('last_run') or ''),
                                'status': str(v.get('status') or 'active'),
                                'exhausted_at': str(v.get('exhausted_at') or ''),
                            }
                        elif isinstance(v, str):
                            normalized[k] = {
                                'value': v,
                                'last_run': '',
                                'status': 'active',
                                'exhausted_at': '',
                            }
                    return normalized
        except Exception as ex:
            logger.warning(f'Error reading {_KEYS_FILE}: {ex}')

    # Bootstrap from .env if gemini_keys.json does not exist yet
    bootstrapped = _bootstrap_from_env()
    if bootstrapped:
        _save_keys_file(bootstrapped)
        return bootstrapped

    return {}


def _bootstrap_from_env() -> Dict[str, Dict[str, Any]]:
    """Extract initial keys from .env if available.

    Returns:
        Dict[str, Dict[str, Any]]: Initial keys structure.
    """
    keys: Dict[str, Dict[str, Any]] = {}
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
                if not v_clean:
                    continue
                if k_clean in ('GEMINI_API_KEY_NAMES', 'GEMINI_API_KEYS'):
                    continue
                if (
                    k_clean == 'GEMINI_API_KEY'
                    or (k_clean.startswith('GEMINI_API_KEY_') and k_clean not in ('GEMINI_API_KEY_NAMES', 'GEMINI_API_KEYS'))
                    or k_clean in ('GEMINI_ANTIGRAVITY_API_KEY', 'AGY_API_KEY')
                    or k_clean.startswith('AGY_API_KEY_')
                ):
                    if v_clean and v_clean != '*':
                        keys[k_clean] = {
                            'value': v_clean,
                            'last_run': '',
                            'status': 'active',
                            'exhausted_at': '',
                        }
        except Exception as ex:
            logger.warning(f'Could not bootstrap keys from .env: {ex}')

    # Check process environment
    for env_k, env_v in os.environ.items():
        if env_k in ('GEMINI_API_KEY_NAMES', 'GEMINI_API_KEYS'):
            continue
        v_clean = env_v.strip().strip('"').strip("'")
        if not v_clean or v_clean == '*':
            continue
        if env_k in ('GEMINI_API_KEY', 'GEMINI_ANTIGRAVITY_API_KEY') and env_k not in keys:
            keys[env_k] = {
                'value': v_clean,
                'last_run': '',
                'status': 'active',
                'exhausted_at': '',
            }

    return keys


def _save_keys_file(data: Dict[str, Dict[str, Any]]) -> bool:
    """Write keys dictionary to JSON file safely.

    Args:
        data (Dict[str, Dict[str, Any]]): Keys data to serialize.

    Returns:
        bool: True on success, False on failure.
    """
    try:
        _ensure_secrets_dir()
        _KEYS_FILE.parent.mkdir(parents=True, exist_ok=True)
        _KEYS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
        return True
    except Exception as ex:
        logger.error(f'Failed to save keys to {_KEYS_FILE}: {ex}')
        return False


def _sync_environment(active_val: str) -> None:
    """Dynamically set the active API key in process environment.

    Args:
        active_val (str): The active secret key value.
    """
    if active_val:
        os.environ['GEMINI_API_KEY'] = active_val


def load_api_keys(
    names: Optional[List[str]] = None,
    skip_exhausted: bool = True,
) -> Tuple[List[str], List[str], List[Dict[str, Any]]]:
    """Load API keys filtered by status and criteria, with dynamic substitution.

    Args:
        names (Optional[List[str]]): Specific key names to load, or empty/None for all.
        skip_exhausted (bool): Whether to skip keys in quota exhaustion.

    Returns:
        Tuple[List[str], List[str], List[Dict[str, Any]]]:
            - list of valid API key values
            - list of corresponding key names
            - list of key dictionaries
    """
    keys_data = _load_keys_file()
    now = _now_ts()

    # Determine desired names filter
    filter_names: List[str] = []
    if names:
        if isinstance(names, str):
            filter_names = [n.strip() for n in str(names).split(',') if n.strip() and n.strip() != '*']
        elif isinstance(names, (list, tuple, set)):
            filter_names = [str(n).strip() for n in names if str(n).strip() and str(n).strip() != '*']

    if not filter_names:
        env_names_str = os.getenv('GEMINI_API_KEY_NAMES', '').strip()
        if env_names_str and env_names_str != '*':
            filter_names = [n.strip() for n in env_names_str.split(',') if n.strip() and n.strip() != '*']

    result_keys: List[str] = []
    result_names: List[str] = []
    result_states: List[Dict[str, Any]] = []
    updated_needed: bool = False

    for name, data in keys_data.items():
        val = data.get('value') or data.get('api_key') or ''
        val = str(val).strip()
        if not val:
            continue

        if filter_names and name not in filter_names and val not in filter_names:
            continue

        status = data.get('status', 'active')
        exhausted_at = data.get('exhausted_at', '')

        # Auto-reset 24h expired cooldowns
        if status == 'exhausted' or exhausted_at:
            ref_ts = _iso_to_ts(exhausted_at) if exhausted_at else _iso_to_ts(data.get('last_run', ''))
            elapsed = now - ref_ts
            if elapsed >= _DAY_SECONDS and ref_ts > 0:
                data['status'] = 'active'
                data['exhausted_at'] = ''
                status = 'active'
                updated_needed = True

        if skip_exhausted and status == 'exhausted':
            continue

        if status == 'disabled':
            continue

        result_keys.append(val)
        result_names.append(name)
        result_states.append(data)

    if updated_needed:
        _save_keys_file(keys_data)

    # Dynamic environment substitution with the first active key
    if result_keys:
        _sync_environment(result_keys[0])

    # Direct raw key fallback if not in file
    if not result_keys and filter_names:
        for item in filter_names:
            if item.startswith('AIza') or len(item) >= 20:
                result_keys.append(item)
                result_names.append('direct_key')
                result_states.append({'value': item, 'status': 'active', 'last_run': ''})
                _sync_environment(item)

    return result_keys, result_names, result_states


def mark_exhausted(key_name: str) -> None:
    """Mark an API key as exhausted and rotate to next available active key.

    Args:
        key_name (str): Key identifier or value to mark exhausted.
    """
    if not key_name:
        return

    keys_data = _load_keys_file()
    target_name = key_name

    if target_name not in keys_data:
        for name, data in keys_data.items():
            if data.get('value') == key_name or data.get('api_key') == key_name:
                target_name = name
                break

    if target_name not in keys_data:
        keys_data[target_name] = {'value': key_name, 'last_run': '', 'status': 'exhausted'}

    now_str = _now_iso()
    keys_data[target_name]['status'] = 'exhausted'
    keys_data[target_name]['exhausted_at'] = now_str
    _save_keys_file(keys_data)
    logger.warning(f'API key "{target_name}" marked as exhausted.')

    # Rotate to next active key in pool
    for name, data in keys_data.items():
        if data.get('status') == 'active' and (data.get('value') or data.get('api_key')):
            active_val = str(data.get('value') or data.get('api_key'))
            _sync_environment(active_val)
            break


def update_last_run(key_name: str) -> None:
    """Update last executed timestamp for specified API key.

    Args:
        key_name (str): Identifier or value of the key executed.
    """
    if not key_name:
        return

    keys_data = _load_keys_file()
    target_name = key_name

    if target_name not in keys_data:
        for name, data in keys_data.items():
            if data.get('value') == key_name or data.get('api_key') == key_name:
                target_name = name
                break

    if target_name in keys_data:
        keys_data[target_name]['last_run'] = _now_iso()
        _save_keys_file(keys_data)


def next_available_in() -> float:
    """Calculate seconds until the earliest exhausted key becomes active.

    Returns:
        float: Remaining seconds, or 0.0 if any keys are already active.
    """
    keys_data = _load_keys_file()
    if not keys_data:
        return 0.0

    now = _now_ts()
    min_wait: float = _DAY_SECONDS
    found_exhausted = False

    for name, data in keys_data.items():
        status = data.get('status', 'active')
        if status == 'disabled':
            continue
        if status == 'active':
            return 0.0

        found_exhausted = True
        exhausted_at = data.get('exhausted_at') or data.get('last_run', '')
        exhausted_ts = _iso_to_ts(exhausted_at) if exhausted_at else 0.0
        elapsed = now - exhausted_ts
        if elapsed >= _DAY_SECONDS or exhausted_ts == 0.0:
            return 0.0
        remaining = _DAY_SECONDS - elapsed
        if remaining < min_wait:
            min_wait = remaining

    return min_wait if found_exhausted else 0.0


def get_status(names: Optional[List[str]] = None) -> Dict[str, Any]:
    """Retrieve detailed runtime status for keys.

    Args:
        names (Optional[List[str]]): List of key names to filter.

    Returns:
        Dict[str, Any]: Mapping of key names to status descriptors.
    """
    keys_data = _load_keys_file()
    now = _now_ts()
    statuses: Dict[str, Any] = {}

    filter_names: List[str] = []
    if names:
        if isinstance(names, str):
            filter_names = [n.strip() for n in str(names).split(',') if n.strip() and n.strip() != '*']
        elif isinstance(names, (list, tuple, set)):
            filter_names = [str(n).strip() for n in names if str(n).strip() and str(n).strip() != '*']

    for name, data in keys_data.items():
        if filter_names and name not in filter_names:
            continue

        status = data.get('status', 'active')
        exhausted_at = data.get('exhausted_at', '')
        is_exhausted = status == 'exhausted'
        remaining_sec = 0.0

        if is_exhausted:
            ref_ts = _iso_to_ts(exhausted_at) if exhausted_at else _iso_to_ts(data.get('last_run', ''))
            if ref_ts > 0:
                elapsed = now - ref_ts
                if 0 <= elapsed < _DAY_SECONDS:
                    remaining_sec = _DAY_SECONDS - elapsed
                else:
                    is_exhausted = False

        statuses[name] = {
            'value': data.get('value') or data.get('api_key', ''),
            'status': status,
            'last_run': data.get('last_run', ''),
            'exhausted_at': exhausted_at,
            'is_exhausted': is_exhausted,
            'reset_in_seconds': int(remaining_sec) if is_exhausted else 0,
        }

    return statuses


def save_api_key(name: str, value: str, status: str = 'active') -> bool:
    """Save or update an API key in gemini_keys.json.

    Args:
        name (str): Unique identifier for the key.
        value (str): The raw secret API key string.
        status (str): Initial status ('active' or 'exhausted').

    Returns:
        bool: True on success.
    """
    if not name or not value:
        return False

    clean_name = name.strip()
    clean_val = value.strip()

    keys_data = _load_keys_file()
    existing = keys_data.get(clean_name, {})

    keys_data[clean_name] = {
        'value': clean_val,
        'last_run': existing.get('last_run', ''),
        'status': status,
        'exhausted_at': existing.get('exhausted_at', '') if status == 'exhausted' else '',
    }

    success = _save_keys_file(keys_data)
    if success and status == 'active':
        _sync_environment(clean_val)

    logger.info(f'API key "{clean_name}" saved to {_KEYS_FILE}.')
    return success


def delete_api_key(name: str) -> bool:
    """Delete an API key from gemini_keys.json.

    Args:
        name (str): Identifier of the key to delete.

    Returns:
        bool: True if key was deleted.
    """
    if not name:
        return False

    clean_name = name.strip()
    keys_data = _load_keys_file()

    if clean_name not in keys_data:
        return False

    deleted_entry = keys_data.pop(clean_name)
    deleted_val = deleted_entry.get('value', '')
    success = _save_keys_file(keys_data)

    if os.environ.get('GEMINI_API_KEY') == deleted_val:
        # Re-sync with next remaining active key
        remaining_active = [
            d.get('value') for d in keys_data.values()
            if d.get('status') == 'active' and d.get('value')
        ]
        if remaining_active:
            _sync_environment(remaining_active[0])
        else:
            os.environ.pop('GEMINI_API_KEY', None)

    logger.info(f'API key "{clean_name}" deleted from {_KEYS_FILE}.')
    return success


def reset_quota(key_name: str) -> bool:
    """Reset quota exhaustion for a specific key.

    Args:
        key_name (str): Identifier of the key.

    Returns:
        bool: True if key was reset to active.
    """
    if not key_name:
        return False

    keys_data = _load_keys_file()
    if key_name in keys_data:
        keys_data[key_name]['status'] = 'active'
        keys_data[key_name]['exhausted_at'] = ''
        _save_keys_file(keys_data)
        _sync_environment(keys_data[key_name].get('value', ''))
        logger.info(f'Quota reset for key "{key_name}".')
        return True
    return False


def reset_all_quotas() -> int:
    """Reset quota exhaustion for all API keys.

    Returns:
        int: Number of reset keys.
    """
    keys_data = _load_keys_file()
    reset_count = 0

    for name, data in keys_data.items():
        if data.get('status') == 'exhausted' or data.get('exhausted_at'):
            data['status'] = 'active'
            data['exhausted_at'] = ''
            reset_count += 1

    if reset_count > 0:
        _save_keys_file(keys_data)
        # Resync active key
        first_active = next(
            (d.get('value') for d in keys_data.values() if d.get('status') == 'active' and d.get('value')),
            None,
        )
        if first_active:
            _sync_environment(first_active)
        logger.info(f'Reset quota for {reset_count} keys.')

    return reset_count
