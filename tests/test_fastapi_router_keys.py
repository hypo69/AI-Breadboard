# -*- coding: utf-8 -*-
"""
Тесты модуля core/fastapi/router_keys.py
"""

import pytest
import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient


class TestRouterKeysHelpers:
    """Тесты внутренних функций router_keys."""

    def test_mask_key_short(self):
        """Тест маскирования короткого ключа."""
        from core.fastapi.router_keys import _mask_key
        
        result = _mask_key("short")
        assert result == "*****"

    def test_mask_key_long(self):
        """Тест маскирования длинного ключа."""
        from core.fastapi.router_keys import _mask_key
        
        api_key = "AIzaSyDaGmWKaJsXk_hKl_pQrBwV8MiFa"  # 33 chars
        result = _mask_key(api_key)
        
        # Маска: первые 8 + "..." + последние 4 = 15 символов
        assert result.startswith("AIzaSyDa")
        assert result.endswith("MiFa")
        assert "..." in result
        assert len(result) == 15

    def test_mask_key_exact_12_chars(self):
        """Тест маскирования ключа ровно 12 символов."""
        from core.fastapi.router_keys import _mask_key
        
        result = _mask_key("123456789012")
        assert result == "12345678...9012"

    def test_now_iso_format(self):
        """Тест формата _now_iso."""
        from core.fastapi.router_keys import _now_iso
        
        result = _now_iso()
        
        assert 'T' in result  # ISO format contains T
        assert '+' in result or 'Z' in result  # UTC timezone

    def test_iso_to_ts_valid(self):
        """Тест конвертации валидной ISO строки."""
        from core.fastapi.router_keys import _iso_to_ts
        
        iso = "2026-01-15T10:30:00+00:00"
        result = _iso_to_ts(iso)
        
        assert result > 0

    def test_iso_to_ts_invalid(self):
        """Тест конвертации невалидной строки."""
        from core.fastapi.router_keys import _iso_to_ts
        
        result = _iso_to_ts("invalid")
        assert result == 0.0

    def test_now_ts_returns_float(self):
        """Тест что _now_ts возвращает float."""
        from core.fastapi.router_keys import _now_ts
        
        result = _now_ts()
        
        assert isinstance(result, float)
        assert result > 1700000000  # Reasonable timestamp for 2024


class TestRouterKeysEndpoints:
    """Тесты API эндпоинтов."""

    @pytest.fixture
    def mock_secrets_files(self, tmp_path):
        """Создание временных файлов для тестов."""
        secrets_file = tmp_path / 'secrets.json'
        keys_file = tmp_path / 'gemini_keys.json'
        
        # Create empty files
        secrets_file.write_text('{}', encoding='utf-8')
        keys_file.write_text('{}', encoding='utf-8')
        
        return secrets_file, keys_file

    def test_list_keys_empty(self, mock_secrets_files):
        """Тест списка ключей при пустых файлах."""
        from core.fastapi.router_keys import init_router, _SECRETS_FILE, _KEYS_FILE
        
        secrets_file, keys_file = mock_secrets_files
        
        with patch.object(type(_SECRETS_FILE), 'exists', return_value=True), \
             patch.object(type(_KEYS_FILE), 'exists', return_value=True), \
             patch.object(type(_SECRETS_FILE), 'read_text', return_value='{}'), \
             patch.object(type(_KEYS_FILE), 'read_text', return_value='{}'):
            
            router = init_router()
            app = __import__('fastapi', fromlist=['FastAPI']).FastAPI()
            app.include_router(router)
            client = TestClient(app)
            
            response = client.get('/api/keys')
            
            assert response.status_code == 200
            data = response.json()
            assert 'keys' in data
            assert 'total' in data

    def test_create_key_validation_empty_name(self):
        """Тест валидации при создании ключа с пустым именем."""
        from core.fastapi.router_keys import init_router, _SECRETS_FILE, _KEYS_FILE
        
        with patch.object(type(_SECRETS_FILE), 'exists', return_value=False):
            router = init_router()
            app = __import__('fastapi', fromlist=['FastAPI']).FastAPI()
            app.include_router(router)
            client = TestClient(app)
            
            response = client.post('/api/keys', json={
                'name': '',
                'api_key': 'test_key'
            })
            
            assert response.status_code == 400

    def test_create_key_validation_empty_api_key(self):
        """Тест валидации при создании ключа с пустым API ключом."""
        from core.fastapi.router_keys import init_router, _SECRETS_FILE, _KEYS_FILE
        
        with patch.object(type(_SECRETS_FILE), 'exists', return_value=False):
            router = init_router()
            app = __import__('fastapi', fromlist=['FastAPI']).FastAPI()
            app.include_router(router)
            client = TestClient(app)
            
            response = client.post('/api/keys', json={
                'name': 'test',
                'api_key': ''
            })
            
            assert response.status_code == 400

    def test_key_create_request_model(self):
        """Тест модели KeyCreateRequest."""
        from core.fastapi.router_keys import KeyCreateRequest
        
        request = KeyCreateRequest(name="test", api_key="key123")
        
        assert request.name == "test"
        assert request.api_key == "key123"
        assert request.status == "active"

    def test_key_update_request_model(self):
        """Тест модели KeyUpdateRequest."""
        from core.fastapi.router_keys import KeyUpdateRequest
        
        request = KeyUpdateRequest(status="disabled")
        
        assert request.status == "disabled"
        assert request.name is None

    def test_key_entry_model(self):
        """Тест модели KeyEntry."""
        from core.fastapi.router_keys import KeyEntry
        
        entry = KeyEntry(api_key="test_key")
        
        assert entry.api_key == "test_key"
        assert entry.status == "active"
        assert entry.last_run is None
        assert entry.exhausted_at is None


class TestRouterKeysLogic:
    """Тесты бизнес-логики."""

    def test_check_exhaustion_not_exhausted(self):
        """Тест проверки неистощённого ключа."""
        from core.fastapi.router_keys import _check_exhaustion, _load_keys_data
        
        with patch('core.fastapi.router_keys._load_keys_data') as mock_load:
            mock_load.return_value = {'test_key': {'exhausted_at': None}}
            
            exhausted, reset_in = _check_exhaustion('test_key')
            
            assert exhausted is False
            assert reset_in is None

    def test_check_exhausted_key(self):
        """Тест проверки истощённого ключа."""
        from core.fastapi.router_keys import _check_exhaustion, _load_keys_data
        from datetime import datetime, timezone
        
        # Exhausted 1 hour ago - still exhausted
        recent_time = datetime.now(timezone.utc).isoformat()
        
        with patch('core.fastapi.router_keys._load_keys_data') as mock_load:
            mock_load.return_value = {'test_key': {'exhausted_at': recent_time}}
            
            exhausted, reset_in = _check_exhaustion('test_key')
            
            # Key is exhausted if there's remaining time
            assert exhausted is True or reset_in is not None

    def test_check_exhaustion_key_not_found(self):
        """Тест проверки несуществующего ключа."""
        from core.fastapi.router_keys import _check_exhaustion, _load_keys_data
        
        with patch('core.fastapi.router_keys._load_keys_data') as mock_load:
            mock_load.return_value = {}
            
            exhausted, reset_in = _check_exhaustion('nonexistent')
            
            assert exhausted is False
            assert reset_in is None