# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Ai - Prompt Templates
# =============================================================================
# Description:
#   Системный промпт для эксперта-диагноста Windows.
#
# Usage Examples:
#   Python API:
#     from apps.windows.ai.prompt_templates import build_system_prompt
#
#     res = build_system_prompt()
#
# File: prompt_templates.py
# Project: ai-breadboard
# Package: apps.windows.ai
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Системный промпт для эксперта-диагноста Windows."""

import json
from typing import Any, Dict, List

def build_system_prompt() -> str:
    """Системный промпт для эксперта-диагноста Windows."""
    return 'Ты — высококвалифицированный эксперт по архитектуре и диагностике Microsoft Windows (AI Windows Diagnostician). Твоя задача — анализировать собранные телеметрические факты, логи событий, информацию о процессах, службах, драйверах и точках автозагрузки, находить скрытые корреляции и первопричины сбоев/замедлений. Правила: 1. Не предлагай сомнительных или деструктивных твиков. 2. Всегда объясняй цепочку: Проблема -> Причина -> Доказательства -> Безопасное исправление. 3. Разделяй действия по уровням риска (Safe / Caution / Critical). 4. Весь ответ должен быть на русском языке. 5. **Ответ LLM обязателен в виде JSON‑блока внутри markdown‑кода ```json { "tool_name": "...", "arguments": { ... } }``` без любого другого текста.**'

def build_audit_prompt(domains_data: Dict[str, Any], health_score: int) -> str:
    """Промпт для генерации экспертного заключения по полному аудиту."""
    summary_json = json.dumps(domains_data, ensure_ascii=False, indent=2)
    return f'Проанализируй результаты аудита Windows (Текущий Health Score: {health_score}/100).\n\nФакты по доменам:\n{summary_json}\n\nСформируй структурированное заключение:\n1. Общий статус здоровья системы.\n2. Ключевые узкие места и риски безопасности.\n3. Рекомендованный пошаговый план оптимизации и очистки (с указанием приоритетов).'

def build_root_cause_prompt(symptom: str, evidence_chain: List[Dict[str, Any]]) -> str:
    """Промпт для расследования первопричины по симптому пользователя."""
    evidence_json = json.dumps(evidence_chain, ensure_ascii=False, indent=2)
    return f'Пользователь сообщил о симптоме проблемы: "{symptom}".\n\nСобранная цепочка фактов и телеметрии:\n{evidence_json}\n\nСформулируй:\n1. Наиболее вероятную первопричину (Root Cause) с оценкой уверенности (%)\n2. Объяснение цепочки влияния (как именно это привело к симптому)\n3. Точный безопасный план устранения (с минимальным воздействием на стабильность ОС).'