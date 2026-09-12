# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit tests for AudioDiarizationService
# =============================================================================
# Description:
#   Tests for audio diarization service, JSON parsing, prompt building, and markdown report generation.
#
# File: test_audio_diarization.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
from unittest.mock import MagicMock, patch
import pytest

from src.ai.audio_diarization import (
    AudioDiarizationService,
    DiarizationResult,
    get_audio_diarization_service,
)


class TestAudioDiarizationService:
    """Test suite for AudioDiarizationService."""

    def test_json_parsing_clean(self):
        service = AudioDiarizationService()
        sample_json = {
            "summary": "Обсуждение архитектуры RAG",
            "key_points": ["Выбор базы данных", "Парсинг PDF"],
            "action_items": ["Написать тесты"],
            "speakers": ["Собеседник 1", "Собеседник 2"],
            "transcript": [
                {"speaker": "Собеседник 1", "text": "Привет, обсудим RAG?", "timestamp": "00:01"},
                {"speaker": "Собеседник 2", "text": "Да, давай.", "timestamp": "00:05"}
            ]
        }
        res = service._parse_json_response(json.dumps(sample_json))
        assert res["summary"] == "Обсуждение архитектуры RAG"
        assert len(res["key_points"]) == 2
        assert len(res["transcript"]) == 2

    def test_json_parsing_with_code_fences(self):
        service = AudioDiarizationService()
        raw_markdown = """```json
{
  "summary": "Разговор о погоде",
  "key_points": ["Идет дождь"],
  "action_items": ["Взять зонт"],
  "speakers": ["Анна", "Борис"],
  "transcript": [
    {"speaker": "Анна", "text": "На улице дождь.", "timestamp": "00:00"}
  ]
}
```"""
        res = service._parse_json_response(raw_markdown)
        assert res["summary"] == "Разговор о погоде"
        assert res["speakers"] == ["Анна", "Борис"]

    def test_format_markdown_report(self):
        service = AudioDiarizationService()
        data = {
            "summary": "Краткое резюме",
            "key_points": ["Пункт 1"],
            "action_items": ["Сделать коммит"],
            "speakers": ["Собеседник 1"],
            "transcript": [{"speaker": "Собеседник 1", "text": "Готово!", "timestamp": "00:10"}]
        }
        md = service._format_markdown_report(data)
        assert "# 🎙️ Сводка и диаризация разговора" in md
        assert "Краткое резюме" in md
        assert "Сделать коммит" in md
        assert "Собеседник 1" in md

    @patch("src.ai.audio_diarization.genai.Client")
    def test_analyze_audio_mock(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "summary": "Тестовое аудиосообщение",
            "key_points": ["Тест 1"],
            "action_items": ["Проверить"],
            "speakers": ["Спикер 1"],
            "transcript": [{"speaker": "Спикер 1", "text": "Привет", "timestamp": "00:00"}]
        })
        mock_client.models.generate_content.return_value = mock_response

        service = AudioDiarizationService()
        result = service.analyze_audio(
            audio_bytes=b"fake_audio_bytes",
            mime_type="audio/mp3",
            api_key="fake_key_123",
            language="ru"
        )

        assert isinstance(result, DiarizationResult)
        assert result.summary == "Тестовое аудиосообщение"
        assert len(result.transcript) == 1
        assert result.transcript[0]["text"] == "Привет"
        assert "# 🎙️ Сводка и диаризация разговора" in result.markdown_report
