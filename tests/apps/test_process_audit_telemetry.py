# -*- coding: utf-8 -*-
"""Тесты для модуля системной телеметрии процессов (Security 4688 & Sysmon)."""

import pytest
from unittest.mock import MagicMock
from apps.windows.core.process_audit_manager import ProcessAuditManager, ProcessTreeNode, TelemetrySensorStatus
from apps.windows.api.wevtapi import WevtAPI


@pytest.fixture
def mock_wevtapi():
    api = MagicMock(spec=WevtAPI)
    return api


def test_telemetry_status(mock_wevtapi):
    mock_wevtapi.get_channel_record_count.side_effect = lambda ch: 150 if "Sysmon" in ch else 200
    manager = ProcessAuditManager(wevtapi=mock_wevtapi)
    status = manager.get_telemetry_status()

    assert isinstance(status, TelemetrySensorStatus)
    assert status.sysmon_installed is True
    assert status.sysmon_channel_active is True
    assert isinstance(status.to_dict(), dict)


def test_build_process_tree(mock_wevtapi):
    sample_events = [
        {
            "process_id": 1000,
            "process_name": "explorer.exe",
            "executable_path": "C:\\Windows\\explorer.exe",
            "command_line": "C:\\Windows\\explorer.exe",
            "parent_process_id": 0,
            "user": "DOMAIN\\user",
            "timestamp": "2026-09-18 20:00:00",
            "process_guid": "{guid-1}",
            "hashes": "",
        },
        {
            "process_id": 2000,
            "process_name": "powershell.exe",
            "executable_path": "C:\\Windows\\System32\\powershell.exe",
            "command_line": "powershell.exe -NoProfile",
            "parent_process_id": 1000,
            "user": "DOMAIN\\user",
            "timestamp": "2026-09-18 20:01:00",
            "process_guid": "{guid-2}",
            "hashes": "",
        },
        {
            "process_id": 3000,
            "process_name": "python.exe",
            "executable_path": "C:\\Python314\\python.exe",
            "command_line": "python.exe script.py --verbose",
            "parent_process_id": 2000,
            "user": "DOMAIN\\user",
            "timestamp": "2026-09-18 20:02:00",
            "process_guid": "{guid-3}",
            "hashes": "",
        },
    ]

    mock_wevtapi.query_process_events.return_value = sample_events
    manager = ProcessAuditManager(wevtapi=mock_wevtapi)
    roots = manager.build_process_tree(limit=10)

    assert len(roots) == 1
    root = roots[0]
    assert root.process_id == 1000
    assert root.process_name == "explorer.exe"
    assert len(root.children) == 1
    ps_node = root.children[0]
    assert ps_node.process_id == 2000
    assert len(ps_node.children) == 1
    py_node = ps_node.children[0]
    assert py_node.process_id == 3000
    assert py_node.command_line == "python.exe script.py --verbose"


def test_file_activity_with_processes(mock_wevtapi):
    mock_wevtapi.read_events.return_value = [
        {
            "event_id": 23,
            "timestamp": "2026-09-18 20:05:00",
            "event_data": {
                "TargetFilename": "C:\\Temp\\old_cache.tmp",
                "Image": "C:\\Python314\\python.exe",
                "ProcessId": "3000",
                "User": "DOMAIN\\user",
            },
        },
        {
            "event_id": 11,
            "timestamp": "2026-09-18 20:06:00",
            "event_data": {
                "TargetFilename": "C:\\Temp\\new_report.pdf",
                "Image": "C:\\Python314\\python.exe",
                "ProcessId": "3000",
                "User": "DOMAIN\\user",
            },
        },
    ]

    manager = ProcessAuditManager(wevtapi=mock_wevtapi)
    activities = manager.get_file_activity_with_processes(limit=10)

    assert len(activities) == 2
    assert activities[0]["action"] == "delete"
    assert activities[0]["target_file"] == "C:\\Temp\\old_cache.tmp"
    assert activities[0]["process_name"] == "python.exe"

    assert activities[1]["action"] == "create"
    assert activities[1]["target_file"] == "C:\\Temp\\new_report.pdf"
