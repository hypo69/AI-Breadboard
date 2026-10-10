# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Model Manager
# =============================================================================
# Description:
#   Тестирование менеджера моделей: отображение полного тела ошибки и параметров без падения.
#
# File: test_model_manager.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 06:59:00
# =============================================================================

"""Тестирование модуля model_manager на корректное логирование ошибок API без падения."""

import pytest
from unittest.mock import MagicMock, patch
from logger import logger
from src.ai.orchestration.model_manager import get_available_models, _fetch_gemini_models_sync


def test_gemini_fetch_models_logs_full_error_without_crash() -> None:
    """Проверка, что при ошибке API Gemini выводится полное тело ошибки в лог, и возвращаются fallback-модели."""
    mock_error_message = (
        "400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid', "
        "'status': 'INVALID_ARGUMENT', 'details': [{'reason': 'API_KEY_INVALID'}]}}"
    )
    
    with patch("google.genai.Client") as mock_client_class, patch.object(logger, "error") as mock_log_error:
        mock_client = MagicMock()
        mock_client.models.list.side_effect = Exception(mock_error_message)
        mock_client_class.return_value = mock_client
        
        # Не должно выбрасывать исключение
        models = _fetch_gemini_models_sync(api_key="AIzaSyInvalidKey12345")
        
        # Проверяем возврат доступных резервных моделей
        assert len(models) > 0
        assert any("gemini" in m for m in models)
        
        # Проверяем, что logger.error был вызван с полным текстом ошибки и параметрами
        assert mock_log_error.called
        log_call_args = str(mock_log_error.call_args)
        assert "Не удалось получить список моделей Gemini через SDK" in log_call_args or "400 INVALID_ARGUMENT" in log_call_args
        assert "genai.Client.models.list()" in log_call_args
        assert "https://generativelanguage.googleapis.com/v1beta/models" in log_call_args


