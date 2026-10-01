# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Wikillm Tests - Test Extractor
# =============================================================================
# Description:
#   Тесты для извлечения артефактов из логов, словарей событий и инцидентов.
#
# Usage Examples:
#   Python API:
#     from apps.windows.wikillm.tests.test_extractor import test_extract_from_event_dict
#
#     res = test_extract_from_event_dict()
#
# File: test_extractor.py
# Project: ai-breadboard
# Package: apps.windows.wikillm.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Тесты для извлечения артефактов из логов, словарей событий и инцидентов."""

import pytest
from apps.windows.wikillm.extractor import ArtifactExtractor
from apps.windows.wikillm.models import ArtifactType


def test_extract_from_event_dict() -> None:
    """Проверка извлечения артефакта из словаря Windows Event."""
    ev = {
        "Provider": "DistributedCOM",
        "EventID": 10016,
        "ProcessName": "svchost.exe",
        "Message": "The application-specific permission settings do not grant Local Activation permission.",
    }
    art = ArtifactExtractor.from_event_dict(ev)
    assert art.type == ArtifactType.WINDOWS_EVENT
    assert art.provider == "DistributedCOM"
    assert art.event_id == 10016
    assert art.process_name == "svchost.exe"


def test_extract_from_incident() -> None:
    """Проверка извлечения артефактов из объекта инцидента."""
    inc = {
        "category": "storage",
        "trigger_type": "disk_burst",
        "description": "High write rate detected",
        "suspects": [{"name": "system.exe", "pid": 4}, {"name": "backup.exe"}],
        "error_code": "0x80070005",
    }
    artifacts = ArtifactExtractor.from_incident(inc)
    assert len(artifacts) >= 3

    types = [a.type for a in artifacts]
    assert ArtifactType.INCIDENT in types
    assert ArtifactType.PROCESS in types
    assert ArtifactType.WINDOWS_ERROR in types


def test_extract_from_raw_text() -> None:
    """Проверка извлечения артефактов из свободного текста."""
    raw = "Failed to open registry HKLM\\Software\\Policies with error 0x80070490 in Event ID 7034"
    artifacts = ArtifactExtractor.from_raw_text(raw)

    types = [a.type for a in artifacts]
    assert ArtifactType.WINDOWS_ERROR in types
    assert ArtifactType.WINDOWS_EVENT in types
    assert ArtifactType.REGISTRY_KEY in types
