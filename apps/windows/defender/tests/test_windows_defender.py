# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Defender Unit Tests
# =============================================================================
# Description:
#   Комплексные модульные тесты для сервисов Microsoft Defender, правил ASR,
#   Controlled Folder Access, аудитора исключений, детектора процессов,
#   AI-диагностики и REST API эндпоинтов.
#
# File: test_windows_defender.py
# Project: ai-breadboard
# Package: apps.windows.defender.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Тесты для приложения Windows Defender & AI Security Diagnostic Center."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from apps.windows.defender.core.ai_diagnostician import AIDiagnostician
from apps.windows.defender.core.asr_manager import ASRManager
from apps.windows.defender.core.cfa_manager import ControlledFolderAccessManager
from apps.windows.defender.core.defender_service import DefenderService
from apps.windows.defender.core.event_correlator import EventCorrelator
from apps.windows.defender.core.exclusions_auditor import ExclusionsAuditor
from apps.windows.defender.core.models import (
    ExclusionRiskLevel,
    ProtectionState,
    ScanRequest,
    ScanType,
    ThreatSeverity,
)
from apps.windows.defender.core.process_tree_watcher import ProcessTreeWatcher
from apps.windows.defender.core.threat_manager import ThreatManager
from apps.windows.defender.router import init_router


@pytest.fixture
def mock_defender_service() -> DefenderService:
    """Фикстура замоканного DefenderService."""
    svc = DefenderService()
    svc._run_powershell_json = MagicMock(return_value={
        "AntivirusEnabled": True,
        "RealTimeProtectionEnabled": True,
        "BehaviorMonitorEnabled": True,
        "IoavProtectionEnabled": True,
        "OnAccessProtectionEnabled": True,
        "ScriptScanningEnabled": True,
        "MAPSReporting": 2,
        "CloudBlockLevel": "High",
        "IsTamperProtected": True,
        "PUAProtection": 1,
        "EnableControlledFolderAccess": 1,
        "EnableNetworkProtection": 1,
        "AntivirusSignatureVersion": "1.421.120.0",
        "AntispywareSignatureVersion": "1.421.120.0",
        "AMEngineVersion": "1.1.24080.9",
        "AMProductVersion": "4.18.24080.9",
        "AttackSurfaceReductionRules_Ids": [
            "d4f940ab-401b-4efc-aadc-ad5f3c50688a",
            "3b5764aa-a486-44a2-ba62-52b393774756",
        ],
        "AttackSurfaceReductionRules_Actions": [1, 2],
        "ControlledFolderAccessProtectedFolders": ["C:\\CustomProtected"],
        "ControlledFolderAccessAllowedApplications": ["C:\\Program Files\\App\\app.exe"],
        "ExclusionPath": ["C:\\", "C:\\Temp", "D:\\SafeProject\\Build"],
        "ExclusionExtension": [".exe", ".log"],
        "ExclusionProcess": ["powershell.exe", "safe_tool.exe"],
    })
    return svc


def test_defender_status_parsing(mock_defender_service: DefenderService) -> None:
    """Тест парсинга полного статуса Defender."""
    status = mock_defender_service.get_defender_status()
    assert status.antivirus_enabled is True
    assert status.real_time_protection_enabled is True
    assert status.behavior_monitor_enabled is True
    assert status.cloud_protection_enabled is True
    assert status.tamper_protection_enabled is True
    assert status.pua_protection_enabled is True
    assert status.controlled_folder_access_enabled is True
    assert status.network_protection_enabled is True
    assert status.engine_version == "1.1.24080.9"


def test_asr_manager_rules(mock_defender_service: DefenderService) -> None:
    """Тест аудита правил Attack Surface Reduction."""
    asr = ASRManager(mock_defender_service)
    rules = asr.get_asr_rules()
    assert len(rules) >= 10

    # Проверка конкретных сконфигурированных правил
    lsass_rule = next((r for r in rules if r.guid == "d4f940ab-401b-4efc-aadc-ad5f3c50688a"), None)
    assert lsass_rule is not None
    assert lsass_rule.state == ProtectionState.ENABLED

    office_rule = next((r for r in rules if r.guid == "3b5764aa-a486-44a2-ba62-52b393774756"), None)
    assert office_rule is not None
    assert office_rule.state == ProtectionState.AUDIT


def test_cfa_manager(mock_defender_service: DefenderService) -> None:
    """Тест Controlled Folder Access менеджера."""
    cfa = ControlledFolderAccessManager(mock_defender_service)
    info = cfa.get_cfa_status()
    assert info.enabled is True
    assert info.mode == ProtectionState.ENABLED
    assert "C:\\CustomProtected" in info.protected_folders
    assert "C:\\Program Files\\App\\app.exe" in info.allowed_applications


def test_exclusions_auditor_risk_evaluation(mock_defender_service: DefenderService) -> None:
    """Тест эвристического анализа рисков исключений."""
    auditor = ExclusionsAuditor(mock_defender_service)
    report = auditor.audit_exclusions()

    assert report.total_exclusions == 7
    assert report.suspicious_count > 0

    # Проверка выявления опасных путей (C:\, C:\Temp)
    c_root = next((p for p in report.path_exclusions if p.value == "C:\\"), None)
    assert c_root is not None
    assert c_root.risk_level == ExclusionRiskLevel.CRITICAL

    # Проверка выявления опасных расширений (.exe)
    exe_ext = next((e for e in report.extension_exclusions if e.value == ".exe"), None)
    assert exe_ext is not None
    assert exe_ext.risk_level == ExclusionRiskLevel.CRITICAL

    # Проверка выявления опасных процессов (powershell.exe)
    ps_proc = next((pr for pr in report.process_exclusions if pr.value == "powershell.exe"), None)
    assert ps_proc is not None
    assert ps_proc.risk_level == ExclusionRiskLevel.CRITICAL


def test_process_tree_watcher_patterns() -> None:
    """Тест поиска подозрительных паттернов командной строки."""
    watcher = ProcessTreeWatcher()
    # Проверка паттернов
    for pat, desc in watcher.SUSPICIOUS_CMD_PATTERNS:
        assert pat is not None


def test_ai_diagnostician_report(mock_defender_service: DefenderService) -> None:
    """Тест генерации комплексного AI-отчета защищенности."""
    diag = AIDiagnostician(defender_service=mock_defender_service)
    report = diag.generate_diagnostic_report()

    assert report.security_score >= 0
    assert report.security_score <= 100
    assert report.status_summary != ""
    assert isinstance(report.recommendations, list)


def test_fastapi_router() -> None:
    """Тест REST API маршрутов роутера Defender."""
    app = FastAPI()
    app.include_router(init_router())
    client = TestClient(app)

    resp = client.get("/api/v1/defender/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "antivirus_enabled" in data
    assert "services" in data

    resp_asr = client.get("/api/v1/defender/asr")
    assert resp_asr.status_code == 200
    assert isinstance(resp_asr.json(), list)

    resp_cfa = client.get("/api/v1/defender/cfa")
    assert resp_cfa.status_code == 200

    resp_exc = client.get("/api/v1/defender/exclusions")
    assert resp_exc.status_code == 200
    assert "total_exclusions" in resp_exc.json()

    resp_diag = client.get("/api/v1/defender/diagnostics")
    assert resp_diag.status_code == 200
    assert "security_score" in resp_diag.json()
