# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Accounts & Identity Service
# =============================================================================
# Description:
#   Центральный сервис-фасад для управления аккаунтами, идентификацией,
#   правами LSA, токенами, сессиями и графом безопасности Windows.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.accounts_identity.service import get_accounts_identity_service
#
#     srv = get_accounts_identity_service()
#     whoami_doc = srv.get_current_identity()
#
# File: service.py
# Project: ai-breadboard
# Package: apps.windows.modules.accounts_identity
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 01:45:00
# =============================================================================

"""Единый сервис-фасад Accounts & Identity Windows."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from logger import logger
from apps.windows.modules.accounts_identity.catalog import get_full_catalog, search_catalog
from apps.windows.modules.accounts_identity.graph_engine import IdentityGraphEngine
from apps.windows.modules.accounts_identity.models import (
    AccountDetails,
    AuditEventItem,
    DomainInfo,
    GroupDetails,
    IdentityGraph,
    OperationCatalogItem,
    PasswordPolicy,
    Principal,
    ProfileDetails,
    SessionDetails,
    TokenDetails,
)
from apps.windows.modules.accounts_identity.win32_bridge import Win32IdentityBridge


class AccountsIdentityService:
    """Главный сервис управления каталогом Accounts & Identity Windows."""

    def __init__(self, bridge: Optional[Win32IdentityBridge] = None) -> None:
        """Инициализация сервиса и движка графа."""
        self.bridge = bridge or Win32IdentityBridge()
        self.engine = IdentityGraphEngine(self.bridge)

    def get_catalog(self, query: Optional[str] = None) -> List[OperationCatalogItem]:
        """Возвращает каталог системных операций."""
        if query:
            return search_catalog(query)
        return get_full_catalog()

    def get_current_identity(self) -> TokenDetails:
        """Возвращает контекст безопасности текущего пользователя."""
        return self.engine.identity.get_current_identity_context()

    def list_users(self) -> List[AccountDetails]:
        """Возвращает список пользователей."""
        return self.engine.users.list_users()

    def get_user(self, name_or_sid: str) -> Optional[AccountDetails]:
        """Возвращает данные пользователя."""
        return self.engine.users.get_user_info(name_or_sid)

    def create_user(self, name: str, password: Optional[str] = None, full_name: str = "", description: str = "") -> bool:
        """Создает нового пользователя."""
        return self.engine.users.create_user(name=name, password=password, full_name=full_name, description=description)

    def delete_user(self, name: str) -> bool:
        """Удаляет пользователя."""
        return self.engine.users.delete_user(name)

    def list_groups(self) -> List[GroupDetails]:
        """Возвращает список групп."""
        return self.engine.groups.list_groups()

    def get_group(self, name: str) -> Optional[GroupDetails]:
        """Возвращает данные группы."""
        return self.engine.groups.get_group(name)

    def add_user_to_group(self, group_name: str, username: str) -> bool:
        """Добавляет пользователя в группу."""
        return self.engine.groups.add_member(group_name, username)

    def remove_user_from_group(self, group_name: str, username: str) -> bool:
        """Удаляет пользователя из группы."""
        return self.engine.groups.remove_member(group_name, username)

    def get_password_policy(self) -> PasswordPolicy:
        """Возвращает политику паролей."""
        return self.engine.auth.get_password_policy()

    def list_sessions(self) -> List[SessionDetails]:
        """Возвращает сессии входа."""
        return self.engine.sessions.list_sessions()

    def list_profiles(self) -> List[ProfileDetails]:
        """Возвращает профили пользователей."""
        return self.engine.profiles.list_profiles()

    def get_domain_info(self) -> DomainInfo:
        """Возвращает данные о домене и Entra ID."""
        return self.engine.domain.get_domain_info()

    def resolve(self, identifier: str) -> Dict[str, Any]:
        """Разрешает SID или имя в субъект безопасности."""
        return self.engine.sid.resolve_principal(identifier)

    def explain(self, identifier: str) -> Principal:
        """Формирует полное досье Principal."""
        return self.engine.explain_principal(identifier)

    def who_is_admin(self) -> List[Dict[str, Any]]:
        """Возвращает список всех администраторов системы."""
        return self.engine.who_is_admin()

    def who_can_logon_as_service(self) -> List[str]:
        """Возвращает аккаунты с правом SeServiceLogonRight."""
        return self.engine.who_can_logon_as_service()

    def who_can_rdp(self) -> List[str]:
        """Возвращает аккаунты с правом входа через RDP."""
        return self.engine.who_can_rdp()

    def find_orphaned_sids(self) -> List[Dict[str, Any]]:
        """Возвращает осиротевшие SID."""
        return self.engine.find_orphaned_sids()

    def find_orphaned_profiles(self) -> List[Dict[str, Any]]:
        """Возвращает осиротевшие профили."""
        return self.engine.find_orphaned_profiles()

    def explain_pid(self, pid: int) -> Dict[str, Any]:
        """Формирует подробный отчет безопасности по процессу (PID)."""
        return self.engine.explain_pid(pid)

    def get_audit_events(self, limit: int = 50, event_id: Optional[int] = None) -> List[AuditEventItem]:
        """Возвращает недавние события безопасности и управления аккаунтами."""
        return self.engine.audit.get_recent_identity_events(limit=limit, event_id=event_id)

    def get_user_audit_events(self, username: str, limit: int = 20) -> List[AuditEventItem]:
        """Возвращает историю событий безопасности для конкретного пользователя."""
        return self.engine.audit.get_events_for_user(username=username, limit=limit)

    def get_identity_graph(self) -> IdentityGraph:
        """Строит полный Windows Identity Graph."""
        return self.engine.build_identity_graph()


_service_instance: Optional[AccountsIdentityService] = None


def get_accounts_identity_service() -> AccountsIdentityService:
    """Возвращает синглтон сервиса AccountsIdentityService."""
    global _service_instance
    if _service_instance is None:
        _service_instance = AccountsIdentityService()
    return _service_instance
