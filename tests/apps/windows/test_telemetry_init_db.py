# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Apps Windows - Test Telemetry Init Db
# =============================================================================
# Description:
#   Модульные тесты для инициализатора и верификатора базы данных телеметрии.
#
# Usage Examples:
#   Python API:
#     from tests.apps.windows.test_telemetry_init_db import test_get_default_telemetry_db_path
#
#     res = test_get_default_telemetry_db_path()
#
# File: test_telemetry_init_db.py
# Project: ai-breadboard
# Package: tests.apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

from __future__ import annotations
"""Модульные тесты для инициализатора и верификатора базы данных телеметрии."""

import os
from pathlib import Path
import pytest
import sqlite3

from apps.windows.telemetry.init_db import (
    get_default_telemetry_db_path,
    init_telemetry_database,
)


def test_get_default_telemetry_db_path() -> None:
    """Проверяет корректность формирования пути к базе данных по умолчанию."""
    path = get_default_telemetry_db_path()
    assert isinstance(path, Path)
    assert path.name == "telemetry.db"
    assert "AI-Breadboard" in str(path)


def test_init_telemetry_database_creates_new_db(tmp_path: Path) -> None:
    """Проверяет создание новой базы данных со всеми таблицами при ее отсутствии."""
    db_file = tmp_path / "test_telemetry_init.db"
    assert not db_file.exists()

    res = init_telemetry_database(db_path=db_file, force=False)

    assert res["status"] == "success"
    assert res["exists"] is True
    assert res["created"] is True
    assert res["tables_count"] > 0
    assert res["integrity_ok"] is True
    assert "system_snapshots" in res["tables"]
    assert "sensor_polls" in res["tables"]
    assert "process_snapshots" in res["tables"]
    assert db_file.exists()


def test_init_telemetry_database_existing_db(tmp_path: Path) -> None:
    """Проверяет обработку уже существующей базы данных без повторного создания."""
    db_file = tmp_path / "existing_telemetry.db"
    # Первичная инициализация
    res1 = init_telemetry_database(db_path=db_file)
    assert res1["created"] is True

    # Повторная проверка
    res2 = init_telemetry_database(db_path=db_file, force=False)
    assert res2["status"] == "success"
    assert res2["exists"] is True
    assert res2["created"] is False
    assert res2["tables_count"] == res1["tables_count"]
    assert res2["integrity_ok"] is True


def test_init_telemetry_database_force(tmp_path: Path) -> None:
    """Проверяет принудительную реинициализацию структуры базы данных."""
    db_file = tmp_path / "force_telemetry.db"
    init_telemetry_database(db_path=db_file)
    assert db_file.exists()

    res_force = init_telemetry_database(db_path=db_file, force=True)
    assert res_force["created"] is True
    assert res_force["integrity_ok"] is True
