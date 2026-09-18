# -*- coding: utf-8 -*-
"""Модульные тесты для DefenderManager и SecurityCollector."""

import pytest
from apps.windows.core.defender_manager import DefenderManager
from apps.windows.core.modules.security_collector import SecurityCollector


def test_defender_manager_initialization():
    mgr = DefenderManager()
    assert mgr.mpcmdrun_path is not None
    assert isinstance(mgr.mpcmdrun_path, str)


def test_defender_manager_status_structure():
    mgr = DefenderManager()
    status = mgr.get_detailed_status()
    assert isinstance(status, dict)
    assert "realtime_protection" in status
    assert "cloud_protection_enabled" in status
    assert "controlled_folder_access" in status
    assert "engine_version" in status


def test_defender_manager_preferences():
    mgr = DefenderManager()
    prefs = mgr.get_preferences()
    assert isinstance(prefs, dict)
    assert "exclusions" in prefs
    assert "pua_protection" in prefs
    assert "asr_rules" in prefs
    assert isinstance(prefs["exclusions"].get("suspicious_paths", []), list)


def test_security_collector_with_defender():
    collector = SecurityCollector()
    res = collector.collect()
    assert res.domain_name == "security"
    assert "defender" in res.metrics
    assert "uac_enabled" in res.metrics