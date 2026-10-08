# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Contracts - Enums
# =============================================================================
# Description:
#   Zero-dependency перечисления и константы для Windows подсистем AI-Breadboard.
#
# Usage Examples:
#   Python API:
#     from apps.windows.contracts.enums import RiskLevel, TelemetryTier
#
# File: enums.py
# Project: ai-breadboard
# Package: apps.windows.contracts
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 09:35:00
# =============================================================================

from __future__ import annotations
"""Единые перечисления (Enums) для всех слоев apps.windows."""

from enum import Enum, IntEnum


class RiskLevel(str, Enum):
    """Уровни риска для операций, проблем и аудитов."""
    SAFE = "safe"
    CAUTION = "caution"
    CRITICAL = "critical"
    INFO = "info"
    READ_ONLY = "READ_ONLY"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class PrivilegeLevel(str, Enum):
    """Требуемые системные привилегии."""
    STANDARD = "STANDARD"
    ADMINISTRATOR = "ADMINISTRATOR"
    SYSTEM = "SYSTEM"


class ExecutionMethod(str, Enum):
    """Способ исполнения операции."""
    CLI = "CLI"
    NATIVE_API = "NATIVE_API"
    COM = "COM"
    WMI = "WMI"
    POWERSHELL = "POWERSHELL"


class HttpMethod(str, Enum):
    """HTTP метод для REST эндпоинтов."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


class CapabilityCategory(str, Enum):
    """17 категорий системных возможностей Windows."""
    STORAGE_FS = "storage_fs"
    BOOT_RECOVERY = "boot_recovery"
    SERVICING_INTEGRITY = "servicing_integrity"
    DRIVERS_HARDWARE = "drivers_hardware"
    PROCESSES = "processes"
    SCHEDULER = "scheduler"
    PERFORMANCE_TRACING = "performance_tracing"
    SERVICES = "services"
    EVENT_LOGS = "event_logs"
    NETWORK = "network"
    FIREWALL = "firewall"
    SECURITY_ACL = "security_acl"
    REGISTRY_GPO = "registry_gpo"
    IDENTITY_USERS = "identity_users"
    VSS_BACKUP = "vss_backup"
    POWER_LIFECYCLE = "power_lifecycle"
    SOFTWARE_PACKAGES = "software_packages"


class CapabilityLevel(IntEnum):
    """Уровни возможностей WinAPI."""
    LEVEL_1_DOCUMENTED = 1
    LEVEL_2_WMI_PERF = 2
    LEVEL_3_ETW = 3
    LEVEL_4_NATIVE_NT = 4
    LEVEL_5_UNDOCUMENTED = 5
    LEVEL_6_KERNEL_DRIVER = 6


class ActionType(str, Enum):
    """Типы корректирующих действий аудита."""
    CLEAN_FILE = "clean_file"
    CLEAN_DIRECTORY = "clean_directory"
    DISABLE_STARTUP = "disable_startup"
    STOP_SERVICE = "stop_service"
    DISABLE_SERVICE = "disable_service"
    DISABLE_TASK = "disable_task"
    REMOVE_DRIVER_PACKAGE = "remove_driver_package"
    REPAIR_INTEGRITY = "repair_integrity"
    KILL_PROCESS = "kill_process"
    APPLY_CONFIG = "apply_config"
    CUSTOM_COMMAND = "custom_command"


class ProcessState(str, Enum):
    """Состояния процесса."""
    RUNNING = "Running"
    SUSPENDED = "Suspended"
    UNKNOWN = "Unknown"


class ThreadState(IntEnum):
    """Состояния потока."""
    INITIALIZED = 0
    READY = 1
    RUNNING = 2
    STANDBY = 3
    TERMINATED = 4
    WAIT = 5
    TRANSITION = 6


class ServiceState(str, Enum):
    """Состояния системной службы."""
    STOPPED = "Stopped"
    START_PENDING = "Start Pending"
    STOP_PENDING = "Stop Pending"
    RUNNING = "Running"
    CONTINUE_PENDING = "Continue Pending"
    PAUSE_PENDING = "Pause Pending"
    PAUSED = "Paused"
    UNKNOWN = "Unknown"


class TelemetryTier(str, Enum):
    """Уровни детальности сбора телеметрии."""
    MINIMAL = "minimal"
    STANDARD = "standard"
    EXPANDED = "expanded"
    FORENSIC = "forensic"


class AccessType(str, Enum):
    """Типы доступа к объектам."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ALL = "all"


class SamplingMode(str, Enum):
    """Режимы дискретизации телеметрии."""
    PERIODIC = "periodic"
    ADAPTIVE = "adaptive"
    EVENT_DRIVEN = "event_driven"
    ON_DEMAND = "on_demand"


class ArtifactType(str, Enum):
    """Типы артефактов Windows и кодовой базы."""
    WINDOWS_EVENT = "windows_event"
    WINDOWS_ERROR = "windows_error"
    REGISTRY_KEY = "registry_key"
    PROCESS = "process"
    SERVICE = "service"
    DRIVER = "driver"
    ETW_EVENT = "etw_event"
    CODE_SYMBOL = "code_symbol"
    INCIDENT = "incident"
    SYMPTOM = "symptom"


class KnowledgeSource(str, Enum):
    """Источники происхождения знаний в базе WikiLLM."""
    OBSERVED = "observed"
    DOCUMENTED = "documented"
    INFERRED = "inferred"
    LLM_GENERATED = "llm_generated"


class LookupLevel(str, Enum):
    """Уровни многоступенчатого конвейера поиска."""
    EXACT = "exact"
    FINGERPRINT = "fingerprint"
    SEMANTIC = "semantic"
    GEMINI = "gemini"
    UNKNOWN = "unknown"
