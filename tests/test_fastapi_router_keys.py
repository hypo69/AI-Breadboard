# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Tests for router_keys module
# =============================================================================
# Description:
#   Validates helper functions, request/response models, and API endpoints
#   for key management router using gemini_keys.json structure.
#
# File: test_fastapi_router_keys.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from datetime import datetime, timezone
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from src.fastapi.router_keys import (
    KeyCreateRequest,
    KeyEntry,
    KeyUpdateRequest,
    _check_exhaustion,
    _mask_key,
    init_router,
)


class TestRouterKeysHelpers:
    """Tests for internal helper functions in router_keys."""

    def test_mask_key_short(self):
        """Test masking short API key."""
        result = _mask_key("short")
        assert result == "*****"

    def test_mask_key_long(self):
        """Test masking long API key."""
        api_key = "AIzaSyDaGmWKaJsXk_hKl_pQrBwV8MiFa"  # 33 chars
        result = _mask_key(api_key)

        assert result.startswith("AIzaSyDa")
        assert result.endswith("MiFa")
        assert "..." in result
        assert len(result) == 15

    def test_mask_key_exact_12_chars(self):
        """Test masking key with exactly 12 characters."""
        result = _mask_key("123456789012")
        assert result == "12345678...9012"


class TestRouterKeysEndpoints:
    """Tests for API endpoints."""

    def test_list_keys_empty(self):
        """Test listing keys when storage is empty."""
        with patch('src.fastapi.router_keys._load_keys_file', return_value={}):
            router = init_router()
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            response = client.get('/api/keys')
            assert response.status_code == 200
            data = response.json()
            assert 'keys' in data
            assert 'total' in data
            assert data['total'] == 0

    def test_create_key_validation_empty_name(self):
        """Test validation when creating a key with empty name."""
        router = init_router()
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        response = client.post('/api/keys', json={
            'name': '',
            'value': 'test_key'
        })
        assert response.status_code == 400

    def test_create_key_validation_empty_value(self):
        """Test validation when creating a key with empty value."""
        router = init_router()
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        response = client.post('/api/keys', json={
            'name': 'test',
            'value': ''
        })
        assert response.status_code == 400

    def test_key_create_request_model(self):
        """Test KeyCreateRequest model."""
        request = KeyCreateRequest(name="test", value="key123")
        assert request.name == "test"
        assert request.value == "key123"
        assert request.status == "active"

    def test_key_update_request_model(self):
        """Test KeyUpdateRequest model."""
        request = KeyUpdateRequest(status="disabled")
        assert request.status == "disabled"
        assert request.name is None

    def test_key_entry_model(self):
        """Test KeyEntry model."""
        entry = KeyEntry(value="test_key")
        assert entry.value == "test_key"
        assert entry.status == "active"
        assert entry.last_run is None
        assert entry.exhausted_at is None


class TestRouterKeysLogic:
    """Tests for business logic."""

    def test_check_exhaustion_not_exhausted(self):
        """Test checking non-exhausted key."""
        with patch('src.fastapi.router_keys._load_keys_file') as mock_data:
            mock_data.return_value = {'GEMINI_API_KEY': {'value': 'k1', 'status': 'active', 'exhausted_at': ''}}

            exhausted, reset_in = _check_exhaustion('GEMINI_API_KEY')
            assert exhausted is False
            assert reset_in is None

    def test_check_exhausted_key(self):
        """Test checking exhausted key."""
        recent_time = datetime.now(timezone.utc).isoformat()

        with patch('src.fastapi.router_keys._load_keys_file') as mock_data:
            mock_data.return_value = {'GEMINI_API_KEY': {'value': 'k1', 'status': 'exhausted', 'exhausted_at': recent_time}}

            exhausted, reset_in = _check_exhaustion('GEMINI_API_KEY')
            assert exhausted is True
            assert reset_in is not None

    def test_check_exhaustion_key_not_found(self):
        """Test checking nonexistent key."""
        with patch('src.fastapi.router_keys._load_keys_file') as mock_data:
            mock_data.return_value = {}

            exhausted, reset_in = _check_exhaustion('nonexistent')
            assert exhausted is False
            assert reset_in is None