# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Google Workspace Multi-Account Pool & Secrets Manager
# =============================================================================
# Description:
#   Manages Google Workspace (Gmail, Drive, Sheets, Docs) multi-account pool,
#   OAuth 2.0 credentials, Service Accounts, token caching, and quota cooldowns.
#   Stored in src/secrets/google_accounts.json with token persistence in src/secrets/tokens/.
#
# File: google_accounts_state.py
# Project: ai-breadboard
# Package: src.ai
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
_TOKENS_DIR: Path = _SECRETS_DIR / 'tokens'
_ACCOUNTS_FILE: Path = _SECRETS_DIR / 'google_accounts.json'
_DAY_SECONDS: float = 86400.0

DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents",
]


def _ensure_dirs() -> None:
    """Ensure secrets and tokens directories exist."""
    try:
        _SECRETS_DIR.mkdir(parents=True, exist_ok=True)
        _TOKENS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as ex:
        logger.error(f"Failed to create Google accounts directories: {ex}")


def _now_iso() -> str:
    """Get current UTC ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _now_ts() -> float:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc).timestamp()


def _iso_to_ts(iso_str: str) -> float:
    """Convert ISO string to timestamp."""
    if not iso_str:
        return 0.0
    try:
        cleaned = iso_str.replace('Z', '+00:00')
        return datetime.fromisoformat(cleaned).timestamp()
    except Exception:
        return 0.0


def _load_accounts_data() -> Dict[str, Any]:
    """Load accounts metadata from google_accounts.json.

    Returns:
        Dict[str, Any]: Structure with 'default_account' and 'accounts' mapping.
    """
    _ensure_dirs()
    if _ACCOUNTS_FILE.exists():
        try:
            content = _ACCOUNTS_FILE.read_text(encoding='utf-8').strip()
            if content:
                data = json.loads(content)
                if isinstance(data, dict):
                    if 'accounts' not in data:
                        data = {'default_account': '', 'accounts': data}
                    return data
        except Exception as ex:
            logger.warning(f"Error reading {_ACCOUNTS_FILE}: {ex}")

    # Bootstrap default single account if existing secrets exist
    bootstrapped = _bootstrap_from_existing_files()
    if bootstrapped.get('accounts'):
        _save_accounts_data(bootstrapped)
        return bootstrapped

    return {'default_account': '', 'accounts': {}}


def _bootstrap_from_existing_files() -> Dict[str, Any]:
    """Discover existing credentials in src/secrets or root."""
    accounts: Dict[str, Any] = {}
    candidates = [
        (_SECRETS_DIR / "credentials.json", "oauth2"),
        (_SECRETS_DIR / "service_account.json", "service_account"),
        (__root__ / "credentials.json", "oauth2"),
        (__root__ / "service_account.json", "service_account"),
    ]

    for cand_path, acc_type in candidates:
        if cand_path.exists():
            acc_name = "default" if "default" not in accounts else cand_path.stem
            accounts[acc_name] = {
                "name": acc_name,
                "email": "",
                "type": acc_type,
                "credentials_file": str(cand_path.relative_to(__root__)),
                "token_file": str((_TOKENS_DIR / f"{acc_name}_token.json").relative_to(__root__)),
                "status": "active",
                "last_run": "",
                "exhausted_at": "",
            }

    default_name = next(iter(accounts.keys()), "")
    return {"default_account": default_name, "accounts": accounts}


def _save_accounts_data(data: Dict[str, Any]) -> bool:
    """Save accounts dictionary to JSON file.

    Args:
        data: Structure to serialize.

    Returns:
        bool: True on success.
    """
    try:
        _ensure_dirs()
        _ACCOUNTS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
        return True
    except Exception as ex:
        logger.error(f"Failed to save Google accounts data to {_ACCOUNTS_FILE}: {ex}")
        return False


def list_google_accounts(skip_exhausted: bool = False) -> List[Dict[str, Any]]:
    """List all configured Google Workspace accounts in pool.

    Args:
        skip_exhausted: Whether to filter out accounts with active quota exhaustion.

    Returns:
        List[Dict[str, Any]]: Account descriptor list.
    """
    data = _load_accounts_data()
    accounts = data.get('accounts', {})
    default_acc = data.get('default_account', '')
    now = _now_ts()
    result = []
    updates_needed = False

    for acc_name, acc_info in accounts.items():
        status = acc_info.get('status', 'active')
        exhausted_at = acc_info.get('exhausted_at', '')

        # Auto-reset 24h cooldown
        if status == 'exhausted' or exhausted_at:
            ref_ts = _iso_to_ts(exhausted_at)
            if ref_ts > 0 and (now - ref_ts) >= _DAY_SECONDS:
                acc_info['status'] = 'active'
                acc_info['exhausted_at'] = ''
                status = 'active'
                updates_needed = True

        if skip_exhausted and status == 'exhausted':
            continue

        item = dict(acc_info)
        item['name'] = acc_name
        item['is_default'] = (acc_name == default_acc)
        result.append(item)

    if updates_needed:
        _save_accounts_data(data)

    return result


def get_account_info(account_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get metadata for a specific or default Google account."""
    data = _load_accounts_data()
    accounts = data.get('accounts', {})
    target = account_name or data.get('default_account', '')

    if target and target in accounts:
        info = dict(accounts[target])
        info['name'] = target
        return info

    # Fallback to first available account
    if accounts:
        first_k = next(iter(accounts.keys()))
        info = dict(accounts[first_k])
        info['name'] = first_k
        return info

    return None


def save_google_account(
    account_name: str,
    credentials_path_or_dict: Any,
    account_type: str = "oauth2",
    email: str = "",
    set_as_default: bool = False,
) -> bool:
    """Add or update a Google Workspace account in pool.

    Args:
        account_name: Unique identifier for account (e.g. 'work', 'personal').
        credentials_path_or_dict: Path to client_secrets / service_account file, or dict.
        account_type: 'oauth2' or 'service_account'.
        email: Associated email address.
        set_as_default: Whether to mark this account as the default.

    Returns:
        bool: True on success.
    """
    _ensure_dirs()
    clean_name = account_name.strip()
    if not clean_name:
        return False

    data = _load_accounts_data()
    accounts = data.setdefault('accounts', {})

    # Determine credential file destination in src/secrets
    creds_rel_path = f"src/secrets/google_{clean_name}_{account_type}.json"
    dest_file = __root__ / creds_rel_path

    if isinstance(credentials_path_or_dict, dict):
        dest_file.write_text(json.dumps(credentials_path_or_dict, indent=2, ensure_ascii=False), encoding='utf-8')
    elif isinstance(credentials_path_or_dict, (str, Path)):
        src_path = Path(credentials_path_or_dict)
        if not src_path.is_absolute():
            src_path = __root__ / src_path
        if src_path.exists() and src_path.resolve() != dest_file.resolve():
            dest_file.write_bytes(src_path.read_bytes())
        elif not src_path.exists():
            logger.error(f"Credentials source file does not exist: {src_path}")
            return False

    token_rel_path = f"src/secrets/tokens/{clean_name}_token.json"

    accounts[clean_name] = {
        "name": clean_name,
        "email": email or accounts.get(clean_name, {}).get("email", ""),
        "type": account_type,
        "credentials_file": creds_rel_path,
        "token_file": token_rel_path,
        "status": "active",
        "last_run": "",
        "exhausted_at": "",
    }

    if set_as_default or not data.get('default_account'):
        data['default_account'] = clean_name

    return _save_accounts_data(data)


def delete_google_account(account_name: str) -> bool:
    """Remove a Google account from the pool."""
    data = _load_accounts_data()
    accounts = data.get('accounts', {})

    if account_name not in accounts:
        return False

    deleted = accounts.pop(account_name)
    if data.get('default_account') == account_name:
        data['default_account'] = next(iter(accounts.keys()), "")

    # Cleanup token file if exists
    token_file = __root__ / deleted.get('token_file', '')
    if token_file.exists():
        try:
            token_file.unlink()
        except Exception as e:
            logger.warning(f"Could not delete token file {token_file}: {e}")

    return _save_accounts_data(data)


def set_default_account(account_name: str) -> bool:
    """Set specified account as default for pool."""
    data = _load_accounts_data()
    accounts = data.get('accounts', {})

    if account_name not in accounts:
        return False

    data['default_account'] = account_name
    return _save_accounts_data(data)


def mark_account_exhausted(account_name: str) -> None:
    """Mark an account as quota-exhausted and rotate."""
    data = _load_accounts_data()
    accounts = data.get('accounts', {})

    if account_name in accounts:
        accounts[account_name]['status'] = 'exhausted'
        accounts[account_name]['exhausted_at'] = _now_iso()
        _save_accounts_data(data)
        logger.warning(f'Google account "{account_name}" marked as quota-exhausted.')


def reset_account_status(account_name: str) -> bool:
    """Reset quota status for an account."""
    data = _load_accounts_data()
    accounts = data.get('accounts', {})

    if account_name in accounts:
        accounts[account_name]['status'] = 'active'
        accounts[account_name]['exhausted_at'] = ''
        return _save_accounts_data(data)
    return False


def load_account_credentials(
    account_name: Optional[str] = None,
    scopes: Optional[List[str]] = None,
):
    """Retrieve authentic Google Credentials object for specified or active pool account.

    Args:
        account_name: Optional explicit account name in pool.
        scopes: Requested OAuth scopes.

    Returns:
        Google Credentials instance or None.
    """
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google.oauth2 import service_account
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        logger.error("Google Auth libraries are not installed.")
        return None

    active_scopes = scopes or DEFAULT_SCOPES
    acc_info = get_account_info(account_name)

    if not acc_info:
        # Fallback to direct credentials search in root / src/secrets
        return None

    creds_rel = acc_info.get("credentials_file", "")
    token_rel = acc_info.get("token_file", "")
    acc_type = acc_info.get("type", "oauth2")
    name = acc_info.get("name", "default")

    creds_path = __root__ / creds_rel if creds_rel else None
    token_path = __root__ / token_rel if token_rel else _TOKENS_DIR / f"{name}_token.json"

    # 1. Service Account Mode
    if acc_type == "service_account" and creds_path and creds_path.exists():
        try:
            return service_account.Credentials.from_service_account_file(
                str(creds_path), scopes=active_scopes
            )
        except Exception as e:
            logger.error(f"Failed to load Service Account for {name}: {e}")
            return None

    # 2. OAuth 2.0 User Token Mode
    creds = None
    if token_path and token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), active_scopes)
        except Exception as e:
            logger.warning(f"Failed to load cached OAuth token for {name}: {e}")
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                logger.info(f"Refreshing expired OAuth token for Google account '{name}'...")
                creds.refresh(Request())
            except Exception as e:
                logger.warning(f"Token refresh failed for {name}: {e}")
                creds = None

        if not creds:
            if not creds_path or not creds_path.exists():
                logger.error(
                    f"No credentials file found for Google account '{name}' at {creds_path}. "
                    f"Please place credentials JSON in src/secrets."
                )
                return None

            try:
                logger.info(f"Starting OAuth consent flow for account '{name}' ({creds_path})...")
                flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), active_scopes)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                logger.error(f"Error during OAuth flow for {name}: {e}")
                return None

        if creds and token_path:
            try:
                token_path.parent.mkdir(parents=True, exist_ok=True)
                with open(token_path, "w", encoding="utf-8") as tf:
                    tf.write(creds.to_json())
                logger.info(f"Saved OAuth token for account '{name}' to {token_path}")
            except Exception as e:
                logger.error(f"Failed to save token file for {name}: {e}")

    # Update last run timestamp
    if creds:
        data = _load_accounts_data()
        if name in data.get('accounts', {}):
            data['accounts'][name]['last_run'] = _now_iso()
            _save_accounts_data(data)

    return creds
