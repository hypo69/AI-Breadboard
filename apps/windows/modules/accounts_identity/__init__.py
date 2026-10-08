# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Accounts & Identity Package
# =============================================================================
# Description:
#   Пакет управления субъектами безопасности, пользователями, группами,
#   правами LSA, токенами, сессиями, профилями и Windows Identity Graph.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.accounts_identity import get_accounts_identity_service, identity_router
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.modules.accounts_identity
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 00:51:00
# =============================================================================

"""Пакет Accounts & Identity Windows для AI-Breadboard."""

from apps.windows.modules.accounts_identity.models import (
    RiskLevel,
    PrincipalType,
    AccountSource,
    IntegrityLevel,
    TokenType,
    ImpersonationLevel,
    ProfileType,
    MachineRole,
    OperationCatalogItem,
    AccountDetails,
    GroupRef,
    GroupDetails,
    TokenPrivilege,
    TokenDetails,
    SessionDetails,
    ProfileDetails,
    AuditEventItem,
    PasswordPolicy,
    DomainInfo,
    Principal,
    IdentityGraph,
    IdentityGraphNode,
    IdentityGraphEdge,
)
from apps.windows.modules.accounts_identity.catalog import (
    get_full_catalog,
    get_operation_by_id,
    get_operations_by_subsystem,
    get_operations_by_risk,
    search_catalog,
)
from apps.windows.modules.accounts_identity.win32_bridge import Win32IdentityBridge
from apps.windows.modules.accounts_identity.graph_engine import IdentityGraphEngine
from apps.windows.modules.accounts_identity.service import (
    AccountsIdentityService,
    get_accounts_identity_service,
)
from apps.windows.modules.accounts_identity.router import router as identity_router
from apps.windows.modules.accounts_identity.tui import format_principal_tree, format_pid_tree

__all__ = [
    "RiskLevel",
    "PrincipalType",
    "AccountSource",
    "IntegrityLevel",
    "TokenType",
    "ImpersonationLevel",
    "ProfileType",
    "MachineRole",
    "OperationCatalogItem",
    "AccountDetails",
    "GroupRef",
    "GroupDetails",
    "TokenPrivilege",
    "TokenDetails",
    "SessionDetails",
    "ProfileDetails",
    "AuditEventItem",
    "PasswordPolicy",
    "DomainInfo",
    "Principal",
    "IdentityGraph",
    "IdentityGraphNode",
    "IdentityGraphEdge",
    "get_full_catalog",
    "get_operation_by_id",
    "get_operations_by_subsystem",
    "get_operations_by_risk",
    "search_catalog",
    "Win32IdentityBridge",
    "IdentityGraphEngine",
    "AccountsIdentityService",
    "get_accounts_identity_service",
    "identity_router",
    "format_principal_tree",
    "format_pid_tree",
]
