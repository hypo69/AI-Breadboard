# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Tests - Test Api
# =============================================================================
# Description:
#   Модульные тесты для низкоуровневых обёрток Win32 (Kernel32, Psapi)
#
# Usage Examples:
#   CLI:
#     python -m apps.windows.tests.test_api
#   Python API:
#     from apps.windows.tests.test_api import TestKernel32API
#
#     service = TestKernel32API()
#
# File: test_api.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Модульные тесты для низкоуровневых обёрток Win32 (Kernel32, Psapi)"""

import unittest
from apps.windows.telemetry.win32_ffi import Kernel32API, PsapiAPI


class TestKernel32API(unittest.TestCase):
    """Тестирование низкоуровневого API Kernel32."""

    def setUp(self):
        """Подготовка тестового окружения."""
        self.api = Kernel32API()

    def test_api_initialization(self):
        """Проверка инициализации хэндлов Win32 DLL."""
        self.assertIsNotNone(self.api.kernel32)

    def test_enumerate_processes(self):
        """Проверка перечисления запущенных процессов."""
        processes = self.api.enumerate_processes()
        self.assertIsInstance(processes, list)
        self.assertGreater(len(processes), 0)


class TestPsapiAPI(unittest.TestCase):
    """Тестирование PSAPI."""

    def setUp(self):
        """Подготовка тестового окружения."""
        self.api = PsapiAPI()

    def test_api_initialization(self):
        """Проверка инициализации PSAPI."""
        self.assertIsNotNone(self.api.psapi)

    def test_enumerate_processes(self):
        """Проверка перечисления PID через PSAPI."""
        pids = self.api.enumerate_processes()
        self.assertIsInstance(pids, list)
        self.assertGreater(len(pids), 0)


class TestInternalApp(unittest.TestCase):
    """Тестирование выделенного внутреннего сервиса FastAPI."""

    def test_load_config(self):
        """Проверка корректной загрузки конфигурации роутеров из config.json."""
        from apps.windows.api.internal_app import load_config
        cfg = load_config()
        self.assertIsInstance(cfg, dict)
        self.assertIn('routers', cfg)
        self.assertGreater(len(cfg['routers']), 0)

    def test_create_internal_app_urls(self):
        """Проверка маршрутов документации и спецификации OpenAPI."""
        from apps.windows.api.internal_app import create_internal_app
        app = create_internal_app()
        self.assertEqual(app.docs_url, '/docs')
        self.assertEqual(app.openapi_url, '/openapi.json')

    def test_health_routes(self):
        """Проверка наличия и работоспособности эндпоинтов здоровья."""
        from fastapi.testclient import TestClient
        from apps.windows.api.internal_app import create_internal_app

        app = create_internal_app()
        client = TestClient(app)

        res_health = client.get('/health')
        self.assertEqual(res_health.status_code, 200)
        self.assertEqual(res_health.json().get('status'), 'ok')
        self.assertIn('configured_routers_count', res_health.json())

        res_internal = client.get('/internal/health')
        self.assertEqual(res_internal.status_code, 200)
        self.assertEqual(res_internal.json().get('status'), 'ok')


if __name__ == '__main__':
    unittest.main()