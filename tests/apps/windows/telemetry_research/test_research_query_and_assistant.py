# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Apps Windows Telemetry_Research - Test Research Query And Assistant
# =============================================================================
# Description:
#   Тесты SQL-движка и AI-ассистента исследования телеметрии без использования моков.
#
# Usage Examples:
#   Python API:
#     from tests.apps.windows.telemetry_research.test_research_query_and_assistant import TestTelemetryQueryEngine
#
#     service = TestTelemetryQueryEngine()
#
# File: test_research_query_and_assistant.py
# Project: ai-breadboard
# Package: tests.apps.windows.telemetry_research
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

from __future__ import annotations
"""Тесты SQL-движка и AI-ассистента исследования телеметрии без использования моков.

Updated: 2026-10-01 11:30:00"""

import sqlite3
from pathlib import Path
import pytest

from apps.windows.telemetry_research.query_engine import TelemetryQueryEngine
from apps.windows.telemetry_research.assistant import TelemetryAssistant


@pytest.fixture
def real_telemetry_db(tmp_path: Path):
    """Создает реальный файл базы данных SQLite со встроенными таблицами для проверок."""
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
    for i in range(1, 10):
        cursor.execute(
            "INSERT INTO system_snapshots (timestamp, created_at, cpu_total_percent, cpu_frequency_mhz, memory_used_gb, gpu_load_percent, uptime_seconds) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (f"2026-10-01T02:{i:02d}:00Z", 1700000000.0 + i * 60, 15.0 + i * 2, 3000.0, 8.0, 10.0, 3600),
        )

    # Таблица sensor_polls
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
    cursor.execute("INSERT INTO sensor_polls (hardware_name, sensor_name, sensor_category, unit, value) VALUES ('Intel CPU', 'CPU Package', 'Powers', 'W', 45.0)")
    cursor.execute("INSERT INTO sensor_polls (hardware_name, sensor_name, sensor_category, unit, value) VALUES ('Nvidia GPU', 'GPU Power', 'Powers', 'W', 65.0)")

    # Таблица process_snapshots
    cursor.execute("""
        CREATE TABLE process_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            cpu_percent REAL,
            memory_mb REAL,
            pid INTEGER
        )
    """)
    cursor.execute("INSERT INTO process_snapshots (name, cpu_percent, memory_mb, pid) VALUES ('python.exe', 12.5, 450.0, 1024)")
    cursor.execute("INSERT INTO process_snapshots (name, cpu_percent, memory_mb, pid) VALUES ('chrome.exe', 5.0, 1200.0, 2048)")

    conn.commit()
    conn.close()
    return db_file


class TestTelemetryQueryEngine:
    """Тестирование SQL-движка выборок telemetry.db."""

    def test_execute_safe_sql_valid_query(self, real_telemetry_db):
        """Проверка безопасного выполнения валидного SELECT-запроса."""
        engine = TelemetryQueryEngine()
        result = engine.execute_safe_sql("SELECT name, memory_mb FROM process_snapshots", db_path=real_telemetry_db)

        assert result["status"] == "ok"
        assert result["count"] == 2
        assert "name" in result["columns"]

    def test_execute_safe_sql_forbidden_statement(self, real_telemetry_db):
        """Проверка защиты от вызовов модифицирующих SQL операторов (DROP/DELETE/INSERT)."""
        engine = TelemetryQueryEngine()
        res_drop = engine.execute_safe_sql("DROP TABLE process_snapshots", db_path=real_telemetry_db)
        assert res_drop["status"] == "error"

        res_delete = engine.execute_safe_sql("DELETE FROM process_snapshots", db_path=real_telemetry_db)
        assert res_delete["status"] == "error"

    def test_get_cpu_timeline(self, real_telemetry_db):
        """Проверка специфического хелпера сбора временного ряда CPU."""
        engine = TelemetryQueryEngine()
        res = engine.get_cpu_timeline(db_path=real_telemetry_db)
        assert res["status"] == "ok"
        assert res["statistics"]["points_count"] == 9

    def test_calculate_power_consumption_24h(self, real_telemetry_db):
        """Проверка расчета энергопотребления по компонентам."""
        engine = TelemetryQueryEngine()
        res = engine.calculate_power_consumption_24h(db_path=real_telemetry_db)
        assert res["status"] == "ok"


class TestTelemetryAssistant:
    """Тестирование диалогового ассистента без использования сложного сетевого LLM-соединения."""

    @pytest.mark.asyncio
    async def test_handle_query_deterministic_intents(self, real_telemetry_db):
        """Проверка обработки намерений через ключевые слова в сообщениях."""
        assistant = TelemetryAssistant()

        # Намерение графиков CPU
        res_cpu = await assistant.handle_query("покажи график загрузки процессора cpu", source_path=str(real_telemetry_db))
        assert "reply" in res_cpu
        assert res_cpu["status"] == "ok"
        assert res_cpu["chart"] is not None

        # Намерение мощности
        res_power = await assistant.handle_query("сколько энергии потребляет система ватт", source_path=str(real_telemetry_db))
        assert res_power["status"] == "ok"

    @pytest.mark.asyncio
    async def test_handle_query_direct_sql(self, real_telemetry_db):
        """Проверка прямых SQL-запросов от пользователя."""
        assistant = TelemetryAssistant()
        res_sql = await assistant.handle_query("SELECT * FROM process_snapshots", source_path=str(real_telemetry_db))

        assert res_sql["status"] == "ok"
        assert "sql_queries" in res_sql
