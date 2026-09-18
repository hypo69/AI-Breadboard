# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows System Administrator Business Logic State Management
# =============================================================================
# Description:
#   Управление состоянием Windows System Administrator:
#   - Сессии пользователей и Active Directory
#   - Журнал событий безопасности Windows (Security Event Log)
#   - Аудит удаления файлов (File Deletion & Security Auditing)
#   - Мониторинг файловой системы в реальном времени (DirectoryWatcher)
#
# File: state.py
# Project: ai-breadboard
# Package: apps.windows_sysadmin.src
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Управление состоянием и бизнес-логика Windows System Administrator."""

from __future__ import annotations

import platform
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from apps.windows_sysadmin.src.directory_watcher import (
    DirectoryWatcher,
    LiveFileEvent,
    get_directory_watcher,
)
from apps.windows_sysadmin.src.file_auditor import (
    AuditPolicyStatus,
    FileAuditEvent,
    FolderSaclStatus,
    WindowsFileAuditor,
)
from src.logger import logger


@dataclass
class UserSession:
    """Модель активной сессии пользователя Windows."""

    username: str
    session_id: int
    status: str = "Active"
    login_time: str = ""
    ip_address: str = ""
    process_count: int = 0


@dataclass
class SecurityEvent:
    """Модель события безопасности Windows."""

    timestamp: datetime
    event_id: int
    level: str  # Critical, Warning, Information, Error
    source: str
    description: str


@dataclass
class SystemAdminState:
    """Текущее состояние системы Windows System Administrator."""

    hostname: str = "WORKSTATION"
    domain: str = "WORKGROUP"
    users: List[UserSession] = field(default_factory=list)
    events: List[SecurityEvent] = field(default_factory=list)
    uptime_seconds: int = 0
    ad_connected: bool = False
    ad_status: str = "Disconnected"

    # Файловый аудит
    file_auditor: WindowsFileAuditor = field(default_factory=WindowsFileAuditor)
    audit_policy: AuditPolicyStatus = field(default_factory=AuditPolicyStatus)
    file_events: List[FileAuditEvent] = field(default_factory=list)
    deletion_count_24h: int = 0
    recent_deleted_files: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Постинициализация состояния."""
        self.hostname = platform.node()

    def refresh(self) -> None:
        """Обновить общее состояние системы."""
        self.hostname = platform.node()
        self._refresh_users()
        self._refresh_security_events()
        self._refresh_file_audit_summary()

    def _refresh_users(self) -> None:
        """Собрать информацию о пользователях."""
        if not self.users:
            self.users = [
                UserSession(
                    username="Administrator",
                    session_id=1,
                    status="Active",
                    login_time=datetime.now().isoformat(),
                    ip_address="127.0.0.1",
                    process_count=23,
                ),
                UserSession(
                    username="CurrentSession",
                    session_id=2,
                    status="Active",
                    login_time=(datetime.now() - timedelta(hours=1)).isoformat(),
                    ip_address="127.0.0.1",
                    process_count=45,
                ),
            ]

    def _refresh_security_events(self) -> None:
        """Собрать недавние события безопасности."""
        if not self.events:
            self.events = [
                SecurityEvent(
                    timestamp=datetime.now(),
                    event_id=4624,
                    level="Information",
                    source="Security",
                    description="An account was successfully logged on.",
                ),
                SecurityEvent(
                    timestamp=datetime.now() - timedelta(minutes=2),
                    event_id=4663,
                    level="Information",
                    source="Microsoft-Windows-Security-Auditing",
                    description="An attempt was made to access an object (Access: DELETE).",
                ),
                SecurityEvent(
                    timestamp=datetime.now() - timedelta(minutes=5),
                    event_id=4660,
                    level="Information",
                    source="Microsoft-Windows-Security-Auditing",
                    description="An object was deleted.",
                ),
            ]

    def _refresh_file_audit_summary(self) -> None:
        """Обновить статус политики аудита файловой системы и метрики."""
        self.audit_policy = self.file_auditor.get_audit_policy_status()
