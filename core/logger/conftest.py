# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: pytest configuration for logger module
# =============================================================================
# Description:
#   Module for conftest.py in ai-breadboard project.
#
# File: conftest.py
# Project: ai-breadboard
# Package: core.logger
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""pytest configuration for logger module testing.

Provides fixtures and configuration for unit tests of core.logger module."""

import pytest
import sys
from pathlib import Path
from header import __root__

# Add project root to sys.path for imports
sys.path.insert(0, str(__root__))

@pytest.fixture(scope="session")
def project_root():
    """Fixture to get project root directory."""
    return __root__

@pytest.fixture(scope="session")
def logger_module_path():
    """Фикстура для получения пути к модулю логирования."""
    return __root__ / 'core' / 'logger'

@pytest.fixture
def temp_log_dir(tmp_path):
    """Фикстура для создания временной директории логов."""
    log_dir = tmp_path / 'logs'
    log_dir.mkdir()
    return log_dir

@pytest.fixture
def temp_reports_dir(tmp_path):
    """Фикстура для создания временной директории отчётов."""
    reports_dir = tmp_path / 'reports'
    reports_dir.mkdir()
    return reports_dir

@pytest.fixture
def mock_logger_config():
    """Фикстура для мокирования конфигурации логгера."""
    from unittest.mock import MagicMock
    config = MagicMock()
    config.mode = "dev"
    config.debug = True
    return config

@pytest.fixture
def mock_ai_model():
    """Фикстура для мокирования AI модели."""
    from unittest.mock import AsyncMock
    model = AsyncMock()
    model.ask.return_value = "# Analysis Report\n\nNo issues found."
    return model

# Markers для организации тестов
def pytest_configure(config):
    """Регистрирует пользовательские markers для pytest."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests for performance testing"
    )

# Hooks для сбора информации о тестах
def pytest_collection_modifyitems(config, items):
    """Модифицирует собранные тесты."""
    for item in items:
        # Добавляем marker если его нет
        if "test_" in item.name:
            if not any(marker.name == "unit" for marker in item.iter_markers()):
                item.add_marker(pytest.mark.unit)

# Configuration для asyncio тестов
pytest_plugins = ['pytest_asyncio']
