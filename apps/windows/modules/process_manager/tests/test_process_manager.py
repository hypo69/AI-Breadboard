# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Process_Manager Tests - Test Process Manager
# =============================================================================
# Description:
#   Тесты для проверки функционала диспетчера процессов, категоризации
#   Apps / Background processes / Windows processes и REST эндпоинтов.
#
# Usage Examples:
#   pytest apps/windows/modules/process_manager/tests/test_process_manager.py
#
# File: test_process_manager.py
# Project: ai-breadboard
# Package: apps.windows.modules.process_manager.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 02:10:00
# =============================================================================

from __future__ import annotations
"""Тесты диспетчера и классификатора процессов Windows."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from apps.windows.modules.process_manager.core.classifier import ProcessClassifier
from apps.windows.modules.process_manager.core.manager import ProcessManager
from apps.windows.modules.process_manager.core.models import ProcessKillRequest
from apps.windows.modules.process_manager.router import init_router


@pytest.fixture
def manager() -> ProcessManager:
    return ProcessManager()


@pytest.fixture
def classifier() -> ProcessClassifier:
    return ProcessClassifier()


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(init_router())
    return TestClient(app)


def test_process_classifier(classifier: ProcessClassifier):
    """Проверка работы классификатора процессов."""
    report = classifier.classify_processes()
    assert report is not None
    assert report.total_processes > 0
    assert report.apps_count >= 0
    assert report.background_count >= 0
    assert report.windows_count >= 0
    assert len(report.apps) == report.apps_count
    assert len(report.background_processes) == report.background_count
    assert len(report.windows_processes) == report.windows_count


def test_process_manager_report(manager: ProcessManager):
    """Проверка генерации отчета процессов с категориями."""
    report = manager.generate_report()
    assert report is not None
    assert report.total_processes > 0
    assert len(report.processes) > 0
    assert hasattr(report, 'apps')
    assert hasattr(report, 'background_processes')
    assert hasattr(report, 'windows_processes')


@pytest.mark.asyncio
async def test_process_kill_simulation(manager: ProcessManager):
    """Проверка симуляции завершения процесса."""
    req = ProcessKillRequest(
        pid=999999,
        kill_tree=True,
        dry_run=True,
        confirmed_by_user=False
    )
    res = await manager.kill_process(req)
    assert res['status'] == 'DRY_RUN_SUCCESS'


def test_process_manager_endpoints(client: TestClient):
    """Проверка REST эндпоинтов process_manager."""
    resp = client.get('/api/process-manager/report')
    assert resp.status_code == 200
    data = resp.json()
    assert 'total_processes' in data
    assert 'processes' in data
    assert 'apps' in data
    assert 'background_processes' in data

    resp_cat = client.get('/api/process-manager/categorized')
    assert resp_cat.status_code == 200
    cat_data = resp_cat.json()
    assert 'apps' in cat_data
    assert 'background_processes' in cat_data
    assert 'windows_processes' in cat_data
    assert 'apps_count' in cat_data

    resp_list = client.get('/api/process-manager/list')
    assert resp_list.status_code == 200
    assert len(resp_list.json()) > 0
