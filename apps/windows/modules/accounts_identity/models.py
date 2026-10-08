# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Accounts & Identity Models
# =============================================================================
# Description:
#   Модели данных, перечисления и структуры домена Accounts & Identity
#   для операционной системы Windows (Windows Identity Graph).
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.accounts_identity.models import Principal, RiskLevel
#
#     principal = Principal(sid="S-1-5-21-...", name="onela", domain="WORKGROUP")
#
# File: models.py
# Project: ai-breadboard
# Package: apps.windows.modules.accounts_identity
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 00:48:00
# =============================================================================

"""Модели данных и схемы для подсистемы Accounts & Identity Windows."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Уровень риска операции согласно каталогу безопасности Windows."""
    SAFE = "🟢 SAFE"
    ADMIN = "🟡 ADMIN"
    DANGEROUS = "🔴 DANGEROUS"
    ADVANCED = "⚫ ADVANCED"


class PrincipalType(str, Enum):
    """Тип субъекта безопасности (Security Principal)."""
    USER = "User"
    LOCAL_GROUP = "LocalGroup"
    GLOBAL_GROUP = "GlobalGroup"
    WELL_KNOWN = "WellKnownPrincipal"
    SERVICE_ACCOUNT = "ServiceAccount"
    COMPUTER = "Computer"
    ORPHANED_SID = "OrphanedSid"
    UNKNOWN = "Unknown"


class AccountSource(str, Enum):
    """Источник учетной записи / провайдер авторизации."""
    SAM = "SAM"
    ACTIVE_DIRECTORY = "ActiveDirectory"
    ENTRA_ID = "EntraID"
    VIRTUAL_ACCOUNT = "VirtualAccount"
    BUILT_IN = "BuiltIn"
    UNKNOWN = "Unknown"


class IntegrityLevel(str, Enum):
    """Уровень целостности маркера доступа (Mandatory Integrity Control)."""
    UNTRUSTED = "Untrusted"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    SYSTEM = "System"
    PROTECTED_PROCESS = "ProtectedProcess"
    UNKNOWN = "Unknown"


class TokenType(str, Enum):
    """Тип токена безопасности Windows."""
    PRIMARY = "Primary"
    IMPERSONATION = "Impersonation"


class ImpersonationLevel(str, Enum):
    """Уровень олицетворения (Impersonation Level) токена."""
    ANONYMOUS = "Anonymous"
    IDENTIFICATION = "Identification"
    IMPERSONATION = "Impersonation"
    DELEGATION = "Delegation"
    NONE = "None"


class ProfileType(str, Enum):
    """Тип профиля пользователя Windows."""
    LOCAL = "Local"
    ROAMING = "Roaming"
    MANDATORY = "Mandatory"
    TEMPORARY = "Temporary"
    UNKNOWN = "Unknown"


class MachineRole(str, Enum):
    """Роль рабочей станции или сервера в домене Windows."""
    STANDALONE_WORKSTATION = "StandaloneWorkstation"
    MEMBER_WORKSTATION = "MemberWorkstation"
    STANDALONE_SERVER = "StandaloneServer"
    MEMBER_SERVER = "MemberServer"
    BACKUP_DOMAIN_CONTROLLER = "BackupDomainController"
    PRIMARY_DOMAIN_CONTROLLER = "PrimaryDomainController"
    UNKNOWN = "Unknown"


class OperationCatalogItem(BaseModel):
    """Элемент официального каталога операций Accounts & Identity."""
    id: int
    name_ru: str
    subsystem_id: str
    subsystem_name_ru: str
    risk_level: RiskLevel
    mechanism: str
    win32_api: Optional[str] = None
    ps_or_cli: Optional[str] = None
    description_ru: str = ""


class GroupRef(BaseModel):
    """Ссылка на группу безопасности."""
    name: str
    sid: str = ""
    domain: str = ""
    is_admin: bool = False
    is_local: bool = True
    description: str = ""


class GroupDetails(BaseModel):
    """Подробные сведения о группе безопасности Windows."""
    name: str
    sid: str = ""
    domain: str = ""
    description: str = ""
    is_admin: bool = False
    is_local: bool = True
    members: List[str] = Field(default_factory=list)
    member_sids: List[str] = Field(default_factory=list)
    nested_members: List[str] = Field(default_factory=list)


class TokenPrivilege(BaseModel):
    """Привилегия токена доступа Windows (Se...Privilege)."""
    name: str
    description: str = ""
    enabled: bool = False
    is_sensitive: bool = False


class TokenDetails(BaseModel):
    """Снимок параметров маркера доступа (Access Token) процесса."""
    pid: int
    process_name: str = ""
    user_name: str = ""
    user_sid: str = ""
    domain: str = ""
    integrity_level: IntegrityLevel = IntegrityLevel.UNKNOWN
    is_elevated: bool = False
    token_type: TokenType = TokenType.PRIMARY
    impersonation_level: ImpersonationLevel = ImpersonationLevel.NONE
    session_id: int = 0
    logon_sid: str = ""
    groups: List[GroupRef] = Field(default_factory=list)
    privileges: List[TokenPrivilege] = Field(default_factory=list)


class SessionDetails(BaseModel):
    """Сведения о сессии входа (Logon / WTS Session)."""
    session_id: int
    user_name: str = ""
    domain: str = ""
    state: str = "Active"
    client_name: str = ""
    client_ip: str = ""
    logon_time: Optional[str] = None
    idle_time_seconds: Optional[int] = None
    session_type: str = "Console"
    is_current: bool = False


class ProfileDetails(BaseModel):
    """Сведения о профиле пользователя Windows (C:\\Users\\...)."""
    sid: str
    username: str = ""
    profile_path: str = ""
    profile_type: ProfileType = ProfileType.LOCAL
    is_loaded: bool = False
    state_flags: int = 0
    last_modified: Optional[str] = None
    registry_hive_path: str = ""
    is_orphaned: bool = False


class AuditEventItem(BaseModel):
    """Событие аудита безопасности Windows (Security Event Log)."""
    event_id: int
    event_name: str
    timestamp: str
    target_account: str = ""
    target_sid: str = ""
    caller_account: str = ""
    caller_domain: str = ""
    caller_sid: str = ""
    status: str = "Success"
    description: str = ""
    details: Dict[str, Any] = Field(default_factory=dict)


class PasswordPolicy(BaseModel):
    """Политика паролей и блокировок учетных записей Windows SAM."""
    min_password_length: int = 0
    password_history_length: int = 0
    max_password_age_days: int = 42
    min_password_age_days: int = 0
    lockout_threshold: int = 0
    lockout_duration_minutes: int = 30
    lockout_window_minutes: int = 30


class AccountDetails(BaseModel):
    """Детали локальной или доменной учетной записи."""
    name: str
    sid: str = ""
    full_name: str = ""
    description: str = ""
    enabled: bool = True
    locked: bool = False
    account_expires: Optional[str] = None
    password_required: bool = True
    password_last_set: Optional[str] = None
    password_expires: Optional[str] = None
    password_never_expires: bool = False
    cannot_change_password: bool = False
    bad_password_count: int = 0
    last_logon: Optional[str] = None
    logon_hours: Optional[str] = None
    logon_workstations: Optional[str] = None


class DomainInfo(BaseModel):
    """Информация о домене и Entra / Active Directory интеграции."""
    domain_name: str = ""
    dns_domain: str = ""
    forest_name: str = ""
    domain_guid: str = ""
    machine_role: MachineRole = MachineRole.STANDALONE_WORKSTATION
    workgroup: str = "WORKGROUP"
    is_domain_joined: bool = False
    is_entra_joined: bool = False
    computer_name: str = ""


class Principal(BaseModel):
    """
    Единый объект субъекта безопасности Windows (Principal).
    
    Объединяет идентификацию, параметры учетной записи, группы,
    LSA-права, сессии, процессы, профиль и журнал аудита.
    """
    sid: str
    name: str
    domain: str = ""
    principal_type: PrincipalType = PrincipalType.USER
    source: AccountSource = AccountSource.SAM
    is_admin: bool = False
    is_built_in: bool = False
    is_orphaned: bool = False
    account: Optional[AccountDetails] = None
    groups: List[GroupRef] = Field(default_factory=list)
    rights: List[str] = Field(default_factory=list)
    sessions: List[SessionDetails] = Field(default_factory=list)
    processes: List[Dict[str, Any]] = Field(default_factory=list)
    profile: Optional[ProfileDetails] = None
    audit_events: List[AuditEventItem] = Field(default_factory=list)


class IdentityGraphNode(BaseModel):
    """Узел графа идентификации Windows."""
    id: str
    label: str
    node_type: str
    data: Dict[str, Any] = Field(default_factory=dict)


class IdentityGraphEdge(BaseModel):
    """Ребро графа идентификации Windows."""
    source: str
    target: str
    relationship: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IdentityGraph(BaseModel):
    """Полный граф субъектов безопасности, групп, прав, сессий и процессов."""
    nodes: List[IdentityGraphNode] = Field(default_factory=list)
    edges: List[IdentityGraphEdge] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)
