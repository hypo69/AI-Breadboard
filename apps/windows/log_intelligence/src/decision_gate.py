# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Log_Intelligence Src - Decision Gate
# =============================================================================
# Description:
#   Интеллектуальный шлюз принятия решений перед созданием RAG.
#
# Usage Examples:
#   Python API:
#     from apps.windows.log_intelligence.src.decision_gate import DecisionGate
#
#     service = DecisionGate()
#
# File: decision_gate.py
# Project: ai-breadboard
# Package: apps.windows.log_intelligence.src
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Интеллектуальный шлюз принятия решений перед созданием RAG."""

from typing import List
from .models import DataProfileReport, IngestionDecision, IngestionStrategy

class DecisionGate:
    """Интеллектуальный шлюз принятия решений перед созданием RAG."""

    def evaluate(self, profile: DataProfileReport) -> IngestionDecision:
        """Оценить аналитический профиль и выбрать наилучшую стратегию RAG.

        Args:
            profile (DataProfileReport): Профиль данных от Data Researcher.

        Returns:
            IngestionDecision: Решение с выбранной стратегией и планом действий.
        """
        if profile.critical_count > 0 or profile.error_count > 0 or profile.health_score < 75.0:
            windows = [b.time_window for b in profile.bursts if b.dominant_level in ('Critical', 'Error', 'Warning')]
            return IngestionDecision(strategy=IngestionStrategy.INCIDENT_FOCUSED, rationale=f'Обнаружен инцидентный сбой: {profile.critical_count} крит., {profile.error_count} ошибок. Health Score: {profile.health_score}%. Векторизуются только цепочки событий вокруг сбоя.', chunks_to_generate=min(12, max(2, len(profile.bursts) + len(profile.novel_signatures))), target_time_windows=windows, skip_providers=[profile.dominant_noise_provider] if profile.redundancy_ratio_pct > 80 else [], recommended_llm_action='Запустить AI-диагностику причин падения и цепочки каскада.')
        if profile.novel_signatures and profile.health_score < 95.0:
            return IngestionDecision(strategy=IngestionStrategy.NOVELTY_SIGNATURE, rationale=f'Обнаружено {len(profile.novel_signatures)} новых сигнатур/событий. Обогащение базы знаний RAG новыми паттернами.', chunks_to_generate=len(profile.novel_signatures) + 1, target_time_windows=[], skip_providers=[profile.dominant_noise_provider] if profile.redundancy_ratio_pct > 85 else [], recommended_llm_action='Классифицировать новые сигнатуры и обновить локальную базу знаний.')
        if profile.redundancy_ratio_pct >= 90.0:
            return IngestionDecision(strategy=IngestionStrategy.NOISE_MASKED, rationale=f'Массив на {profile.redundancy_ratio_pct}% состоит из однотипного монотонного шума (доминирует {profile.dominant_noise_provider}). Создается 1 агрегированный дайджест с маскированием.', chunks_to_generate=min(5, max(1, profile.unique_templates_count)), target_time_windows=[], skip_providers=[profile.dominant_noise_provider], recommended_llm_action='Сжать и зафиксировать статистику фоновых сервисов без лишних токенов.')
        return IngestionDecision(strategy=IngestionStrategy.SNAPSHOT_ONLY, rationale=f'Система полностью стабильна: Health Score {profile.health_score}%, 0 сбоев. В RAG сохраняется только 1 почасовой снимок здоровья ОС (0 токенов на события).', chunks_to_generate=1, target_time_windows=[], skip_providers=[], recommended_llm_action='Система в норме. Вмешательство ИИ не требуется.')