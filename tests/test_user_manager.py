# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Тесты модуля core/user_manager
# =============================================================================
# Описание:
#   Модуль содержит тесты для модуля управления пользователями. Проверяет
#   получение пути к профилю, структуру профиля по умолчанию и основные
#   функции управления пользователями. Обеспечивает покрытие ключевых
#   сценариев работы с пользовательскими данными.
#
# File: tests/test_user_manager.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
"""
Тесты модуля core/user_manager
"""

import pytest
import sqlite3
from unittest.mock import Mock, patch
from pathlib import Path


class TestUserProfile:
    """Тесты user_profile.py."""

    def test_get_profile_path(self):
        """Тест получения пути к профилю - проверка структуры пути."""
        from core.user_manager.user_profile import _get_profile_path
        
        result = _get_profile_path(1)
        
        assert isinstance(result, Path)
        # Проверяем что путь содержит user_profile_1
        assert "user_profile_1" in str(result)
        assert result.suffix == ".json"

    def test_default_profile_structure(self):
        """Тест структуры профиля по умолчанию."""
        from core.user_manager.user_profile import _default_profile_structure
        
        result = _default_profile_structure(1)
        
        assert isinstance(result, dict)
        # Проверяем ключевые поля структуры профиля
        assert 'user_id' in result
        assert 'created_at' in result
        assert 'updated_at' in result
        assert 'watch_history' in result
        assert 'last_watched' in result  # Может быть None
        assert 'search_history' in result
        assert 'preferences' in result  # Используется 'preferences', не 'settings'

    def test_load_user_profile(self, tmp_path):
        """Тест загрузки профиля."""
        from core.user_manager.user_profile import load_user_profile
        
        user_id = 1
        profile_path = tmp_path / 'user_1_profile.json'
        
        with patch('core.user_manager.user_profile._get_profile_path') as mock_path:
            mock_path.return_value = profile_path
            
            # Профиль не существует - создается новый
            result = load_user_profile(user_id)
            
            assert isinstance(result, dict)

    def test_save_user_profile(self, tmp_path):
        """Тест сохранения профиля."""
        from core.user_manager.user_profile import save_user_profile
        
        user_id = 1
        profile = {'last_watched': 'test'}
        profile_path = tmp_path / 'user_1_profile.json'
        
        with patch('core.user_manager.user_profile._get_profile_path') as mock_path:
            mock_path.return_value = profile_path
            
            result = save_user_profile(user_id, profile)
            
            assert result is True

    def test_update_watch_progress(self, tmp_path):
        """Тест обновления прогресса просмотра."""
        from core.user_manager.user_profile import update_watch_progress
        
        result = update_watch_progress(
            user_id='1',
            file_path='/test/path.mp4',
            file_name='test.mp4',
            current_time=120.5,
            duration=7200.0
        )
        
        assert result is not None


class TestUserManager:
    """Тесты UserManager."""

    def test_init(self, temp_db_path):
        """Тест инициализации UserManager."""
        from core.user_manager import UserManager
        
        manager = UserManager(temp_db_path)
        
        assert manager is not None
        assert manager.db_path == temp_db_path

    def test_add_user(self, temp_db_path):
        """Тест добавления пользователя."""
        from core.user_manager import UserManager
        
        manager = UserManager(temp_db_path)
        
        user_id = manager.add_user(
            email='test@example.com',
            name='Test User',
            role='user'
        )
        
        assert user_id > 0

    def test_get_user_by_id(self, temp_db_path):
        """Тест получения пользователя по ID."""
        from core.user_manager import UserManager
        
        manager = UserManager(temp_db_path)
        
        user_id = manager.add_user(
            email='test@example.com',
            name='Test User'
        )
        
        user = manager.get_user_by_id(user_id)
        
        assert user is not None
        assert user['email'] == 'test@example.com'

    def test_get_user_by_email(self, temp_db_path):
        """Тест получения пользователя по email."""
        from core.user_manager import UserManager
        
        manager = UserManager(temp_db_path)
        
        manager.add_user(
            email='test@example.com',
            name='Test User'
        )
        
        user = manager.get_user_by_email('test@example.com')
        
        assert user is not None
        assert user['email'] == 'test@example.com'

    def test_get_user_settings(self, temp_db_path):
        """Тест получения настроек пользователя."""
        from core.user_manager import UserManager
        
        manager = UserManager(temp_db_path)
        
        user_id = manager.add_user(
            email='test@example.com',
            name='Test User'
        )
        
        settings = manager.get_user_settings(user_id)
        
        assert isinstance(settings, dict)

    def test_google_oauth_tokens(self, temp_db_path):
        """Тест сохранения и получения токенов Google OAuth."""
        from core.user_manager import UserManager
        
        manager = UserManager(temp_db_path)
        user_id = manager.add_user(
            email='google_user@example.com',
            name='Google User'
        )
        
        assert manager.has_google_auth(user_id) is False
        
        success = manager.save_google_tokens(
            user_id=user_id,
            access_token='ya29.test_access_token',
            refresh_token='1//test_refresh_token',
            expires_in=3600,
            scope='openid email profile https://www.googleapis.com/auth/calendar'
        )
        assert success is True
        assert manager.has_google_auth(user_id) is True
        
        tokens = manager.get_google_tokens(user_id)
        assert tokens['access_token'] == 'ya29.test_access_token'
        assert tokens['refresh_token'] == '1//test_refresh_token'
        assert 'calendar' in tokens['scope']

