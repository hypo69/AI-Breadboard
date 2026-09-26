# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit Tests for System and Hardware Inspector
# =============================================================================
# Description:
#   Unit and integration tests for System telemetry collector, hardware tree,
#   sensors prober, AI diagnostics, Rich TUI, and FastAPI endpoints.
#
# File: test_system_inspector.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Unit and integration tests for System & Hardware Inspector."""

import asyncio
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.system_inspector.tui import SystemInspectorState, render_ui
from src.api.router_system import init_router
from apps.windows.telemetry import (
    # (используйте src.ai.observability.system_engine для SystemDiagnosticEngine)

    CpuMetrics,
    GpuMetrics,
    HardwareNode,
    HardwareSensor,
    MemoryMetrics,
    ProcessMetrics,
    SystemDiagnosticEngine,
    SystemCollector,
    SystemSnapshot,
    get_hardware_sensors,
)


class TestSystemTelemetryCollector:
    """Test suite for SystemCollector core metrics engine."""

    @pytest.fixture
    def collector(self) -> SystemCollector:
        return SystemCollector()

    def test_cpu_metrics_collection(self, collector: SystemCollector):
        cpu = asyncio.run(collector.get_cpu_metrics())
        assert isinstance(cpu, CpuMetrics)
        assert cpu.logical_cores >= 1
        assert cpu.physical_cores >= 1
        assert 0.0 <= cpu.total_percent <= 100.0
        assert isinstance(cpu.per_core_percent, list)

    def test_memory_metrics_collection(self, collector: SystemCollector):
        mem = collector.get_memory_metrics()
        assert isinstance(mem, MemoryMetrics)
        assert mem.total_gb > 0.0
        assert mem.available_gb >= 0.0
        assert 0.0 <= mem.percent <= 100.0

    def test_gpu_metrics_collection(self, collector: SystemCollector):
        gpus = collector.get_gpu_metrics()
        assert isinstance(gpus, list)
        assert len(gpus) >= 1
        assert isinstance(gpus[0], GpuMetrics)

    def test_disk_metrics_collection(self, collector: SystemCollector):
        partitions, disk_io = collector.get_disk_metrics()
        assert isinstance(partitions, list)
        assert len(partitions) >= 1
        assert partitions[0].total_gb > 0.0
        assert disk_io.read_bytes_per_sec >= 0.0

    def test_network_metrics_collection(self, collector: SystemCollector):
        net = collector.get_network_metrics()
        assert isinstance(net, list)
        assert len(net) >= 1

    def test_top_processes_sorting(self, collector: SystemCollector):
        procs_cpu = collector.get_top_processes(limit=10, sort_by="cpu")
        assert isinstance(procs_cpu, list)
        assert len(procs_cpu) <= 10
        if len(procs_cpu) >= 2:
            assert procs_cpu[0].cpu_percent >= procs_cpu[-1].cpu_percent

        procs_mem = collector.get_top_processes(limit=10, sort_by="memory")
        assert isinstance(procs_mem, list)
        if len(procs_mem) >= 2:
            assert procs_mem[0].memory_mb >= procs_mem[-1].memory_mb

        procs_handles = collector.get_top_processes(limit=10, sort_by="handles")
        assert isinstance(procs_handles, list)
        if len(procs_handles) >= 2:
            assert procs_handles[0].num_handles >= procs_handles[-1].num_handles

        procs_all = collector.get_top_processes(limit=0, sort_by="cpu")
        assert isinstance(procs_all, list)
        assert len(procs_all) >= len(procs_cpu)

    def test_office_metrics_collection(self, collector: SystemCollector):
        office = collector.get_ms_office_info()
        assert office is not None
        assert isinstance(office.installed, bool)
        assert isinstance(office.status, str)

    def test_onedrive_metrics_collection(self, collector: SystemCollector):
        od = collector.get_onedrive_info()
        assert od is not None
        assert isinstance(od.installed, bool)
        assert isinstance(od.status, str)

    def test_snapshot_aggregation(self, collector: SystemCollector):
        snap = asyncio.run(collector.get_snapshot(process_limit=5))
        assert isinstance(snap, SystemSnapshot)
        assert snap.hostname != ""
        assert snap.cpu.logical_cores >= 1
        assert snap.memory.total_gb > 0
        assert snap.office is not None
        assert snap.onedrive is not None
        assert len(snap.top_processes) <= 5

    def test_hardware_tree_generation(self, collector: SystemCollector):
        tree = asyncio.run(collector.get_hardware_tree_async())
        assert isinstance(tree, list)
        assert len(tree) >= 5
        categories = [node.category for node in tree]
        assert "System" in categories
        assert "Processor (CPU)" in categories
        assert "System Memory" in categories
        assert "Network Adapter" in categories

        # Проверка расширенных свойств сетевых адаптеров
        net_nodes = [n for n in tree if n.category == "Network Adapter"]
        assert len(net_nodes) > 0
        for net in net_nodes:
            assert "Имя подключения" in net.properties
            assert "Производитель" in net.properties
            assert "Тип адаптера" in net.properties
            assert "Физический (MAC) адрес" in net.properties
            assert "Состояние соединения" in net.properties
            assert "Скорость канала" in net.properties


class TestHardwareSensors:
    """Test suite for sensor probers."""

    def test_get_hardware_sensors_returns_list(self):
        sensors = get_hardware_sensors()
        assert isinstance(sensors, list)
        for s in sensors:
            assert isinstance(s, HardwareSensor)
            assert isinstance(s.unit, str)


class TestAIDiagnostician:
    """Test suite for heuristic and AI diagnostic logic."""

    @pytest.fixture
    def diagnostician(self) -> SystemDiagnosticEngine:
        return SystemDiagnosticEngine()

    def test_heuristic_evaluation_nominal(self, diagnostician: SystemDiagnosticEngine):
        snap = SystemSnapshot(
            hostname="test-host",
            cpu=CpuMetrics(total_percent=15.0),
            memory=MemoryMetrics(percent=45.0, total_gb=32.0, used_gb=14.4),
        )
        score, anomalies, recs = diagnostician.evaluate_heuristics(snap)
        assert score == 100
        assert len(anomalies) == 0

    def test_heuristic_evaluation_critical_bottlenecks(self, diagnostician: SystemDiagnosticEngine):
        snap = SystemSnapshot(
            hostname="test-host",
            cpu=CpuMetrics(total_percent=95.0),
            memory=MemoryMetrics(percent=96.0, total_gb=16.0, used_gb=15.5),
            sensors=[HardwareSensor(sensor_id="temp1", name="CPU Package", value=92.0, unit="°C")],
            top_processes=[ProcessMetrics(pid=999, name="runaway.exe", cpu_percent=80.0, memory_mb=2000.0)],
        )
        score, anomalies, recs = diagnostician.evaluate_heuristics(snap)
        assert score < 60
        assert len(anomalies) >= 3
        subsystems = [a.subsystem for a in anomalies]
        assert "CPU" in subsystems
        assert "RAM" in subsystems
        assert "Thermals" in subsystems

    def test_diagnose_report_structure(self, diagnostician: SystemDiagnosticEngine):
        snap = SystemSnapshot(
            hostname="test-host",
            cpu=CpuMetrics(total_percent=20.0),
            memory=MemoryMetrics(percent=50.0, total_gb=32.0, used_gb=16.0),
        )
        report = asyncio.run(diagnostician.diagnose(snap))
        assert report.health_score == 100
        assert "Health score: 100/100" in report.summary


class TestSystemInspectorTUI:
    """Test suite for Rich TUI layout renderer."""

    def test_tui_state_and_render(self):
        from apps.system_inspector.tui import RICH_AVAILABLE

        state = SystemInspectorState(sort_by="cpu", process_limit=5)
        asyncio.run(state.refresh())
        assert state.latest_snapshot is not None
        assert state.latest_report is not None

        layout = render_ui(state)
        if RICH_AVAILABLE:
            assert layout is not None
        else:
            assert layout is None


class TestSystemInspectorFastAPI:
    """Test suite for FastAPI REST endpoints."""

    @pytest.fixture
    def client(self) -> TestClient:
        app = FastAPI()
        app.include_router(init_router())
        return TestClient(app)

    def test_get_summary_endpoint(self, client: TestClient):
        response = client.get("/api/v1/system/summary")
        assert response.status_code == 200
        data = response.json()
        assert "hostname" in data
        assert "cpu" in data
        assert "memory" in data

    def test_get_processes_endpoint(self, client: TestClient):
        response = client.get("/api/v1/system/processes?limit=10&sort_by=cpu")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10

    def test_get_hardware_endpoint(self, client: TestClient):
        response = client.get("/api/v1/system/hardware")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_get_sensors_endpoint(self, client: TestClient):
        response = client.get("/api/v1/system/sensors")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_post_diagnose_endpoint(self, client: TestClient):
        """Проверка эндпоинта диагностики системы."""
        response = client.post("/api/v1/system/diagnose", json={})
        assert response.status_code == 200
        data = response.json()
        assert "health_score" in data
        assert "summary" in data

    def test_websocket_stream_endpoint(self, client: TestClient):
        """Проверка WebSocket потока телеметрии."""
        with client.websocket_connect("/api/v1/system/stream") as websocket:
            data = websocket.receive_json()
            assert "hostname" in data
            assert "cpu" in data
            assert "memory" in data
            assert "network_activity" in data

    def test_get_network_activity_endpoint(self, client: TestClient):
        """Проверка эндпоинта /api/v1/system/network-activity."""
        response = client.get("/api/v1/system/network-activity?limit=15")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if data:
            item = data[0]
            assert "pid" in item
            assert "name" in item
            assert "remote_address" in item
            assert "protocol" in item
            assert "sent_summary" in item
            assert "recv_summary" in item

    def test_get_processes_from_db_endpoint(self, client: TestClient):
        """Проверка получения процессов из SQLite базы данных."""
        response = client.get("/api/v1/system/processes?limit=10&source=db")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if data:
            proc = data[0]
            assert "pid" in proc
            assert "name" in proc
            assert "cpu_percent" in proc
            assert "memory_mb" in proc

    def test_get_processes_stats_endpoint(self, client: TestClient):
        """Проверка эндпоинта статистики процессов."""
        response = client.get("/api/v1/system/processes/stats?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "rollups_2min" in data
        assert "daily_stats" in data
        assert "outliers" in data

    def test_post_processes_rollup_endpoint(self, client: TestClient):
        """Проверка запуска роллапа процессов через API."""
        response = client.post("/api/v1/system/processes/rollup?cutoff_seconds=120&outlier_cpu_threshold=30.0")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert "rollup_2min" in data
        assert "rollup_daily" in data

    def test_get_core_metrics_endpoint(self, client: TestClient):
        """Проверка быстрого эндпоинта /api/v1/system/metrics/core."""
        response = client.get("/api/v1/system/metrics/core")
        assert response.status_code == 200
        data = response.json()
        assert "cpu" in data
        assert "memory" in data
        assert "disk_io" in data
        assert "battery" in data
        assert "uptime_seconds" in data

    def test_get_hardware_quick_endpoint(self, client: TestClient):
        """Проверка экспресс-эндпоинта /api/v1/system/hardware/quick."""
        response = client.get("/api/v1/system/hardware/quick")
        assert response.status_code == 200
        data = response.json()
        assert "ram_sticks" in data
        assert "physical_disks" in data
        assert "listening_ports" in data
        assert "alerts" in data



