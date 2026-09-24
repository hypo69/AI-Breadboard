# -*- coding: utf-8 -*-
import pytest
import asyncio
from unittest.mock import AsyncMock
from apps.windows.telemetry.models import SystemSnapshot, CpuMetrics, MemoryMetrics, PhysicalDiskHealth
from apps.trading_terminal.engine import TradingState, OrderRecord
from src.ai.observability.system_engine import SystemDiagnosticEngine
from src.ai.observability.trading_engine import TradingDiagnosticEngine
from src.ai.observability.grouped_telemetry import GroupedTelemetryBuilder

def test_system_diagnostic_engine_heuristics():
    engine = SystemDiagnosticEngine()
    snap = SystemSnapshot(
        cpu=CpuMetrics(total_percent=95.0), # Trigger critical CPU
        memory=MemoryMetrics(percent=50.0)
    )
    score, anomalies, recs = engine.evaluate_heuristics(snap)
    assert score < 100
    assert len(anomalies) > 0
    assert any(a.subsystem == "CPU" for a in anomalies)

def test_trading_diagnostic_engine_heuristics():
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

def test_diagnose_with_llm_integration():
    mock_chat = AsyncMock()
    mock_chat.ask.return_value = "Diagnostic analysis from LLM"
    mock_chat.active_provider = "Mock Provider"
    
    engine = SystemDiagnosticEngine(chat_model=mock_chat)
    snap = SystemSnapshot(cpu=CpuMetrics(total_percent=95.0))
    
    report = asyncio.run(engine.diagnose(snap))
    
    assert report.ai_model_used == "Mock Provider"
    assert "Diagnostic analysis from LLM" in report.summary
    # Check that generated prompt contains structured host telemetry in JSON format
    assert "```json" in report.generated_prompt
    assert '"host_system"' in report.generated_prompt
    assert '"sensors"' in report.generated_prompt

def test_system_idle_process_not_flagged_as_anomaly():
    from apps.windows.telemetry.models import ProcessMetrics
    engine = SystemDiagnosticEngine()
    snap = SystemSnapshot(
        top_processes=[
            ProcessMetrics(pid=0, name="System Idle Process", cpu_percent=99.9),
            ProcessMetrics(pid=4, name="System", cpu_percent=85.0),
        ]
    )
    score, anomalies, recs = engine.evaluate_heuristics(snap)
    assert not any("System Idle Process" in a.title for a in anomalies)
    assert not any("PID 0" in a.title for a in anomalies)
    assert not any("PID 4" in a.title for a in anomalies)

def test_storage_smart_group_with_physical_disks():
    builder = GroupedTelemetryBuilder()
    snap = SystemSnapshot(
        physical_disks=[
            PhysicalDiskHealth(
                device_id="Disk 0",
                model="Samsung 980 PRO 1TB",
                media_type="SSD",
                size_gb=1000.0,
                health_status="Healthy",
                interface_type="NVMe",
            )
        ]
    )
    group = builder.build_storage_smart_group(snap)
    assert group.group_id == "storage_smart"
    assert len(group.payload["physical_drives_smart"]) == 1
    assert group.payload["physical_drives_smart"][0]["interface_type"] == "NVMe"


