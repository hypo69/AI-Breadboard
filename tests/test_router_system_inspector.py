# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Router System Inspector
# =============================================================================
# Description:
#   Unit tests for TC System Inspector FastAPI router endpoints.
#
# Usage Examples:
#   CLI:
#     python -m tests.test_router_system_inspector
#   Python API:
#     from tests.test_router_system_inspector import TestSystemInspectorRouter
#
#     service = TestSystemInspectorRouter()
#
# File: test_router_system_inspector.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 00:16:00
# =============================================================================

"""Unit tests for TC System Inspector FastAPI router endpoints."""

import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from apps.windows.api.routers.router_tc import init_router
from apps.windows.api.routers.router_system import init_router as init_system_router


class TestSystemInspectorRouter(unittest.TestCase):
    """Набор тестов для эндпоинтов инспектора системы в TC."""

    def test_get_status(self):
        """Тест эндпоинта /api/v1/tc/status."""
        app = FastAPI()
        app.include_router(init_router())
        test_client = TestClient(app)
        response = test_client.get('/api/v1/tc/status')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('hostname', data)
        self.assertIn('process_count', data)

    def test_get_cpu(self):
        """Тест эндпоинтов /api/v1/tc/cpu и /api/v1/tc/cpu/load."""
        app = FastAPI()
        app.include_router(init_router())
        test_client = TestClient(app)
        response = test_client.get('/api/v1/tc/cpu')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('total_percent', data)
        self.assertIn('physical_cores', data)
        self.assertIn('logical_cores', data)
        self.assertIn('display_val', data)
        self.assertIn('display_cores', data)
        self.assertIn('source', data)

        res_load = test_client.get('/api/v1/tc/cpu/load')
        self.assertEqual(res_load.status_code, 200)
        self.assertEqual(res_load.json()['display_val'], data['display_val'])

    def test_get_cpu_history(self):
        """Тест эндпоинта /api/v1/tc/cpu/history."""
        app = FastAPI()
        app.include_router(init_router())
        test_client = TestClient(app)
        response = test_client.get('/api/v1/tc/cpu/history?limit=10')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('status'), 'ok')
        self.assertIn('history', data)
        self.assertIsInstance(data['history'], list)

    def test_get_system_cpu(self):
        """Тест эндпоинта /api/v1/system/cpu."""
        app = FastAPI()
        app.include_router(init_system_router())
        test_client = TestClient(app)
        response = test_client.get('/api/v1/system/cpu')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('total_percent', data)
        self.assertIn('display_val', data)
        self.assertIn('display_cores', data)

    def test_get_processes(self):
        """Тест эндпоинта /api/v1/tc/processes."""
        app = FastAPI()
        app.include_router(init_router())
        test_client = TestClient(app)
        response = test_client.get('/api/v1/tc/processes?limit=10&sort_by=cpu')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('processes', data)
        self.assertIsInstance(data['processes'], list)

    def test_get_hardware(self):
        """Тест эндпоинта /api/v1/tc/hardware."""
        app = FastAPI()
        app.include_router(init_router())
        test_client = TestClient(app)
        response = test_client.get('/api/v1/tc/hardware')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('hardware', data)
        self.assertIn('sensors', data)

    def test_get_diagnostic(self):
        """Тест эндпоинта /api/v1/tc/diagnostic."""
        app = FastAPI()
        app.include_router(init_router())
        test_client = TestClient(app)
        response = test_client.get('/api/v1/tc/diagnostic?process_limit=15')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('health_score', data)
        self.assertIn('anomalies', data)

    def test_get_hardware_tree(self):
        """Тест эндпоинта /api/v1/tc/hardware/tree."""
        app = FastAPI()
        app.include_router(init_router())
        test_client = TestClient(app)
        response = test_client.get('/api/v1/tc/hardware/tree')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('tree', data)

    def test_get_hardware_sensors(self):
        """Тест эндпоинта /api/v1/tc/hardware/sensors."""
        app = FastAPI()
        app.include_router(init_router())
        test_client = TestClient(app)
        response = test_client.get('/api/v1/tc/hardware/sensors')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('sensors', data)

    def test_trigger_diagnostic(self):
        """Тест эндпоинта /api/v1/tc/trigger-diagnostic."""
        app = FastAPI()
        app.include_router(init_router())
        test_client = TestClient(app)
        response = test_client.post('/api/v1/tc/trigger-diagnostic')
        self.assertIn(response.status_code, [200, 401, 403])

    def test_init_router(self):
        """Тест создания инстанции роутера."""
        router = init_router()
        self.assertIsNotNone(router)
        self.assertEqual(router.prefix, '/api/v1/tc')


if __name__ == '__main__':
    unittest.main()