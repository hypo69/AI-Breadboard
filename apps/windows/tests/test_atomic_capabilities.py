# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Tests - Test Atomic Capabilities
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.tests.test_atomic_capabilities import registry
#
#     res = registry()
#
# File: test_atomic_capabilities.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.windows.sdk.core.atomic_capabilities import get_atomic_registry, WindowsAtomicCapabilitiesRegistry
from apps.windows.sdk.core.atomic_models import (
    AtomicOperationExecutionRequest,
    CapabilityCategory,
    PrivilegeLevel,
    RiskLevel,
)
from apps.windows.api.router_capabilities import init_router


@pytest.fixture
def registry() -> WindowsAtomicCapabilitiesRegistry:
    """Фикстура получения реестра атомарных возможностей."""
    return get_atomic_registry()


@pytest.fixture
def test_client() -> TestClient:
    """Фикстура тестового клиента FastAPI с подключенным роутером возможностей."""
    app = FastAPI()
    app.include_router(init_router())
    return TestClient(app)


def test_registry_has_all_17_categories(registry: WindowsAtomicCapabilitiesRegistry):
    """Проверка присутствия операций во всех 17 категориях."""
    for cat in CapabilityCategory:
        ops = registry.get_operations_by_category(cat)
        assert len(ops) > 0, f"Категория {cat.value} не содержит зарегистрированных операций"


def test_registry_utilities_coverage(registry: WindowsAtomicCapabilitiesRegistry):
    """Проверка покрытия всех ключевых консольных утилит Windows."""
    required_utilities = [
        'diskpart', 'fsutil', 'mountvol', 'chkdsk',
        'bcdedit', 'bcdboot', 'reagentc',
        'sfc', 'dism',
        'pnputil', 'driverquery',
        'tasklist', 'taskkill',
        'schtasks',
        'logman', 'typeperf',
        'sc',
        'wevtutil',
        'ipconfig', 'netstat', 'route',
        'advfirewall',
        'icacls', 'manage-bde',
        'reg', 'gpupdate', 'gpresult',
        'net.exe user', 'whoami',
        'vssadmin',
        'powercfg', 'systeminfo',
        'winget'
    ]

    all_ops = registry.get_all_operations()
    found_utils = " ".join(o.utility.lower() for o in all_ops)
    for u in required_utilities:
        assert u.lower() in found_utils, f"Утилита {u} отсутствует в зарегистрированных операциях"


def test_tree_generation(registry: WindowsAtomicCapabilitiesRegistry):
    """Проверка генерации иерархических деревьев по утилитам и категориям."""
    util_tree = registry.get_tree()
    assert isinstance(util_tree, dict)
    assert len(util_tree) > 0
    assert 'diskpart.exe' in util_tree
    assert any(op['id'] == 'diskpart.disk.list' for op in util_tree['diskpart.exe'])

    cat_tree = registry.get_categories_tree()
    assert isinstance(cat_tree, dict)
    assert 'storage_fs' in cat_tree
    assert 'diskpart.exe' in cat_tree['storage_fs']


@pytest.mark.asyncio
async def test_dry_run_execution(registry: WindowsAtomicCapabilitiesRegistry):
    """Проверка симуляции (Dry-Run) опасной операции."""
    req = AtomicOperationExecutionRequest(
        operation_id='diskpart.disk.clean',
        parameters={'disk_id': 1},
        dry_run=True,
        confirmed_by_user=False
    )
    res = await registry.execute_operation(req)
    assert res.is_dry_run is True
    assert res.status == 'DRY_RUN_SIMULATED'
    assert 'diskpart' in res.command_executed
    assert res.risk_level == RiskLevel.CRITICAL.value


@pytest.mark.asyncio
async def test_high_risk_requires_confirmation(registry: WindowsAtomicCapabilitiesRegistry):
    """Проверка требования подтверждения для критических операций в боевом режиме."""
    req = AtomicOperationExecutionRequest(
        operation_id='diskpart.disk.clean',
        parameters={'disk_id': 1},
        dry_run=False,
        confirmed_by_user=False
    )
    res = await registry.execute_operation(req)
    assert res.is_dry_run is False
    assert res.status == 'CONFIRMATION_REQUIRED'


def test_api_catalog_endpoint(test_client: TestClient):
    """Проверка эндпоинта /api/v1/capabilities/catalog."""
    resp = test_client.get('/api/v1/capabilities/catalog')
    assert resp.status_code == 200
    data = resp.json()
    assert data['total'] > 0
    assert len(data['operations']) == data['total']


def test_api_tree_endpoint(test_client: TestClient):
    """Проверка эндпоинта /api/v1/capabilities/tree."""
    resp = test_client.get('/api/v1/capabilities/tree?group_by=utility')
    assert resp.status_code == 200
    data = resp.json()
    assert 'tree' in data
    assert 'diskpart.exe' in data['tree']


def test_api_categories_endpoint(test_client: TestClient):
    """Проверка эндпоинта /api/v1/capabilities/categories."""
    resp = test_client.get('/api/v1/capabilities/categories')
    assert resp.status_code == 200
    data = resp.json()
    assert data['total'] == 17
    assert len(data['categories']) == 17


def test_api_utility_operations_endpoint(test_client: TestClient):
    """Проверка эндпоинта /api/v1/capabilities/utilities/{utility}."""
    resp = test_client.get('/api/v1/capabilities/utilities/diskpart')
    assert resp.status_code == 200
    data = resp.json()
    assert data['utility'] == 'diskpart'
    assert data['total'] > 0


def test_api_execute_simulation(test_client: TestClient):
    """Проверка POST /api/v1/capabilities/execute с симуляцией."""
    payload = {
        'operation_id': 'fsutil.fs.trim_query',
        'parameters': {},
        'dry_run': True,
        'confirmed_by_user': False
    }
    resp = test_client.post('/api/v1/capabilities/execute', json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data['status'] == 'DRY_RUN_SIMULATED'
    assert data['operation_id'] == 'fsutil.fs.trim_query'
