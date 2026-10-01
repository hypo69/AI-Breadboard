# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Security_Acl Core - Models
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.security_acl.core.models import BitLockerVolumeStatus
#
#     service = BitLockerVolumeStatus()
#
# File: models.py
# Project: ai-breadboard
# Package: apps.windows.modules.security_acl.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BitLockerVolumeStatus(BaseModel):
    """Статус шифрования BitLocker на томе."""
    drive_letter: str = 'C:'
    conversion_status: str = 'FullyEncrypted'
    protection_status: str = 'ProtectionOn'
    encryption_method: str = 'XTS-AES 128'
    lock_status: str = 'Unlocked'
    key_protector_types: List[str] = Field(default_factory=lambda: ['TPM', 'Numerical Password'])


class AclEntry(BaseModel):
    """Запись контроля доступа (ACE) для объекта файловой системы."""
    principal: str
    access_type: str = 'Allow'  # Allow, Deny
    rights: str = 'ReadAndExecute'
    is_inherited: bool = True


class SecurityAclReport(BaseModel):
    """Сводный отчет о безопасности ACL и BitLocker."""
    bitlocker_volumes: List[BitLockerVolumeStatus] = Field(default_factory=list)
    efs_enabled: bool = True
    uac_level: str = 'AlwaysNotify'
    timestamp: str = ''


class AclModifyRequest(BaseModel):
    """Запрос на модификацию прав ACL."""
    target_path: str
    principal: str
    permission: str  # Read, Modify, FullControl
    action: str = 'grant'  # grant, deny, remove, reset
    dry_run: bool = True
    confirmed_by_user: bool = False


__all__ = [
    'BitLockerVolumeStatus',
    'AclEntry',
    'SecurityAclReport',
    'AclModifyRequest',
]
