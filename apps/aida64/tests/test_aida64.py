# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AIDA64 Service Unit & Integration Tests
# =============================================================================
# Description:
#   Набор тестов для проверки AIDA64 Service, чтения Shared Memory,
#   генерации CLI отчетов и FastAPI роутера.
#
# File: test_aida64.py
# Project: ai-breadboard
# Package: apps.aida64.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Тесты для приложения интеграции с AIDA64."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from apps.aida64.core.aida64_service import Aida64Service
from apps.aida64.router import router
from fastapi import FastAPI


class TestAida64Service(unittest.TestCase):
    """Тестирование функциональности Aida64Service."""

    def setUp(self) -> None:
        """Подготовка тестового окружения."""
        self.service = Aida64Service()
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

    def test_binary_discovery(self) -> None:
        """Проверка поиска исполняемого файла AIDA64."""
        self.assertIsNotNone(self.service.binary_path, "Путь к бинарнику AIDA64 не найден")
        self.assertTrue(self.service.is_binary_available(), "Бинарный файл AIDA64 недоступен на диске")

    def test_live_sensors_read(self) -> None:
        """Проверка чтения данных датчиков из Shared Memory."""
        sensors = self.service.get_live_sensors()
        self.assertIsInstance(sensors, list, "get_live_sensors должен возвращать список")
        if self.service.is_running():
            self.assertGreater(len(sensors), 0, "Список сенсоров не должен быть пустым при активной памяти")
            sensor = sensors[0]
            self.assertIn("id", sensor)
            self.assertIn("label", sensor)
            self.assertIn("type", sensor)
            self.assertIn("value", sensor)
            self.assertIn("unit", sensor)

    def test_router_status_endpoint(self) -> None:
        """Проверка эндпоинта /api/v1/aida64/status."""
        response = self.client.get("/api/v1/aida64/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("is_running", data)
        self.assertIn("is_binary_available", data)
        self.assertIn("binary_path", data)
        self.assertIn("portable_guide", data)
        self.assertIn("shared memory", data["portable_guide"]["instruction_ru"].lower())

    def test_router_sensors_endpoint(self) -> None:
        """Проверка эндпоинта /api/v1/aida64/sensors."""
        response = self.client.get("/api/v1/aida64/sensors")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("count", data)
        self.assertIn("sensors", data)
        self.assertEqual(data["count"], len(data["sensors"]))

    def test_xml_sensor_parsing(self) -> None:
        """Тест разбора XML-строки из Shared Memory."""
        mock_xml = "<temp><id>TCPU</id><label>CPU</label><value>45</value></temp><fan><id>FCPU</id><label>CPU Fan</label><value>1200</value></fan>"
        with patch.object(self.service, "read_shared_memory", return_value=mock_xml):
            sensors = self.service.get_live_sensors()
            self.assertEqual(len(sensors), 2)
            self.assertEqual(sensors[0]["label"], "CPU")
            self.assertEqual(sensors[0]["value"], 45.0)
            self.assertEqual(sensors[0]["unit"], "°C")
            self.assertEqual(sensors[1]["type"], "Fan")
            self.assertEqual(sensors[1]["value"], 1200.0)
            self.assertEqual(sensors[1]["unit"], "RPM")


if __name__ == "__main__":
    unittest.main()
