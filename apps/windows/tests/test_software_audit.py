# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit Tests for Windows Software Audit
# =============================================================================
# Description:
#   Тесты модулей аудита установленного ПО:
#   - Парсинг структуры UserAssist и декодирование ROT13
#   - Категоризация программ и генерация описания назначения
#   - Сборщик данных SoftwareAuditEngine и формирование отчета
#   - DTO и сериализация моделей
#
# File: test_software_audit.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модульные тесты для подсистемы аудита программного обеспечения Windows."""

import codecs
import struct
import unittest
from datetime import datetime, timezone


from apps.windows.core.data_model import (
    AppCategory,
    AppExecutionInfo,
    InstalledAppInfo,
    SoftwareAuditReport,
    SoftwareRowViewModel,
)
from apps.windows.core.software_audit import (
    SoftwareAuditEngine,
    SoftwareCategorizer,
    UserAssistParser,
    _decode_rot13,
    _filetime_to_datetime,
)



class TestSoftwareAuditUtils(unittest.TestCase):
    """Тестирование вспомогательных функций аудита."""

    def test_decode_rot13(self):
        """Проверка декодирования ROT13."""
        original = r"C:\Program Files\Test\app.exe"
        encoded = codecs.encode(original, "rot_13")
        decoded = _decode_rot13(encoded)
        self.assertEqual(decoded, original)


    def test_filetime_to_datetime(self):
        """Проверка конвертации Windows FILETIME в datetime."""
        # 133400000000000000 - пример корректного современного FILETIME (около 2023 г.)
        filetime = 133400000000000000
        dt = _filetime_to_datetime(filetime)
        self.assertIsNotNone(dt)
        self.assertGreaterEqual(dt.year, 2020)

        # Невалидный / пустой FILETIME
        self.assertIsNone(_filetime_to_datetime(0))
        self.assertIsNone(_filetime_to_datetime(-1))


class TestSoftwareCategorizer(unittest.TestCase):
    """Тестирование классификатора программ и назначения."""

    def test_classify_known_apps(self):
        """Проверка классификации известных программ."""
        cat, desc = SoftwareCategorizer.classify(
            name="Google Chrome",
            display_name="Google Chrome",
            publisher="Google LLC",
        )
        self.assertEqual(cat, AppCategory.BROWSER)
        self.assertIn("веб-браузер", desc.lower())

        cat, desc = SoftwareCategorizer.classify(
            name="VSCode",
            display_name="Microsoft Visual Studio Code",
            publisher="Microsoft Corporation",
        )
        self.assertEqual(cat, AppCategory.DEVELOPMENT)
        self.assertIn("исходного кода", desc.lower())

        cat, desc = SoftwareCategorizer.classify(
            name="7-Zip",
            display_name="7-Zip 23.01",
            publisher="Igor Pavlov",
        )
        self.assertEqual(cat, AppCategory.UTILITIES)
        self.assertIn("архиватор", desc.lower())

        cat, desc = SoftwareCategorizer.classify(
            name="Telegram",
            display_name="Telegram Desktop",
            publisher="Telegram FZ-LLC",
        )
        self.assertEqual(cat, AppCategory.COMMUNICATION)
        self.assertIn("мессенджер", desc.lower())

    def test_classify_by_keywords(self):
        """Проверка классификации по ключевым словам."""
        cat, desc = SoftwareCategorizer.classify(
            name="UnknownVPN",
            display_name="Secure Tunnel VPN Client",
            publisher="Privacy Corp",
        )
        self.assertEqual(cat, AppCategory.SECURITY)
        self.assertIn("vpn", desc.lower())

    def test_classify_fallback(self):
        """Проверка категоризации по умолчанию для неизвестных утилит."""
        cat, desc = SoftwareCategorizer.classify(
            name="CustomTool",
            display_name="My Company Internal Helper",
            publisher="My Company",
        )
        self.assertEqual(cat, AppCategory.OTHER)
        self.assertIn("прикладное программное обеспечение", desc.lower())


class TestUserAssistParser(unittest.TestCase):
    """Тестирование разбора структур UserAssist."""

    def test_parse_72_byte_entry(self):
        """Проверка разбора 72-байтовой структуры UserAssist."""
        # Создаем 72 байта: session_id=1, run_count=42, focus_count=10, focus_time_ms=50000
        # затем padding до 60 байта, и 8-байтный FILETIME (133400000000000000)
        raw_header = struct.pack("<IIII", 1, 42, 10, 50000)
        padding = b"\x00" * (60 - len(raw_header))
        raw_filetime = struct.pack("<Q", 133400000000000000)
        padding_end = b"\x00" * (72 - 60 - 8)
        raw_bytes = raw_header + padding + raw_filetime + padding_end

        parsed = UserAssistParser._parse_userassist_entry(raw_bytes, r"C:\app.exe")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.run_count, 42)
        self.assertEqual(parsed.focus_time_seconds, 50)
        self.assertIsNotNone(parsed.last_run_time)
        self.assertEqual(parsed.source_artifact, "UserAssist")


class TestSoftwareAuditEngine(unittest.TestCase):
    """Тестирование движка аудита программного обеспечения."""

    def setUp(self):
        self.engine = SoftwareAuditEngine()

    def test_get_installed_applications(self):
        """Проверка получения списка приложений."""
        apps = self.engine.get_installed_applications()
        self.assertIsInstance(apps, list)
        self.assertGreater(len(apps), 0)
        
        # Проверяем первое приложение
        first_app = apps[0]
        self.assertIsInstance(first_app, InstalledAppInfo)
        self.assertTrue(bool(first_app.display_name))
        self.assertIsInstance(first_app.category, AppCategory)
        self.assertTrue(bool(first_app.purpose_description))

    def test_generate_audit_report(self):
        """Проверка формирования сводного отчета аудита."""
        report = self.engine.generate_audit_report()
        self.assertIsInstance(report, SoftwareAuditReport)
        self.assertGreater(report.total_apps, 0)
        self.assertIsInstance(report.categories_breakdown, dict)
        self.assertGreater(len(report.categories_breakdown), 0)

        report_dict = report.to_dict()
        self.assertIn("total_apps", report_dict)
        self.assertIn("categories_breakdown", report_dict)
        self.assertIn("recently_launched", report_dict)

    def test_view_model_mapping(self):
        """Проверка формирования view model для CLI."""
        app = InstalledAppInfo(
            name="TestApp",
            display_name="Test Application",
            version="1.0.0",
            publisher="Tester",
            install_date="2024-01-15",
            category=AppCategory.UTILITIES,
            purpose_description="Тестовая утилита для проверки.",
            execution_info=AppExecutionInfo(
                last_run_time=datetime(2024, 2, 1, 14, 30, tzinfo=timezone.utc),
                run_count=15,
            ),
        )
        vm = SoftwareRowViewModel.from_app_info(app)
        self.assertEqual(vm.name, "Test Application")
        self.assertEqual(vm.version, "1.0.0")
        self.assertEqual(vm.run_count, 15)
        self.assertEqual(vm.category, AppCategory.UTILITIES.value)


if __name__ == "__main__":
    unittest.main()
