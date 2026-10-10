# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Software Audit
# =============================================================================
# Description:
#   Тест успешной инициализации движка аудита.
#
# Usage Examples:
#   Python API:
#     from tests.test_software_audit import mock_winreg
#
#     res = mock_winreg()
#
# File: test_software_audit.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-03 23:57:00
# =============================================================================

"""Тесты движка аудита программного обеспечения и коллектора ПО."""

import pytest
from unittest.mock import MagicMock, patch
from apps.windows.sdk.core.audits.software_collector import SoftwareCollector
from apps.windows.sdk.core.models import FullAuditReport
from apps.windows.sdk.core.software_audit import SoftwareAuditEngine

@pytest.fixture
def mock_winreg():
    with patch('apps.windows.sdk.core.software_audit.winreg') as mock:
        yield mock

def test_software_audit_engine_initialization(mock_winreg):
    """Тест успешной инициализации движка аудита."""
    engine = SoftwareAuditEngine()
    assert engine is not None
    assert engine._categorizer is not None

def test_generate_audit_report_structure(mock_winreg):
    """Тест структуры отчета аудита."""
    with patch.object(SoftwareAuditEngine, 'get_installed_applications', return_value=[]), patch.object(SoftwareAuditEngine, '_save_to_csv'):
        engine = SoftwareAuditEngine()
        report = engine.generate_audit_report()
        assert report is not None
        assert report.total_apps == 0
        assert report.timestamp is not None

def test_software_collector_collect_and_to_dict():
    """Тест работы SoftwareCollector и сериализации to_dict без ошибок AttributeError."""
    collector = SoftwareCollector()
    result = collector.collect()
    assert result is not None
    result_dict = result.to_dict()
    assert isinstance(result_dict, dict)
    assert 'findings' in result_dict
    assert isinstance(result_dict['findings'], list)
    for finding in result_dict['findings']:
        assert isinstance(finding['actions'], list)
        for act in finding['actions']:
            assert isinstance(act, dict)
            assert 'action_id' in act

    report = FullAuditReport(domains={'software': result})
    report_dict = report.to_dict()
    assert isinstance(report_dict, dict)
    assert 'domains' in report_dict
    assert 'software' in report_dict['domains']