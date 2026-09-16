# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows AI Diagnostics Prompt Templates
# =============================================================================
# Description:
#   Шаблоны промптов для языковых моделей (LLM) для проведения интеллектуального
#   аудита Windows, формулирования гипотез первопричин и анализа рисков.
#
# Examples:
#   >>> from apps.windows.ai.prompt_templates import build_root_cause_prompt
#   >>> prompt = build_root_cause_prompt(symptom, facts)
#
# File: prompt_templates.py
# Project: ai-breadboard
# Package: apps.windows.ai
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Шаблоны промптов для AI-диагностики Windows."""

from __future__ import annotations

import json
from typing import Any, Dict, List


def build_system_prompt() -> str:
    """Системный промпт для эксперта-диагноста Windows."""
    return (
        "Ты — высококвалифицированный эксперт по архитектуре и диагностике Microsoft Windows (AI Windows Diagnostician). "
        "Твоя задача — анализировать собранные телеметрические факты, логи событий, информацию о процессах, службах, "
        "драйверах и точках автозагрузки, находить скрытые корреляции и первопричины сбоев/замедлений. "
        "Правила: "
        "1. Не предлагай сомнительных или деструктивных твиков. "
        "2. Всегда объясняй цепочку: Проблема -> Причина -> Доказательства -> Безопасное исправление. "
        "3. Разделяй действия по уровням риска (Safe / Caution / Critical). "
        "4. Весь ответ должен быть на русском языке."
    )


def build_audit_prompt(domains_data: Dict[str, Any], health_score: int) -> str:
    """Промпт для генерации экспертного заключения по полному аудиту."""
    summary_json = json.dumps(domains_data, ensure_ascii=False, indent=2)
    return (
        f"Проанализируй результаты аудита Windows (Текущий Health Score: {health_score}/100).\n\n"
        f"Факты по доменам:\n{summary_json}\n\n"
        "Сформируй структурированное заключение:\n"
        "1. Общий статус здоровья системы.\n"
        "2. Ключевые узкие места и риски безопасности.\n"
        "3. Рекомендованный пошаговый план оптимизации и очистки (с указанием приоритетов)."
    )


def build_root_cause_prompt(symptom: str, evidence_chain: List[Dict[str, Any]]) -> str:
    """Промпт для расследования первопричины по симптому пользователя."""
    evidence_json = json.dumps(evidence_chain, ensure_ascii=False, indent=2)
    return (
        f"Пользователь сообщил о симптоме проблемы: \"{symptom}\".\n\n"
        f"Собранная цепочка фактов и телеметрии:\n{evidence_json}\n\n"
        "Сформулируй:\n"
        "1. Наиболее вероятную первопричину (Root Cause) с оценкой уверенности (%)\n"
        "2. Объяснение цепочки влияния (как именно это привело к симптому)\n"
        "3. Точный безопасный план устранения (с минимальным воздействием на стабильность ОС)."
    )
