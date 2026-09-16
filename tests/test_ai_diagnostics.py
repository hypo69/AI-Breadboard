# -*- coding: utf-8 -*-
import pytest
from unittest.mock import AsyncMock
from apps.windows.telemetry.models import SystemSnapshot, CpuMetrics, MemoryMetrics
from apps.trading_terminal.engine import TradingState, OrderRecord
from src.ai.observability.system_engine import SystemDiagnosticEngine
from src.ai.observability.trading_engine import TradingDiagnosticEngine

@pytest.mark.asyncio
async def test_system_diagnostic_engine_heuristics():
    engine = SystemDiagnosticEngine()
    snap = SystemSnapshot(
        cpu=CpuMetrics(total_percent=95.0), # Trigger critical CPU
        memory=MemoryMetrics(percent=50.0)
    )
    score, anomalies, recs = engine.evaluate_heuristics(snap)
    assert score < 100
    assert len(anomalies) > 0
    assert any(a.subsystem == "CPU" for a in anomalies)

@pytest.mark.asyncio
async def test_trading_diagnostic_engine_heuristics():
    engine = TradingDiagnosticEngine()
    state = TradingState(
        symbol="BTC/USDT",
        current_price=50000.0,
        balance=10000.0,
        position_size=1.0,
        entry_price=55000.0, # 10% drawdown
        unrealized_pnl=-5000.0,
        realized_pnl=0.0,
        total_equity=10000.0,
        recent_logs=["[ERROR] API failure"],
        recent_orders=[]
    )
    score, anomalies, recs = engine.evaluate_heuristics(state)
    assert score < 100
    assert any(a.subsystem == "Trading" for a in anomalies)

@pytest.mark.asyncio
async def test_diagnose_with_llm_integration():
    mock_chat = AsyncMock()
    mock_chat.ask.return_value = "Diagnostic analysis from LLM"
    mock_chat.active_provider = "Mock Provider"
    
    engine = SystemDiagnosticEngine(chat_model=mock_chat)
    snap = SystemSnapshot(cpu=CpuMetrics(total_percent=95.0))
    
    report = await engine.diagnose(snap)
    
    assert report.ai_model_used == "Mock Provider"
    assert "Diagnostic analysis from LLM" in report.summary
    mock_chat.ask.assert_called_once()
