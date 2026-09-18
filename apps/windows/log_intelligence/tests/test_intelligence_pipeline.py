# -*- coding: utf-8 -*-
from pathlib import Path
import pytest

from apps.windows.log_intelligence.src.models import (
    DataProfileReport,
    IngestionDecision,
    IngestionStrategy,
    LogEntry,
    LogSeverity,
)
from apps.windows.log_intelligence.src.data_researcher import LogDataResearcher
from apps.windows.log_intelligence.src.decision_gate import DecisionGate
from apps.windows.log_intelligence.src.adaptive_rag import AdaptiveLogRAG, get_default_storage_dir
from apps.windows.log_intelligence.src.pipeline import LogIntelligencePipeline


def test_data_researcher_profiling() -> None:
    """Проверка работы Data Researcher: подсчет Redundancy Ratio, Health Score и детекция всплесков."""
    researcher = LogDataResearcher()
    entries = [
        LogEntry(timestamp="2026-09-16 15:00:01", level="Information", provider="Service", event_id=7036, message="Service started"),
        LogEntry(timestamp="2026-09-16 15:00:02", level="Information", provider="Service", event_id=7036, message="Service started"),
        LogEntry(timestamp="2026-09-16 15:00:03", level="Information", provider="Service", event_id=7036, message="Service started"),
        LogEntry(timestamp="2026-09-16 15:05:00", level="Error", provider="Kernel-Power", event_id=41, message="Reboot without shutdown"),
        LogEntry(timestamp="2026-09-16 15:05:01", level="Warning", provider="rt640x64", event_id=1, message="Network disconnected"),
    ]
    profile = researcher.profile_data(entries, channel="System")
    assert profile.total_events == 5
    assert profile.unique_templates_count < 5
    assert profile.redundancy_ratio_pct > 0.0
    assert profile.error_count == 1
    assert profile.warning_count == 1
    assert profile.health_score < 100.0


def test_decision_gate_strategies() -> None:
    """Проверка выбора стратегий в Decision Gate."""
    gate = DecisionGate()

    # Сценарий 1: Инцидентный сбой
    err_profile = DataProfileReport(
        channel="System", total_events=100, unique_templates_count=20,
        redundancy_ratio_pct=80.0, health_score=65.0, error_count=2,
    )
    dec1 = gate.evaluate(err_profile)
    assert dec1.strategy == IngestionStrategy.INCIDENT_FOCUSED

    # Сценарий 2: Абсолютно стабильная система
    healthy_profile = DataProfileReport(
        channel="System", total_events=100, unique_templates_count=15,
        redundancy_ratio_pct=85.0, health_score=100.0, error_count=0, warning_count=0,
    )
    dec2 = gate.evaluate(healthy_profile)
    assert dec2.strategy == IngestionStrategy.SNAPSHOT_ONLY

    # Сценарий 3: Шторм монотонного шума
    noisy_profile = DataProfileReport(
        channel="System", total_events=500, unique_templates_count=5,
        redundancy_ratio_pct=99.0, health_score=98.0, dominant_noise_provider="Kernel-PnP",
    )
    dec3 = gate.evaluate(noisy_profile)
    assert dec3.strategy == IngestionStrategy.NOISE_MASKED


def test_adaptive_rag_pipeline(tmp_path: Path) -> None:
    """Проверка полного цикла LogIntelligencePipeline с сохранением и поиском."""
    pipeline = LogIntelligencePipeline(storage_dir=tmp_path / "rag_storage")
    entries = [
        LogEntry(timestamp="2026-09-16 16:30:00", level="Warning", provider="rt640x64", event_id=1, message="Realtek network adapter disconnected"),
        LogEntry(timestamp="2026-09-16 16:30:05", level="Error", provider="BITS", event_id=16393, message="BITS gateway communication failure 0x80040500"),
    ]
    res = pipeline.process_events(entries, channel="System")
    assert res["profile"]["total_events"] == 2
    assert res["decision"]["chunks_generated"] > 0

    # Поиск по RAG
    search_res = pipeline.search_rag("почему отключился сетевой адаптер?")
    assert len(search_res) > 0
    assert "Realtek" in search_res[0]["text"] or "network" in search_res[0]["text"].lower() or "сбо" in search_res[0]["text"].lower()


def test_wevtapi_channel_enumeration() -> None:
    """Проверка нативного перечисления каналов через WevtAPI."""
    from apps.windows.api.wevtapi import WevtAPI
    api = WevtAPI()
    channels = api.enumerate_channels()
    assert len(channels) >= 10
    names = [c.channel_name.lower() for c in channels]
    assert "system" in names
    assert "application" in names


def test_log_discovery_engine_sources() -> None:
    """Проверка обнаружения всех источников логов в системе через LogDiscoveryEngine."""
    from apps.windows.core.modules.log_discovery_engine import LogDiscoveryEngine
    engine = LogDiscoveryEngine()
    sources = engine.discover_all_sources()
    assert len(sources) > 50
    categories = {s.category for s in sources}
    assert "Windows Event Log" in categories

