# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Apps Windows - Test Telemetry Research Assistant
# =============================================================================
# Description:
#   Unit-тесты для AI-ассистента телеметрии, SQL-движка и генерации графиков.
#
# Usage Examples:
#   Python API:
#     from tests.apps.windows.test_telemetry_research_assistant import temp_telemetry_db
#
#     res = temp_telemetry_db()
#
# File: test_telemetry_research_assistant.py
# Project: ai-breadboard
# Package: tests.apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

"""Unit-тесты для AI-ассистента телеметрии, SQL-движка и генерации графиков."""

import pytest
import sqlite3
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient
from apps.windows.telemetry_research.query_engine import TelemetryQueryEngine
from apps.windows.telemetry_research.assistant import TelemetryAssistant
from apps.windows.telemetry_research.server import app


@pytest.fixture
def temp_telemetry_db(tmp_path: Path):
    """Создает временную SQLite базу данных со структурой и тестовыми записями telemetry.db."""
    db_file = tmp_path / "test_telemetry.db"
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()

    # Таблица system_snapshots
    cursor.execute("""
        CREATE TABLE system_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            created_at REAL NOT NULL,
            cpu_total_percent REAL,
            cpu_frequency_mhz REAL,
            memory_used_gb REAL,
            gpu_load_percent REAL,
            uptime_seconds REAL
        )
    """)
    for i in range(1, 21):
        cursor.execute(
            "INSERT INTO system_snapshots (timestamp, created_at, cpu_total_percent, cpu_frequency_mhz, memory_used_gb, gpu_load_percent, uptime_seconds) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (f"2026-10-01T02:{i:02d}:00Z", 1700000000.0 + i * 60, 10.0 + (i % 5) * 5, 2900.0 + i * 10, 8.5, 5.0 + i, 3600 + i * 60),
        )

    # Таблица sensor_polls (категория Powers)
    cursor.execute("""
        CREATE TABLE sensor_polls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hardware_name TEXT,
            sensor_name TEXT,
            sensor_category TEXT,
            unit TEXT,
            value REAL
        )
    """)
    cursor.execute("INSERT INTO sensor_polls (hardware_name, sensor_name, sensor_category, unit, value) VALUES ('Intel CPU', 'CPU Package', 'Powers', 'W', 25.5)")
    cursor.execute("INSERT INTO sensor_polls (hardware_name, sensor_name, sensor_category, unit, value) VALUES ('Intel CPU', 'CPU Cores', 'Powers', 'W', 18.0)")
    cursor.execute("INSERT INTO sensor_polls (hardware_name, sensor_name, sensor_category, unit, value) VALUES ('Intel CPU', 'CPU Memory', 'Powers', 'W', 2.0)")
    cursor.execute("INSERT INTO sensor_polls (hardware_name, sensor_name, sensor_category, unit, value) VALUES ('Nvidia GPU', 'GPU Power', 'Powers', 'W', 15.0)")

    # Таблица process_snapshots
    cursor.execute("""
        CREATE TABLE process_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            cpu_percent REAL,
            memory_mb REAL
        )
    """)
    cursor.execute("INSERT INTO process_snapshots (name, cpu_percent, memory_mb) VALUES ('chrome.exe', 12.5, 850.0)")
    cursor.execute("INSERT INTO process_snapshots (name, cpu_percent, memory_mb) VALUES ('python.exe', 8.2, 320.0)")
    cursor.execute("INSERT INTO process_snapshots (name, cpu_percent, memory_mb) VALUES ('code.exe', 4.1, 410.0)")

    conn.commit()
    conn.close()
    return db_file


def test_query_engine_cpu_timeline(temp_telemetry_db: Path):
    """Проверка выборки временного ряда загрузки процессора."""
    engine = TelemetryQueryEngine()
    result = engine.get_cpu_timeline(limit=15, db_path=temp_telemetry_db)

    assert result["status"] == "ok"
    assert len(result["labels"]) == 15
    assert len(result["cpu_load"]) == 15
    assert len(result["cpu_freq_ghz"]) == 15
    assert result["chart"]["type"] == "line"
    assert result["statistics"]["avg_cpu_percent"] > 0


def test_query_engine_power_calculation(temp_telemetry_db: Path):
    """Проверка расчета суточного энергопотребления и круговой диаграммы."""
    engine = TelemetryQueryEngine()
    result = engine.calculate_power_consumption_24h(db_path=temp_telemetry_db, hours=24)

    assert result["status"] == "ok"
    assert result["total_kwh"] > 0.0
    assert result["avg_system_power_watts"] > 0.0
    assert result["chart"]["type"] == "doughnut"
    assert len(result["chart"]["labels"]) > 0
    assert len(result["breakdown"]) == len(result["chart"]["labels"])


def test_query_engine_safe_sql(temp_telemetry_db: Path):
    """Проверка безопасного выполнения SELECT запросов."""
    engine = TelemetryQueryEngine()

    # Корректный SELECT
    res = engine.execute_safe_sql("SELECT name, cpu_percent FROM process_snapshots", db_path=temp_telemetry_db)
    assert res["status"] == "ok"
    assert res["count"] == 3
    assert "name" in res["columns"]

    # Запрет не-SELECT выражений
    res_drop = engine.execute_safe_sql("DROP TABLE system_snapshots", db_path=temp_telemetry_db)
    assert res_drop["status"] == "error"
    assert "Разрешены только запросы" in res_drop["message"]


@pytest.mark.asyncio
async def test_assistant_cpu_timeline_query(temp_telemetry_db: Path):
    """Проверка обработки вопроса о графике ЦПУ."""
    engine = TelemetryQueryEngine()
    assistant = TelemetryAssistant(query_engine=engine)

    res = await assistant.handle_query(
        "покажи график загрузки цпу по времени", source_path=str(temp_telemetry_db)
    )

    assert res["status"] == "ok"
    assert "Анализ динамики загрузки" in res["reply"]
    assert res["chart"] is not None
    assert res["chart"]["type"] == "line"
    assert len(res["sql_queries"]) > 0


@pytest.mark.asyncio
async def test_assistant_power_doughnut_query(temp_telemetry_db: Path):
    """Проверка обработки вопроса о суточном потреблении электроэнергии."""
    engine = TelemetryQueryEngine()
    assistant = TelemetryAssistant(query_engine=engine)

    res = await assistant.handle_query(
        "Посчитай примерное общее потребление электроэнергии компьютреом и покажи суточную круговую диаграмма",
        source_path=str(temp_telemetry_db),
    )

    assert res["status"] == "ok"
    assert "Расчет суточного энергопотребления" in res["reply"]
    assert res["chart"] is not None
    assert res["chart"]["type"] == "doughnut"
    assert "total_kwh_24h" in res["metrics_summary"]


@pytest.mark.asyncio
async def test_assistant_direct_sql_query(temp_telemetry_db: Path):
    """Проверка прямого SQL-запроса через ассистента."""
    engine = TelemetryQueryEngine()
    assistant = TelemetryAssistant(query_engine=engine)

    res = await assistant.handle_query(
        "SELECT id, timestamp, cpu_total_percent FROM system_snapshots LIMIT 3",
        source_path=str(temp_telemetry_db),
    )

    assert res["status"] == "ok"
    assert "Результаты SQL-запроса" in res["reply"]
    assert res["metrics_summary"]["rows_count"] == 3


def test_api_chat_endpoint(temp_telemetry_db: Path):
    """Проверка FastAPI эндпоинта /api/chat."""
    client = TestClient(app)

    # 1. Запрос графика ЦП
    resp = client.post(
        "/api/chat",
        json={
            "message": "покажи график загрузки цпу по времени",
            "source_path": str(temp_telemetry_db),
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["chart"]["type"] == "line"

    # 2. Запрос мощности
    resp_power = client.post(
        "/api/chat",
        json={
            "message": "Посчитай примерное общее потребление электроэнергии компьютреом и покажи суточную круговую диаграмма",
            "source_path": str(temp_telemetry_db),
        },
    )
    assert resp_power.status_code == 200
    data_power = resp_power.json()
    assert data_power["status"] == "ok"
    assert data_power["chart"]["type"] == "doughnut"

    # 3. Прямой API вызов инструмента мощности
    resp_tool = client.get(f"/api/telemetry-sql/power?db_path={temp_telemetry_db}&hours=24")
    assert resp_tool.status_code == 200
    assert resp_tool.json()["status"] == "ok"
