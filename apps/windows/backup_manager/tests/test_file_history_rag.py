# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows File History RAG Tests
# =============================================================================
# Description:
#   Модульные и интеграционные тесты для подсистемы семантического поиска
#   и инкрементальной индексации архивов Истории файлов Windows (File History).
#
# File: test_file_history_rag.py
# Project: ai-breadboard
# Package: apps.windows.backup_manager.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from datetime import datetime
from pathlib import Path
from typing import Tuple
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


from apps.windows.backup_manager.core.file_history_rag import (
    WindowsFileHistoryRAG,
    compute_file_sha256,
)
from apps.windows.backup_manager.router import init_router


@pytest.fixture
def mock_file_history_env(tmp_path: Path) -> Tuple[Path, Path]:
    """Создает фиктивное окружение Windows File History и каталог индекса RAG."""
    backup_root = tmp_path / "BackupDrive"
    index_dir = tmp_path / "rag_index"

    # Структура: BackupDrive/FileHistory/Alex/DESKTOP-01/Data/C/Users/Alex/Documents
    data_dir = backup_root / "FileHistory" / "Alex" / "DESKTOP-01" / "Data" / "C" / "Users" / "Alex" / "Documents"
    data_dir.mkdir(parents=True, exist_ok=True)
    index_dir.mkdir(parents=True, exist_ok=True)

    return backup_root, index_dir


def test_parse_version_filename():
    """Тест парсинга имен файлов Windows File History с суффиксом даты."""
    rag = WindowsFileHistoryRAG(index_dir=Path("."))
    
    # 1. Файл с меткой времени
    fname = "Project Roadmap (2026_09_16 19_30_00 UTC).docx"
    base, dt, ext = rag.parse_version_filename(fname)
    assert base == "Project Roadmap"
    assert ext == ".docx"
    assert dt == datetime(2026, 9, 16, 19, 30, 0)

    # 2. Обычный файл без суффикса
    fname_plain = "notes.txt"
    base2, dt2, ext2 = rag.parse_version_filename(fname_plain)
    assert base2 == "notes"
    assert ext2 == ".txt"
    assert dt2 is None


def test_incremental_sync_and_search(mock_file_history_env):
    """Тест однократной инициализации и инкрементального дополнения индекса."""
    backup_root, index_dir = mock_file_history_env
    doc_dir = backup_root / "FileHistory" / "Alex" / "DESKTOP-01" / "Data" / "C" / "Users" / "Alex" / "Documents"

    # 1. Создаем первую версию документа
    file_v1 = doc_dir / "Budget_Report (2026_01_10 10_00_00 UTC).txt"
    file_v1.write_text("Первая версия отчета: утвержден бюджет проекта Альфа на сумму 100000 долларов.", encoding="utf-8")

    rag = WindowsFileHistoryRAG(index_dir=index_dir)
    sync_res_1 = rag.sync(target_path=str(backup_root))

    assert sync_res_1["success"] is True
    assert sync_res_1["new_files_added"] == 1
    assert sync_res_1["new_chunks_added"] >= 1
    assert sync_res_1["total_files_indexed"] == 1

    # 2. Повторная синхронизация без изменений — ничего не добавляется
    sync_res_2 = rag.sync(target_path=str(backup_root))
    assert sync_res_2["new_files_added"] == 0
    assert sync_res_2["skipped_unchanged"] == 1
    assert sync_res_2["new_chunks_added"] == 0

    # 3. Поиск по первой версии
    search_res_1 = rag.search("бюджет проекта Альфа", top_k=5)
    assert len(search_res_1) >= 1
    assert search_res_1[0].score > 0
    assert "100000 долларов" in search_res_1[0].text

    # 4. Добавляем вторую версию документа и новый документ
    file_v2 = doc_dir / "Budget_Report (2026_02_15 14_30_00 UTC).txt"
    file_v2.write_text("Вторая версия отчета: скорректирован бюджет проекта Альфа до 150000 долларов из-за расходов.", encoding="utf-8")

    notes_file = doc_dir / "Architecture_Notes (2026_02_20 09_00_00 UTC).md"
    notes_file.write_text("# Архитектура системы\nВнедрен микросервисный подход и брокер сообщений Kafka.", encoding="utf-8")

    # Инкрементальное обновление
    sync_res_3 = rag.sync(target_path=str(backup_root))
    assert sync_res_3["new_files_added"] == 2
    assert sync_res_3["skipped_unchanged"] == 1
    assert sync_res_3["total_files_indexed"] == 3

    # 5. Поиск по истории: находим обе версии Budget_Report
    history_matches = rag.search("бюджет проекта Альфа", top_k=10)
    assert len(history_matches) >= 2

    # 6. Фильтрация по дате
    feb_matches = rag.search(
        "бюджет",
        date_from=datetime(2026, 2, 1),
        date_to=datetime(2026, 2, 28),
    )
    assert len(feb_matches) == 1
    assert "150000 долларов" in feb_matches[0].text

    # 7. Получение истории версий конкретного файла
    summary = rag.get_file_versions("Budget_Report")
    assert summary.total_versions == 2
    assert len(summary.versions) == 2
    assert summary.versions[0].version_timestamp == datetime(2026, 2, 15, 14, 30, 0)
    assert summary.versions[1].version_timestamp == datetime(2026, 1, 10, 10, 0, 0)

    # 8. Проверка статуса
    status = rag.get_status()
    assert status.total_files_indexed == 3
    assert status.total_chunks >= 3
    assert status.is_ready is True


def test_api_endpoints_integration(mock_file_history_env):
    """Интеграционный тест FastAPI эндпоинтов RAG истории файлов."""
    backup_root, index_dir = mock_file_history_env
    doc_dir = backup_root / "FileHistory" / "Alex" / "DESKTOP-01" / "Data" / "C" / "Users" / "Alex" / "Documents"

    file_v1 = doc_dir / "Contract (2026_03_01 11_00_00 UTC).txt"
    file_v1.write_text("Договор поставки серверного оборудования от компании NovaTech.", encoding="utf-8")

    app = FastAPI()
    app.include_router(init_router())
    client = TestClient(app)

    # Синхронизация через API
    sync_resp = client.post(
        "/api/v1/windows-backup/file-history/rag/sync",
        json={"target_path": str(backup_root), "force_rebuild": True}
    )
    assert sync_resp.status_code == 200
    sync_data = sync_resp.json()
    assert sync_data["success"] is True

    # Статус через API
    status_resp = client.get("/api/v1/windows-backup/file-history/rag/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["total_files_indexed"] >= 1

    # Поиск через API
    search_resp = client.post(
        "/api/v1/windows-backup/file-history/rag/search",
        json={"query": "поставка серверного оборудования NovaTech", "top_k": 5}
    )
    assert search_resp.status_code == 200
    results = search_resp.json()
    assert len(results) >= 1
    assert "NovaTech" in results[0]["text"]

    # Просмотр версий документа через API
    versions_resp = client.get("/api/v1/windows-backup/file-history/rag/versions?query=Contract")
    assert versions_resp.status_code == 200
    versions_data = versions_resp.json()
    assert versions_data["total_versions"] >= 1
