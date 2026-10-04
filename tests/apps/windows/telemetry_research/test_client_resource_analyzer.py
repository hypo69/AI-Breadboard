# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Tests Apps Windows Telemetry_Research - Client Resource Analyzer
# =============================================================================
# Description:
#   Модульные тесты для анализа ресурсов клиентских программ и оценки неизвестных процессов через Gemini.
#
# Usage Examples:
#   pytest tests/apps/windows/telemetry_research/test_client_resource_analyzer.py -v
#
# File: test_client_resource_analyzer.py
# Project: ai-breadboard
# Package: tests.apps.windows.telemetry_research
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 07:50:00
# =============================================================================

from __future__ import annotations
"""Модульные тесты анализа ресурсов клиентских программ и оценки в Gemini."""

import json
import sqlite3
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from apps.windows.telemetry_research.assistant import TelemetryAssistant
from apps.windows.telemetry_research.client_resource_analyzer import ClientResourceAnalyzer
from apps.windows.telemetry_research.models import (
    ClientProgramResource,
    ClientResourceSummary,
    UnknownProgramEvaluation,
)
from apps.windows.telemetry_research.query_engine import TelemetryQueryEngine
from apps.windows.telemetry_research.server import app


@pytest.fixture
def mock_telemetry_db(tmp_path: Path) -> Path:
    """Создать временную тестовую базу данных telemetry.db со снимками процессов."""
    db_file = tmp_path / "telemetry.db"
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE process_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER,
            timestamp TEXT,
            pid INTEGER,
            name TEXT,
            status TEXT,
            cpu_percent REAL,
            memory_mb REAL,
            memory_percent REAL,
            num_threads INTEGER,
            num_handles INTEGER,
            username TEXT,
            read_bytes_sec REAL,
            write_bytes_sec REAL,
            integrity_level TEXT,
            elevation INTEGER,
            ppid INTEGER,
            parent_name TEXT,
            executable TEXT,
            cmdline TEXT,
            sid TEXT,
            session_id INTEGER,
            creation_time TEXT,
            process_guid TEXT,
            ancestor_chain TEXT,
            launch_reason TEXT
        )
    """)

    # Добавляем тестовые процессы:
    # 1. Системный процесс (должен быть отфильтрован из клиентских)
    cursor.execute("""
        INSERT INTO process_snapshots (
            snapshot_id, timestamp, pid, name, cpu_percent, memory_mb, memory_percent,
            num_threads, num_handles, username, read_bytes_sec, write_bytes_sec, executable, cmdline
        ) VALUES (1, '2026-10-04T07:00:00Z', 100, 'svchost.exe', 0.5, 45.0, 0.2, 12, 150, 'NT AUTHORITY\\SYSTEM', 0, 0, 'C:\\Windows\\System32\\svchost.exe', '-k netsvcs')
    """)

    # 2. Известная клиентская программа (Google Chrome)
    cursor.execute("""
        INSERT INTO process_snapshots (
            snapshot_id, timestamp, pid, name, cpu_percent, memory_mb, memory_percent,
            num_threads, num_handles, username, read_bytes_sec, write_bytes_sec, executable, cmdline
        ) VALUES (1, '2026-10-04T07:00:00Z', 1234, 'chrome.exe', 4.5, 650.0, 4.0, 24, 400, 'User', 1024, 2048, 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', '--type=renderer')
    """)

    # 3. Неизвестная ресурсоемкая программа из папки Temp (потенциальный майнер/малварь)
    cursor.execute("""
        INSERT INTO process_snapshots (
            snapshot_id, timestamp, pid, name, cpu_percent, memory_mb, memory_percent,
            num_threads, num_handles, username, read_bytes_sec, write_bytes_sec, executable, cmdline
        ) VALUES (1, '2026-10-04T07:00:00Z', 5678, 'xmr_miner_service.exe', 85.0, 1200.0, 8.0, 32, 210, 'User', 52428800, 10485760, 'C:\\Users\\User\\AppData\\Local\\Temp\\xmr_miner_service.exe', '--threads 8')
    """)

    conn.commit()
    conn.close()
    return db_file


@pytest.mark.asyncio
async def test_client_resource_analyzer_classification(mock_telemetry_db: Path):
    """Тест классификации клиентских программ и распознавания известных/неизвестных приложений."""
    query_engine = TelemetryQueryEngine()
    analyzer = ClientResourceAnalyzer(query_engine=query_engine)

    # 1. Проверка системных vs клиентских процессов
    assert analyzer.is_client_program("svchost.exe", username="NT AUTHORITY\\SYSTEM") is False
    assert analyzer.is_client_program("System") is False
    assert analyzer.is_client_program("chrome.exe", username="User") is True
    assert analyzer.is_client_program("xmr_miner_service.exe", username="User") is True

    # 2. Проверка известных vs неизвестных приложений
    assert analyzer.is_known_software("chrome.exe") is True
    assert analyzer.is_known_software("code.exe") is True
    assert analyzer.is_known_software("xmr_miner_service.exe") is False

    # 3. Проверка порогов ресурсоемкости
    assert analyzer.is_heavy_resource_consumer(cpu_pct=5.0, ram_mb=200.0, disk_io_mbs=1.0) is False
    assert analyzer.is_heavy_resource_consumer(cpu_pct=85.0, ram_mb=1200.0, disk_io_mbs=50.0) is True


@pytest.mark.asyncio
async def test_client_resource_analyzer_summary_and_gemini_fallback(mock_telemetry_db: Path):
    """Тест формирования сводки ресурсов клиентских программ и эвристической оценки Gemini."""
    query_engine = TelemetryQueryEngine()
    analyzer = ClientResourceAnalyzer(query_engine=query_engine)

    summary: ClientResourceSummary = await analyzer.analyze_client_resources(
        db_path=mock_telemetry_db, ask_gemini_for_unknown=True, limit=10
    )

    assert summary.total_client_programs == 2  # chrome.exe and xmr_miner_service.exe (svchost filtered out)
    assert summary.heavy_programs_count == 2   # chrome (650MB RAM) and xmr (85% CPU, 1200MB RAM)
    assert summary.unknown_heavy_programs_count == 1  # xmr_miner_service.exe

    # Проверяем, что для неизвестной тяжелой программы была сгенерирована оценка
    assert len(summary.evaluations) == 1
    eval_item = summary.evaluations[0]
    assert eval_item.program_name == "xmr_miner_service.exe"
    assert eval_item.risk_level in ["high", "critical", "medium"]
    assert len(eval_item.recommendations) > 0


@pytest.mark.asyncio
async def test_client_resource_analyzer_with_mocked_gemini_llm(mock_telemetry_db: Path):
    """Тест интеграции с моделью Gemini при структурированном JSON-ответе."""
    mock_chat = MagicMock()
    mock_gemini_json_reply = json.dumps({
        "is_normal": False,
        "confidence": 0.98,
        "risk_level": "critical",
        "verdict": "Обнаружен скрытый криптомайнер",
        "analysis": "Процесс xmr_miner_service.exe запущен из временной папки Temp и утилизирует 85% CPU.",
        "recommendations": [
            "Немедленно завершить процесс PID 5678",
            "Удалить исполняемый файл из AppData\\Local\\Temp",
            "Выполнить полное сканирование Microsoft Defender"
        ]
    })
    mock_chat.ask = AsyncMock(return_value=f"```json\n{mock_gemini_json_reply}\n```")

    query_engine = TelemetryQueryEngine()
    analyzer = ClientResourceAnalyzer(query_engine=query_engine, chat_model=mock_chat)

    summary: ClientResourceSummary = await analyzer.analyze_client_resources(
        db_path=mock_telemetry_db, ask_gemini_for_unknown=True, limit=10
    )

    assert len(summary.evaluations) == 1
    ev = summary.evaluations[0]
    assert ev.is_normal is False
    assert ev.risk_level == "critical"
    assert "майнер" in ev.verdict.lower()
    assert "PID 5678" in ev.recommendations[0]


@pytest.mark.asyncio
async def test_assistant_client_resources_query(mock_telemetry_db: Path):
    """Тест обработки естественного языка в AI-ассистенте по ресурсам клиентских программ."""
    query_engine = TelemetryQueryEngine()
    analyzer = ClientResourceAnalyzer(query_engine=query_engine)
    assistant = TelemetryAssistant(query_engine=query_engine, client_analyzer=analyzer)

    user_query = "Сколько места и ресурсов занимает какая программа запущенная клиентом?"
    response = await assistant.handle_query(user_query, source_path=str(mock_telemetry_db))

    assert response["status"] == "ok"
    assert "### 💻 Ресурсы программ, запущенных клиентом" in response["reply"]
    assert "chrome.exe" in response["reply"]
    assert "xmr_miner_service.exe" in response["reply"]
    assert response["chart"] is not None
    assert response["chart"]["type"] == "bar"


def test_api_client_resources_endpoints(mock_telemetry_db: Path):
    """Тест REST API эндпоинтов /api/client-resources и /api/client-resources/evaluate."""
    client = TestClient(app)

    # 1. GET /api/client-resources
    res = client.get(f"/api/client-resources?db_path={mock_telemetry_db}&ask_gemini=false")
    assert res.status_code == 200
    data = res.json()
    assert "total_client_programs" in data
    assert "programs" in data
    assert data["total_client_programs"] == 2

    # 2. POST /api/client-resources/evaluate
    sample_program = {
        "pid": 9999,
        "name": "suspicious_crypto.exe",
        "display_name": "Suspicious Crypto App",
        "executable_path": "C:\\Users\\User\\Downloads\\suspicious_crypto.exe",
        "command_line": "--pool stratum+tcp://pool.mine.com",
        "username": "User",
        "cpu_percent": 90.5,
        "memory_mb": 800.0,
        "memory_percent": 5.0,
        "disk_read_bytes_sec": 0.0,
        "disk_write_bytes_sec": 0.0,
        "num_threads": 16,
        "num_handles": 100,
        "is_known_software": False,
        "is_client_program": True,
        "is_resource_heavy": True,
        "resource_score": 98.5,
        "category": "Неизвестное ПО"
    }
    res_eval = client.post("/api/client-resources/evaluate", json=sample_program)
    assert res_eval.status_code == 200
    eval_data = res_eval.json()
    assert eval_data["program_name"] == "suspicious_crypto.exe"
    assert "verdict" in eval_data
    assert "analysis" in eval_data
    assert isinstance(eval_data["recommendations"], list)
