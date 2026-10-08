# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Wikillm - Models
# =============================================================================
# Description:
#   Модели данных, перечисления и Pydantic-схемы для Progressive Knowledge Base WikiLLM.
#
# Usage Examples:
#   Python API:
#     from apps.windows.wikillm.models import ArtifactType
#
#     service = ArtifactType()
#
# File: models.py
# Project: ai-breadboard
# Package: apps.windows.wikillm
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 09:50:00
# =============================================================================

from __future__ import annotations
"""Модели данных, перечисления и Pydantic-схемы для Progressive Knowledge Base WikiLLM."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    """Возвращает текущее время UTC в формате ISO 8601."""
    return datetime.now(timezone.utc).isoformat()


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
    SOFTWARE = "software"
    TASK = "task"
    NETWORK = "network"
    WEBSITE = "website"
    DISK = "disk"
    USER = "user"
    GENERIC = "generic"


class KnowledgeSource(str, Enum):
    """Источники происхождения знаний в базе WikiLLM."""

    OBSERVED = "observed"
    DOCUMENTED = "documented"
    INFERRED = "inferred"
    LLM_GENERATED = "llm_generated"


class LookupLevel(str, Enum):
    """Уровни многоступенчатого конвейера поиска."""

    EXACT = "exact"              # Level 1: точное совпадение по canonical_key
    FINGERPRINT = "fingerprint"  # Level 2: шаблонное совпадение
    SEMANTIC = "semantic"        # Level 3: FTS5 / семантический поиск
    GEMINI = "gemini"            # Level 4: обращение к Gemini LLM
    UNKNOWN = "unknown"          # Не найдено


class ResolutionAction(BaseModel):
    """Диагностическое действие или инструкция по устранению проблемы."""

    title: str = Field(description="Заголовок действия")
    description: str = Field(default="", description="Описание шага")
    command: Optional[str] = Field(default=None, description="Команда CLI/PowerShell для выполнения")
    risk_level: str = Field(default="safe", description="Уровень риска (safe/moderate/high)")
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


class ObservationRecord(BaseModel):
    """Статистика наблюдений сущности на локальной машине."""

    canonical_key: str = Field(description="Канонический ключ сущности")
    total_occurrences: int = Field(default=1, description="Общее число наблюдений")
    first_seen: str = Field(default_factory=utc_now_iso, description="Дата первого обнаружения")
    last_seen: str = Field(default_factory=utc_now_iso, description="Дата последнего обнаружения")
    co_occurrences: Dict[str, int] = Field(
        default_factory=dict,
        description="Совместные появления с другими canonical_key",
    )


class DiagnosticKnowledge(BaseModel):
    """Диагностические знания по ошибке или событию Windows."""

    symptoms: List[str] = Field(default_factory=list, description="Наблюдаемые симптомы")
    possible_causes: List[str] = Field(default_factory=list, description="Возможные причины")
    diagnostic_actions: List[ResolutionAction] = Field(
        default_factory=list,
        description="Диагностические тесты и проверки",
    )
    remediation_steps: List[ResolutionAction] = Field(
        default_factory=list,
        description="Шаги по устранению проблемы",
    )
    related_components: List[str] = Field(
        default_factory=list,
        description="Связанные компоненты, службы или библиотеки",
    )


class CodeKnowledge(BaseModel):
    """Знания о программном коде и модулях."""

    module_path: str = Field(default="", description="Путь к модулю в проекте")
    symbol_name: str = Field(default="", description="Имя функции, класса или метода")
    symbol_type: str = Field(default="function", description="Тип символа (class/function/method/api)")
    docstring: str = Field(default="", description="Документация символа")
    parameters: List[str] = Field(default_factory=list, description="Параметры сигнатуры")
    return_type: Optional[str] = Field(default=None, description="Возвращаемый тип")
    dependencies: List[str] = Field(default_factory=list, description="Импортируемые зависимости")


class KnowledgeEntity(BaseModel):
    """Главная модель сущности базы знаний WikiLLM."""

    canonical_key: str = Field(description="Уникальный канонический ключ (например win32:0x80070490)")
    entity_type: ArtifactType = Field(description="Тип сущности")
    name: str = Field(description="Человекочитаемое имя или идентификатор")
    summary: str = Field(description="Краткая сводка о назначении или значении сущности")
    category: str = Field(default="system", description="Категория (system/security/storage/network/code)")
    severity: str = Field(default="info", description="Критичность (info/warning/error/critical)")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Уверенность в информации")
    provenance_source: KnowledgeSource = Field(
        default=KnowledgeSource.OBSERVED,
        description="Основной источник знания",
    )
    provenance_model: Optional[str] = Field(default=None, description="Модель LLM, создавшая запись")
    diagnostic_info: Optional[DiagnosticKnowledge] = Field(
        default=None,
        description="Диагностические атрибуты",
    )
    code_info: Optional[CodeKnowledge] = Field(
        default=None,
        description="Атрибуты сущности кодовой базы",
    )
    claims: List[Claim] = Field(default_factory=list, description="Список утверждений")
    evidence: List[Evidence] = Field(default_factory=list, description="Список свидетельств")
    tags: List[str] = Field(default_factory=list, description="Теги для быстрого поиска")
    fingerprint: Optional[str] = Field(default=None, description="Структурный отпечаток/шаблон")
    created_at: str = Field(default_factory=utc_now_iso, description="Время создания")
    updated_at: str = Field(default_factory=utc_now_iso, description="Время последнего обновления")


class ArtifactInput(BaseModel):
    """Входной артефакт для разрешения в WikiLLM."""

    type: Optional[ArtifactType] = Field(default=None, description="Тип артефакта")
    raw_query: Optional[str] = Field(default=None, description="Сырая строка запроса/кода ошибки")
    provider: Optional[str] = Field(default=None, description="Windows Event Provider")
    event_id: Optional[int] = Field(default=None, description="Windows Event ID")
    error_code: Optional[str] = Field(default=None, description="Код ошибки (0x8007..., 10016)")
    process_name: Optional[str] = Field(default=None, description="Имя процесса (svchost.exe)")
    service_name: Optional[str] = Field(default=None, description="Имя службы")
    driver_name: Optional[str] = Field(default=None, description="Имя драйвера")
    registry_path: Optional[str] = Field(default=None, description="Путь в реестре Windows")
    message: Optional[str] = Field(default=None, description="Текст сообщения или лога")
    code_symbol: Optional[str] = Field(default=None, description="Символ кода (модуль.класс)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Дополнительные метаданные")


class ResolutionResult(BaseModel):
    """Результат разрешения артефакта через 4-уровневый конвейер WikiLLM."""

    canonical_key: str = Field(description="Канонический ключ артефакта")
    lookup_level: LookupLevel = Field(description="Уровень, на котором найдено знание")
    cached: bool = Field(default=False, description="Было ли знание уже закэшировано в локальной БД")
    entity: Optional[KnowledgeEntity] = Field(default=None, description="Разрешенная сущность базы знаний")
    confidence: float = Field(default=1.0, description="Итоговая уверенность")
    execution_time_ms: float = Field(default=0.0, description="Время обработки запроса в миллисекундах")
    message: str = Field(default="Успешно разрешено", description="Статусное сообщение")
