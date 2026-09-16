# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit Tests for User Admin Service
# =============================================================================
# Description:
#   Тестирование сервиса UserAdminService: получение списка пользователей,
#   фильтрация, переключение активности/роли, защита суперадмина и удаление.
#
# File: test_user_admin_service.py
# Project: AI-Breadboard
# Package: apps.ai_breadboard_admin.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from unittest.mock import MagicMock, patch
import pytest

from apps.ai_breadboard_admin.src.user_admin_service import UserAdminService


@pytest.fixture
def mock_user_mgr():
    """Фикстура мока UserManager."""
    with patch("apps.ai_breadboard_admin.src.user_admin_service.user_manager") as m:
        yield m


def test_get_users_list_happy_path(mock_user_mgr) -> None:
    """Happy Path: получение списка пользователей с подсчетом статистики."""
    # Arrange: настраиваем мок пользователей
    mock_user_mgr.get_all_users.return_value = [
        {"id": 1, "name": "Admin", "email": "admin@example.com", "role": "admin", "is_admin": 1, "is_active": 1, "password_hash": "hash1"},
        {"id": 2, "name": "User2", "email": "user2@example.com", "role": "user", "is_admin": 0, "is_active": 1, "password_hash": "hash2"},
        {"id": 3, "name": "User3", "email": "user3@example.com", "role": "user", "is_admin": 0, "is_active": 0, "password_hash": None},
    ]

    service = UserAdminService()

    # Act: получаем список пользователей
    res = service.get_users_list()

    # Assert: проверяем фильтрацию паролей и подсчет статистики
    assert res["status"] == "ok"
    assert len(res["users"]) == 3
    assert "password_hash" not in res["users"][0]
    assert res["users"][0]["has_password"] is True
    assert res["users"][2]["has_password"] is False
    assert res["stats"]["total"] == 3
    assert res["stats"]["active"] == 2
    assert res["stats"]["suspended"] == 1
    assert res["stats"]["admins"] == 1


def test_get_users_list_filtering(mock_user_mgr) -> None:
    """Edge Cases & Filtering: фильтрация по запросу q, роли и статусу."""
    # Arrange: тестовые пользователи
    mock_user_mgr.get_all_users.return_value = [
        {"id": 1, "name": "Super Admin", "email": "admin@test.com", "role": "admin", "is_admin": 1, "is_active": 1},
        {"id": 2, "name": "Regular Alex", "email": "alex@test.com", "role": "user", "is_admin": 0, "is_active": 1},
    ]
    service = UserAdminService()

    # Act: поиск по 'Alex'
    alex_res = service.get_users_list(q="Alex")
    admin_res = service.get_users_list(role="admin")

    # Assert: результаты соответствуют фильтрам
    assert len(alex_res["users"]) == 1
    assert alex_res["users"][0]["name"] == "Regular Alex"
    assert len(admin_res["users"]) == 1
    assert admin_res["users"][0]["name"] == "Super Admin"


def test_create_user_validation_and_success(mock_user_mgr) -> None:
    """Happy Path & Error Scenarios: валидация входных данных при создании."""
    mock_user_mgr.user_exists.return_value = False
    mock_user_mgr.create_user_admin.return_value = 5
    mock_user_mgr.get_user_by_id.return_value = {
        "id": 5, "name": "New User", "email": "new@test.com", "role": "user", "is_active": 1
    }

    service = UserAdminService()

    # Act: успешное создание
    res = service.create_user(email="new@test.com", name="New User", password="pass")
    assert res["status"] == "ok"
    assert res["user"]["id"] == 5

    # Error Scenario: пустой email
    with pytest.raises(ValueError, match="Email обязателен"):
        service.create_user(email="", name="Name")

    # Error Scenario: уже существующий email
    mock_user_mgr.user_exists.return_value = True
    with pytest.raises(ValueError, match="уже существует"):
        service.create_user(email="new@test.com", name="Name")


def test_superadmin_protection(mock_user_mgr) -> None:
    """Boundary Values & Security: запрет деактивации и снятия прав с ID 1."""
    mock_user_mgr.get_user_by_id.return_value = {"id": 1, "name": "Admin", "role": "admin", "is_admin": 1, "is_active": 1}
    service = UserAdminService()

    # Попытка снять права
    with pytest.raises(ValueError, match="главного администратора"):
        service.update_user(1, is_admin=0)

    # Попытка деактивировать
    with pytest.raises(ValueError, match="главного администратора"):
        service.toggle_user_active(1)

    # Попытка изменить роль
    with pytest.raises(ValueError, match="главного администратора"):
        service.toggle_user_role(1)

    # Попытка удалить
    with pytest.raises(ValueError, match="главного администратора"):
        service.delete_user(1)
