# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Core - Atomic Models
# =============================================================================
# Description:
#   Уровень риска операции.
#
# Usage Examples:
#   Python API:
#     from apps.windows.core.atomic_models import RiskLevel
#
#     service = RiskLevel()
#
# File: atomic_models.py
# Project: ai-breadboard
# Package: apps.windows.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Уровень риска операции."""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Уровень риска операции."""
    READ_ONLY = 'READ_ONLY'
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'
    CRITICAL = 'CRITICAL'


class PrivilegeLevel(str, Enum):
    """Требуемые системные привилегии."""
    STANDARD = 'STANDARD'
    ADMINISTRATOR = 'ADMINISTRATOR'
    SYSTEM = 'SYSTEM'


class ExecutionMethod(str, Enum):
    """Способ исполнения операции."""
    CLI = 'CLI'
    NATIVE_API = 'NATIVE_API'
    COM = 'COM'
    WMI = 'WMI'
    POWERSHELL = 'POWERSHELL'


class HttpMethod(str, Enum):
    """HTTP метод для REST эндпоинта."""
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'


class CapabilityCategory(str, Enum):
    """17 категорий системных возможностей Windows."""
    STORAGE_FS = 'storage_fs'
    BOOT_RECOVERY = 'boot_recovery'
    SERVICING_INTEGRITY = 'servicing_integrity'
    DRIVERS_HARDWARE = 'drivers_hardware'
    PROCESSES = 'processes'
    SCHEDULER = 'scheduler'
    PERFORMANCE_TRACING = 'performance_tracing'
    SERVICES = 'services'
    EVENT_LOGS = 'event_logs'
    NETWORK = 'network'
    FIREWALL = 'firewall'
    SECURITY_ACL = 'security_acl'
    REGISTRY_GPO = 'registry_gpo'
    IDENTITY_USERS = 'identity_users'
    VSS_BACKUP = 'vss_backup'
    POWER_LIFECYCLE = 'power_lifecycle'
    SOFTWARE_PACKAGES = 'software_packages'


@dataclass
class AtomicOperation:
    """Атомарная операция утилиты/API Windows."""
    id: str
    utility: str
    category: CapabilityCategory
    name_ru: str
    description: str
    risk_level: RiskLevel
    required_privilege: PrivilegeLevel
    execution_method: ExecutionMethod
    http_method: HttpMethod
    api_route: str
    cli_template: str = ''
    native_api_equivalent: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование операции в словарь."""
        res = asdict(self)
        res['category'] = self.category.value
        res['risk_level'] = self.risk_level.value
        res['required_privilege'] = self.required_privilege.value
        res['execution_method'] = self.execution_method.value
        res['http_method'] = self.http_method.value
        return res


class AtomicOperationExecutionRequest(BaseModel):
    """Запрос на исполнение или симуляцию атомарной операции."""
    operation_id: str = Field(..., description='Идентификатор атомарной операции (например diskpart.disk.list)')
    parameters: Dict[str, Any] = Field(default_factory=dict, description='Параметры операции')
    dry_run: bool = Field(True, description='Режим симуляции (без внесения изменений в систему)')
    confirmed_by_user: bool = Field(False, description='Подтверждение пользователя для операций с риском HIGH/CRITICAL')


class AtomicOperationExecutionResult(BaseModel):
    """Результат исполнения или симуляции атомарной операции."""
    operation_id: str
    utility: str
    status: str
    is_dry_run: bool
    risk_level: str
    required_privilege: str
    command_executed: str
    message: str
    data: Optional[Any] = None
    execution_time_ms: float = 0.0


__all__ = [
    'RiskLevel',
    'PrivilegeLevel',
    'ExecutionMethod',
    'HttpMethod',
    'CapabilityCategory',
    'AtomicOperation',
    'AtomicOperationExecutionRequest',
    'AtomicOperationExecutionResult',
]
