# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Тестирование API управления пользователями в админке
# =============================================================================
# Описание:
#   Модуль содержит тесты для REST API эндпоинтов /api/admin/users/*
#   и вспомогательных методов UserManager.
#
# File: tests/test_router_admin_users.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
from fastapi.testclient import TestClient

from main import app
from core.user_manager import user_manager

client = TestClient(app)


class TestAdminUsersAPI:
    """Тестирование эндпоинтов управления пользователями в панели администратора."""

    @pytest.fixture(autouse=True)
    def setup_cleanup(self):
        """Создание тестовых пользователей и очистка после тестов."""
        self.test_emails = [
            "test_user_admin_1@test.com",
            "test_user_admin_2@test.com",
            "searchable_unique@test.com"
        ]
        # Очистка перед тестом
        for email in self.test_emails:
            u = user_manager.get_user_by_email(email)
            if u:
                user_manager.delete_user(u["id"])

        yield

        # Очистка после теста
        for email in self.test_emails:
            u = user_manager.get_user_by_email(email)
            if u:
                user_manager.delete_user(u["id"])

    def test_list_users_and_stats(self):
        """Проверка получения списка пользователей и статистики."""
        response = client.get("/api/admin/users")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "users" in data
        assert isinstance(data["users"], list)
        assert len(data["users"]) > 0
        assert "stats" in data
        assert "total" in data["stats"]
        assert "active" in data["stats"]
        assert "admins" in data["stats"]
        assert "telegram" in data["stats"]

        # Пароли не должны отдаваться в открытом виде или хешем
        for u in data["users"]:
            assert "password_hash" not in u
            assert "has_password" in u

    def test_create_user(self):
        """Проверка создания нового пользователя через API."""
        payload = {
            "email": "test_user_admin_1@test.com",
            "name": "Тестовый Пользователь",
            "password": "SecurePassword123!",
            "role": "user",
            "is_admin": 0,
            "is_active": 1,
            "is_email_verified": 1
        }
        response = client.post("/api/admin/users", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "user" in data
        created = data["user"]
        assert created["email"] == "test_user_admin_1@test.com"
        assert created["name"] == "Тестовый Пользователь"
        assert created["role"] == "user"
        assert created["has_password"] is True

        # Проверка валидации дубликата
        duplicate_response = client.post("/api/admin/users", json=payload)
        assert duplicate_response.status_code == 400

    def test_get_user_details(self):
        """Проверка получения детальной информации о пользователе и его настройках."""
        user_id = user_manager.create_user_admin(
            email="test_user_admin_2@test.com",
            name="Детальный Пользователь",
            role="user"
        )
        assert user_id > 0

        response = client.get(f"/api/admin/users/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["user"]["id"] == user_id
        assert data["user"]["email"] == "test_user_admin_2@test.com"
        assert "settings" in data
        assert "permissions" in data

    def test_update_user(self):
        """Проверка редактирования пользователя."""
        user_id = user_manager.create_user_admin(
            email="test_user_admin_1@test.com",
            name="Старое Имя",
            role="user"
        )
        assert user_id > 0

        update_payload = {
            "name": "Новое Имя",
            "email": "test_user_admin_1@test.com",
            "role": "admin",
            "is_admin": 1,
            "is_active": 1,
            "is_email_verified": 1
        }
        response = client.put(f"/api/admin/users/{user_id}", json=update_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["user"]["name"] == "Новое Имя"
        assert data["user"]["role"] == "admin"
        assert data["user"]["is_admin"] == 1

    def test_set_user_password(self):
        """Проверка установки/смены пароля."""
        user_id = user_manager.create_user_admin(
            email="test_user_admin_1@test.com",
            name="Парольный Пользователь"
        )
        assert user_id > 0

        response = client.post(
            f"/api/admin/users/{user_id}/password",
            json={"password": "NewSecretPassword2026!"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

        # Проверка валидности хеша пароля
        db_user = user_manager.get_user_by_id(user_id)
        assert db_user.get("password_hash")
        assert user_manager.verify_password("NewSecretPassword2026!", db_user["password_hash"])
        assert not user_manager.verify_password("WrongPassword", db_user["password_hash"])

    def test_toggle_active(self):
        """Проверка переключения статуса активности."""
        user_id = user_manager.create_user_admin(
            email="test_user_admin_1@test.com",
            name="Статусный Пользователь",
            is_active=1
        )
        assert user_id > 0

        # Блокировка
        resp1 = client.post(f"/api/admin/users/{user_id}/toggle-active")
        assert resp1.status_code == 200
        assert resp1.json()["is_active"] == 0

        # Разблокировка
        resp2 = client.post(f"/api/admin/users/{user_id}/toggle-active")
        assert resp2.status_code == 200
        assert resp2.json()["is_active"] == 1

        # Защита ID 1
        resp_root = client.post("/api/admin/users/1/toggle-active")
        assert resp_root.status_code == 400

    def test_toggle_role(self):
        """Проверка переключения роли (User <-> Admin)."""
        user_id = user_manager.create_user_admin(
            email="test_user_admin_1@test.com",
            name="Ролевой Пользователь",
            role="user",
            is_admin=0
        )
        assert user_id > 0

        # Делаем администратором
        resp1 = client.post(f"/api/admin/users/{user_id}/toggle-role")
        assert resp1.status_code == 200
        assert resp1.json()["role"] == "admin"
        assert resp1.json()["is_admin"] == 1

        # Возвращаем в обычного пользователя
        resp2 = client.post(f"/api/admin/users/{user_id}/toggle-role")
        assert resp2.status_code == 200
        assert resp2.json()["role"] == "user"
        assert resp2.json()["is_admin"] == 0

        # Защита Root ID 1
        resp_root = client.post("/api/admin/users/1/toggle-role")
        assert resp_root.status_code == 400

    def test_delete_user(self):
        """Проверка удаления пользователя и защиты ID 1."""
        user_id = user_manager.create_user_admin(
            email="test_user_admin_1@test.com",
            name="Удаляемый Пользователь"
        )
        assert user_id > 0

        response = client.delete(f"/api/admin/users/{user_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

        # Проверка, что пользователь удален
        assert not user_manager.get_user_by_id(user_id)

        # Проверка защиты root ID 1
        root_del = client.delete("/api/admin/users/1")
        assert root_del.status_code == 400

    def test_search_and_filter_users(self):
        """Проверка фильтрации и поиска пользователей."""
        u1_id = user_manager.create_user_admin(
            email="searchable_unique@test.com",
            name="Алексей Уникальный",
            role="guest",
            is_active=0
        )
        assert u1_id > 0

        # Поиск по имени
        resp_search = client.get("/api/admin/users?q=Уникальный")
        assert resp_search.status_code == 200
        users = resp_search.json()["users"]
        assert len(users) == 1
        assert users[0]["id"] == u1_id

        # Фильтр по роли
        resp_role = client.get("/api/admin/users?role=guest")
        assert resp_role.status_code == 200
        roles = [u["role"] for u in resp_role.json()["users"]]
        assert all(r == "guest" for r in roles)

        # Фильтр по статусу
        resp_status = client.get("/api/admin/users?status=inactive")
        assert resp_status.status_code == 200
        statuses = [u["is_active"] for u in resp_status.json()["users"]]
        assert all(s == 0 for s in statuses)
