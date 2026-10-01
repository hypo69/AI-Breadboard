# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard APP -   Init   Module
# =============================================================================
# Description:
#   Tests for src/app modules.
#
# Usage Examples:
#   Python API:
#     from src.app.tests.__init__ import test_app
#
#     res = test_app()
#     print(res)
#
# File: __init__.py
# Project: ai-breadboard
# Package: src.app.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

"""Tests for src/app modules."""

import pytest
from pathlib import Path

@pytest.fixture
def test_app():
    """Create a test FastAPI app instance."""
    from src.app import create_app, register_pages, register_config_api
    app = create_app()
    register_pages(app)
    register_config_api(app)
    return app

@pytest.fixture
def client(test_app):
    """Create a test client for the FastAPI app."""
    from fastapi.testclient import TestClient
    return TestClient(test_app)
TEST_ROOT = Path(__file__).parent.parent.parent