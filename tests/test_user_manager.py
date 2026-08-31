# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Tests for core/user_manager module
# =============================================================================
# Description:
#   Module contains tests for user management module. Checks for functionality.
#
# File: test_user_manager.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""
Tests for core/user_manager module
"""

import pytest
import sqlite3
from unittest.mock import Mock, patch
from pathlib import Path

class TestUserProfile:
    """Tests for user_profile.py."""

    def test_get_profile_path(self):
        """Test retrieving profile path - check path structure."""
        from core.user_manager.user_profile import _get_profile_path
        
        result = _get_profile_path(1)
        
        assert isinstance(result, Path)
        # Check that path contains user_profile_1
        assert "user_profile_1" in str(result)
        assert result.suffix == ".json"

    def test_default_profile_structure(self):
        """Test default profile structure."""
        from core.user_manager.user_profile import _default_profile_structure
        
        result = _default_profile_structure(1)
        
        assert isinstance(result, dict)
        # Check key fields of profile structure
        assert 'user_id' in result
        assert 'created_at' in result
        assert 'updated_at' in result
        assert 'watch_history' in result
        assert 'last_watched' in result  # Can be None
        assert 'search_history' in result
        assert 'preferences' in result  # Uses 'preferences', not 'settings'

    def test_load_user_profile(self, tmp_path):
        """Test loading profile."""
        from core.user_manager.user_profile import load_user_profile
        
        user_id = 1
        profile_path = tmp_path / 'user_1_profile.json'
        
        with patch('core.user_manager.user_profile._get_profile_path') as mock_path:
            mock_path.return_value = profile_path
            
            # Profile does not exist - new one is created
            result = load_user_profile(user_id)
            
            assert isinstance(result, dict)

    def test_save_user_profile(self, tmp_path):
        """Test saving profile."""
        from core.user_manager.user_profile import save_user_profile
        
        user_id = 1
        profile = {'last_watched': 'test'}
        profile_path = tmp_path / 'user_1_profile.json'
        
        with patch('core.user_manager.user_profile._get_profile_path') as mock_path:
            mock_path.return_value = profile_path
            
            result = save_user_profile(user_id, profile)
