# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Test Grouped AI Telemetry Diagnostics
# =============================================================================
# Description:
#   Тестирование разделения телеметрии на 4 домена, пошагового опроса групп
#   и финального синтеза с расчетом Health Score.
#
# File: test_grouped_diagnostics.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
from unittest.mock import AsyncMock

from apps.windows.telemetry.models import (
    CpuMetrics,
    DiskPartitionMetrics,
    GpuMetrics,
    HardwareSensor,
    MemoryMetrics,
    ProcessMetrics,
    SystemSnapshot,
)
from src.ai.observability.grouped_telemetry import (
    GroupDiagnosticResult,
    GroupedTelemetryBuilder,
)
from src.ai.observability.system_engine import SystemDiagnosticEngine


@pytest.fixture
def sample_snapshot() -> SystemSnapshot:
    """Фикстура снимка телеметрии с несколькими выраженными узкими местами."""
    return SystemSnapshot(
        hostname="TEST-WORKSTATION",
        os_name="Windows 11",
        os_build="26200",
        uptime_seconds=36000.0,
        cpu=CpuMetrics(
            model="Intel Core i5-10400",
            total_percent=88.5,
            physical_cores=6,
            logical_cores=12,
            frequency_mhz=2900.0,
        ),
        memory=MemoryMetrics(
            total_gb=32.0,
            used_gb=28.0,
            available_gb=4.0,
            percent=87.5,
        ),
        gpus=[
            GpuMetrics(name="NVIDIA GeForce GT 710", load_percent=15.0, temperature_celsius=62.0)
        ],
        disks=[
            DiskPartitionMetrics(device="C:\\", mountpoint="C:\\", total_gb=500.0, free_gb=250.0, percent=50.0),
            DiskPartitionMetrics(device="T:\\", mountpoint="T:\\", total_gb=500.0, free_gb=5.0, percent=99.0),
        ],
        sensors=[
            HardwareSensor(sensor_id="temp_cpu", name="CPU Package Temp", category="temperature", value=88.0, unit="°C"),
            HardwareSensor(sensor_id="fan_cpu", name="CPU Fan", category="fan", value=2200.0, unit="RPM"),
        ],
        top_processes=[
            ProcessMetrics(pid=1234, name="python.exe", cpu_percent=85.0, memory_mb=1200.0),
            ProcessMetrics(pid=0, name="System Idle Process", cpu_percent=10.0, memory_mb=0.0),
        ],
    )


def test_grouped_telemetry_builder_split(sample_snapshot: SystemSnapshot):
    """Проверка корректного разбиения телеметрии на 4 специализированные группы."""
    builder = GroupedTelemetryBuilder()
    groups = builder.build_all_groups(sample_snapshot)

    assert len(groups) == 4
    group_ids = [g.group_id for g in groups]
    assert "compute_thermals" in group_ids
    assert "memory_processes" in group_ids
    assert "storage_smart" in group_ids
    assert "system_network" in group_ids

    # Проверка содержимого группы 1 (compute_thermals)
    compute = next(g for g in groups if g.group_id == "compute_thermals")
    assert "cpu" in compute.payload
    assert "sensors" in compute.payload
    assert compute.payload["cpu"]["load_percent"] == 88.5

    # Проверка содержимого группы 2 (memory_processes)
    mem_proc = next(g for g in groups if g.group_id == "memory_processes")
    assert "ram" in mem_proc.payload
    assert "top_active_processes" in mem_proc.payload
    assert len(mem_proc.payload["top_active_processes"]) > 0
    # Проверка, что System Idle Process отфильтрован
    assert not any(p["name"] == "System Idle Process" for p in mem_proc.payload["top_active_processes"])

    # Проверка содержимого группы 3 (storage_smart)
    storage = next(g for g in groups if g.group_id == "storage_smart")
    assert "storage_partitions" in storage.payload
    assert any(p["device"] == "T:\\" for p in storage.payload["storage_partitions"])


def test_diagnose_group_heuristic_and_llm(sample_snapshot: SystemSnapshot):
    """Тестирование пошаговой AI-диагностики группы с эмуляцией ответа модели."""
    mock_chat = AsyncMock()
    mock_chat.ask.return_value = "Экспертный анализ CPU: обнаружен повышенный нагрев 88°C и загрузка 88.5%."
    mock_chat.active_provider = "Mock LLM"

    engine = SystemDiagnosticEngine(chat_model=mock_chat)
    builder = GroupedTelemetryBuilder()
    compute_group = builder.build_compute_thermals_group(sample_snapshot)

    import asyncio
    res = asyncio.run(engine.diagnose_group(
        group_id=compute_group.group_id,
        payload=compute_group.payload,
        title=compute_group.title,
    ))

    assert res.group_id == "compute_thermals"
    assert res.status in ["warning", "critical"]
    assert "Экспертный анализ CPU" in res.summary
    assert res.ai_model_used == "Mock LLM"
    assert "cpu_load" in res.key_metrics


def test_synthesis_final_report():
    """Тестирование финального синтеза по всем завершенным группам."""
    mock_chat = AsyncMock()
    mock_chat.ask.return_value = "Общий вердикт: система перегружена, требуется охлаждение и очистка диска T:\\."
    mock_chat.active_provider = "Mock LLM"

    engine = SystemDiagnosticEngine(chat_model=mock_chat)
    mock_groups = [
        GroupDiagnosticResult(group_id="compute_thermals", title="CPU, GPU", status="critical", summary="Перегрев CPU"),
        GroupDiagnosticResult(group_id="memory_processes", title="Память", status="warning", summary="Высокая нагрузка RAM"),
        GroupDiagnosticResult(group_id="storage_smart", title="Диски", status="critical", summary="Диск T заполнен на 99%"),
        GroupDiagnosticResult(group_id="system_network", title="Сеть", status="ok", summary="Сеть в норме"),
    ]

    import asyncio
    synthesis = asyncio.run(engine.synthesize_final_report(mock_groups))

    assert synthesis.health_score < 80
    assert synthesis.status_label in ["Внимание", "Критическое"]
    assert synthesis.groups_evaluated == 4
    assert len(synthesis.critical_actions) > 0
    assert "Общий вердикт" in synthesis.executive_summary


def test_grouped_telemetry_builder_empty_snapshot():
    """Проверка отказоустойчивости билдера при пустом или частично поврежденном снимке."""
    empty_snap = SystemSnapshot()
    builder = GroupedTelemetryBuilder()
    groups = builder.build_all_groups(empty_snap)

    assert len(groups) == 4
    for g in groups:
        assert g.group_id in ["compute_thermals", "memory_processes", "storage_smart", "system_network"]
        assert isinstance(g.payload, dict)


def test_router_diagnose_endpoints():
    """Проверка работы и устойчивости роутов /diagnose/groups, /diagnose/group, /diagnose/synthesize."""
    from fastapi.testclient import TestClient
    from src.app import create_app, register_routers, AppState

    app = create_app()
    state = AppState()
    register_routers(app, state)
    client = TestClient(app)

    # 1. GET /api/v1/system/diagnose/groups
    res_groups = client.get("/api/v1/system/diagnose/groups")
    assert res_groups.status_code == 200
    groups_data = res_groups.json()
    assert len(groups_data) == 4

    # 2. POST /api/v1/system/diagnose/group
    res_group = client.post(
        "/api/v1/system/diagnose/group",
        json={
            "group_id": groups_data[0]["group_id"],
            "title": groups_data[0]["title"],
            "payload": groups_data[0]["payload"],
        },
    )
    assert res_group.status_code == 200
    group_res = res_group.json()
    assert group_res["group_id"] == groups_data[0]["group_id"]

    # 3. POST /api/v1/system/diagnose/synthesize
    res_synth = client.post(
        "/api/v1/system/diagnose/synthesize",
        json={"groups": [group_res]},
    )
    assert res_synth.status_code == 200
    synth_res = res_synth.json()
    assert "health_score" in synth_res
    assert synth_res["groups_evaluated"] == 1
