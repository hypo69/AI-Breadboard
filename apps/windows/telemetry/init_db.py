# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry - Init Db
# =============================================================================
# Description:
#   Модуль проверки, создания и валидации целостности структуры базы данных
#
# Usage Examples:
#   CLI:
#     python -m apps.windows.telemetry.init_db
#   Python API:
#     from apps.windows.telemetry.init_db import get_default_telemetry_db_path
#
#     res = get_default_telemetry_db_path()
#
# File: init_db.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 07:50:00
# =============================================================================

from __future__ import annotations
"""Модуль проверки, создания и валидации целостности структуры базы данных"""

import argparse
import json
import os
from pathlib import Path
import sqlite3
import sys
from typing import Any, Dict, List, Optional, Union

_project_root = str(Path(__file__).resolve().parents[3])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
if __package__ in (None, ''):
    __package__ = 'apps.windows.telemetry'

try:
    from logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from .sqlite import TelemetryStorage


def get_default_telemetry_db_path() -> Path:
    """Возвращает стандартный путь к файлу базы данных telemetry.db.

    Returns:
        Path: Путь к файлу telemetry.db в каталоге логов приложения.
    """
    programdata = os.environ.get('ProgramData') or os.environ.get('ALLUSERSPROFILE')
    if programdata and os.path.exists(programdata):
        base_dir = Path(programdata)
    else:
        appdata = os.environ.get('APPDATA') or os.environ.get('LOCALAPPDATA')
        if appdata and os.path.exists(appdata):
            base_dir = Path(appdata)
        else:
            base_dir = Path.home() / '.config'
    return base_dir / 'AI-Breadboard' / 'apps' / 'windows' / 'telemetry' / 'logs' / 'telemetry.db'


def init_telemetry_database(
    db_path: Optional[Union[str, Path]] = None,
    force: bool = False,
    check_integrity: bool = True,
) -> Dict[str, Any]:
    """Инициализирует базу данных telemetry.db, создавая все таблицы и индексы при отсутствии.

    Args:
        db_path: Путь к целевому файлу SQLite базы данных (по умолчанию стандартный путь).
        force: Принудительно переинициализировать структуру таблиц.
        check_integrity: Выполнить проверку целостности PRAGMA integrity_check.

    Returns:
        Dict[str, Any]: Словарь с результатами инициализации и метаданными БД.
    """
    target_path = Path(db_path) if db_path else get_default_telemetry_db_path()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    was_created = False
    if not target_path.exists() or force:
        logger.debug(f'Инициализация новой базы данных телеметрии по пути: {target_path}')
        storage = TelemetryStorage(db_path=target_path)
        was_created = True
    else:
        storage = TelemetryStorage.get_instance(db_path=target_path)

    # Получение списка созданных таблиц
    tables: List[str] = []
    integrity_ok = True
    integrity_msg = 'ok'

    try:
        with sqlite3.connect(str(target_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = sorted([row[0] for row in cursor.fetchall()])

            if check_integrity:
                cursor.execute('PRAGMA integrity_check;')
                res = cursor.fetchone()
                if res and res[0] != 'ok':
                    integrity_ok = False
                    integrity_msg = str(res[0])
    except Exception as ex:
        logger.error(f'Ошибка проверки схемы и целостности БД {target_path}: {ex}')
        integrity_ok = False
        integrity_msg = str(ex)

    size_bytes = target_path.stat().st_size if target_path.exists() else 0
    size_mb = round(size_bytes / (1024 * 1024), 3)

    result = {
        'status': 'success' if integrity_ok else 'warning',
        'db_path': str(target_path),
        'exists': target_path.exists(),
        'created': was_created,
        'size_bytes': size_bytes,
        'size_mb': size_mb,
        'tables_count': len(tables),
        'tables': tables,
        'integrity_ok': integrity_ok,
        'integrity_message': integrity_msg,
    }

    if was_created:
        logger.info(f'✅ База данных telemetry.db успешно создана: {len(tables)} таблиц ({size_mb} МБ)')
    else:
        logger.debug(f'База данных telemetry.db подтверждена: {len(tables)} таблиц ({size_mb} МБ)')

    return result


def main() -> int:
    """Точка входа CLI для инициализации и проверки базы данных телеметрии."""
    parser = argparse.ArgumentParser(
        description='Инициализатор и верификатор SQLite базы данных системной телеметрии (telemetry.db)'
    )
    parser.add_argument('--db-path', type=str, default=None, help='Пользовательский путь к telemetry.db')
    parser.add_argument('--force', action='store_true', help='Принудительно переинициализировать структуру')
    parser.add_argument('--check-only', action='store_true', help='Только проверить существующую БД без создания')
    parser.add_argument('--json', action='store_true', help='Вывод результата в формате JSON')

    args = parser.parse_args()

    target_path = Path(args.db_path) if args.db_path else get_default_telemetry_db_path()

    if args.check_only and not target_path.exists():
        if args.json:
            print(json.dumps({'status': 'error', 'message': f'Файл не найден: {target_path}', 'exists': False}, ensure_ascii=False))
        else:
            print(f'❌ База данных телеметрии не найдена: {target_path}')
        return 1

    res = init_telemetry_database(db_path=args.db_path, force=args.force)

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        status_icon = '✅' if res['integrity_ok'] else '⚠️'
        print(f"\n{status_icon} База данных телеметрии: {res['db_path']}")
        print(f"   • Существует:     {res['exists']}")
        print(f"   • Вновь создана:  {res['created']}")
        print(f"   • Размер файла:   {res['size_mb']} МБ ({res['size_bytes']} байт)")
        print(f"   • Таблиц в схеме: {res['tables_count']}")
        print(f"   • Целостность:    {res['integrity_message']}")
        if res['tables']:
            print(f"   • Таблицы:        {', '.join(res['tables'][:8])}{'...' if len(res['tables']) > 8 else ''}")
        print('')

    return 0 if res['integrity_ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
