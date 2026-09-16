# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Health & Audit Data Models
# =============================================================================
# Description:
#   Структурированные модели данных для 15 доменов аудита Windows,
#   оценки рисков (SafeOps), классификации аномалий и планов исправления.
#
# Examples:
#   >>> from apps.windows.core.models import HealthScoreSummary, RiskLevel
#   >>> score = HealthScoreSummary(score=87, critical_count=0, high_count=2)
#
# File: models.py
# Project: ai-breadboard
# Package: apps.windows.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модели данных аудита, диагностики и безопасного выполнения для Windows."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class RiskLevel(str, Enum):
    """Уровни риска для операций и найденных проблем."""
    SAFE = "safe"              # Зеленый: полностью безопасно (кэши, temp)
    CAUTION = "caution"        # Желтый: требует подтверждения пользователя (дубликаты, автозагрузка)
    CRITICAL = "critical"      # Красный: критическое системное действие (службы, драйверы, реестр)
    INFO = "info"              # Информационный уровень


class ActionType(str, Enum):
    """Типы корректирующих действий."""
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
            "action_type": self.action_type.value,
            "title": self.title,
            "description": self.description,
            "target": self.target,
            "risk": self.risk.value,
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
            "severity": self.severity.value,
            "evidence": self.evidence,
            "actions": [a.to_dict() for a in self.actions],
        }


@dataclass
class DomainAuditResult:
    """Результат аудита отдельного домена."""
    domain_name: str
    title_ru: str
    status: str  # "ok", "warning", "critical", "error"
    findings: List[AuditFinding] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    scan_duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь."""
        return {
            "domain_name": self.domain_name,
            "title_ru": self.title_ru,
            "status": self.status,
            "findings": [f.to_dict() for f in self.findings],
            "metrics": self.metrics,
            "scan_duration_ms": self.scan_duration_ms,
        }


@dataclass
class HealthScoreSummary:
    """Сводка индекса здоровья системы (Health Score)."""
    score: int  # 0..100
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0
    total_findings: int = 0
    status_label: str = "Excellent"  # "Critical", "Degraded", "Fair", "Good", "Excellent"

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
            "timestamp": self.timestamp.isoformat(),
            "mode": self.mode,
            "health_score": self.health_score.to_dict(),
            "domains": {k: v.to_dict() for k, v in self.domains.items()},
            "ai_summary": self.ai_summary,
            "ai_hypotheses": self.ai_hypotheses,
            "proposed_actions": [a.to_dict() for a in self.proposed_actions],
        }


@dataclass
class InvestigationReport:
    """Отчёт расследования первопричины по симптому."""
    symptom: str
    confidence_score: float  # 0.0 .. 1.0
    probable_root_cause: str
    evidence_chain: List[Dict[str, Any]] = field(default_factory=list)
    timeline: List[Dict[str, Any]] = field(default_factory=list)
    remediation_plan: List[RemediationAction] = field(default_factory=list)
    ai_explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь."""
        return {
            "symptom": self.symptom,
            "confidence_score": self.confidence_score,
            "probable_root_cause": self.probable_root_cause,
            "evidence_chain": self.evidence_chain,
            "timeline": self.timeline,
            "remediation_plan": [a.to_dict() for a in self.remediation_plan],
            "ai_explanation": self.ai_explanation,
        }
