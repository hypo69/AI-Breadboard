# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Accounts & Identity Graph Engine
# =============================================================================
# Description:
#   Движок Windows Identity Graph: построение единого объекта Principal,
#   связывание пользователей, групп, прав LSA, сессий, процессов, профилей и аудита.
#   Выполнение высокоуровневых аналитических запросов (who-is-admin, explain-pid и др.).
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.accounts_identity.graph_engine import IdentityGraphEngine
#
#     engine = IdentityGraphEngine()
#     principal = engine.explain_principal("onela")
#     admins = engine.who_is_admin()
#
# File: graph_engine.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.accounts_identity
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 00:51:00
# =============================================================================

"""Движок построения графа субъектов безопасности Windows (Identity Graph Engine)."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
import psutil

from logger import logger
from apps.windows.sdk.modules.accounts_identity.models import (
    AccountDetails,
    AccountSource,
    GroupRef,
    IdentityGraph,
    IdentityGraphEdge,
    IdentityGraphNode,
    Principal,
    PrincipalType,
)
from apps.windows.sdk.modules.accounts_identity.subsystems.subsystem_01_identity import IdentitySubsystem
from apps.windows.sdk.modules.accounts_identity.subsystems.subsystem_02_users import UsersSubsystem
from apps.windows.sdk.modules.accounts_identity.subsystems.subsystem_03_groups import GroupsSubsystem
from apps.windows.sdk.modules.accounts_identity.subsystems.subsystem_04_sid import SidSubsystem
from apps.windows.sdk.modules.accounts_identity.subsystems.subsystem_05_auth import AuthPolicySubsystem
from apps.windows.sdk.modules.accounts_identity.subsystems.subsystem_06_rights import LsaRightsSubsystem
from apps.windows.sdk.modules.accounts_identity.subsystems.subsystem_07_tokens import TokensSubsystem
from apps.windows.sdk.modules.accounts_identity.subsystems.subsystem_08_sessions import SessionsSubsystem
from apps.windows.sdk.modules.accounts_identity.subsystems.subsystem_09_profiles import ProfilesSubsystem
from apps.windows.sdk.modules.accounts_identity.subsystems.subsystem_10_audit import AuditSubsystem
from apps.windows.sdk.modules.accounts_identity.subsystems.subsystem_domain import DomainSubsystem
from apps.windows.sdk.modules.accounts_identity.win32_bridge import Win32IdentityBridge


class IdentityGraphEngine:
    """Движок корреляции сущностей и построения Windows Identity Graph."""

    def __init__(self, bridge: Optional[Win32IdentityBridge] = None) -> None:
        """Инициализация подсистем и движка графа."""
        self.bridge = bridge or Win32IdentityBridge()
        self.identity = IdentitySubsystem(self.bridge)
        self.users = UsersSubsystem(self.bridge)
        self.groups = GroupsSubsystem(self.bridge)
        self.sid = SidSubsystem(self.bridge)
        self.auth = AuthPolicySubsystem(self.bridge)
        self.rights = LsaRightsSubsystem(self.bridge)
        self.tokens = TokensSubsystem(self.bridge)
        self.sessions = SessionsSubsystem(self.bridge)
        self.profiles = ProfilesSubsystem(self.bridge)
        self.audit = AuditSubsystem(self.bridge)
        self.domain = DomainSubsystem(self.bridge)

    def explain_principal(self, identifier: str) -> Principal:
        """
        Формирует полное досье субъекта безопасности (Principal).

        Args:
            identifier: Имя пользователя, SID или UPN.

        Returns:
            Объект Principal со всеми связанными ресурсами.
        """
        resolved = self.sid.resolve_principal(identifier)
        sid_val = resolved["sid"]
        name_val = resolved["name"]
        domain_val = resolved["domain"] or os.environ.get("USERDOMAIN", "WORKGROUP")
        is_built_in = resolved["is_built_in"]
        is_orphaned = resolved["is_orphaned"]

        # Получение деталей учетной записи
        account_details = self.users.get_user_info(name_val or sid_val)
        
        # Получение групп
        user_groups = self.groups.get_user_groups(name_val) if name_val and not is_orphaned else []
        is_admin = any(g.is_admin for g in user_groups) or bool(self.groups.find_path_to_administrators(name_val))

        # Получение LSA-прав
        user_rights = self.rights.list_user_rights(name_val or sid_val)

        # Активные сессии
        all_sessions = self.sessions.list_sessions()
        user_sessions = [s for s in all_sessions if s.user_name.lower() == name_val.lower()]

        # Процессы пользователя
        user_processes: List[Dict[str, Any]] = []
        try:
            for proc in psutil.process_iter(["pid", "name", "username"]):
                try:
                    p_info = proc.info
                    p_user = p_info.get("username") or ""
                    if name_val.lower() in p_user.lower():
                        user_processes.append({"pid": p_info["pid"], "name": p_info["name"]})
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.debug(f"Ошибка сбора процессов для {name_val}: {e}")

        # Профиль пользователя
        all_profiles = self.profiles.list_profiles()
        matched_profile = next((p for p in all_profiles if p.username.lower() == name_val.lower() or p.sid == sid_val), None)

        # События аудита
        user_events = self.audit.get_events_for_user(name_val, limit=10) if name_val else []

        # Тип субъекта
        p_type = PrincipalType.ORPHANED_SID if is_orphaned else (
            PrincipalType.WELL_KNOWN if is_built_in else PrincipalType.USER
        )

        return Principal(
            sid=sid_val or "S-1-0-0",
            name=name_val,
            domain=domain_val,
            principal_type=p_type,
            source=AccountSource.BUILT_IN if is_built_in else AccountSource.SAM,
            is_admin=is_admin,
            is_built_in=is_built_in,
            is_orphaned=is_orphaned,
            account=account_details,
            groups=user_groups,
            rights=user_rights,
            sessions=user_sessions,
            processes=user_processes[:50],
            profile=matched_profile,
            audit_events=user_events,
        )

    def who_is_admin(self) -> List[Dict[str, Any]]:
        """
        Находит всех администраторов системы (включая непрямое вложенное членство).

        Returns:
            Список административных аккаунтов с указанием цепочки прав.
        """
        admins_group_members = self.groups.enumerate_nested_membership("Administrators")
        all_users = self.users.list_users()
        results: List[Dict[str, Any]] = []

        for user in all_users:
            path = self.groups.find_path_to_administrators(user.name)
            is_direct = any(m.lower() == user.name.lower() or m.lower().endswith(f"\\{user.name.lower()}") for m in admins_group_members)
            if is_direct or path:
                results.append({
                    "username": user.name,
                    "sid": user.sid,
                    "enabled": user.enabled,
                    "is_direct": is_direct,
                    "path_to_admin": path or [user.name, "Administrators"],
                })

        return results

    def who_can_logon_as_service(self) -> List[str]:
        """Находит учетные записи, обладающие правом SeServiceLogonRight."""
        return self.rights.get_accounts_with_service_logon()

    def who_can_rdp(self) -> List[str]:
        """Находит учетные записи с доступом к удаленному рабочему столу (RDP)."""
        return self.rights.get_accounts_with_remote_logon()

    def find_orphaned_sids(self) -> List[Dict[str, Any]]:
        """Выявляет осиротевшие SID в профилях и правах безопасности."""
        orphaned: List[Dict[str, Any]] = []
        for profile in self.profiles.find_orphaned_profiles():
            orphaned.append({
                "sid": profile.sid,
                "location": profile.profile_path,
                "source": "UserProfile / ProfileList",
                "state": "ORPHANED",
            })
        return orphaned

    def find_orphaned_profiles(self) -> List[Dict[str, Any]]:
        """Выявляет папки и записи профилей без действительных учетных записей."""
        return [p.model_dump() for p in self.profiles.find_orphaned_profiles()]

    def explain_pid(self, pid: int) -> Dict[str, Any]:
        """
        Формирует подробный отчет безопасности по PID.
        
        PID -> Process Token -> User SID -> Account -> Groups -> Privileges -> Integrity -> Elevation -> Session.
        """
        return self.tokens.explain_pid(pid)

    def build_identity_graph(self) -> IdentityGraph:
        """
        Строит полный граф субъектов безопасности Windows.

        Returns:
            Объект IdentityGraph с узлами и связями.
        """
        nodes: List[IdentityGraphNode] = []
        edges: List[IdentityGraphEdge] = []

        all_users = self.users.list_users()
        all_groups = self.groups.list_groups()
        all_sessions = self.sessions.list_sessions()

        # Добавление пользователей
        for u in all_users:
            nodes.append(
                IdentityGraphNode(
                    id=f"user:{u.name}",
                    label=u.name,
                    node_type="User",
                    data={"sid": u.sid, "enabled": u.enabled, "full_name": u.full_name},
                )
            )

        # Добавление групп
        for g in all_groups:
            nodes.append(
                IdentityGraphNode(
                    id=f"group:{g.name}",
                    label=g.name,
                    node_type="Group",
                    data={"sid": g.sid, "is_admin": g.is_admin},
                )
            )

        # Добавление сессий
        for s in all_sessions:
            nodes.append(
                IdentityGraphNode(
                    id=f"session:{s.session_id}",
                    label=f"Session {s.session_id} ({s.session_type})",
                    node_type="Session",
                    data={"state": s.state, "user": s.user_name},
                )
            )

        # Построение связей User -> Group
        for g in all_groups:
            for member in g.members:
                m_clean = member.split("\\")[-1] if "\\" in member else member
                edges.append(
                    IdentityGraphEdge(
                        source=f"user:{m_clean}",
                        target=f"group:{g.name}",
                        relationship="MEMBER_OF",
                        metadata={"is_admin": g.is_admin},
                    )
                )

        # Связи User -> Session
        for s in all_sessions:
            if s.user_name:
                edges.append(
                    IdentityGraphEdge(
                        source=f"user:{s.user_name}",
                        target=f"session:{s.session_id}",
                        relationship="LOGGED_IN_SESSION",
                        metadata={"state": s.state},
                    )
                )

        summary = {
            "total_users": len(all_users),
            "total_groups": len(all_groups),
            "total_sessions": len(all_sessions),
            "total_nodes": len(nodes),
            "total_edges": len(edges),
        }

        return IdentityGraph(nodes=nodes, edges=edges, summary=summary)
