# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Firewall_Manager Tests - Test Firewall Manager
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.firewall_manager.tests.test_firewall_manager import manager
#
#     res = manager()
#
# File: test_firewall_manager.py
# Project: ai-breadboard
# Package: apps.windows.modules.firewall_manager.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from apps.windows.modules.firewall_manager.core.manager import FirewallManager
from apps.windows.modules.firewall_manager.core.models import FirewallRuleActionRequest
from apps.windows.modules.firewall_manager.router import init_router


@pytest.fixture
def manager() -> FirewallManager:
    return FirewallManager()


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(init_router())
    return TestClient(app)


def test_firewall_report(manager: FirewallManager):
    """Проверка генерации отчета брандмауэра."""
    report = manager.generate_report()
    assert report is not None
    assert len(report.profiles) == 3
    assert report.total_rules > 0


@pytest.mark.asyncio
async def test_firewall_rule_simulation(manager: FirewallManager):
    """Проверка симуляции безопасного действия с правилом."""
    req = FirewallRuleActionRequest(
        rule_name='AI-Breadboard Test Rule',
        action='add',
        port='9000',
        dry_run=True,
        confirmed_by_user=False
    )
    res = await manager.execute_rule_action(req)
    assert res['status'] == 'DRY_RUN_SUCCESS'


def test_firewall_endpoints(client: TestClient):
    """Проверка REST эндпоинтов firewall_manager."""
    resp = client.get('/api/firewall-manager/report')
    assert resp.status_code == 200
    data = resp.json()
    assert 'profiles' in data
    assert 'rules' in data

    resp_profiles = client.get('/api/firewall-manager/profiles')
    assert resp_profiles.status_code == 200
    assert len(resp_profiles.json()) == 3
