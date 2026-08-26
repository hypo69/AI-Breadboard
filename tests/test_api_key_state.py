# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit Tests for core.secrets.api_key_state
# =============================================================================
# Description:
#   Validates API key loading, priority merging, rotation, 24-hour quota
#   exhaustion tracking, and status retrieval.
#
# File: test_api_key_state.py
# Project: ai-assistant
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

from core.secrets.api_key_state import (
    get_status,
    load_api_keys,
    mark_exhausted,
    next_available_in,
    save_api_key,
    update_last_run,
)


def test_save_and_load_api_key(tmp_path):
    """Test saving an API key and loading it back."""
    keys_file = tmp_path / 'gemini_keys.json'
    legacy_file = tmp_path / 'secrets.json'
    with patch('core.secrets.api_key_state._KEYS_FILE', keys_file), \
         patch('core.secrets.api_key_state._LEGACY_SECRETS_FILE', legacy_file), \
         patch('core.secrets.api_key_state._SECRETS_DIR', tmp_path), \
         patch.dict('os.environ', {}, clear=True):

        assert save_api_key('test_main', 'AIzaSyTest1234567890') is True

        keys, names, states = load_api_keys()
        assert 'AIzaSyTest1234567890' in keys
        assert 'test_main' in names
        assert len(states) == 1
        assert states[0]['status'] == 'active'


def test_mark_exhausted_and_cooldown(tmp_path):
    """Test marking key exhausted and calculating cooldown."""
    keys_file = tmp_path / 'gemini_keys.json'
    legacy_file = tmp_path / 'secrets.json'
    with patch('core.secrets.api_key_state._KEYS_FILE', keys_file), \
         patch('core.secrets.api_key_state._LEGACY_SECRETS_FILE', legacy_file), \
         patch('core.secrets.api_key_state._SECRETS_DIR', tmp_path), \
         patch.dict('os.environ', {}, clear=True):

        save_api_key('k1', 'AIzaSyKeyOne1111111111111')
        mark_exhausted('k1')

        # Should be skipped when skip_exhausted is True
        keys, names, _ = load_api_keys(skip_exhausted=True)
        assert 'AIzaSyKeyOne1111111111111' not in keys

        # Should be included when skip_exhausted is False
        keys_all, _, _ = load_api_keys(skip_exhausted=False)
        assert 'AIzaSyKeyOne1111111111111' in keys_all

        # Cooldown should be > 0 and <= 86400
        wait_time = next_available_in()
        assert 0 < wait_time <= 86400


def test_update_last_run(tmp_path):
    """Test updating last_run timestamp."""
    keys_file = tmp_path / 'gemini_keys.json'
    legacy_file = tmp_path / 'secrets.json'
    with patch('core.secrets.api_key_state._KEYS_FILE', keys_file), \
         patch('core.secrets.api_key_state._LEGACY_SECRETS_FILE', legacy_file), \
         patch('core.secrets.api_key_state._SECRETS_DIR', tmp_path), \
         patch.dict('os.environ', {}, clear=True):

        save_api_key('k_run', 'AIzaSyKeyRun2222222222222')
        update_last_run('k_run')

        statuses = get_status(['k_run'])
        assert 'k_run' in statuses
        assert statuses['k_run']['last_run'] != ''
