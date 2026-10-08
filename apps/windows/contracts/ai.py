# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Contracts - AI & Knowledge Models
# =============================================================================
# Description:
#   Zero-dependency DTO-контракты для контура ИИ, WikiLLM и интеллектуальной диагностики.
#
# Usage Examples:
#   Python API:
#     from apps.windows.contracts.ai import KnowledgeEntity, ResolutionResult
#
# File: ai.py
# Project: ai-breadboard
# Package: apps.windows.contracts
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 09:35:00
# =============================================================================

from __future__ import annotations
"""Контракты и модели базы знаний WikiLLM, артефактов и гипотез ИИ-диагноста."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from apps.windows.contracts.enums import (
    ArtifactType,
    KnowledgeSource,
    LookupLevel,
    RiskLevel,
)


def utc_now_iso() -> str:
    """Возвращает текущее время UTC в формате ISO 8601."""
    return datetime.now(timezone.utc).isoformat()


class ResolutionAction(BaseModel):
    """Диагностическое действие или инструкция по устранению проблемы."""
    title: str = Field(description="Заголовок действия")
    description: str = Field(default="", description="Описание шага")
    command: Optional[str] = Field(default=None, description="Команда CLI/PowerShell для выполнения")
    risk_level: str = Field(default="safe", description="Уровень риска")
    is_automated: bool = Field(default=False, description="Возможность автоматического запуска")


class Claim(BaseModel):
    """Утверждение о сущности с фиксацией источника и верификации."""
    claim_id: Optional[str] = Field(default=None, description="Уникальный ID утверждения")
    statement: str = Field(description="Текст утверждения")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Уверенность в утверждении")
    source: KnowledgeSource = Field(default=KnowledgeSource.OBSERVED, description="Источник факта")
    verified: bool = Field(default=False, description="Проверен ли факт документацией/наблюдением")
    created_at: str = Field(default_factory=utc_now_iso, description="Время создания записи")


class Evidence(BaseModel):
    """Свидетельство или наблюдаемый факт, подтверждающий знание."""
    evidence_id: Optional[str] = Field(default=None, description="Идентификатор свидетельства")
    description: str = Field(description="Описание наблюдаемого свидетельства")
    telemetry_metric: Optional[str] = Field(default=None, description="Связанная телеметрическая метрика")
    sample_value: Optional[str] = Field(default=None, description="Значение или вырезка лога")
    observed_at: str = Field(default_factory=utc_now_iso, description="Время фиксации")


class KnowledgeEntity(BaseModel):
    """Каноническая сущность в базе знаний WikiLLM."""
    entity_id: Optional[str] = Field(default=None, description="Уникальный ID сущности (UUID)")
    canonical_key: str = Field(description="Уникальный ключ сущности")
    artifact_type: ArtifactType = Field(description="Тип артефакта")
    title: str = Field(description="Человекочитаемый заголовок сущности")
    description: str = Field(default="", description="Детальное описание сущности")
    tags: List[str] = Field(default_factory=list, description="Теги для семантического поиска")
    claims: List[Claim] = Field(default_factory=list, description="Список фактов и утверждений")
    evidence: List[Evidence] = Field(default_factory=list, description="Список подтверждающих свидетельств")
    actions: List[ResolutionAction] = Field(default_factory=list, description="Рекомендуемые действия")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Дополнительные атрибуты")
    created_at: str = Field(default_factory=utc_now_iso, description="Время создания записи")
    updated_at: str = Field(default_factory=utc_now_iso, description="Время последнего обновления")


class ResolutionResult(BaseModel):
    """Результат разрешения запроса к WikiLLM на одном из уровней конвейера."""
    lookup_level: LookupLevel = Field(description="Уровень конвейера, на котором найден ответ")
    success: bool = Field(description="Успешно ли найдена сущность")
    entity: Optional[KnowledgeEntity] = Field(default=None, description="Найденная каноническая сущность")
    confidence: float = Field(default=0.0, description="Уверенность в релевантности результата")
    explanation: str = Field(default="", description="Объяснение происхождения ответа")
    latency_ms: float = Field(default=0.0, description="Время разрешения запроса в миллисекундах")


class ArtifactInput(BaseModel):
    """Входные данные для извлечения знаний из артефакта."""
    raw_text: str = Field(description="Сырой текст артефакта, лога, трассировки или кода")
    artifact_type_hint: Optional[ArtifactType] = Field(default=None, description="Подсказка о типе")
    context: Dict[str, Any] = Field(default_factory=dict, description="Контекст генерации артефакта")


class AnomalyHypothesis(BaseModel):
    """Гипотеза ИИ-диагноста о корневой причине аномалии."""
    hypothesis_id: str
    component: str
    root_cause: str
    confidence: float
    risk: RiskLevel = RiskLevel.MEDIUM
    reasoning: str = ""
    suggested_actions: List[str] = Field(default_factory=list)


class AiDiagnosticReport(BaseModel):
    """Полный отчет ИИ-диагноста по телеметрии и аудиту."""
    timestamp: str = Field(default_factory=utc_now_iso)
    health_score: int = 100
    status: str = "Healthy"
    summary_ru: str = ""
    hypotheses: List[AnomalyHypothesis] = Field(default_factory=list)
    remediation_recommendations: List[ResolutionAction] = Field(default_factory=list)
