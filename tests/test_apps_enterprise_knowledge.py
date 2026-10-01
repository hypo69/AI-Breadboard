# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Apps Enterprise Knowledge
# =============================================================================
# Description:
#   Проверки локального ядра Enterprise Knowledge Platform.
#
# Usage Examples:
#   Python API:
#     from tests.test_apps_enterprise_knowledge import test_ingestion_resolves_identity_and_is_idempotent
#
#     res = test_ingestion_resolves_identity_and_is_idempotent()
#
# File: test_apps_enterprise_knowledge.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

from __future__ import annotations
"""Проверки локального ядра Enterprise Knowledge Platform."""

from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
from apps.enterprise_knowledge.engine import EnterpriseKnowledgeEngine
from apps.enterprise_knowledge.routers.router import init_router

def _event() -> dict:
    return {'event_id': 'EVT-10001', 'source': {'type': 'email', 'external_id': 'EMAIL-1001'}, 'occurred_at': '2026-09-21T10:30:00Z', 'content': {'text': 'Проверь API до пятницы.'}, 'facts': [{'subject': 'a.petrov@company.com', 'predicate': 'assigned_task', 'object': 'Проверка API'}]}

def test_ingestion_resolves_identity_and_is_idempotent(tmp_path: Path) -> None:
    engine = EnterpriseKnowledgeEngine(str(tmp_path / 'knowledge.db'))
    engine.register_employee({'employee_id': 'EMP-0042', 'name': 'Александр Петров', 'email': 'a.petrov@company.com'})
    assert engine.ingest(_event())['facts_created'] == 1
    assert engine.ingest(_event())['status'] == 'duplicate'
    profile = engine.employee('EMP-0042')
    assert profile is not None
    assert profile['facts'][0]['employee_id'] == 'EMP-0042'

def test_query_applies_employee_filter(tmp_path: Path) -> None:
    engine = EnterpriseKnowledgeEngine(str(tmp_path / 'knowledge.db'))
    engine.register_employee({'employee_id': 'EMP-0042', 'name': 'Александр Петров', 'email': 'a.petrov@company.com'})
    engine.register_employee({'employee_id': 'EMP-0043', 'name': 'Анна Смирнова', 'email': 'a.smirnova@company.com'})
    engine.ingest(_event())
    other_event = _event() | {'event_id': 'EVT-10002', 'facts': [{'employee_id': 'EMP-0043', 'predicate': 'assigned_task', 'object': 'Проверка API'}]}
    engine.ingest(other_event)
    result = engine.query('API', employee_id='EMP-0042')
    assert len(result['facts']) == 1
    assert result['facts'][0]['employee_id'] == 'EMP-0042'

def test_router_can_be_used_as_standalone_app(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv('ENTERPRISE_KNOWLEDGE_DB', str(tmp_path / 'knowledge.db'))
    app = FastAPI()
    app.include_router(init_router())
    client = TestClient(app)
    response = client.get('/api/v1/enterprise-knowledge/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}