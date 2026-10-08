# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Wikillm - Router
# =============================================================================
# Description:
#   REST API эндпоинты для разрешения артефактов, поиска по базе знаний WikiLLM,
#
# Usage Examples:
#   Python API:
#     from apps.windows.wikillm.router import ResolveRequest
#
#     service = ResolveRequest()
#
# File: router.py
# Project: ai-breadboard
# Package: apps.windows.wikillm
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 09:50:00
# =============================================================================

from __future__ import annotations
"""REST API эндпоинты для разрешения артефактов, поиска по базе знаний WikiLLM,"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field
from logger import logger
from .code_indexer import CodeKnowledgeIndexer
from .engine import WikiLLMEngine
from .extractor import ArtifactExtractor
from .models import (
    ArtifactInput,
    ArtifactType,
    KnowledgeEntity,
    LookupLevel,
    ObservationRecord,
    ResolutionResult,
)


router = APIRouter(prefix="/api/windows/wikillm", tags=["windows-wikillm"])
_engine_instance: Optional[WikiLLMEngine] = None


def get_engine() -> WikiLLMEngine:
    """Возвращает или лениво инициализирует синглтон WikiLLMEngine."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = WikiLLMEngine()
    return _engine_instance


def init_router(engine: Optional[WikiLLMEngine] = None) -> APIRouter:
    """Инициализирует роутер с внедрением экземпляра движка.

    Args:
        engine: Пользовательский экземпляр WikiLLMEngine.

    Returns:
        Сконфигурированный APIRouter.
    """
    global _engine_instance
    if engine is not None:
        _engine_instance = engine
    return router


class ResolveRequest(BaseModel):
    """Схема запроса на разрешение артефакта."""

    raw_query: Optional[str] = Field(default=None, description="Строка ошибки или симптом")
    artifact: Optional[ArtifactInput] = Field(default=None, description="Типизированный объект артефакта")
    sync_gemini: bool = Field(default=True, description="Разрешать ли через Gemini синхронно")
    record_observation: bool = Field(default=True, description="Фиксировать ли наблюдение")


class CodeIngestRequest(BaseModel):
    """Схема запроса на индексацию кодовой базы."""

    target_path: str = Field(default="apps/windows", description="Директория или файл для индексации")


class ObserveRequest(BaseModel):
    """Схема фиксации наблюдения артефакта."""

    canonical_key: str = Field(description="Канонический ключ артефакта")
    co_occurring_keys: List[str] = Field(default_factory=list, description="Сопутствующие ключи")


@router.post("/resolve", response_model=ResolutionResult)
async def resolve_artifact(req: ResolveRequest) -> ResolutionResult:
    """Разрешает артефакт по 4-уровневому конвейеру (Exact -> Fingerprint -> Semantic -> Gemini)."""
    engine = get_engine()

    if req.artifact:
        art = req.artifact
    elif req.raw_query:
        extracted = ArtifactExtractor.from_raw_text(req.raw_query)
        art = extracted[0] if extracted else ArtifactInput(raw_query=req.raw_query)
    else:
        raise HTTPException(status_code=400, detail="Необходимо передать raw_query или artifact")

    res = await engine.resolve(
        art,
        sync_gemini=req.sync_gemini,
        record_observation=req.record_observation,
    )
    return res


@router.get("/entities/{canonical_key:path}", response_model=KnowledgeEntity)
async def get_entity_by_key(canonical_key: str) -> KnowledgeEntity:
    """Возвращает подробную информацию о сущности по её каноническому ключу."""
    engine = get_engine()
    entity = engine.storage.get_entity(canonical_key)
    if not entity:
        raise HTTPException(status_code=404, detail=f"Сущность не найдена: {canonical_key}")
    return entity


@router.get("/entities", response_model=List[KnowledgeEntity])
async def list_entities(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    type: Optional[str] = Query(default=None, description="Фильтр по типу сущности"),
) -> List[KnowledgeEntity]:
    """Возвращает постраничный список сущностей базы знаний."""
    engine = get_engine()
    return engine.storage.list_entities(limit=limit, offset=offset, entity_type=type)


@router.get("/search", response_model=List[KnowledgeEntity])
async def search_knowledge(
    q: str = Query(..., min_length=2, description="Поисковая строка"),
    limit: int = Query(default=10, ge=1, le=50),
) -> List[KnowledgeEntity]:
    """Выполняет полнотекстовый поиск FTS5 по базе знаний WikiLLM."""
    engine = get_engine()
    return engine.storage.search_fts(q, limit=limit)


@router.get("/observations/{canonical_key:path}", response_model=ObservationRecord)
async def get_observations(canonical_key: str) -> ObservationRecord:
    """Возвращает статистику наблюдений артефакта на локальной машине."""
    engine = get_engine()
    obs = engine.storage.get_observation(canonical_key)
    if not obs:
        raise HTTPException(status_code=404, detail=f"Наблюдений для {canonical_key} не найдено")
    return obs


@router.post("/observe", response_model=ObservationRecord)
async def record_observation_endpoint(req: ObserveRequest) -> ObservationRecord:
    """Вручную фиксирует наблюдение артефакта и совместные появления."""
    engine = get_engine()
    return engine.storage.record_observation(req.canonical_key, req.co_occurring_keys)


@router.post("/code/ingest")
async def ingest_code(req: CodeIngestRequest) -> Dict[str, Any]:
    """Запускает индексацию AST структуры исходного кода кодовой базы."""
    engine = get_engine()
    indexer = CodeKnowledgeIndexer(engine.storage)
    count = indexer.index_directory(req.target_path)
    return {
        "status": "success",
        "target_path": req.target_path,
        "indexed_symbols_count": count,
    }


@router.get("/stats")
async def get_system_stats() -> Dict[str, Any]:
    """Возвращает метрики эффективности, статистику кэш-хитов и состояние хранилища."""
    engine = get_engine()
    return engine.get_metrics()


class ApproveKnowledgeRequest(BaseModel):
    """Схема одобрения и фиксации знания в базе знаний WikiLLM."""

    canonical_key: Optional[str] = Field(default=None, description="Канонический ключ сущности")
    table_type: str = Field(default="generic", description="Тип таблицы / артефакта")
    title: str = Field(description="Заголовок или имя сущности")
    subtitle: Optional[str] = Field(default="", description="Подзаголовок / разработчик")
    summary: str = Field(description="Краткое описание / назначение")
    category: Optional[str] = Field(default="system", description="Категория")
    severity: Optional[str] = Field(default="info", description="Критичность (info/warning/error/critical)")
    security_verdict: Optional[str] = Field(default="", description="Оценка безопасности")
    performance_impact: Optional[str] = Field(default="", description="Влияние на ресурсы")
    recommendation: Optional[str] = Field(default="", description="Рекомендация")
    action_steps: List[str] = Field(default_factory=list, description="Пошаговые действия")
    possible_causes: List[str] = Field(default_factory=list, description="Возможные причины")
    tags: List[str] = Field(default_factory=list, description="Теги для поиска")
    model_name: Optional[str] = Field(default=None, description="Модель, сгенерировавшая исходный ответ")


@router.post("/approve", response_model=Dict[str, Any])
async def approve_knowledge(req: ApproveKnowledgeRequest) -> Dict[str, Any]:
    """Фиксирует и одобряет проверенное пользователем знание в локальной базе WikiLLM."""
    engine = get_engine()

    canonical_key = req.canonical_key
    if not canonical_key or canonical_key == "unknown:unspecified":
        from .normalizer import CanonicalKeyNormalizer
        canonical_key = CanonicalKeyNormalizer.compute_key_from_parts(
            table_type=req.table_type,
            title=req.title,
            subtitle=req.subtitle or "",
        )

    from .models import (
        Claim,
        DiagnosticKnowledge,
        KnowledgeSource,
        ResolutionAction,
    )

    # Определяем тип артефакта
    type_map = {
        "process": ArtifactType.PROCESS,
        "service": ArtifactType.SERVICE,
        "driver": ArtifactType.DRIVER,
        "registry": ArtifactType.REGISTRY_KEY,
        "software": ArtifactType.SOFTWARE,
        "task": ArtifactType.TASK,
        "network": ArtifactType.NETWORK,
        "website": ArtifactType.WEBSITE,
        "disk": ArtifactType.DISK,
        "user": ArtifactType.USER,
        "windows_event": ArtifactType.WINDOWS_EVENT,
        "windows_error": ArtifactType.WINDOWS_ERROR,
    }
    entity_type = type_map.get(req.table_type.lower(), ArtifactType.GENERIC)

    # Формируем диагностические шаги
    remediation_steps = [
        ResolutionAction(title=step, description="", risk_level="safe", is_automated=False)
        for step in req.action_steps
    ]

    diag_info = DiagnosticKnowledge(
        symptoms=[req.security_verdict] if req.security_verdict else [],
        possible_causes=req.possible_causes,
        remediation_steps=remediation_steps,
        related_components=[req.subtitle] if req.subtitle else [],
    )

    claims = [
        Claim(
            statement=req.summary,
            confidence=1.0,
            source=KnowledgeSource.DOCUMENTED,
            verified=True,
        )
    ]
    if req.recommendation:
        claims.append(
            Claim(
                statement=f"Рекомендация: {req.recommendation}",
                confidence=1.0,
                source=KnowledgeSource.DOCUMENTED,
                verified=True,
            )
        )

    entity = KnowledgeEntity(
        canonical_key=canonical_key,
        entity_type=entity_type,
        name=req.title,
        summary=req.summary,
        category=req.category or "system",
        severity=req.severity or "info",
        confidence=1.0,
        provenance_source=KnowledgeSource.DOCUMENTED,
        provenance_model=req.model_name,
        diagnostic_info=diag_info,
        claims=claims,
        tags=list(set(req.tags + [req.table_type, "verified", "user_approved"])),
    )

    # Сохраняем сущность и обновляем счетчик наблюдений
    engine.storage.save_entity(entity)
    engine.storage.record_observation(canonical_key)

    logger.info(f"[WikiLLM] Знание для '{canonical_key}' успешно одобрено пользователем и сохранено.")
    return {
        "success": True,
        "canonical_key": canonical_key,
        "message": f"Знание '{canonical_key}' верифицировано и сохранено в локальной базе WikiLLM.",
        "entity": entity.model_dump(),
    }
