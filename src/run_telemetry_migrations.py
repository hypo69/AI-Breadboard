# -*- coding: utf-8 -*-
"""Скрипт для применения всех отложенных миграций к базе telemetry.db.
Запуск: `python run_telemetry_migrations.py`
"""
import sys
import pathlib

# Добавляем корень проекта в sys.path
project_root = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from src.db.migrations import get_migration_manager

if __name__ == "__main__":
    manager = get_migration_manager()
    result = manager.apply_all_pending()
    print("Результат применения миграций:")
    print(result)
