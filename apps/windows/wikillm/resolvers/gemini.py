# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Wikillm Resolvers - Gemini
# =============================================================================
# Description:
#   Интеллектуальный генератор и структуризатор знаний на базе Google Gemini.
#
# Usage Examples:
#   Python API:
#     from apps.windows.wikillm.resolvers.gemini import GeminiKnowledgeResolver
#
#     service = GeminiKnowledgeResolver()
#
# File: gemini.py
# Project: ai-breadboard
# Package: apps.windows.wikillm.resolvers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Интеллектуальный генератор и структуризатор знаний на базе Google Gemini."""

import json
import re
from typing import Any, Dict, List, Optional
from logger import logger
from ..models import (
    ArtifactInput,
    ArtifactType,
    Claim,
    DiagnosticKnowledge,
    KnowledgeEntity,
    KnowledgeSource,
    LookupLevel,
    ResolutionAction,
)
from ..normalizer import CanonicalKeyNormalizer
from .base import BaseResolver


_SYSTEM_PROMPT = """Ты — экспертный аналитик операционной системы Windows и архитектор баз знаний.
Твоя задача — проанализировать входящий артефакт Windows (Event ID, код ошибки HRESULT/Win32/NTSTATUS, имя процесса, ключ реестра, симптом) и вернуть СТРОГИЙ валидный JSON без markdown-оберток (без ```json ... ```) со следующей структурой:
{
  "name": "Понятное наименование ошибки или артефакта",
  "summary": "Четкое описание того, что означает данный артефакт",
  "category": "system|security|storage|network|driver|code",
  "severity": "info|warning|error|critical",
  "confidence": 0.85,
  "possible_causes": ["причина 1", "причина 2"],
  "diagnostic_actions": [
    {
      "title": "Название проверки",
      "description": "Что именно проверять",
      "command": "powershell/cmd команда (если применимо)",
      "risk_level": "safe",
      "is_automated": true
    }
  ],
  "remediation_steps": [
    {
      "title": "Шаг устранения",
      "description": "Подробное действие",
      "command": "powershell/cmd команда",
      "risk_level": "safe",
      "is_automated": false
    }
  ],
  "related_components": ["DistributedCOM", "svchost.exe"],
  "tags": ["dcom", "event-10016", "permissions"]
}
"""


class GeminiKnowledgeResolver(BaseResolver):
    """Резолвер синтеза знаний через Google Gemini с возвратом валидированного JSON."""

    def __init__(self, chat_model: Optional[Any] = None, model_id: str = "gemini-3.5-flash-lite") -> None:
        """Инициализирует GeminiKnowledgeResolver.

        Args:
            chat_model: Экземпляр адаптера Gemini Chat (опционально).
            model_id: Идентификатор модели Gemini по умолчанию.
        """
        super().__init__(level=LookupLevel.GEMINI, name="GeminiKnowledgeResolver")
        self.chat_model = chat_model
        self.model_id = model_id

    def _get_chat_client(self) -> Optional[Any]:
        """Получает или лениво инициализирует адаптер Gemini."""
        if self.chat_model is not None:
            return self.chat_model

        try:
            from src.ai.chat.gemini import GeminiChatBase
            if GeminiChatBase.is_available():
                self.chat_model = GeminiChatBase(
                    model_id=self.model_id,
                    system_prompt=_SYSTEM_PROMPT,
                )
                return self.chat_model
        except Exception as exc:
            logger.debug(f"Не удалось инициализировать GeminiChatBase: {exc}")

        return None

    def _build_prompt(self, artifact: ArtifactInput, canonical_key: str) -> str:
        """Формирует структурированный запрос для Gemini."""
        parts = [
            f"Анализируй артефакт Windows:\nCanonical Key: {canonical_key}",
            f"Тип: {artifact.type.value if artifact.type else 'unknown'}",
        ]
        if artifact.provider:
            parts.append(f"Provider: {artifact.provider}")
        if artifact.event_id is not None:
            parts.append(f"Event ID: {artifact.event_id}")
        if artifact.error_code:
            parts.append(f"Код ошибки: {artifact.error_code}")
        if artifact.process_name:
            parts.append(f"Процесс: {artifact.process_name}")
        if artifact.registry_path:
            parts.append(f"Реестр: {artifact.registry_path}")
        if artifact.message:
            parts.append(f"Сообщение лога: {artifact.message}")
        if artifact.raw_query:
            parts.append(f"Сырой запрос: {artifact.raw_query}")

        parts.append("\nВерни СТРОГИЙ валидный JSON по заданной схеме.")
        return "\n".join(parts)

    def _parse_and_validate_json(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Извлекает и валидирует JSON из текстового ответа LLM."""
        if not response_text:
            return None

        clean_text = response_text.strip()
        # Очистка от markdown блоков ```json ... ```
        if "```" in clean_text:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean_text)
            if match:
                clean_text = match.group(1).strip()

        try:
            data = json.loads(clean_text)
            if isinstance(data, dict):
                return data
        except Exception as exc:
            logger.warning(f"Ошибка парсинга JSON ответа Gemini: {exc}. Текст: {response_text[:200]}")

        return None

    async def resolve(self, artifact: ArtifactInput) -> Optional[KnowledgeEntity]:
        """Обращается к Gemini, структурирует ответ и создает объект KnowledgeEntity.

        Args:
            artifact: Входной артефакт.

        Returns:
            Сущность KnowledgeEntity или None при ошибке обращения к LLM.
        """
        canonical_key = CanonicalKeyNormalizer.compute_canonical_key(artifact)
        fingerprint = CanonicalKeyNormalizer.compute_fingerprint(artifact)
        client = self._get_chat_client()

        if client is None:
            logger.debug("Gemini клиент недоступен для разрешения артефакта.")
            return None

        prompt = self._build_prompt(artifact, canonical_key)
        try:
            raw_answer: Optional[str] = None
            if hasattr(client, "ask"):
                raw_answer = await client.ask(
                    prompt,
                    system_instruction=_SYSTEM_PROMPT,
                    temperature=0.1,
                )
            elif hasattr(client, "send_message"):
                raw_answer = await client.send_message(prompt)

            if not raw_answer:
                return None

            payload = self._parse_and_validate_json(raw_answer)
            if not payload:
                return None

            # Построение структурированного объекта знаний
            diag_actions = [
                ResolutionAction(
                    title=a.get("title", ""),
                    description=a.get("description", ""),
                    command=a.get("command"),
                    risk_level=a.get("risk_level", "safe"),
                    is_automated=bool(a.get("is_automated", False)),
                )
                for a in payload.get("diagnostic_actions", [])
                if isinstance(a, dict) and a.get("title")
            ]

            remed_steps = [
                ResolutionAction(
                    title=s.get("title", ""),
                    description=s.get("description", ""),
                    command=s.get("command"),
                    risk_level=s.get("risk_level", "safe"),
                    is_automated=bool(s.get("is_automated", False)),
                )
                for s in payload.get("remediation_steps", [])
                if isinstance(s, dict) and s.get("title")
            ]

            diag_info = DiagnosticKnowledge(
                possible_causes=payload.get("possible_causes", []),
                diagnostic_actions=diag_actions,
                remediation_steps=remed_steps,
                related_components=payload.get("related_components", []),
            )

            claims = [
                Claim(
                    statement=f"Первопричина: {cause}",
                    confidence=float(payload.get("confidence", 0.8)),
                    source=KnowledgeSource.LLM_GENERATED,
                    verified=False,
                )
                for cause in payload.get("possible_causes", [])
            ]

            entity_type = artifact.type or ArtifactType.WINDOWS_EVENT
            entity = KnowledgeEntity(
                canonical_key=canonical_key,
                entity_type=entity_type,
                name=payload.get("name", canonical_key),
                summary=payload.get("summary", ""),
                category=payload.get("category", "system"),
                severity=payload.get("severity", "info"),
                confidence=float(payload.get("confidence", 0.85)),
                provenance_source=KnowledgeSource.LLM_GENERATED,
                provenance_model=self.model_id,
                fingerprint=fingerprint,
                diagnostic_info=diag_info,
                claims=claims,
                tags=payload.get("tags", []),
            )

            return entity

        except Exception as exc:
            logger.warning(f"Исключение при обращении к Gemini в WikiLLM: {exc}")
            return None
