# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Defender Tests - Test Windows Defender
# =============================================================================
# Description:
#   Тесты для приложения Windows Defender & AI Security Diagnostic Center.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.defender.tests.test_windows_defender import mock_defender_service
#
#     res = mock_defender_service()
#
# File: test_windows_defender.py
# Project: ai-breadboard
# Package: apps.windows.modules.defender.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 14:13:00
# =============================================================================

from __future__ import annotations
"""Тесты для приложения Windows Defender & AI Security Diagnostic Center."""

import time
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
    DefenderEventRecord,
    DefenderTaskInfo,
    DefenderTaskStatus,
    DefenderTaskType,
    ExclusionRiskLevel,
    ProtectionState,
    ScanRequest,
    ScanResponse,
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
    svc._run_powershell_json = MagicMock(return_value={'AntivirusEnabled': True, 'RealTimeProtectionEnabled': True, 'BehaviorMonitorEnabled': True, 'IoavProtectionEnabled': True, 'OnAccessProtectionEnabled': True, 'ScriptScanningEnabled': True, 'MAPSReporting': 2, 'CloudBlockLevel': 'High', 'IsTamperProtected': True, 'PUAProtection': 1, 'EnableControlledFolderAccess': 1, 'EnableNetworkProtection': 1, 'AntivirusSignatureVersion': '1.421.120.0', 'AntispywareSignatureVersion': '1.421.120.0', 'AMEngineVersion': '1.1.24080.9', 'AMProductVersion': '4.18.24080.9', 'AttackSurfaceReductionRules_Ids': ['d4f940ab-401b-4efc-aadc-ad5f3c50688a', '3b5764aa-a486-44a2-ba62-52b393774756'], 'AttackSurfaceReductionRules_Actions': [1, 2], 'ControlledFolderAccessProtectedFolders': ['C:\\CustomProtected'], 'ControlledFolderAccessAllowedApplications': ['C:\\Program Files\\App\\app.exe'], 'ExclusionPath': ['C:\\', 'C:\\Temp', 'D:\\SafeProject\\Build'], 'ExclusionExtension': ['.exe', '.log'], 'ExclusionProcess': ['powershell.exe', 'safe_tool.exe']})
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
    assert status.engine_version == '1.1.24080.9'

def test_asr_manager_rules(mock_defender_service: DefenderService) -> None:
    """Тест аудита правил Attack Surface Reduction."""
    asr = ASRManager(mock_defender_service)
    rules = asr.get_asr_rules()
    assert len(rules) >= 10
    lsass_rule = next((r for r in rules if r.guid == 'd4f940ab-401b-4efc-aadc-ad5f3c50688a'), None)
    assert lsass_rule is not None
    assert lsass_rule.state == ProtectionState.ENABLED
    office_rule = next((r for r in rules if r.guid == '3b5764aa-a486-44a2-ba62-52b393774756'), None)
    assert office_rule is not None
    assert office_rule.state == ProtectionState.AUDIT

def test_cfa_manager(mock_defender_service: DefenderService) -> None:
    """Тест Controlled Folder Access менеджера."""
    cfa = ControlledFolderAccessManager(mock_defender_service)
    info = cfa.get_cfa_status()
    assert info.enabled is True
    assert info.mode == ProtectionState.ENABLED
    assert 'C:\\CustomProtected' in info.protected_folders
    assert 'C:\\Program Files\\App\\app.exe' in info.allowed_applications

def test_exclusions_auditor_risk_evaluation(mock_defender_service: DefenderService) -> None:
    """Тест эвристического анализа рисков исключений."""
    auditor = ExclusionsAuditor(mock_defender_service)
    report = auditor.audit_exclusions()
    assert report.total_exclusions == 7
    assert report.suspicious_count > 0
    c_root = next((p for p in report.path_exclusions if p.value == 'C:\\'), None)
    assert c_root is not None
    assert c_root.risk_level == ExclusionRiskLevel.CRITICAL
    exe_ext = next((e for e in report.extension_exclusions if e.value == '.exe'), None)
    assert exe_ext is not None
    assert exe_ext.risk_level == ExclusionRiskLevel.CRITICAL
    ps_proc = next((pr for pr in report.process_exclusions if pr.value == 'powershell.exe'), None)
    assert ps_proc is not None
    assert ps_proc.risk_level == ExclusionRiskLevel.CRITICAL

def test_process_tree_watcher_patterns() -> None:
    """Тест поиска подозрительных паттернов командной строки."""
    watcher = ProcessTreeWatcher()
    for pat, desc in watcher.SUSPICIOUS_CMD_PATTERNS:
        assert pat is not None

def test_ai_diagnostician_report(mock_defender_service: DefenderService) -> None:
    """Тест генерации комплексного AI-отчета защищенности."""
    diag = AIDiagnostician(defender_service=mock_defender_service)
    report = diag.generate_diagnostic_report()
    assert report.security_score >= 0
    assert report.security_score <= 100
    assert report.status_summary != ''
    assert isinstance(report.recommendations, list)

def test_defender_async_tasks_and_telemetry(mock_defender_service: DefenderService) -> None:
    """Тест создания фоновых задач, обновления статуса и телеметрии."""
    with patch.object(mock_defender_service, 'trigger_scan', return_value=ScanResponse(success=True, scan_type=ScanType.QUICK, message='ОК')), \
         patch.object(mock_defender_service._correlator, 'find_latest_event_for_task', return_value=DefenderEventRecord(event_id=1001, timestamp='2026-10-06 12:00:00', level='Information', message='Scan done', category='Scan Completed')), \
         patch.object(mock_defender_service, '_record_telemetry_event') as mock_telemetry:
        
        task = mock_defender_service.start_scan_task(ScanRequest(scan_type=ScanType.QUICK))
        assert task.task_id.startswith('def-scan-')
        assert task.status in (DefenderTaskStatus.RUNNING, DefenderTaskStatus.COMPLETED)
        
        # Даем отработать фоновому воркеру
        for _ in range(50):
            retrieved = mock_defender_service.get_task(task.task_id)
            if retrieved and retrieved.status == DefenderTaskStatus.COMPLETED:
                break
            time.sleep(0.05)

        assert retrieved is not None
        assert retrieved.status == DefenderTaskStatus.COMPLETED
        assert retrieved.windows_event is not None
        assert retrieved.windows_event.event_id == 1001
        assert mock_telemetry.called

def test_fastapi_router(mock_defender_service: DefenderService) -> None:
    """Тест REST API маршрутов роутера Defender."""
    app = FastAPI()
    app.include_router(init_router())
    client = TestClient(app)

    with patch.object(DefenderService, 'get_defender_status', return_value=mock_defender_service.get_defender_status()), \
         patch.object(DefenderService, 'trigger_scan', return_value=ScanResponse(success=True, scan_type=ScanType.FULL, message='Сканирование успешно завершено.')), \
         patch.object(DefenderService, 'update_signatures', return_value=ScanResponse(success=True, scan_type=ScanType.QUICK, message='Сигнатуры обновлены.')):

        resp = client.get('/api/v1/defender/status')
        assert resp.status_code == 200
        data = resp.json()
        assert 'antivirus_enabled' in data

        resp_asr = client.get('/api/v1/defender/asr')
        assert resp_asr.status_code == 200
        assert isinstance(resp_asr.json(), list)

        resp_cfa = client.get('/api/v1/defender/cfa')
        assert resp_cfa.status_code == 200

        resp_exc = client.get('/api/v1/defender/exclusions')
        assert resp_exc.status_code == 200
        assert 'total_exclusions' in resp_exc.json()

        resp_diag = client.get('/api/v1/defender/diagnostics')
        assert resp_diag.status_code == 200
        assert 'security_score' in resp_diag.json()

        # Асинхронный запуск сканирования
        resp_scan = client.post('/api/v1/defender/scan', json={'scan_type': 'full'})
        assert resp_scan.status_code == 200
        task_data = resp_scan.json()
        assert 'task_id' in task_data
        assert task_data['task_id'].startswith('def-scan-')

        # Проверка статуса задачи по ID
        task_id = task_data['task_id']
        resp_task = client.get(f'/api/v1/defender/tasks/{task_id}')
        assert resp_task.status_code == 200
        assert resp_task.json()['task_id'] == task_id

        # Асинхронный запуск обновления баз
        resp_sig = client.post('/api/v1/defender/update-signatures')
        assert resp_sig.status_code == 200
        sig_data = resp_sig.json()
        assert sig_data['task_id'].startswith('def-sig-')

        # Список задач
        resp_tasks = client.get('/api/v1/defender/tasks')
        assert resp_tasks.status_code == 200
        assert len(resp_tasks.json()) >= 2