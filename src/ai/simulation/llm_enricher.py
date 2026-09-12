# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: LLM Simulation Enricher
# =============================================================================
# Description:
#   Enriches generated mock entities with realistic business context, legal notes,
#   manager recommendations, and negotiation history via the default LLM model.
#
# File: llm_enricher.py
# Project: ai-breadboard
# Package: src.ai.simulation
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import asyncio
import inspect
from typing import Any, Dict, Optional

from src.logger import logger


_ENRICHMENT_SYSTEM_PROMPT = (
    "Ты — ведущий эксперт и юридический консультант крупного многопрофильного агентства "
    "(недвижимость, премиальный автотранспорт, готовый бизнес, страхование).\n"
    "Тебе предоставлена структурированная карточка фиктивного документа/сделки с клиентом.\n"
    "Твоя задача: дополнить и обогатить этот документ профессиональным экспертным комментарием:\n"
    "1. Сохрани все исходные ключевые факты (номер, даты, суммы, имена, объекты) БЕЗ ИЗМЕНЕНИЙ.\n"
    "2. Добавь краткую предысторию или статус согласования (1-2 емких предложения).\n"
    "3. Добавь блок «💡 Примечания и рекомендации для менеджера» (например, напоминание о пролонгации, "
    "особые условия доступа, статус оплат или страховки).\n"
    "4. Оформи ответ в красивом, чистом Markdown."
)


async def call_model_adapter(model: Any, prompt: str, system_prompt: str = "") -> str:
    """Invoke various LLM model interfaces asynchronously.

    Args:
        model: Model instance (UnifiedChatModel, Gemini, Ollama, Foundry, or callable).
        prompt: User prompt for enrichment.
        system_prompt: System prompt instructing role and format.

    Returns:
        str: Model text response.
    """
    if model is None:
        return ""

    try:
        # 1. Check for chat method (UnifiedChatModel, etc)
        if hasattr(model, "chat"):
            chat_fn = getattr(model, "chat")
            if inspect.iscoroutinefunction(chat_fn):
                res = await chat_fn(prompt, system_instruction=system_prompt)
            else:
                res = await asyncio.to_thread(chat_fn, prompt, system_instruction=system_prompt)
            return str(res) if res else ""

        # 2. Check for ask method
        if hasattr(model, "ask"):
            ask_fn = getattr(model, "ask")
            if inspect.iscoroutinefunction(ask_fn):
                res = await ask_fn(prompt)
            else:
                res = await asyncio.to_thread(ask_fn, prompt)
            return str(res) if res else ""

        # 3. Check for generate_content_async (GoogleGenerativeAI)
        if hasattr(model, "generate_content_async"):
            res = await model.generate_content_async(prompt)
            return str(res) if res else ""

        # 4. Check for callable
        if callable(model):
            if inspect.iscoroutinefunction(model):
                res = await model(prompt)
            else:
                res = await asyncio.to_thread(model, prompt)
            return str(res) if res else ""

    except Exception as ex:
        logger.error(f"[LLMEnricher] Failed to call LLM model: {ex}", ex, False)

    return ""


async def enrich_simulation_with_llm(
    model: Any,
    entity_type: str,
    raw_text: str,
    structured_data: Dict[str, Any],
    query: str
) -> str:
    """Enrich simulated document content using the default LLM model.

    Args:
        model: Connected LLM model instance.
        entity_type: Type of simulated entity (contract, invoice, etc.).
        raw_text: Base generated Markdown text.
        structured_data: Extracted key-value facts.
        query: Original user query.

    Returns:
        str: Enriched markdown text, or raw_text on fallback.
    """
    if not model:
        return raw_text

    prompt = (
        f"Запрос пользователя: «{query}»\n"
        f"Тип сущности: {entity_type}\n"
        f"Ключевые данные: {structured_data}\n\n"
        f"Базовый документ:\n{raw_text}\n\n"
        f"Пожалуйста, сформируй итоговый презентационный ответ с экспертным комментарием и рекомендациями."
    )

    try:
        enriched_response = await call_model_adapter(
            model=model,
            prompt=prompt,
            system_prompt=_ENRICHMENT_SYSTEM_PROMPT,
        )
        if enriched_response and len(enriched_response.strip()) > 30:
            logger.info(f"[LLMEnricher] Successfully enriched entity '{entity_type}' via LLM model")
            return enriched_response.strip()

    except Exception as ex:
        logger.warning(f"[LLMEnricher] Enrichment failed, falling back to raw template: {ex}")

    return raw_text
