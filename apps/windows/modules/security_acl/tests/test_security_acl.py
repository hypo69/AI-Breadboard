# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Security_Acl Tests - Test Security Acl
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.security_acl.tests.test_security_acl import manager
#
#     res = manager()
#
# File: test_security_acl.py
# Project: ai-breadboard
# Package: apps.windows.modules.security_acl.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from apps.windows.modules.security_acl.core.manager import SecurityAclManager
from apps.windows.modules.security_acl.core.models import AclModifyRequest
from apps.windows.modules.security_acl.router import init_router


@pytest.fixture
def manager() -> SecurityAclManager:
    return SecurityAclManager()


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(init_router())
    return TestClient(app)


def test_security_acl_report(manager: SecurityAclManager):
    """Проверка генерации отчета безопасности."""
    report = manager.generate_report()
    assert report is not None
    assert len(report.bitlocker_volumes) > 0
    assert report.efs_enabled is True


@pytest.mark.asyncio
async def test_acl_modify_simulation(manager: SecurityAclManager):
    """Проверка симуляции изменения прав ACL."""
    req = AclModifyRequest(
        target_path='C:\\Windows\\Temp',
        principal='Users',
        permission='Read',
        action='grant',
        dry_run=True,
        confirmed_by_user=False
    )
    res = await manager.execute_acl_modification(req)
    assert res['status'] == 'DRY_RUN_SUCCESS'


def test_security_acl_endpoints(client: TestClient):
    """Проверка REST эндпоинтов security_acl."""
    resp = client.get('/api/security-acl/report')
    assert resp.status_code == 200
    data = resp.json()
    assert 'bitlocker_volumes' in data

    resp_bitlocker = client.get('/api/security-acl/bitlocker')
    assert resp_bitlocker.status_code == 200

    resp_acl = client.get('/api/security-acl/acl?path=C:\\Windows')
    assert resp_acl.status_code == 200
    assert len(resp_acl.json()) > 0
