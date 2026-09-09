# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Secrets Management Module Initialization
# =============================================================================
# Description:
#   Package for managing API keys, tokens, credentials, and their runtime states.
#
# File: __init__.py
# Project: ai-breadboard
# Package: src.secrets
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

from src.ai.gemini.gemini_api_key_state import (
    get_status,
    load_api_keys,
    mark_exhausted,
    next_available_in,
    save_api_key,
    update_last_run,
)
from src.ai.google_accounts_state import (
    list_google_accounts,
    get_account_info,
    save_google_account,
    delete_google_account,
    set_default_account,
    mark_account_exhausted,
    reset_account_status,
    load_account_credentials,
)

__all__ = [
    'get_status',
    'load_api_keys',
    'mark_exhausted',
    'next_available_in',
    'save_api_key',
    'update_last_run',
    'list_google_accounts',
    'get_account_info',
    'save_google_account',
    'delete_google_account',
    'set_default_account',
    'mark_account_exhausted',
    'reset_account_status',
    'load_account_credentials',
]

