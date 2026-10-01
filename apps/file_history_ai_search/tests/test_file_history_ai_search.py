# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps File_History_Ai_Search Tests - Test File History Ai Search
# =============================================================================
# Description:
#   Модульные тесты для сервиса Поиска по истории файлов Windows через RAG.
#
# Usage Examples:
#   CLI:
#     python -m apps.file_history_ai_search.tests.test_file_history_ai_search
#   Python API:
#     from apps.file_history_ai_search.tests.test_file_history_ai_search import temp_dir
#
#     res = temp_dir()
#
# File: test_file_history_ai_search.py
# Project: ai-breadboard
# Package: apps.file_history_ai_search.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Модульные тесты для сервиса Поиска по истории файлов Windows через RAG."""

import os
import tempfile
import time
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from apps.file_history_ai_search.collector import WindowsFileHistoryCollector
from apps.file_history_ai_search.models import FileHistoryItem, SearchQuery
from apps.file_history_ai_search.rag_service import FileHistoryRAGService
from apps.file_history_ai_search.router import router
from apps.file_history_ai_search.scheduler import FileHistoryScheduler


@pytest.fixture
def temp_dir():
    """Фикстура создающая временный каталог для тестов."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_items():
    """Фикстура с тестовыми элементами истории файлов."""
    return [
        FileHistoryItem(
            item_id="item_001",
            file_path="C:\\Docs\\Quarterly_Report_2025.docx",
            file_name="Quarterly_Report_2025.docx",
            source_type="file_history_xml",
            event_type="backed_up",
            timestamp="2025-09-20T10:00:00Z",
            content_preview="Финансовый отчет компании за третий квартал 2025 года.",
            file_size=10240,
        ),
        FileHistoryItem(
            item_id="item_002",
            file_path="C:\\Projects\\python_script.py",
            file_name="python_script.py",
            source_type="fs_scan",
            event_type="modified",
            timestamp="2025-09-22T14:30:00Z",
            content_preview="import sys\ndef main(): print('AI Breadboard')",
            file_size=512,
        ),
    ]


def test_file_history_item_to_rag_document(sample_items):
    """Тестирование преобразования элемента истории файла в RAG документ."""
    item = sample_items[0]
    doc = item.to_rag_document()

    assert doc["id"] == "item_001"
    assert "Quarterly_Report_2025.docx" in doc["text"]
    assert doc["meta"]["file_path"] == "C:\\Docs\\Quarterly_Report_2025.docx"
    assert doc["meta"]["source_type"] == "file_history_xml"


def test_collector_filesystem_recent(temp_dir):
    """Тестирование сбора недавно измененных файлов из файловой системы."""
    test_file = temp_dir / "test_doc.txt"
    test_file.write_text("Приветственный файл для проверки сбора истории.", encoding="utf-8")

    collector = WindowsFileHistoryCollector(target_directories=[str(temp_dir)])
    items = collector.collect_filesystem_recent(max_files=10)

    assert len(items) > 0
    found = [i for i in items if i.file_name == "test_doc.txt"]
    assert len(found) == 1
    assert "Приветственный" in found[0].content_preview
    assert found[0].source_type == "fs_scan"


def test_collector_file_history_xml(temp_dir, monkeypatch):
    """Тестирование сбора конфигурации из Windows File History XML."""
    fh_config_dir = temp_dir / "Microsoft" / "Windows" / "FileHistory" / "Configuration"
    fh_config_dir.mkdir(parents=True, exist_ok=True)

    dummy_xml = temp_dir / "target_file.txt"
    dummy_xml.write_text("Содержимое тестового бэкапа", encoding="utf-8")

    xml_content = f"""<?xml version="1.0" encoding="utf-8"?>
    <FileHistory>
        <Folder>{dummy_xml}</Folder>
    </FileHistory>
    """
    (fh_config_dir / "Config1.xml").write_text(xml_content, encoding="utf-8")

    collector = WindowsFileHistoryCollector()
    monkeypatch.setattr(collector, "localappdata", temp_dir)

    items = collector.collect_file_history_xml()
    assert len(items) >= 1
    paths = [i.file_path for i in items]
    assert str(dummy_xml) in paths


def test_rag_service_indexing_and_search(temp_dir, sample_items):
    """Тестирование индексации и семантического поиска RAG-сервиса."""
    db_path = temp_dir / "rag_db"
    rag_service = FileHistoryRAGService(db_path=db_path)

    # Индексация
    count = rag_service.index_items(sample_items)
    assert count == len(sample_items)

    # Проверка статуса
    status = rag_service.get_status()
    assert status.total_indexed_documents == len(sample_items)
    assert status.last_indexed_at is not None

    # Поиск
    res = rag_service.search(query="Финансовый отчет", top_k=2)
    assert res.total_found > 0
    assert "Quarterly_Report" in res.results[0].file_name

    # Очистка
    rag_service.clear()
    status_after = rag_service.get_status()
    assert status_after.total_indexed_documents == 0


def test_scheduler_lifecycle(temp_dir, sample_items):
    """Тестирование планировщика регулярного обновления RAG."""
    collector = WindowsFileHistoryCollector(target_directories=[str(temp_dir)])
    rag_service = FileHistoryRAGService(db_path=temp_dir / "sched_rag")

    scheduler = FileHistoryScheduler(collector=collector, rag_service=rag_service, interval_minutes=1)

    assert not scheduler.is_running
    # Однократный триггер
    indexed = scheduler.trigger_now()
    assert indexed >= 0

    # Запуск и остановка планировщика
    started = scheduler.start()
    assert started is True
    assert scheduler.is_running is True

    time.sleep(0.5)

    stopped = scheduler.stop()
    assert stopped is True
    assert scheduler.is_running is False


def test_fastapi_router_endpoints(temp_dir, sample_items):
    """Тестирование REST API эндпоинтов для поиска по истории файлов."""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    # Эндпоинт статуса
    response = client.get("/api/windows/file-history/status")
    assert response.status_code == 200
    data = response.json()
    assert "total_indexed_documents" in data

    # Эндпоинт сканирования
    response_scan = client.get("/api/windows/file-history/scan")
    assert response_scan.status_code == 200
    assert isinstance(response_scan.json(), list)

    # Эндпоинт индексации
    response_idx = client.post("/api/windows/file-history/index")
    assert response_idx.status_code == 200
    assert response_idx.json()["status"] == "success"

    # Эндпоинт поиска
    response_search = client.post(
        "/api/windows/file-history/search",
        json={"query": "отчет", "top_k": 3},
    )
    assert response_search.status_code == 200
    res_data = response_search.json()
    assert "total_found" in res_data
    assert "execution_time_ms" in res_data
