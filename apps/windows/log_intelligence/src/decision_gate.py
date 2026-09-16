# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Decision Gate for Adaptive Log Processing
# =============================================================================
# Description:
#   Evaluates DataProfileReport against expert policies to select
#   the optimal ingestion and RAG strategy (Snapshot, Incident Cascade, Novelty, Noise-mask).
#
# Examples:
#   >>> from apps.windows.log_intelligence.src.decision_gate import DecisionGate
#   >>> gate = DecisionGate()
#   >>> decision = gate.evaluate(profile_report)
#
# File: decision_gate.py
# Project: AI-Breadboard
# Package: apps.windows.log_intelligence.src
# Class: DecisionGate
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

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
        # Правило 1: Критический сбой или падение индекса здоровья (Red State)
        if profile.critical_count > 0 or profile.error_count > 0 or profile.health_score < 75.0:
            windows = [b.time_window for b in profile.bursts if b.dominant_level in ("Critical", "Error", "Warning")]
            return IngestionDecision(
                strategy=IngestionStrategy.INCIDENT_FOCUSED,
                rationale=(
                    f"Обнаружен инцидентный сбой: {profile.critical_count} крит., {profile.error_count} ошибок. "
                    f"Health Score: {profile.health_score}%. Векторизуются только цепочки событий вокруг сбоя."
                ),
                chunks_to_generate=min(12, max(2, len(profile.bursts) + len(profile.novel_signatures))),
                target_time_windows=windows,
                skip_providers=[profile.dominant_noise_provider] if profile.redundancy_ratio_pct > 80 else [],
                recommended_llm_action="Запустить AI-диагностику причин падения и цепочки каскада.",
            )

        # Правило 2: Появление новых неизвестных сигнатур (Knowledge Discovery)
        if profile.novel_signatures and profile.health_score < 95.0:
            return IngestionDecision(
                strategy=IngestionStrategy.NOVELTY_SIGNATURE,
                rationale=(
                    f"Обнаружено {len(profile.novel_signatures)} новых сигнатур/событий. "
                    f"Обогащение базы знаний RAG новыми паттернами."
                ),
                chunks_to_generate=len(profile.novel_signatures) + 1,
                target_time_windows=[],
                skip_providers=[profile.dominant_noise_provider] if profile.redundancy_ratio_pct > 85 else [],
                recommended_llm_action="Классифицировать новые сигнатуры и обновить локальную базу знаний.",
            )

        # Правило 3: Массовый шторм повторов при высокой избыточности (Noise Storm)
        if profile.redundancy_ratio_pct >= 90.0:
            return IngestionDecision(
                strategy=IngestionStrategy.NOISE_MASKED,
                rationale=(
                    f"Массив на {profile.redundancy_ratio_pct}% состоит из однотипного монотонного шума "
                    f"(доминирует {profile.dominant_noise_provider}). Создается 1 агрегированный дайджест с маскированием."
                ),
                chunks_to_generate=min(5, max(1, profile.unique_templates_count)),
                target_time_windows=[],
                skip_providers=[profile.dominant_noise_provider],
                recommended_llm_action="Сжать и зафиксировать статистику фоновых сервисов без лишних токенов.",
            )

        # Правило 4: Абсолютно штатная работа системы (Green State)
        return IngestionDecision(
            strategy=IngestionStrategy.SNAPSHOT_ONLY,
            rationale=(
                f"Система полностью стабильна: Health Score {profile.health_score}%, 0 сбоев. "
                f"В RAG сохраняется только 1 почасовой снимок здоровья ОС (0 токенов на события)."
            ),
            chunks_to_generate=1,
            target_time_windows=[],
            skip_providers=[],
            recommended_llm_action="Система в норме. Вмешательство ИИ не требуется.",
        )
