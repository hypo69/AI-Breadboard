"""Tests for src/app modules."""

import pytest
from pathlib import Path

# Test fixtures
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

# Test configuration
TEST_ROOT = Path(__file__).parent.parent.parent
