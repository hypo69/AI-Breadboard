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
        from src.user_manager.user_profile import _get_profile_path
        
        result = _get_profile_path(1)
        
        assert isinstance(result, Path)
        # Check that path contains user_profile_1
        assert "user_profile_1" in str(result)
        assert result.suffix == ".json"

    def test_default_profile_structure(self):
        """Test default profile structure."""
        from src.user_manager.user_profile import _default_profile_structure
        
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
        from src.user_manager.user_profile import load_user_profile
        
        user_id = 1
        profile_path = tmp_path / 'user_1_profile.json'
        
        with patch('src.user_manager.user_profile._get_profile_path') as mock_path:
            mock_path.return_value = profile_path
            
            # Profile does not exist - new one is created
            result = load_user_profile(user_id)
            
            assert isinstance(result, dict)

    def test_save_user_profile(self, tmp_path):
        """Test saving profile."""
        from src.user_manager.user_profile import save_user_profile
        
        user_id = 1
        profile = {'last_watched': 'test'}
        profile_path = tmp_path / 'user_1_profile.json'
        
        with patch('src.user_manager.user_profile._get_profile_path') as mock_path:
            mock_path.return_value = profile_path
            
            result = save_user_profile(user_id, profile)
            assert result is True


class TestUserManagerStorage:
    """Tests for UserManager personal directory and workspace features."""

    @pytest.fixture
    def custom_user_manager(self, tmp_path):
        """Create an isolated UserManager with temporary DB and users_dir."""
        from src.user_manager import UserManager
        db_path = tmp_path / "test_users.db"
        users_dir = tmp_path / "user_storage"
        return UserManager(db_path=db_path, users_dir=users_dir)

    def test_sanitize_user_id(self, custom_user_manager):
        """Test sanitizing user identifiers."""
        assert custom_user_manager.sanitize_user_id(123) == "123"
        assert custom_user_manager.sanitize_user_id("user@test.com") == "user_test_com"
        assert custom_user_manager.sanitize_user_id("../../etc/passwd") == "______etc_passwd"

    def test_init_user_workspace(self, custom_user_manager):
        """Test initialization of standard user directory tree."""
        user_id = 42
        root_dir = custom_user_manager.init_user_workspace(user_id)
        
        assert root_dir.exists()
        assert (root_dir / 'files').is_dir()
        assert (root_dir / 'rag').is_dir()
        assert (root_dir / 'profile').is_dir()
        assert (root_dir / 'temp').is_dir()

    def test_auto_workspace_creation_on_add_user(self, custom_user_manager):
        """Verify that adding a user automatically creates their personal directory."""
        user_id = custom_user_manager.add_user(
            email="storage_test@example.com",
            name="Storage User"
        )
        assert user_id > 0
        user_dir = custom_user_manager.get_user_directory(user_id, create=False)
        assert user_dir.exists()
        assert (user_dir / "files").exists()

    def test_get_user_storage_stats(self, custom_user_manager):
        """Test calculating storage statistics."""
        user_id = 99
        custom_user_manager.init_user_workspace(user_id)
        files_dir = custom_user_manager.get_user_directory(user_id, 'files')
        
        # Write dummy files
        (files_dir / "sample.txt").write_text("Hello World!", encoding="utf-8")
        (files_dir / "document.pdf").write_bytes(b"%PDF-1.4 dummy binary content")

        stats = custom_user_manager.get_user_storage_stats(user_id)
        assert stats["exists"] is True
        assert stats["total_files"] == 2
        assert stats["total_size_bytes"] > 0
        assert "files" in stats["subfolders"]
        assert stats["subfolders"]["files"]["files"] == 2

    def test_delete_user_workspace(self, custom_user_manager):
        """Test cleanup of user workspace upon deletion."""
        user_id = custom_user_manager.add_user(
            email="to_delete@example.com",
            name="Deletable User"
        )
        user_dir = custom_user_manager.get_user_directory(user_id)
        assert user_dir.exists()

        success = custom_user_manager.delete_user(user_id)
        assert success is True
        assert not user_dir.exists()


class TestFavoriteModels:
    """Tests for user favorite models management and notes."""

    @pytest.fixture
    def user_mgr(self, tmp_path):
        """Create an isolated UserManager with temporary DB."""
        from src.user_manager import UserManager
        db_path = tmp_path / "test_favorites.db"
        users_dir = tmp_path / "fav_storage"
        mgr = UserManager(db_path=db_path, users_dir=users_dir)
        mgr.add_user(email="fav_test@example.com", name="Fav User")
        return mgr

    def test_add_and_get_favorite_models(self, user_mgr):
        """Test adding and retrieving favorite models with notes."""
        user_id = 1
        assert user_mgr.get_favorite_models(user_id) == {}

        # Add favorite model with note
        success = user_mgr.set_favorite_model(user_id, "gemini-2.5-flash", "Fast model for general tasks")
        assert success is True

        favs = user_mgr.get_favorite_models(user_id)
        assert "gemini-2.5-flash" in favs
        assert favs["gemini-2.5-flash"]["note"] == "Fast model for general tasks"

        # Update note
        success = user_mgr.set_favorite_model(user_id, "gemini-2.5-flash", "Updated note for model")
        assert success is True
        favs2 = user_mgr.get_favorite_models(user_id)
        assert favs2["gemini-2.5-flash"]["note"] == "Updated note for model"

    def test_remove_favorite_model(self, user_mgr):
        """Test removing favorite model."""
        user_id = 1
        user_mgr.set_favorite_model(user_id, "qwen2.5:7b", "Local model")
        assert "qwen2.5:7b" in user_mgr.get_favorite_models(user_id)

        removed = user_mgr.remove_favorite_model(user_id, "qwen2.5:7b")
        assert removed is True
        assert "qwen2.5:7b" not in user_mgr.get_favorite_models(user_id)

    def test_settings_includes_favorite_models(self, user_mgr):
        """Test that get_user_settings includes favorite_models dict."""
        user_id = 1
        user_mgr.set_favorite_model(user_id, "agy-flash", "Google Antigravity Flash")
        settings = user_mgr.get_user_settings(user_id)

        assert "favorite_models" in settings
        assert "agy-flash" in settings["favorite_models"]
        assert settings["favorite_models"]["agy-flash"]["note"] == "Google Antigravity Flash"

