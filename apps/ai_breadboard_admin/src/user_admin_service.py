# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: User Administration Service Module
# =============================================================================
# Description:
#   Сервис администрирования пользователей, управления ролями, правами доступа,
#   паролями, статусом активности и очистки осиротевших каталогов пользователей.
#
# Examples:
#   >>> from apps.ai_breadboard_admin.src.user_admin_service import UserAdminService
#   >>> service = UserAdminService()
#   >>> users_data = service.get_users_list()
#
# File: user_admin_service.py
# Project: AI-Breadboard
# Package: apps.ai_breadboard_admin.src
# Module: user_admin_service
# Class: UserAdminService
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

from typing import Any, Dict, List, Optional

from logger import logger
from src.user_manager import user_manager


class UserAdminService:
    """Сервис для административного управления пользователями и их ресурсами."""

    def __init__(self) -> None:
        """Инициализация сервиса администрирования пользователей."""
        self.mgr = user_manager

    def get_users_list(
        self,
        q: str = "",
        role: str = "",
        status: str = "",
    ) -> Dict[str, Any]:
        """Получение списка пользователей с фильтрацией, поиском и статистикой.

        Args:
            q (str): Поисковый запрос по имени, email или telegram.
            role (str): Фильтр по роли ('admin', 'user').
            status (str): Фильтр по статусу ('active', 'inactive').

        Returns:
            Dict[str, Any]: Словарь со списком пользователей и агрегированной статистикой.
        """
        all_users = self.mgr.get_all_users(active_only=False)

        total_count = len(all_users)
        active_count = sum(1 for u in all_users if u.get("is_active", 0) == 1)
        admin_count = sum(
            1 for u in all_users if u.get("is_admin", 0) == 1 or u.get("role") == "admin"
        )
        tg_count = sum(1 for u in all_users if u.get("telegram_id"))

        filtered: List[Dict[str, Any]] = []
        q_lower = q.lower().strip()

        for u in all_users:
            if q_lower:
                name_match = q_lower in str(u.get("name", "")).lower()
                email_match = q_lower in str(u.get("email", "")).lower()
                tg_match = (
                    q_lower in str(u.get("telegram_username", "")).lower()
                    or q_lower in str(u.get("telegram_id", ""))
                )
                if not (name_match or email_match or tg_match):
                    continue

            if role and u.get("role") != role:
                continue

            if status == "active" and u.get("is_active", 0) != 1:
                continue
            if status == "inactive" and u.get("is_active", 0) == 1:
                continue

            sanitized = {k: v for k, v in u.items() if k != "password_hash"}
            sanitized["has_password"] = bool(u.get("password_hash"))
            filtered.append(sanitized)

        return {
            "status": "ok",
            "users": filtered,
            "stats": {
                "total": total_count,
                "active": active_count,
                "suspended": total_count - active_count,
                "admins": admin_count,
                "telegram": tg_count,
            },
        }

    def create_user(
        self,
        email: str,
        name: str,
        password: str = "",
        role: str = "user",
        is_admin: int = 0,
        is_active: int = 1,
        is_email_verified: int = 1,
    ) -> Dict[str, Any]:
        """Создание нового пользователя администратором.

        Args:
            email (str): Адрес электронной почты.
            name (str): Отображаемое имя пользователя.
            password (str): Пароль учетной записи.
            role (str): Роль пользователя ('user' или 'admin').
            is_admin (int): Флаг администратора (1 или 0).
            is_active (int): Флаг активности аккаунта (1 или 0).
            is_email_verified (int): Флаг подтверждения почты (1 или 0).

        Returns:
            Dict[str, Any]: Словарь с данными созданного пользователя.

        Exceptions:
            ValueError: При отсутствии обязательных полей или если пользователь уже существует.
        """
        clean_email = email.strip().lower()
        clean_name = name.strip()

        if not clean_email:
            raise ValueError("Email обязателен для создания пользователя")
        if not clean_name:
            raise ValueError("Имя обязательно для создания пользователя")
        if self.mgr.user_exists(clean_email):
            raise ValueError(f"Пользователь с email {clean_email} уже существует")

        user_id = self.mgr.create_user_admin(
            email=clean_email,
            name=clean_name,
            password=password,
            role=role,
            is_admin=is_admin,
            is_active=is_active,
            is_email_verified=is_email_verified,
        )

        if not user_id:
            raise RuntimeError("Ошибка базы данных при создании пользователя")

        created = self.mgr.get_user_by_id(user_id)
        sanitized = {k: v for k, v in created.items() if k != "password_hash"}
        sanitized["has_password"] = bool(created.get("password_hash"))
        return {"status": "ok", "user": sanitized}

    def get_user_details(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение детальной информации о пользователе.

        Args:
            user_id (int): Идентификатор пользователя.

        Returns:
            Optional[Dict[str, Any]]: Детали профиля, настройки и квоты хранилища.
        """
        user = self.mgr.get_user_by_id(user_id)
        if not user:
            return None

        settings = self.mgr.get_user_settings(user_id)
        permissions = self.mgr.get_user_permissions(user_id)
        storage_stats = self.mgr.get_user_storage_stats(user_id)

        sanitized = {k: v for k, v in user.items() if k != "password_hash"}
        sanitized["has_password"] = bool(user.get("password_hash"))

        return {
            "status": "ok",
            "user": sanitized,
            "settings": settings,
            "permissions": permissions,
            "storage": storage_stats,
        }

    def update_user(self, user_id: int, **fields: Any) -> Dict[str, Any]:
        """Обновление полей учетной записи пользователя.

        Args:
            user_id (int): Идентификатор пользователя.
            **fields: Обновляемые параметры пользователя.

        Returns:
            Dict[str, Any]: Обновленный профиль пользователя.

        Exceptions:
            ValueError: При попытке снять права с супер-админа ID 1 или при конфликте email.
            KeyError: Если пользователь не найден.
        """
        user = self.mgr.get_user_by_id(user_id)
        if not user:
            raise KeyError("Пользователь не найден")

        # Защита супер-администратора (ID 1)
        if user_id == 1:
            if "is_admin" in fields and fields["is_admin"] == 0:
                raise ValueError("Нельзя снять права у главного администратора (ID 1)")
            if "is_active" in fields and fields["is_active"] == 0:
                raise ValueError("Нельзя деактивировать главного администратора (ID 1)")

        if "email" in fields and fields["email"]:
            new_email = fields["email"].strip().lower()
            if new_email != user.get("email"):
                existing = self.mgr.get_user_by_email(new_email)
                if existing and existing.get("id") != user_id:
                    raise ValueError("Этот email уже занят другим пользователем")
                fields["email"] = new_email

        self.mgr.update_user(user_id, **fields)
        updated = self.mgr.get_user_by_id(user_id)
        sanitized = {k: v for k, v in updated.items() if k != "password_hash"}
        sanitized["has_password"] = bool(updated.get("password_hash"))
        return {"status": "ok", "user": sanitized}

    def set_user_password(self, user_id: int, password: str) -> bool:
        """Установка нового пароля пользователя.

        Args:
            user_id (int): Идентификатор пользователя.
            password (str): Новый пароль.

        Returns:
            bool: True при успехе, иначе False.
        """
        if not password.strip():
            raise ValueError("Пароль не может быть пустым")
        user = self.mgr.get_user_by_id(user_id)
        if not user:
            raise KeyError("Пользователь не найден")
        return self.mgr.set_user_password(user_id, password.strip())

    def toggle_user_active(self, user_id: int) -> int:
        """Переключение статуса активности пользователя (активен / заблокирован).

        Args:
            user_id (int): Идентификатор пользователя.

        Returns:
            int: Новый статус активности (1 или 0).
        """
        if user_id == 1:
            raise ValueError("Нельзя деактивировать главного администратора (ID 1)")
        user = self.mgr.get_user_by_id(user_id)
        if not user:
            raise KeyError("Пользователь не найден")
        new_status = 0 if user.get("is_active", 1) == 1 else 1
        self.mgr.update_user(user_id, is_active=new_status)
        return new_status

    def toggle_user_role(self, user_id: int) -> Dict[str, Any]:
        """Переключение роли пользователя (admin <-> user).

        Args:
            user_id (int): Идентификатор пользователя.

        Returns:
            Dict[str, Any]: Словарь с новыми значениями role и is_admin.
        """
        if user_id == 1:
            raise ValueError("Нельзя изменить роль главного администратора (ID 1)")
        user = self.mgr.get_user_by_id(user_id)
        if not user:
            raise KeyError("Пользователь не найден")

        is_currently_admin = bool(user.get("is_admin", 0) or user.get("role") == "admin")
        new_role = "user" if is_currently_admin else "admin"
        new_is_admin = 0 if is_currently_admin else 1

        self.mgr.update_user(user_id, role=new_role, is_admin=new_is_admin)
        return {"role": new_role, "is_admin": new_is_admin}

    def delete_user(self, user_id: int) -> bool:
        """Удаление пользователя из базы данных.

        Args:
            user_id (int): Идентификатор пользователя.

        Returns:
            bool: True при успешном удалении.
        """
        if user_id == 1:
            raise ValueError("Нельзя удалить главного администратора (ID 1)")
        user = self.mgr.get_user_by_id(user_id)
        if not user:
            raise KeyError("Пользователь не найден")
        return self.mgr.delete_user(user_id)

    def get_orphaned_directories(self) -> Dict[str, Any]:
        """Получение списка осиротевших каталогов пользователей.

        Returns:
            Dict[str, Any]: Метаданные и список осиротевших папок.
        """
        orphaned = self.mgr.get_orphaned_user_directories()
        total_size = sum(item["size_bytes"] for item in orphaned)
        total_files = sum(item["files_count"] for item in orphaned)
        return {
            "status": "ok",
            "total": len(orphaned),
            "total_size_bytes": total_size,
            "total_files": total_files,
            "orphaned_dirs": orphaned,
        }

    def clean_orphaned_directories(self, dir_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """Очистка осиротевших каталогов пользователей.

        Args:
            dir_names (Optional[List[str]]): Список конкретных директорий для удаления.

        Returns:
            Dict[str, Any]: Результаты очистки.
        """
        return self.mgr.cleanup_orphaned_user_directories(dir_names=dir_names)


__all__ = ["UserAdminService"]
