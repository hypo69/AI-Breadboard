# -*- coding: utf-8 -*-
import pytest
from unittest.mock import MagicMock, patch
from apps.windows.core.software_audit import SoftwareAuditEngine

@pytest.fixture
def mock_winreg():
    with patch("apps.windows.core.software_audit.winreg") as mock:
        yield mock

def test_software_audit_engine_initialization(mock_winreg):
    """Тест успешной инициализации движка аудита."""
    engine = SoftwareAuditEngine()
    assert engine is not None
    assert engine._categorizer is not None

def test_generate_audit_report_structure(mock_winreg):
    """Тест структуры отчета аудита."""
    # Мокаем методы сбора данных, чтобы не обращаться к реальному реестру
    with patch.object(SoftwareAuditEngine, 'get_installed_applications', return_value=[]), \
         patch.object(SoftwareAuditEngine, '_save_to_csv'):
        engine = SoftwareAuditEngine()
        report = engine.generate_audit_report()
        
        assert report is not None
        assert report.total_apps == 0
        assert report.timestamp is not None
