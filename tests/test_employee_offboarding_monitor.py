# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Tests for Employee Offboarding Monitor Skill
# =============================================================================
# Description:
#   Unit tests verifying document parsing, order classification, resource
#   discovery, and administrator alert generation.
#
# File: test_employee_offboarding_monitor.py
# Package: tests
# Author: hypo69
# Copyright: (c) 2026 hypo69
# =============================================================================
import tempfile
from pathlib import Path
import pytest
import sys

# Ensure scripts can be imported
skill_scripts = Path(__file__).resolve().parent.parent / '.agents' / 'skills' / 'user-skills' / 'employee-offboarding-monitor' / 'scripts'
if str(skill_scripts) not in sys.path:
    sys.path.insert(0, str(skill_scripts))

from parse_order import parse_document_text
from classify_order import extract_dismissal_order_info
from check_resources import discover_user_resources
from send_alert import format_offboarding_alert


class TestEmployeeOffboardingMonitor:
    """Test suite for employee offboarding monitor skill components."""

    def test_parse_document_text(self, tmp_path):
        doc = tmp_path / "order.txt"
        doc.write_text("Приказ об увольнении сотрудника", encoding="utf-8")
        text = parse_document_text(doc)
        assert text == "Приказ об увольнении сотрудника"

    def test_parse_document_not_found(self):
        with pytest.raises(FileNotFoundError):
            parse_document_text("non_existent_order_file.docx")

    def test_classify_order_valid_russian(self):
        sample = "ПРИКАЗ № 142-К от 30.09.2026 о прекращении трудового договора с работника Иванов Иван Иванович"
        result = extract_dismissal_order_info(sample)
        assert result["is_dismissal_order"] is True
        assert result["order_number"] == "142-К"
        assert result["termination_date"] == "30.09.2026"
        assert result["employee_name"] == "Иванов Иван Иванович"
        assert result["confidence"] >= 0.9

    def test_classify_order_non_dismissal(self):
        sample = "Служебная записка на закупку офисной бумаги для отдела бухгалтерии"
        result = extract_dismissal_order_info(sample)
        assert result["is_dismissal_order"] is False
        assert result["employee_name"] is None

    def test_discover_user_resources(self):
        res = discover_user_resources("Иванов Иван Иванович", "i.ivanov")
        assert res["username"] == "i.ivanov"
        assert res["resources_count"] >= 4
        identifiers = [r["identifier"] for r in res["resources"]]
        assert "DOMAIN\\i.ivanov" in identifiers
        assert "i.ivanov@company.com" in identifiers

    def test_format_offboarding_alert(self):
        order_data = {
            "employee_name": "Иванов Иван Иванович",
            "order_number": "142-К",
            "termination_date": "30.09.2026"
        }
        resources = discover_user_resources("Иванов Иван Иванович", "i.ivanov")
        alert_md = format_offboarding_alert(order_data, resources)
        
        assert "🚨" in alert_md
        assert "Иванов Иван Иванович" in alert_md
        assert "142-К" in alert_md
        assert "DOMAIN\\i.ivanov" in alert_md
        assert "Human-in-the-Loop" in alert_md
