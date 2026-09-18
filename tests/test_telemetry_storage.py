# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Telemetry Storage and Logger Unit Tests
# =============================================================================
# Description:
#   Тестирование SQLite хранилища телеметрии, сервиса сбора метрик 1 Гц
#   и REST API эндпоинтов управления логгером.
#
# File: test_telemetry_storage.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import time
import pytest
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.windows.telemetry.models import (
    CpuMetrics,
    DiskIoMetrics,
    MemoryMetrics,
    NetworkInterfaceMetrics,
    ProcessMetrics,
    SystemSnapshot,
)
from apps.windows.telemetry.storage import TelemetryStorage
from apps.windows.telemetry.service import TelemetryLoggerService
from src.api.router_system import init_router


@pytest.fixture
def temp_storage(tmp_path: Path):
    """Создает временное хранилище SQLite в изолированной директории."""
    db_file = tmp_path / "test_telemetry.db"
    return TelemetryStorage(db_path=db_file)


@pytest.fixture
def sample_snapshot():
    """Формирует тестовый снимок системы с 25 процессами."""
    procs = [
        ProcessMetrics(
            pid=1000 + i,
            name=f"process_{i}.exe",
            cpu_percent=round(float(25 - i), 1),
            memory_mb=round(float(100 + i * 10), 1),
            memory_percent=1.5,
            num_threads=4,
            username="SYSTEM",
            read_bytes_sec=1024.0 * i,
            write_bytes_sec=512.0 * i,
        )
        for i in range(25)
    ]

    return SystemSnapshot(
        hostname="TEST-WORKSTATION",
        uptime_seconds=3600.0,
        cpu=CpuMetrics(
            model="AMD Ryzen Test Core",
            total_percent=42.5,
            frequency_mhz=3800.0,
            physical_cores=8,
            logical_cores=16,
        ),
        memory=MemoryMetrics(
            total_gb=32.0,
            used_gb=12.5,
            percent=39.0,
            swap_percent=10.0,
        ),
        disk_io=DiskIoMetrics(
            read_bytes_per_sec=1048576.0,
            write_bytes_per_sec=2097152.0,
            read_count_per_sec=120.0,
            write_count_per_sec=240.0,
        ),
        network=[
            NetworkInterfaceMetrics(
                name="Ethernet",
                is_up=True,
                speed_mbps=1000,
                bytes_sent_per_sec=50000.0,
                bytes_recv_per_sec=150000.0,
            )
        ],
        top_processes=procs,
    )


class TestTelemetryStorage:
    """Тестирование функциональности SQLite хранилища TelemetryStorage."""

    def test_save_snapshot_and_top_processes(self, temp_storage: TelemetryStorage, sample_snapshot: SystemSnapshot):
        """Проверка сохранения снимка системы и ограничения среза до 20 процессов."""
        snap_id = temp_storage.save_snapshot(sample_snapshot, top_n=20)
        assert snap_id > 0

        # Проверяем извлечение снапшота
        snapshots = temp_storage.get_snapshots(limit=10)
        assert len(snapshots) == 1
        s = snapshots[0]
        assert s["id"] == snap_id
        assert s["hostname"] == "TEST-WORKSTATION"
        assert s["cpu_total_percent"] == 42.5
        assert s["memory_percent"] == 39.0
        assert s["disk_read_bytes_sec"] == 1048576.0
        assert s["disk_write_bytes_sec"] == 2097152.0
        assert s["network_sent_bytes_sec"] == 50000.0
        assert s["network_recv_bytes_sec"] == 150000.0

        # Проверяем процессы снимка (должно быть ровно 20)
        procs = temp_storage.get_snapshot_processes(snap_id)
        assert len(procs) == 20
        assert procs[0]["name"] == "process_0.exe"
        assert procs[0]["cpu_percent"] == 25.0

    def test_get_process_history(self, temp_storage: TelemetryStorage, sample_snapshot: SystemSnapshot):
        """Проверка выборки истории конкретного процесса."""
        temp_storage.save_snapshot(sample_snapshot, top_n=20)
        
        history_name = temp_storage.get_process_history(name="process_0.exe")
        assert len(history_name) == 1
        assert history_name[0]["name"] == "process_0.exe"
        assert history_name[0]["pid"] == 1000

        history_pid = temp_storage.get_process_history(pid=1000)
        assert len(history_pid) == 1
        assert history_pid[0]["pid"] == 1000

    def test_storage_stats_and_cleanup(self, temp_storage: TelemetryStorage, sample_snapshot: SystemSnapshot):
        """Проверка подсчета статистики хранилища и очистки записей."""
        temp_storage.save_snapshot(sample_snapshot, top_n=20)
        stats = temp_storage.get_storage_stats()
        assert stats["snapshots_count"] == 1
        assert stats["process_snapshots_count"] == 20
        assert stats["file_size_mb"] >= 0.0

        # Очистка записей (порог 0 дней удалит всё)
        deleted = temp_storage.cleanup_old_records(retention_days=0)
        assert deleted == 1

        stats_after = temp_storage.get_storage_stats()
        assert stats_after["snapshots_count"] == 0
        assert stats_after["process_snapshots_count"] == 0


class TestTelemetryLoggerService:
    """Тестирование жизненного цикла сервиса TelemetryLoggerService."""

    def test_service_start_stop(self, temp_storage: TelemetryStorage, sample_snapshot: SystemSnapshot):
        """Проверка корректного старта и остановки сервиса."""
        from unittest.mock import MagicMock

        mock_collector = MagicMock()
        mock_collector.get_snapshot.return_value = sample_snapshot

        service = TelemetryLoggerService(
            interval_sec=0.1,
            top_processes=10,
            storage=temp_storage,
            collector=mock_collector,
        )
        assert not service.is_running

        started = service.start()
        assert started is True
        assert service.is_running is True

        # Ожидаем хотя бы 1 тика
        for _ in range(30):
            if service.get_status()["ticks_recorded"] >= 1:
                break
            time.sleep(0.05)

        status = service.get_status()
        assert status["is_running"] is True
        assert status["ticks_recorded"] >= 1

        stopped = service.stop()
        assert stopped is True
        assert service.is_running is False



class TestSystemTelemetryRouterEndpoints:
    """Тестирование REST API роутера /api/v1/system/logger/*."""

    @pytest.fixture
    def client(self):
        """FastAPI TestClient с инициализированным роутером системы."""
        app = FastAPI()
        app.include_router(init_router())
        return TestClient(app)

    def test_logger_status_endpoint(self, client: TestClient):
        """Проверка эндпоинта GET /api/v1/system/logger/status."""
        response = client.get("/api/v1/system/logger/status")
        assert response.status_code == 200
        data = response.json()
        assert "is_running" in data
        assert "interval_sec" in data
        assert "storage" in data

    def test_logger_history_endpoint(self, client: TestClient):
        """Проверка эндпоинта GET /api/v1/system/logger/history."""
        response = client.get("/api/v1/system/logger/history?limit=10")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_logger_processes_endpoint(self, client: TestClient):
        """Проверка эндпоинта GET /api/v1/system/logger/processes."""
        response = client.get("/api/v1/system/logger/processes?limit=10")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_logger_start_stop_cycle(self, client: TestClient):
        """Проверка вызовов start и stop через REST API."""
        start_res = client.post("/api/v1/system/logger/start?interval_sec=1.0&top_processes=20")
        assert start_res.status_code == 200
        assert start_res.json()["success"] is True

        stop_res = client.post("/api/v1/system/logger/stop")
        assert stop_res.status_code == 200
        assert stop_res.json()["success"] is True
