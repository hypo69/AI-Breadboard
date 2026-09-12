# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit tests for Audio Diarization Router endpoints
# =============================================================================
# Description:
#   Tests for /api/audio/diarize and /api/audio/save-to-rag FastAPI routes.
#
# File: test_router_audio.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import io
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app
from src.ai.audio_diarization import DiarizationResult
from src.rag.document_rag import DocumentRAGManager

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_rag(monkeypatch):
    temp_dir = Path(tempfile.mkdtemp())
    docs_dir = temp_dir / "docs"
    index_dir = temp_dir / "index"
    docs_dir.mkdir(parents=True, exist_ok=True)
    index_dir.mkdir(parents=True, exist_ok=True)

    mgr = DocumentRAGManager(docs_dir=docs_dir, index_dir=index_dir)
    monkeypatch.setattr("src.fastapi.router_audio.get_document_rag_manager", lambda: mgr)

    yield mgr

    shutil.rmtree(temp_dir, ignore_errors=True)


class TestRouterAudio:
    """Test suite for /api/audio endpoints."""

    @patch("src.fastapi.router_audio.get_audio_diarization_service")
    def test_diarize_endpoint(self, mock_get_service):
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        mock_service.analyze_audio.return_value = DiarizationResult(
            summary="Договоренность о встрече в 18:00",
            key_points=["Обсуждение проекта"],
            action_items=["Созвониться в пятницу"],
            speakers=["Иван", "Сергей"],
            transcript=[
                {"speaker": "Иван", "text": "Встретимся в 18:00?", "timestamp": "00:01"},
                {"speaker": "Сергей", "text": "Договорились.", "timestamp": "00:04"}
            ],
            markdown_report="# Сводка\nДоговоренность о встрече",
        )

        audio_file = ("meeting.mp3", io.BytesIO(b"fake_mp3_content"), "audio/mpeg")
        response = client.post(
            "/api/audio/diarize",
            files={"file": (audio_file[0], audio_file[1], audio_file[2])},
            data={"language": "ru"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["summary"] == "Договоренность о встрече в 18:00"
        assert len(data["data"]["speakers"]) == 2
        assert len(data["data"]["transcript"]) == 2

    def test_save_to_rag_endpoint(self, isolated_rag):
        payload = {
            "title": "Совещание по RAG",
            "summary": "Разработали архитектуру аудио диаризации.",
            "transcript": [
                {"speaker": "Собеседник 1", "text": "Давайте добавим вкладку RAG", "timestamp": "00:01"},
                {"speaker": "Собеседник 2", "text": "Отличная идея!", "timestamp": "00:05"}
            ],
            "key_points": ["Вкладка RAG", "Загрузка файлов"],
            "action_items": ["Выполнить релиз"]
        }

        response = client.post("/api/audio/save-to-rag", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

        # Verify that document was saved in isolated RAG
        docs = isolated_rag.list_documents()
        assert len(docs) == 1
        assert "Совещание_по_RAG" in docs[0].name
