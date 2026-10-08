# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Contracts - Package Root
# =============================================================================
# Description:
#   Zero-dependency единый реестр контрактов, DTO и перечислений для Windows подсистем.
#
# Usage Examples:
#   Python API:
#     from apps.windows.contracts import RiskLevel, AuditFinding, SystemSnapshot, CpuMetrics
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.contracts
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 12:20:00
# =============================================================================

from __future__ import annotations
"""Единый пакет контрактов (Слой 1) платформы AI-Breadboard Windows."""

from apps.windows.contracts.enums import (
    RiskLevel,
    PrivilegeLevel,
    ExecutionMethod,
    HttpMethod,
    CapabilityCategory,
    CapabilityLevel,
    ActionType,
    ProcessState,
    ThreadState,
    ServiceState,
    TelemetryTier,
    AccessType,
    SamplingMode,
    ArtifactType,
    KnowledgeSource,
    LookupLevel,
)

from apps.windows.contracts.audit import (
    RemediationAction,
    AuditFinding,
    DomainAuditResult,
    HealthScoreSummary,
    FullAuditReport,
    InvestigationReport,
    AtomicOperation,
    ExecutionRequest,
    ExecutionResult,
)

from apps.windows.contracts.hardware import (
    CpuInventoryInfo,
    ContractCpuMetrics,
    CpuTelemetrySample,
    RamModuleInventoryInfo,
    ContractMemoryMetrics,
    RamTelemetrySample,
    GpuInventoryInfo,
    ContractGpuMetrics,
    GpuTelemetrySample,
    NpuMetrics,
    StorageDriveInventoryInfo,
    ContractDiskPartitionMetrics,
    ContractDiskIoMetrics,
    DiskTelemetrySample,
    NetworkAdapterInventoryInfo,
    NetworkTelemetrySample,
    MotherboardInventoryInfo,
    SystemHardwareInventory,
    ContractHardwareSensor,
)

from apps.windows.contracts.telemetry import (
    MemoryInfo,
    ThreadInfo,
    ModuleInfo,
    HandleInfo,
    ProcessInfo,
    ContractSystemSnapshot,
    ContractTelemetryIncident,
    ContractProcessMetrics,
    ContractProcessTokenInfo,
    ProcessNetworkConnection,
    ProcessIoCounters,
    ProcessThreadDetail,
    RebootIncident,
    CrashDumpArtifact,
)

from apps.windows.contracts.ai import (
    ResolutionAction,
    Claim,
    Evidence,
    KnowledgeEntity,
    ResolutionResult,
    ArtifactInput,
    AnomalyHypothesis,
    AiDiagnosticReport,
)

__all__ = [
    # Enums
    "RiskLevel",
    "PrivilegeLevel",
    "ExecutionMethod",
    "HttpMethod",
    "CapabilityCategory",
    "CapabilityLevel",
    "ActionType",
    "ProcessState",
    "ThreadState",
    "ServiceState",
    "TelemetryTier",
    "AccessType",
    "SamplingMode",
    "ArtifactType",
    "KnowledgeSource",
    "LookupLevel",
    # Audit & SafeOps
    "RemediationAction",
    "AuditFinding",
    "DomainAuditResult",
    "HealthScoreSummary",
    "FullAuditReport",
    "InvestigationReport",
    "AtomicOperation",
    "ExecutionRequest",
    "ExecutionResult",
    # Hardware
    "CpuInventoryInfo",
    "ContractCpuMetrics",
    "CpuTelemetrySample",
    "RamModuleInventoryInfo",
    "ContractMemoryMetrics",
    "RamTelemetrySample",
    "GpuInventoryInfo",
    "ContractGpuMetrics",
    "GpuTelemetrySample",
    "NpuMetrics",
    "StorageDriveInventoryInfo",
    "ContractDiskPartitionMetrics",
    "ContractDiskIoMetrics",
    "DiskTelemetrySample",
    "NetworkAdapterInventoryInfo",
    "NetworkTelemetrySample",
    "MotherboardInventoryInfo",
    "SystemHardwareInventory",
    "ContractHardwareSensor",
    # Telemetry
    "MemoryInfo",
    "ThreadInfo",
    "ModuleInfo",
    "HandleInfo",
    "ProcessInfo",
    "ContractSystemSnapshot",
    "ContractTelemetryIncident",
    "ContractProcessMetrics",
    "ContractProcessTokenInfo",
    "ProcessNetworkConnection",
    "ProcessIoCounters",
    "ProcessThreadDetail",
    "RebootIncident",
    "CrashDumpArtifact",
    # AI & Knowledge
    "ResolutionAction",
    "Claim",
    "Evidence",
    "KnowledgeEntity",
    "ResolutionResult",
    "ArtifactInput",
    "AnomalyHypothesis",
    "AiDiagnosticReport",
]
