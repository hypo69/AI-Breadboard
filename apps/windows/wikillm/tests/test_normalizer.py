# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Wikillm Tests - Test Normalizer
# =============================================================================
# Description:
#   Тесты для нормализатора канонических ключей и шаблонов артефактов.
#
# Usage Examples:
#   Python API:
#     from apps.windows.wikillm.tests.test_normalizer import test_normalize_hex_code
#
#     res = test_normalize_hex_code()
#
# File: test_normalizer.py
# Project: ai-breadboard
# Package: apps.windows.wikillm.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Тесты для нормализатора канонических ключей и шаблонов артефактов."""

import pytest
from apps.windows.wikillm.models import ArtifactInput, ArtifactType
from apps.windows.wikillm.normalizer import CanonicalKeyNormalizer


def test_normalize_hex_code() -> None:
    """Проверка нормализации шестнадцатеричных кодов ошибок."""
    assert CanonicalKeyNormalizer.normalize_hex_code("0x80070490") == "0x80070490"
    assert CanonicalKeyNormalizer.normalize_hex_code("80070490") == "0x80070490"
    assert CanonicalKeyNormalizer.normalize_hex_code("0X80070005") == "0x80070005"
    assert CanonicalKeyNormalizer.normalize_hex_code("-2147024891") == "0x80070005"


def test_normalize_registry_path() -> None:
    """Проверка нормализации путей реестра."""
    assert (
        CanonicalKeyNormalizer.normalize_registry_path(
            "HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"
        )
        == "HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"
    )
    assert (
        CanonicalKeyNormalizer.normalize_registry_path("HKEY_CURRENT_USER/Software/App")
        == "HKCU\\Software\\App"
    )


def test_canonical_key_generation() -> None:
    """Проверка генерации канонических ключей для разных типов артефактов."""
    # 1. Windows Event
    art_ev = ArtifactInput(
        type=ArtifactType.WINDOWS_EVENT,
        provider="DistributedCOM",
        event_id=10016,
    )
    assert CanonicalKeyNormalizer.compute_canonical_key(art_ev) == "windows_event:DistributedCOM:10016"

    # 2. Win32 Error
    art_err = ArtifactInput(
        type=ArtifactType.WINDOWS_ERROR,
        error_code="0x80070490",
    )
    assert CanonicalKeyNormalizer.compute_canonical_key(art_err) == "win32:0x80070490"

    # 3. NTSTATUS Error
    art_nt = ArtifactInput(
        type=ArtifactType.WINDOWS_ERROR,
        error_code="0xc0000005",
    )
    assert CanonicalKeyNormalizer.compute_canonical_key(art_nt) == "ntstatus:0xc0000005"

    # 4. Process
    art_proc = ArtifactInput(
        type=ArtifactType.PROCESS,
        process_name="Svchost.EXE",
    )
    assert CanonicalKeyNormalizer.compute_canonical_key(art_proc) == "process:svchost.exe"

    # 5. Service
    art_srv = ArtifactInput(
        type=ArtifactType.SERVICE,
        service_name="wuauserv",
    )
    assert CanonicalKeyNormalizer.compute_canonical_key(art_srv) == "service:wuauserv"

    # 6. Raw query error code
    art_raw = ArtifactInput(raw_query="0x80070005")
    assert CanonicalKeyNormalizer.compute_canonical_key(art_raw) == "win32:0x80070005"


def test_fingerprint_generation() -> None:
    """Проверка очистки шаблона и генерации стабильного отпечатка."""
    msg1 = "The application svchost.exe at address 0x7FFE1234AB failed with GUID {12345678-1234-1234-1234-123456789abc} on 2026-10-01T07:00:00Z"
    msg2 = "The application svchost.exe at address 0x7FFE9876CD failed with GUID {87654321-4321-4321-4321-cba987654321} on 2026-10-02T10:15:30Z"

    art1 = ArtifactInput(provider="AppCrash", event_id=1000, message=msg1)
    art2 = ArtifactInput(provider="AppCrash", event_id=1000, message=msg2)

    fp1 = CanonicalKeyNormalizer.compute_fingerprint(art1)
    fp2 = CanonicalKeyNormalizer.compute_fingerprint(art2)

    assert fp1 == fp2, "Отпечатки с динамическими GUID и адресами должны совпадать!"
