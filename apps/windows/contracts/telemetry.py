# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Contracts - Telemetry Models
# =============================================================================
# Description:
#   Zero-dependency DTO-контракты для процессов, потоков, снимков системы и инцидентов.
#
# Usage Examples:
#   Python API:
#     from apps.windows.contracts.telemetry import ProcessInfo, SystemSnapshot
#
# File: telemetry.py
# Project: ai-breadboard
# Package: apps.windows.contracts
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 12:20:00
# =============================================================================

from __future__ import annotations
"""Контракты телеметрии процессов, дескрипторов, потоков, системных срезов и инцидентов."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from apps.windows.contracts.enums import (
    ProcessState,
    ThreadState,
    ServiceState,
    RiskLevel,
    TelemetryTier,
)


@dataclass
class MemoryInfo:
    """Структура использования оперативной памяти процессом."""
    working_set: int = 0
    working_set_peak: int = 0
    private_bytes: int = 0
    pagefile_usage: int = 0
    pagefile_peak: int = 0
    paged_pool: int = 0
    nonpaged_pool: int = 0
    page_faults: int = 0
    hard_page_faults: int = 0

    @property
    def working_set_mb(self) -> float:
        return self.working_set / (1024 * 1024)

    @property
    def private_bytes_mb(self) -> float:
        return self.private_bytes / (1024 * 1024)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "working_set": self.working_set,
            "working_set_peak": self.working_set_peak,
            "private_bytes": self.private_bytes,
            "working_set_mb": self.working_set_mb,
            "private_bytes_mb": self.private_bytes_mb,
            "pagefile_usage": self.pagefile_usage,
            "paged_pool": self.paged_pool,
            "nonpaged_pool": self.nonpaged_pool,
            "page_faults": self.page_faults,
        }


@dataclass
class ThreadInfo:
    """Информация об отдельном потоке выполнения."""
    tid: int
    pid: int
    state: ThreadState = ThreadState.RUNNING
    wait_reason: str = "Unknown"
    base_priority: int = 0
    current_priority: int = 0
    cpu_time: int = 0
    kernel_time: int = 0
    user_time: int = 0
    start_time: Optional[datetime] = None
    start_address: int = 0
    suspended: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tid": self.tid,
            "pid": self.pid,
            "state": self.state.name if hasattr(self.state, "name") else str(self.state),
            "wait_reason": self.wait_reason,
            "base_priority": self.base_priority,
            "cpu_time_ms": self.cpu_time // 10000,
        }


@dataclass
class ModuleInfo:
    """Информация о загруженной DLL/модуле."""
    name: str
    path: str
    base_address: int = 0
    size: int = 0
    entry_point: int = 0
    version: str = ""
    company: str = ""
    description: str = ""
    product: str = ""
    is_signed: bool = False
    signer: str = ""
    load_time: Optional[datetime] = None
    architecture: str = ""

    @property
    def size_mb(self) -> float:
        return self.size / (1024 * 1024)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "version": self.version,
            "company": self.company,
            "signed": self.is_signed,
            "signer": self.signer,
            "size_mb": self.size_mb,
        }


@dataclass
class HandleInfo:
    """Информация о дескрипторе (Handle) операционной системы."""
    handle_value: int
    pid: int
    object_type: str
    object_name: str
    access_mask: int = 0
    attributes: int = 0
    inheritance: bool = False
    duplicated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "handle": hex(self.handle_value),
            "type": self.object_type,
            "name": self.object_name,
            "access": hex(self.access_mask),
        }


@dataclass
class ProcessInfo:
    """Комплексная информация о процессе."""
    pid: int
    ppid: int
    name: str
    executable: Optional[str] = None
    command_line: str = ""
    working_directory: str = ""
    username: str = ""
    user_sid: str = ""
    session_id: int = 0
    cpu_percent: float = 0.0
    cpu_time: int = 0
    kernel_time: int = 0
    user_time: int = 0
    state: ProcessState = ProcessState.RUNNING
    priority_class: int = 0
    base_priority: int = 0
    handle_count: int = 0
    thread_count: int = 0
    memory: MemoryInfo = field(default_factory=MemoryInfo)
    threads: List[ThreadInfo] = field(default_factory=list)
    modules: List[ModuleInfo] = field(default_factory=list)
    handles: List[HandleInfo] = field(default_factory=list)
    is_elevated: bool = False
    is_sandboxed: bool = False
    integrity_level: str = "Medium"
    creation_time: Optional[datetime] = None
    risk_score: float = 0.0
    anomalies: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pid": self.pid,
            "ppid": self.ppid,
            "name": self.name,
            "executable": self.executable,
            "command_line": self.command_line,
            "username": self.username,
            "cpu_percent": self.cpu_percent,
            "memory": self.memory.to_dict() if hasattr(self.memory, "to_dict") else self.memory,
            "handle_count": self.handle_count,
            "thread_count": self.thread_count,
            "is_elevated": self.is_elevated,
            "integrity_level": self.integrity_level,
            "risk_score": self.risk_score,
            "anomalies": self.anomalies,
        }


@dataclass
class ContractSystemSnapshot:
    """Комплексный снимок состояния операционной системы."""
    timestamp: datetime = field(default_factory=datetime.now)
    tier: TelemetryTier = TelemetryTier.STANDARD
    cpu_percent: float = 0.0
    memory_used_gb: float = 0.0
    memory_total_gb: float = 0.0
    active_processes: int = 0
    total_handles: int = 0
    processes: List[ProcessInfo] = field(default_factory=list)
    incidents: List[ContractTelemetryIncident] = field(default_factory=list)
    sensors: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat() if hasattr(self.timestamp, "isoformat") else str(self.timestamp),
            "tier": self.tier.value if hasattr(self.tier, "value") else str(self.tier),
            "cpu_percent": self.cpu_percent,
            "memory_used_gb": self.memory_used_gb,
            "memory_total_gb": self.memory_total_gb,
            "active_processes": self.active_processes,
            "total_handles": self.total_handles,
            "processes_count": len(self.processes),
            "incidents_count": len(self.incidents),
            "sensors": self.sensors,
        }


@dataclass
class ContractTelemetryIncident:
    """Инцидент или критическая аномалия телеметрии."""
    incident_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    source_domain: str = ""
    severity: RiskLevel = RiskLevel.MEDIUM
    title: str = ""
    description: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)
    remediation_suggested: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "timestamp": self.timestamp.isoformat() if hasattr(self.timestamp, "isoformat") else str(self.timestamp),
            "source_domain": self.source_domain,
            "severity": self.severity.value if hasattr(self.severity, "value") else str(self.severity),
            "title": self.title,
            "description": self.description,
            "metrics": self.metrics,
            "remediation_suggested": self.remediation_suggested,
        }


class ContractProcessMetrics(BaseModel):
    """Срез метрик отдельного процесса."""
    pid: int
    name: str
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    io_read_kb: float = 0.0
    io_write_kb: float = 0.0
    handle_count: int = 0
    thread_count: int = 0


class ContractProcessTokenInfo(BaseModel):
    """Атрибуты маркера безопасности процесса (Security Token)."""
    pid: int
    username: str = ""
    user_sid: str = ""
    elevation_type: str = "Default"
    is_elevated: bool = False
    integrity_level: str = "Medium"
    privileges: List[str] = Field(default_factory=list)


class ProcessNetworkConnection(BaseModel):
    """Сетевое соединение процесса (IPHLPAPI / Netstat)."""
    pid: int
    protocol: str = "TCP"
    local_address: str = ""
    local_port: int = 0
    remote_address: str = ""
    remote_port: int = 0
    state: str = "ESTABLISHED"


class ProcessIoCounters(BaseModel):
    """Счетчики ввода-вывода процесса."""
    pid: int
    read_operation_count: int = 0
    write_operation_count: int = 0
    other_operation_count: int = 0
    read_transfer_bytes: int = 0
    write_transfer_bytes: int = 0
    other_transfer_bytes: int = 0


class ProcessThreadDetail(BaseModel):
    """Детальная информация о потоке процесса."""
    tid: int
    pid: int
    start_address: str = ""
    state: str = "Running"
    priority: int = 8
    kernel_time_ms: float = 0.0
    user_time_ms: float = 0.0


class RebootIncident(BaseModel):
    """Инцидент перезагрузки или аварийного выключения."""
    timestamp: str
    reboot_type: str = "Unexpected"
    event_id: int = 41
    bugcheck_code: Optional[str] = None
    bugcheck_parameter1: Optional[str] = None
    bugcheck_parameter2: Optional[str] = None
    cause_analysis: str = ""


class CrashDumpArtifact(BaseModel):
    """Сведения об аварийном дампе памяти (Memory Dump)."""
    dump_path: str
    dump_size_bytes: int
    creation_time: str
    stop_code: str = ""
    faulting_driver: Optional[str] = None
