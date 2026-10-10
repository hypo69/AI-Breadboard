# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Storage_Manager Tests - Test Benchmark
# =============================================================================
# Description:
#   Модульные и интеграционные тесты для сервиса бенчмарка дисков DiskSpd и его REST эндпоинтов.
#
# Usage Examples:
#   pytest apps/windows/modules/storage_manager/tests/test_storage_benchmark.py
#
# File: test_storage_benchmark.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.storage_manager.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 08:16:00
# =============================================================================

from __future__ import annotations
"""Тестирование сервиса бенчмарка дисковой подсистемы DiskSpd."""

import asyncio
from pathlib import Path
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.windows.sdk.modules.storage_manager.core.benchmark import (
    DEFAULT_CDM_PROFILES,
    StorageBenchmarkService,
)
from apps.windows.sdk.modules.storage_manager.core.models import (
    BenchmarkHistoryItem,
    BenchmarkProfileResult,
    BenchmarkRequest,
    BenchmarkSuiteResult,
)
from apps.windows.sdk.modules.storage_manager.router import init_router

_SAMPLE_DISKSPD_XML = """<?xml version="1.0" encoding="utf-8"?>
<Results>
  <TimeSpan>
    <TestTimeSeconds>2.00</TestTimeSeconds>
    <ThreadCount>1</ThreadCount>
    <CpuUtilization>
      <CPU>
        <UsagePercent>25.50</UsagePercent>
      </CPU>
    </CpuUtilization>
    <Latency>
      <AverageReadMilliseconds>0.050</AverageReadMilliseconds>
      <AverageWriteMilliseconds>0.080</AverageWriteMilliseconds>
      <AverageTotalMilliseconds>0.065</AverageTotalMilliseconds>
    </Latency>
    <Thread>
      <Target>
        <ReadBytes>209715200</ReadBytes>
        <WriteBytes>104857600</WriteBytes>
        <ReadCount>51200</ReadCount>
        <WriteCount>25600</WriteCount>
      </Target>
    </Thread>
  </TimeSpan>
</Results>"""


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    """Временный путь к файлу SQLite для тестов."""
    return tmp_path / 'test_benchmarks.db'


@pytest.fixture
def benchmark_service(temp_db: Path) -> StorageBenchmarkService:
    """Экземпляр сервиса с изолированной БД."""
    return StorageBenchmarkService(db_path=temp_db)


@pytest.fixture
def client() -> TestClient:
    """FastAPI тестовый клиент с подключенным роутером хранилища."""
    app = FastAPI()
    app.include_router(init_router())
    return TestClient(app)


def test_find_or_ensure_diskspd_binary(benchmark_service: StorageBenchmarkService):
    """Проверка поиска или загрузки исполняемого файла DiskSpd."""
    bin_path = benchmark_service.find_diskspd_binary()
    assert bin_path is None or bin_path.is_file()

    # ensure должен вернуть валидный путь
    ensured = benchmark_service.ensure_diskspd_binary()
    assert ensured.is_file()
    assert ensured.name.lower() == 'diskspd.exe'


def test_get_available_targets(benchmark_service: StorageBenchmarkService):
    """Проверка обнаружения локальных дисков для бенчмарка."""
    targets = benchmark_service.get_available_targets()
    assert len(targets) > 0
    drives = [t.drive_letter for t in targets]
    assert any('C:' in d for d in drives)
    for t in targets:
        assert t.free_bytes >= 0
        assert t.recommended_dir != ''


def test_parse_xml_results(benchmark_service: StorageBenchmarkService):
    """Проверка корректного парсинга XML вывода DiskSpd."""
    meta = DEFAULT_CDM_PROFILES['seq1m_q8t1']
    res = benchmark_service._parse_xml_results(
        xml_text=_SAMPLE_DISKSPD_XML,
        profile_key='seq1m_q8t1',
        profile_meta=meta,
        is_write_test=False,
    )
    assert res.profile_name == 'seq1m_q8t1'
    assert res.read_mb_s == 100.0  # 200MB / 2s
    assert res.read_iops == 25600.0  # 51200 / 2s
    assert res.read_latency_ms == 0.050
    assert res.read_latency_us == 50.0
    assert res.cpu_usage_pct == 25.5


def test_sqlite_history_crud(benchmark_service: StorageBenchmarkService):
    """Проверка записи, чтения и удаления истории в SQLite."""
    suite = BenchmarkSuiteResult(
        id='bench_test_123',
        target='C:',
        target_path='C:\\test.dat',
        file_size_mb=64,
        test_duration_sec=2,
        test_type='both',
        created_at='2026-10-04 08:00:00',
        completed_at='2026-10-04 08:00:04',
        total_duration_sec=4.2,
        profiles={
            'seq1m_q8t1': BenchmarkProfileResult(
                profile_name='seq1m_q8t1',
                profile_label='SEQ1M Q8T1',
                block_size='1M',
                access_type='Sequential',
                queue_depth=8,
                threads=1,
                read_mb_s=3200.5,
                write_mb_s=2800.0,
                read_iops=3200.5,
                write_iops=2800.0,
            ),
            'rnd4k_q32t16': BenchmarkProfileResult(
                profile_name='rnd4k_q32t16',
                profile_label='RND4K Q32T16',
                block_size='4K',
                access_type='Random',
                queue_depth=32,
                threads=1,
                read_mb_s=450.0,
                write_mb_s=400.0,
                read_iops=115200.0,
                write_iops=102400.0,
            ),
        },
    )

    benchmark_service._save_to_history(suite)
    history = benchmark_service.get_history(limit=10)
    assert len(history) == 1
    assert history[0].id == 'bench_test_123'
    assert history[0].target == 'C:'
    assert history[0].seq1m_read_mb_s == 3200.5
    assert history[0].rnd4k_read_iops == 115200.0

    deleted = benchmark_service.delete_history_item('bench_test_123')
    assert deleted is True
    history_after = benchmark_service.get_history(limit=10)
    assert len(history_after) == 0


def test_rest_endpoints_benchmark(client: TestClient):
    """Проверка REST эндпоинтов управления бенчмарком."""
    resp = client.get('/api/v1/storage/benchmark/engine')
    assert resp.status_code == 200
    engine_data = resp.json()
    assert 'available' in engine_data
    assert engine_data['available'] is True

    resp_targets = client.get('/api/v1/storage/benchmark/targets')
    assert resp_targets.status_code == 200
    targets = resp_targets.json()
    assert isinstance(targets, list)
    assert len(targets) > 0

    resp_hist = client.get('/api/v1/storage/benchmark/history')
    assert resp_hist.status_code == 200
    assert isinstance(resp_hist.json(), list)


@pytest.mark.asyncio
async def test_async_benchmark_task_workflow(benchmark_service: StorageBenchmarkService):
    """Проверка асинхронного запуска и отслеживания задачи бенчмарка."""
    req = BenchmarkRequest(
        target_drive='C:',
        file_size_mb=10,
        duration_sec=1,
        profiles=['seq1m_q8t1'],
        test_type='read',
        delete_test_file=True,
    )
    task = await benchmark_service.start_async_benchmark(req)
    assert task.task_id.startswith('task_bench_')
    assert task.status == 'running'

    # Ожидаем завершения
    for _ in range(25):
        await asyncio.sleep(0.5)
        st = benchmark_service.get_task_status(task.task_id)
        if st and st.status in ('completed', 'failed', 'cancelled'):
            break

    final_task = benchmark_service.get_task_status(task.task_id)
    assert final_task is not None
    assert final_task.status in ('completed', 'failed')
    if final_task.status == 'completed':
        assert final_task.progress_percent == 100.0


def test_storage_benchmark_sensor_quick_run(benchmark_service: StorageBenchmarkService):
    """Проверка работы сенсора телеметрии StorageBenchmarkSensor."""
    from apps.windows.sdk.modules.storage_manager.core.benchmark_sensor import StorageBenchmarkSensor
    sensor = StorageBenchmarkSensor(benchmark_service=benchmark_service)
    res = sensor.run_quick_benchmark(target_drives=['C:'], file_size_mb=10, duration_sec=1, test_type='read')
    assert res is not None
    assert 'results' in res
    assert 'C:' in res['results']
    c_res = res['results']['C:']
    assert c_res.get('status') == 'ok'
    assert c_res.get('seq_read_mb_s', 0) > 0


@pytest.mark.asyncio
async def test_scenario_run_includes_disk_telemetry():
    """Проверка включения шага телеметрии бенчмарка дисков при запуске сценария."""
    from apps.windows.api.routers.router_scenarios import ScenarioRunRequest, init_router as init_scenarios_router
    app = FastAPI()
    app.include_router(init_scenarios_router())
    sc_client = TestClient(app)

    # 1. Запуск сценария quick_check
    resp = sc_client.post('/api/v1/scenarios/run', json={'scenario_id': 'quick_check'})
    assert resp.status_code == 200
    data = resp.json()
    assert 'steps' in data
    step_names = [s['name'] for s in data['steps']]
    assert any('Телеметрия дисков: Экспресс-бенчмарк (DiskSpd)' in name for name in step_names)

    # 2. Запуск выделенного сценария disk_benchmark_audit
    resp_bench = sc_client.post('/api/v1/scenarios/run', json={'scenario_id': 'disk_benchmark_audit'})
    assert resp_bench.status_code == 200
    bench_data = resp_bench.json()
    assert bench_data['scenario_id'] == 'disk_benchmark_audit'
    assert len(bench_data['steps']) >= 1

