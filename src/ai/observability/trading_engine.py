# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Trading Terminal Diagnostic Engine
# =============================================================================
# Description:
#   Implements heuristic rules for TradingState.
#
# File: trading_engine.py
# Project: ai-breadboard
# Package: src.ai.observability
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Trading terminal specific diagnostic engine."""

from __future__ import annotations
from typing import List, Tuple, Any
from src.ai.observability.engine import DiagnosticEngine
from src.ai.observability.models import AnomalyItem

class TradingDiagnosticEngine(DiagnosticEngine):
    """Diagnoses trading terminal anomalies."""

    def evaluate_heuristics(self, state: Any) -> Tuple[int, List[AnomalyItem], List[str]]:
        """Run rule-based heuristic checks over trading state."""
        # Импорт здесь, чтобы избежать циклической зависимости
        from apps.trading_terminal.engine import TradingState
        if not isinstance(state, TradingState):
            raise ValueError("Expected TradingState")
        score = 100
        anomalies: List[AnomalyItem] = []
        recommendations: List[str] = []

        # 1. Error Log Analysis
        error_logs = [log for log in state.recent_logs if "ERROR" in log or "failed" in log.lower()]
        if len(error_logs) > 5:
            score -= 40
            anomalies.append(
                AnomalyItem(
                    subsystem="Trading",
                    severity="critical",
                    title="High Error Rate",
                    description=f"Detected {len(error_logs)} errors in recent logs.",
                )
            )
            recommendations.append("Inspect error logs immediately for API connectivity issues.")
        
        # 2. Drawdown Analysis (if equity > 0)
        if state.total_equity > 0 and (state.unrealized_pnl / state.total_equity) < -0.1:
            score -= 20
            anomalies.append(
                AnomalyItem(
                    subsystem="Trading",
                    severity="warning",
                    title="Significant Drawdown",
                    description=f"Unrealized PnL is at {(state.unrealized_pnl / state.total_equity)*100:.1f}% of equity.",
                )
            )
            recommendations.append("Review risk management settings and stop-loss levels.")

        score = max(0, min(100, score))
        if not recommendations:
            recommendations.append("Trading state is nominal.")
        
        return score, anomalies, recommendations
