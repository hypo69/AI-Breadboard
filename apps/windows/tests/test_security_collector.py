# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Tests - Security Collector
# =============================================================================
# Description:
#   Модульные тесты для подсистемы Windows Security Event Log:
#   WevtAPI (закладки и инкрементальное чтение), нормализатор, схемы SQLite,
#   сборщик, корреляция с телеметрией и CLI/API интерфейсы.
#
# Usage Examples:
#   CLI:
#     pytest apps/windows/tests/test_security_collector.py -v
#
# File: test_security_collector.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 05:40:00
# =============================================================================

from __future__ import annotations
"""Модульные тесты для подсистемы сбора и анализа событий журнала безопасности Windows и Defender."""

import sqlite3
import time
from unittest.mock import MagicMock, patch
import pytest

from apps.windows.telemetry.models import (
    SecurityAuditStatus,
    SecurityBookmarkState,
    SecurityCollectorReport,
    SecurityCorrelationItem,
    SecurityEventItem,
    SecurityEventRaw,
)
from apps.windows.telemetry.security_collector import (
    DEFENDER_CHANNEL,
    DEFAULT_DEFENDER_EVENT_IDS,
    DEFAULT_SECURITY_EVENT_IDS,
    WindowsSecurityCollector,
)
from apps.windows.telemetry.security_normalizer import (
    SecurityEventNormalizer,
    _parse_int,
)
from apps.windows.telemetry.sqlite.connection import TelemetryConnectionManager
from apps.windows.telemetry.sqlite.reader import TelemetryReader
from apps.windows.telemetry.sqlite.schema import init_database_schema
from apps.windows.telemetry.sqlite.storage import TelemetryStorage
from apps.windows.telemetry.sqlite.writer import TelemetryWriter
from apps.windows.telemetry.win32_ffi.wevtapi import WevtAPI


@pytest.fixture
def in_memory_storage(tmp_path):
    """Фикстура изолированного экземпляра TelemetryStorage в файловой БД tmp_path."""
    db_file = tmp_path / "test_telemetry.db"
    storage = TelemetryStorage(db_path=db_file, auto_flush=True, read_only=False)
    yield storage
    storage.close()


class TestSecurityNormalizer:
    """Тесты нормализатора событий журнала безопасности Windows."""

    def test_parse_int_helpers(self):
        """Проверка парсинга чисел из десятичных и шестнадцатеричных строк."""
        assert _parse_int("123") == 123
        assert _parse_int("0x1a4") == 420
        assert _parse_int("0X20") == 32
        assert _parse_int("-") == 0
        assert _parse_int(None, default=10) == 10
        assert _parse_int("invalid", default=5) == 5

    def test_normalize_process_creation_4688(self):
        """Проверка нормализации события создания процесса (Event ID 4688)."""
        normalizer = SecurityEventNormalizer()
        raw_event = {
            "event_id": 4688,
            "record_id": 2812395,
            "timestamp": "2026-10-08 01:42:17",
            "computer": "WORKSTATION-01",
            "channel": "Security",
            "level": "Information",
            "raw_data": "<Event>Mock XML</Event>",
            "event_data": {
                "SubjectUserName": "David",
                "SubjectDomainName": "ONELA",
                "SubjectUserSid": "S-1-5-21-12345",
                "NewProcessId": "0x1a4",
                "NewProcessName": "C:\\Python314\\python.exe",
                "ProcessId": "0x20f0",
                "ParentProcessName": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
                "CommandLine": "python -m uvicorn apps.windows.main:app",
                "TokenElevationType": "2",
                "SubjectLogonId": "0x3e7",
            },
        }

        item, raw_item = normalizer.normalize_event(raw_event, extract_raw=True)

        assert item.event_id == 4688
        assert item.event_record_id == 2812395
        assert item.subject_user == "David"
        assert item.subject_domain == "ONELA"
        assert item.process_id == 420
        assert item.process_name == "C:\\Python314\\python.exe"
        assert item.parent_process_id == 8432
        assert "powershell.exe" in item.parent_process_name
        assert "uvicorn" in item.command_line
        assert item.elevated_token == 2
        assert "python.exe" in item.message
        assert "David" in item.message
        assert raw_item is not None
        assert raw_item.event_record_id == 2812395

    def test_normalize_logon_4624(self):
        """Проверка нормализации события успешного входа (Event ID 4624)."""
        normalizer = SecurityEventNormalizer()
        raw_event = {
            "event_id": 4624,
            "record_id": 2812400,
            "timestamp": "2026-10-08 02:00:00",
            "event_data": {
                "TargetUserName": "Administrator",
                "TargetDomainName": "WORKGROUP",
                "TargetUserSid": "S-1-5-21-9999",
                "LogonType": "10",
                "IpAddress": "192.168.1.50",
                "IpPort": "54321",
            },
        }

        item, raw = normalizer.normalize_event(raw_event, extract_raw=False)
        assert item.event_id == 4624
        assert item.target_user == "Administrator"
        assert item.logon_type == 10
        assert item.source_ip == "192.168.1.50"
        assert item.source_port == 54321
        assert "Успешный вход" in item.message
        assert "Administrator" in item.message

    def test_normalize_failed_logon_4625(self):
        """Проверка нормализации события неудачного входа (Event ID 4625)."""
        normalizer = SecurityEventNormalizer()
        raw_event = {
            "event_id": 4625,
            "record_id": 2812401,
            "timestamp": "2026-10-08 02:01:00",
            "event_data": {
                "TargetUserName": "guest",
                "Status": "0xC000006D",
                "SubStatus": "0xC0000064",
                "IpAddress": "10.0.0.99",
            },
        }

        item, _ = normalizer.normalize_event(raw_event)
        assert item.event_id == 4625
        assert item.target_user == "guest"
        assert item.status_code == "0xC000006D"
        assert item.source_ip == "10.0.0.99"
        assert "Неудачная попытка входа" in item.message

    def test_normalize_audit_log_cleared_1102(self):
        """Проверка нормализации события очистки журнала безопасности (Event ID 1102)."""
        normalizer = SecurityEventNormalizer()
        raw_event = {
            "event_id": 1102,
            "record_id": 2812405,
            "timestamp": "2026-10-08 02:05:00",
            "event_data": {
                "SubjectUserName": "Attacker",
            },
        }

        item, _ = normalizer.normalize_event(raw_event)
        assert item.event_id == 1102
        assert "ВНИМАНИЕ: Журнал аудита безопасности был очищен" in item.message
        assert "Attacker" in item.message

    def test_normalize_defender_threat_1116(self):
        """Проверка нормализации обнаружения угрозы Microsoft Defender (Event ID 1116)."""
        normalizer = SecurityEventNormalizer()
        raw_event = {
            "event_id": 1116,
            "record_id": 9812,
            "timestamp": "2026-10-10 05:30:00",
            "computer": "WORKSTATION-01",
            "channel": DEFENDER_CHANNEL,
            "level": "Warning",
            "event_data": {
                "Threat Name": "Trojan:Win32/Wacatac.B!ml",
                "Path": "C:\\Downloads\\malware.exe",
                "Process Name": "C:\\Windows\\explorer.exe",
                "Detection User": "ONELA\\onela",
                "Severity Name": "Severe",
                "Action Name": "Quarantine",
            },
        }

        item, _ = normalizer.normalize_event(raw_event)
        assert item.event_id == 1116
        assert item.channel == DEFENDER_CHANNEL
        assert item.object_name == "Trojan:Win32/Wacatac.B!ml"
        assert item.command_line == "C:\\Downloads\\malware.exe"
        assert item.process_name == "C:\\Windows\\explorer.exe"
        assert item.subject_user == "ONELA\\onela"
        assert "Trojan:Win32/Wacatac.B!ml" in item.message
        assert "Обнаружена угроза" in item.message

    def test_normalize_defender_realtime_disabled_5001(self):
        """Проверка нормализации отключения защиты в реальном времени Defender (Event ID 5001)."""
        normalizer = SecurityEventNormalizer()
        raw_event = {
            "event_id": 5001,
            "record_id": 9815,
            "timestamp": "2026-10-10 05:32:00",
            "channel": DEFENDER_CHANNEL,
            "level": "Error",
            "event_data": {},
        }

        item, _ = normalizer.normalize_event(raw_event)
        assert item.event_id == 5001
        assert "отключена" in item.message


class TestSecurityDatabaseStorage:
    """Тесты хранения и выборки событий безопасности в SQLite."""

    def test_save_and_retrieve_security_events(self, in_memory_storage):
        """Проверка сохранения списка событий и фильтрации выборки."""
        now_ts = "2026-10-08 02:10:00"
        events = [
            SecurityEventItem(
                event_record_id=1001,
                event_id=4688,
                timestamp=now_ts,
                subject_user="David",
                process_id=1234,
                process_name="C:\\Windows\\System32\\cmd.exe",
                command_line="cmd.exe /c dir",
                message="Создание процесса: cmd.exe",
            ),
            SecurityEventItem(
                event_record_id=1002,
                event_id=4624,
                timestamp=now_ts,
                target_user="David",
                logon_type=2,
                source_ip="127.0.0.1",
                message="Успешный вход пользователя: David",
            ),
            SecurityEventItem(
                event_record_id=1003,
                event_id=4625,
                timestamp=now_ts,
                target_user="Hacker",
                status_code="0xC000006D",
                source_ip="192.168.1.100",
                message="Неудачная попытка входа: Hacker",
            ),
        ]

        saved_count = in_memory_storage.save_security_events(events, save_raw=False)
        assert saved_count == 3

        # Выборка всех событий
        all_events = in_memory_storage.get_security_events(limit=10)
        assert len(all_events) == 3

        # Выборка по Event ID
        proc_events = in_memory_storage.get_security_events(event_id=4688)
        assert len(proc_events) == 1
        assert proc_events[0]["process_id"] == 1234
        assert "cmd.exe" in proc_events[0]["process_name"]

        # Выборка по имени пользователя
        user_events = in_memory_storage.get_security_events(user="David")
        assert len(user_events) == 2

        # Выборка неудачных входов
        failed = in_memory_storage.get_security_failed_logons(hours=24)
        assert len(failed) == 1
        assert failed[0]["target_user"] == "Hacker"

        # Проверка создания процессов через отдельный метод
        procs = in_memory_storage.get_security_process_creations(process_name="cmd.exe")
        assert len(procs) == 1
        assert procs[0]["process_id"] == 1234

        # Статистика
        stats = in_memory_storage.get_security_stats()
        assert stats["total_events"] == 3
        assert stats["max_record_id"] == 1003
        assert stats["process_creation_count"] == 1
        assert stats["failed_logon_count"] == 1

    def test_bookmark_lifecycle(self, in_memory_storage):
        """Проверка сохранения и извлечения закладки инкрементального сбора."""
        bookmark_xml = "<BookmarkList><Bookmark Channel='Security' RecordId='2812394'/></BookmarkList>"
        in_memory_storage.save_security_bookmark(
            channel="Security",
            last_record_id=2812394,
            bookmark_xml=bookmark_xml,
            last_timestamp="2026-10-08 01:00:00",
        )

        bm = in_memory_storage.get_security_bookmark(channel="Security")
        assert bm is not None
        assert bm["channel"] == "Security"
        assert bm["last_record_id"] == 2812394
        assert "<BookmarkList>" in bm["bookmark_xml"]

        # Обновление существующей закладки
        new_xml = "<BookmarkList><Bookmark Channel='Security' RecordId='2812400'/></BookmarkList>"
        in_memory_storage.save_security_bookmark(
            channel="Security",
            last_record_id=2812400,
            bookmark_xml=new_xml,
            last_timestamp="2026-10-08 02:00:00",
        )

        updated_bm = in_memory_storage.get_security_bookmark(channel="Security")
        assert updated_bm["last_record_id"] == 2812400
        assert "2812400" in updated_bm["bookmark_xml"]


class TestWindowsSecurityCollector:
    """Тесты основного сервиса WindowsSecurityCollector."""

    def test_check_access_and_audit(self, in_memory_storage):
        """Проверка формирования статуса аудита и прав доступа."""
        mock_wevtapi = MagicMock(spec=WevtAPI)
        mock_wevtapi.check_channel_access.return_value = {
            "accessible": True,
            "channel": "Security",
            "error": None,
            "record_count": 2812394,
        }

        collector = WindowsSecurityCollector(storage=in_memory_storage, wevtapi=mock_wevtapi)
        status = collector.check_access_and_audit()

        assert isinstance(status, SecurityAuditStatus)
        assert status.accessible is True
        assert status.record_count == 2812394
        assert status.error is None

    def test_collect_incremental_flow(self, in_memory_storage):
        """Проверка полного цикла инкрементального сбора с сохранением закладки."""
        mock_wevtapi = MagicMock(spec=WevtAPI)
        mock_wevtapi.check_channel_access.return_value = {
            "accessible": True,
            "channel": "Security",
            "error": None,
            "record_count": 1000,
        }

        mock_raw_events = [
            {
                "event_id": 4688,
                "record_id": 101,
                "timestamp": "2026-10-08 02:10:00",
                "computer": "PC-01",
                "raw_data": "<Event/>",
                "event_data": {
                    "SubjectUserName": "David",
                    "NewProcessId": "0x400",
                    "NewProcessName": "C:\\Windows\\explorer.exe",
                },
            },
            {
                "event_id": 4624,
                "record_id": 102,
                "timestamp": "2026-10-08 02:11:00",
                "computer": "PC-01",
                "raw_data": "<Event/>",
                "event_data": {
                    "TargetUserName": "David",
                    "LogonType": "2",
                },
            },
        ]

        mock_wevtapi.read_events_incremental.side_effect = [
            (mock_raw_events, "<Bookmark XML 102>", 102),
            ([], "<Bookmark XML 102>", 102),
        ]

        collector = WindowsSecurityCollector(storage=in_memory_storage, wevtapi=mock_wevtapi)
        report = collector.collect_incremental(batch_size=10, max_records=20)

        assert isinstance(report, SecurityCollectorReport)
        assert report.total_events_ingested == 2
        assert report.last_record_id == 102
        assert report.events_by_id.get(4688) == 1
        assert report.events_by_id.get(4624) == 1

        # Проверка, что события действительно появились в SQLite
        saved_events = in_memory_storage.get_security_events()
        assert len(saved_events) == 2

        # Проверка сохранения закладки
        bm = in_memory_storage.get_security_bookmark("Security")
        assert bm is not None
        assert bm["last_record_id"] == 102

    def test_collect_incremental_access_denied(self, in_memory_storage):
        """Проверка Fail-Safe поведения при нехватке прав доступа (ERROR_ACCESS_DENIED)."""
        mock_wevtapi = MagicMock(spec=WevtAPI)
        mock_wevtapi.check_channel_access.return_value = {
            "accessible": False,
            "channel": "Security",
            "error": "Отказано в доступе (ERROR_ACCESS_DENIED, код 5).",
            "record_count": 0,
        }

        collector = WindowsSecurityCollector(storage=in_memory_storage, wevtapi=mock_wevtapi)
        report = collector.collect_incremental()

        assert report.total_events_ingested == 0
        assert len(report.errors) == 1
        assert "Отказано в доступе" in report.errors[0]

    def test_correlate_security_with_telemetry(self, in_memory_storage):
        """Проверка движка корреляции событий создания процессов и сессий с телеметрией."""
        # 1. Записываем событие процесса
        in_memory_storage.save_security_events([
            SecurityEventItem(
                event_record_id=200,
                event_id=4688,
                timestamp="2026-10-08 02:14:31",
                subject_user="David",
                process_id=8420,
                process_name="python.exe",
                parent_process_name="powershell.exe",
                command_line="python -m uvicorn ...",
                elevated_token=1,
            )
        ])

        collector = WindowsSecurityCollector(storage=in_memory_storage)
        corrs = collector.correlate_security_with_telemetry(pid=8420)

        assert len(corrs) == 1
        c = corrs[0]
        assert c.event_type == "ProcessCreate"
        assert c.process_name == "python.exe"
        assert c.pid == 8420
        assert any("powershell.exe" in note for note in c.notes)
        assert any("повышенными привилегиями" in note for note in c.notes)

    def test_collect_defender_incremental(self, in_memory_storage):
        """Проверка инкрементального сбора событий Microsoft Defender Operational."""
        mock_wevtapi = MagicMock(spec=WevtAPI)
        mock_wevtapi.check_channel_access.return_value = {
            "accessible": True,
            "channel": DEFENDER_CHANNEL,
            "error": None,
            "record_count": 500,
        }

        mock_defender_events = [
            {
                "event_id": 1116,
                "record_id": 501,
                "timestamp": "2026-10-10 05:20:00",
                "computer": "PC-01",
                "channel": DEFENDER_CHANNEL,
                "level": "Warning",
                "raw_data": "<Event/>",
                "event_data": {
                    "Threat Name": "Trojan:Win32/FakeAlert",
                    "Path": "C:\\temp\\threat.dll",
                },
            },
            {
                "event_id": 1117,
                "record_id": 502,
                "timestamp": "2026-10-10 05:20:01",
                "computer": "PC-01",
                "channel": DEFENDER_CHANNEL,
                "level": "Information",
                "raw_data": "<Event/>",
                "event_data": {
                    "Threat Name": "Trojan:Win32/FakeAlert",
                    "Action Name": "Quarantine",
                },
            },
        ]

        mock_wevtapi.read_events_incremental.side_effect = [
            (mock_defender_events, "<Bookmark XML Def 502>", 502),
            ([], "<Bookmark XML Def 502>", 502),
        ]

        collector = WindowsSecurityCollector(storage=in_memory_storage, wevtapi=mock_wevtapi)
        report = collector.collect_defender_events(batch_size=10, max_records=20)

        assert isinstance(report, SecurityCollectorReport)
        assert report.channel == DEFENDER_CHANNEL
        assert report.total_events_ingested == 2
        assert report.last_record_id == 502
        assert report.events_by_id.get(1116) == 1
        assert report.events_by_id.get(1117) == 1

        # Проверка сохранения в SQLite с правильным каналом
        events = in_memory_storage.get_security_events(channel=DEFENDER_CHANNEL)
        assert len(events) == 2
        assert events[0]["channel"] == DEFENDER_CHANNEL

        # Проверка сохранения закладки для канала Defender
        bm = in_memory_storage.get_security_bookmark(DEFENDER_CHANNEL)
        assert bm is not None
        assert bm["last_record_id"] == 502

    def test_collect_all_security_and_defender(self, in_memory_storage):
        """Проверка одновременного сбора Security и Defender журналов."""
        mock_wevtapi = MagicMock(spec=WevtAPI)
        mock_wevtapi.check_channel_access.return_value = {
            "accessible": True,
            "error": None,
            "record_count": 100,
        }
        mock_wevtapi.read_events_incremental.return_value = ([], "<BM>", 10)

        collector = WindowsSecurityCollector(storage=in_memory_storage, wevtapi=mock_wevtapi)
        results = collector.collect_all_security_and_defender(batch_size=50, max_records=100)

        assert "Security" in results
        assert DEFENDER_CHANNEL in results
        assert isinstance(results["Security"], SecurityCollectorReport)
        assert isinstance(results[DEFENDER_CHANNEL], SecurityCollectorReport)
