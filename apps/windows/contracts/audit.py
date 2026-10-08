# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Contracts - Audit Models
# =============================================================================
# Description:
#   Zero-dependency DTO-модели для аудита, диагностики и безопасного выполнения.
#
# Usage Examples:
#   Python API:
#     from apps.windows.contracts.audit import AuditFinding, DomainAuditResult
#
# File: audit.py
# Project: ai-breadboard
# Package: apps.windows.contracts
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 09:35:00
# =============================================================================

from __future__ import annotations
"""Контракты и модели данных аудита, поиска неисправностей и планов восстановления."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from apps.windows.contracts.enums import (
    RiskLevel,
    ActionType,
    PrivilegeLevel,
    ExecutionMethod,
    HttpMethod,
    CapabilityCategory,
)


@dataclass
class RemediationAction:
    """Структура предлагаемого или выполняемого действия."""
    action_id: str
    action_type: ActionType
    title: str
    description: str
    target: str
    risk: RiskLevel
    releasable_bytes: int = 0
    dry_run_command: str = ""
    execution_command: str = ""
    requires_reboot: bool = False
    requires_elevation: bool = True
    executed: bool = False
    success: bool = False
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь."""
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value if hasattr(self.action_type, "value") else str(self.action_type),
            "title": self.title,
            "description": self.description,
            "target": self.target,
            "risk": self.risk.value if hasattr(self.risk, "value") else str(self.risk),
            "releasable_bytes": self.releasable_bytes,
            "dry_run_command": self.dry_run_command,
            "execution_command": self.execution_command,
            "requires_reboot": self.requires_reboot,
            "requires_elevation": self.requires_elevation,
            "executed": self.executed,
            "success": self.success,
            "error_message": self.error_message,
        }


@dataclass
class AuditFinding:
    """Обнаруженная аномалия или факт аудита."""
    domain: str
    category: str
    title: str
    description: str
    severity: RiskLevel
    evidence: Dict[str, Any] = field(default_factory=dict)
    actions: List[RemediationAction] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь."""
        return {
            "domain": self.domain,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value if hasattr(self.severity, "value") else str(self.severity),
            "evidence": self.evidence,
            "actions": [a.to_dict() if hasattr(a, "to_dict") else a for a in self.actions],
        }


@dataclass
class DomainAuditResult:
    """Результат аудита отдельного домена."""
    domain_name: str
    title_ru: str
    status: str
    findings: List[AuditFinding] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    scan_duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь."""
        return {
            "domain_name": self.domain_name,
            "title_ru": self.title_ru,
            "status": self.status,
            "findings": [f.to_dict() if hasattr(f, "to_dict") else f for f in self.findings],
            "metrics": self.metrics,
            "scan_duration_ms": self.scan_duration_ms,
        }


@dataclass
class HealthScoreSummary:
    """Сводка индекса здоровья системы (Health Score)."""
    score: int
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0
    total_findings: int = 0
    status_label: str = "Excellent"

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь."""
        return {
            "score": self.score,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "info_count": self.info_count,
            "total_findings": self.total_findings,
            "status_label": self.status_label,
        }


@dataclass
class FullAuditReport:
    """Полный отчёт аудита по всем доменам."""
    timestamp: datetime = field(default_factory=datetime.now)
    mode: str = "full"
    health_score: HealthScoreSummary = field(default_factory=lambda: HealthScoreSummary(score=100))
    domains: Dict[str, DomainAuditResult] = field(default_factory=dict)
    ai_summary: str = ""
    ai_hypotheses: List[Dict[str, Any]] = field(default_factory=list)
    proposed_actions: List[RemediationAction] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь."""
        return {
            "timestamp": self.timestamp.isoformat() if hasattr(self.timestamp, "isoformat") else str(self.timestamp),
            "mode": self.mode,
            "health_score": self.health_score.to_dict() if hasattr(self.health_score, "to_dict") else self.health_score,
            "domains": {k: (v.to_dict() if hasattr(v, "to_dict") else v) for k, v in self.domains.items()},
            "ai_summary": self.ai_summary,
            "ai_hypotheses": self.ai_hypotheses,
            "proposed_actions": [a.to_dict() if hasattr(a, "to_dict") else a for a in self.proposed_actions],
        }


@dataclass
class InvestigationReport:
    """Отчет о детальном расследовании неисправности/аномалии."""
    investigation_id: str = ""
    target_component: str = ""
    status: str = "completed"
    findings: List[AuditFinding] = field(default_factory=list)
    evidence_bundle: Dict[str, Any] = field(default_factory=dict)
    remediation_plan: List[RemediationAction] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    symptom: str = ""
    confidence_score: float = 0.0
    probable_root_cause: str = ""
    evidence_chain: List[Dict[str, Any]] = field(default_factory=list)
    timeline: List[Dict[str, Any]] = field(default_factory=list)
    ai_explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь."""
        return {
            "investigation_id": self.investigation_id,
            "target_component": self.target_component,
            "status": self.status,
            "findings": [f.to_dict() if hasattr(f, "to_dict") else f for f in self.findings],
            "evidence_bundle": self.evidence_bundle,
            "remediation_plan": [r.to_dict() if hasattr(r, "to_dict") else r for r in self.remediation_plan],
            "created_at": self.created_at.isoformat() if hasattr(self.created_at, "isoformat") else str(self.created_at),
            "symptom": self.symptom,
            "confidence_score": self.confidence_score,
            "probable_root_cause": self.probable_root_cause,
            "evidence_chain": self.evidence_chain,
            "timeline": self.timeline,
            "ai_explanation": self.ai_explanation,
        }



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
    cli_template: str = ""
    native_api_equivalent: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    is_safe: bool = True
    safe_reason: str = ""
    safety_mechanisms: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Сериализация операции в словарь."""
        res = asdict(self)
        res["category"] = self.category.value if hasattr(self.category, "value") else str(self.category)
        res["risk_level"] = self.risk_level.value if hasattr(self.risk_level, "value") else str(self.risk_level)
        res["required_privilege"] = self.required_privilege.value if hasattr(self.required_privilege, "value") else str(self.required_privilege)
        res["execution_method"] = self.execution_method.value if hasattr(self.execution_method, "value") else str(self.execution_method)
        res["http_method"] = self.http_method.value if hasattr(self.http_method, "value") else str(self.http_method)
        return res


class ExecutionRequest(BaseModel):
    """Схема запроса на исполнение атомарной операции."""
    model_config = {"extra": "allow"}

    operation_id: str = Field(..., description="ID атомарной операции")
    dry_run: bool = Field(True, description="Режим имитации (dry-run) без реальных изменений")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Параметры операции")
    user_confirmed: bool = Field(False, description="Подтверждение пользователя для рискованных действий")
    confirmed_by_user: bool = Field(False, description="Алиас для user_confirmed")

    @property
    def is_confirmed(self) -> bool:
        """Проверка подтверждения пользователем."""
        return self.user_confirmed or self.confirmed_by_user



class ExecutionResult(BaseModel):
    """Результат выполнения операции."""
    model_config = {"extra": "allow"}

    operation_id: str
    dry_run: bool = True
    status: str
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    simulated_changes: List[str] = Field(default_factory=list)
    execution_time_ms: float = 0.0
    error: Optional[str] = None
    is_dry_run: Optional[bool] = None
    utility: Optional[str] = None
    risk_level: Optional[str] = None
    required_privilege: Optional[str] = None
    command_executed: Optional[str] = None
    message: Optional[str] = None


# Алиасы совместимости
AtomicOperationExecutionRequest = ExecutionRequest
AtomicOperationExecutionResult = ExecutionResult


