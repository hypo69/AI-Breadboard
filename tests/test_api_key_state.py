# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Test API Key State and Rotation Pool Manager
# =============================================================================
# Description:
#   Validates API key loading, gemini_keys.json persistence, dynamic substitution
#   into GEMINI_API_KEY, and 24-hour quota exhaustion handling.
#
# File: test_api_key_state.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
from unittest.mock import patch

from src.secrets.api_key_state import (
    delete_api_key,
    get_status,
    load_api_keys,
    mark_exhausted,
    next_available_in,
    reset_all_quotas,
    reset_quota,
    save_api_key,
    update_last_run,
)


def test_save_and_load_api_key(tmp_path):
    """Test saving an API key to gemini_keys.json and dynamic env substitution."""
    keys_file = tmp_path / 'gemini_keys.json'
    env_file = tmp_path / '.env'
    with patch('src.secrets.api_key_state._KEYS_FILE', keys_file), \
         patch('src.secrets.api_key_state._ENV_FILE', env_file), \
         patch('src.secrets.api_key_state._SECRETS_DIR', tmp_path), \
         patch.dict('os.environ', {}, clear=True):

        assert save_api_key('GEMINI_API_KEY_MAIN', 'AIzaSyTest1234567890') is True

        keys, names, states = load_api_keys()
        assert 'AIzaSyTest1234567890' in keys
        assert 'GEMINI_API_KEY_MAIN' in names
        assert len(states) == 1
        assert states[0]['status'] == 'active'
        assert states[0]['value'] == 'AIzaSyTest1234567890'

        # Check dynamic substitution into environment
        assert os.environ.get('GEMINI_API_KEY') == 'AIzaSyTest1234567890'


def test_mark_exhausted_and_cooldown(tmp_path):
    """Test marking key exhausted, rotating env key, and calculating cooldown."""
    keys_file = tmp_path / 'gemini_keys.json'
    env_file = tmp_path / '.env'
    with patch('src.secrets.api_key_state._KEYS_FILE', keys_file), \
         patch('src.secrets.api_key_state._ENV_FILE', env_file), \
         patch('src.secrets.api_key_state._SECRETS_DIR', tmp_path), \
         patch.dict('os.environ', {}, clear=True):

        save_api_key('key_primary', 'AIzaSyKeyOne1111111111111')
        save_api_key('key_secondary', 'AIzaSyKeyTwo2222222222222')

        mark_exhausted('key_primary')

        # Environment should dynamically rotate to secondary active key
        assert os.environ.get('GEMINI_API_KEY') == 'AIzaSyKeyTwo2222222222222'

        # When skip_exhausted is True, primary is skipped
        keys, names, _ = load_api_keys(skip_exhausted=True)
        assert 'AIzaSyKeyOne1111111111111' not in keys
        assert 'AIzaSyKeyTwo2222222222222' in keys

        # When skip_exhausted is False, both are included
        keys_all, _, _ = load_api_keys(skip_exhausted=False)
        assert 'AIzaSyKeyOne1111111111111' in keys_all
        assert 'AIzaSyKeyTwo2222222222222' in keys_all

        # Cooldown should be 0 because key_secondary is still available
        assert next_available_in() == 0.0

        # When all keys are exhausted, cooldown > 0
        mark_exhausted('key_secondary')
        wait_time = next_available_in()
        assert 0 < wait_time <= 86400


def test_update_last_run(tmp_path):
    """Test updating last_run timestamp."""
    keys_file = tmp_path / 'gemini_keys.json'
    env_file = tmp_path / '.env'
    with patch('src.secrets.api_key_state._KEYS_FILE', keys_file), \
         patch('src.secrets.api_key_state._ENV_FILE', env_file), \
         patch('src.secrets.api_key_state._SECRETS_DIR', tmp_path), \
         patch.dict('os.environ', {}, clear=True):

        save_api_key('k_run', 'AIzaSyKeyRun3333333333333')
        update_last_run('k_run')

        statuses = get_status(['k_run'])
        assert 'k_run' in statuses
        assert statuses['k_run']['last_run'] != ''


def test_reset_quota_and_delete_key(tmp_path):
    """Test quota reset and key deletion."""
    keys_file = tmp_path / 'gemini_keys.json'
    env_file = tmp_path / '.env'
    with patch('src.secrets.api_key_state._KEYS_FILE', keys_file), \
         patch('src.secrets.api_key_state._ENV_FILE', env_file), \
         patch('src.secrets.api_key_state._SECRETS_DIR', tmp_path), \
         patch.dict('os.environ', {}, clear=True):

        save_api_key('key_to_delete', 'AIzaSyKeyDel4444444444444')
        mark_exhausted('key_to_delete')

        status_before = get_status(['key_to_delete'])
        assert status_before['key_to_delete']['is_exhausted'] is True

        assert reset_quota('key_to_delete') is True
        status_after = get_status(['key_to_delete'])
        assert status_after['key_to_delete']['is_exhausted'] is False

        assert delete_api_key('key_to_delete') is True
        keys, names, _ = load_api_keys()
        assert 'AIzaSyKeyDel4444444444444' not in keys
