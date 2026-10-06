# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry - CLI Controller
# =============================================================================
# Description:
#   Консольный контроллер AITelemetryCtl для мониторинга, управления службой
#   Windows Service, проверки базы данных и выполнения диагностики.
#
# Usage Examples:
#   CLI:
#     AITelemetryCtl.exe status
#     AITelemetryCtl.exe start
#     AITelemetryCtl.exe stop
#     AITelemetryCtl.exe restart
#     AITelemetryCtl.exe diagnose
#     AITelemetryCtl.exe database
#
# File: ctl.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 07:58:00
# =============================================================================

from __future__ import annotations
"""Консольная утилита управления и диагностики службы AITelemetry."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

_current_dir = Path(__file__).resolve().parent
_project_root = str(_current_dir.parents[2]) if len(_current_dir.parents) >= 3 else str(_current_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


def get_service_status_scm(service_name: str = 'AITelemetry') -> Dict[str, Any]:
    """Запрашивает состояние службы через Windows SCM (sc.exe).

    Args:
        service_name: Имя службы в диспетчере Windows.

    Returns:
        Dict[str, Any]: Словарь со статусом и деталями службы.
    """
    try:
        res = subprocess.run(
            ['sc.exe', 'query', service_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        output = res.stdout
        is_installed = res.returncode == 0
        state = 'UNKNOWN'
        if 'RUNNING' in output:
            state = 'RUNNING'
        elif 'STOPPED' in output:
            state = 'STOPPED'
        elif 'START_PENDING' in output:
            state = 'START_PENDING'
        elif 'STOP_PENDING' in output:
            state = 'STOP_PENDING'
        elif not is_installed:
            state = 'NOT_INSTALLED'

        return {
            'installed': is_installed,
            'state': state,
            'raw_output': output.strip()
        }
    except Exception as ex:
        return {'installed': False, 'state': 'ERROR', 'error': str(ex)}


def cmd_status() -> int:
    """Выводит подробный статус службы и базы данных."""
    print("=" * 60)
    print("       AITelemetry - Статус службы и мониторинга")
    print("=" * 60)

    scm_status = get_service_status_scm('AITelemetry')
    state = scm_status.get('state', 'UNKNOWN')
    state_icon = "🟢" if state == 'RUNNING' else ("🔴" if state == 'STOPPED' else "⚪")
    print(f"Служба Windows (SCM):   {state_icon} {state}")
    print(f"Установлена в системе: {'Да' if scm_status.get('installed') else 'Нет'}")

    try:
        from apps.windows.telemetry.telemetry_config import TelemetryConfigManager
        cfg_mgr = TelemetryConfigManager()
        cfg_path = cfg_mgr.config_path
        print(f"Файл конфигурации:     {cfg_path} (существует: {cfg_path.exists()})")
        print(f"Режим работы:          {cfg_mgr.get_mode()}")
        print(f"Интервал замеров:      {cfg_mgr.get_interval_seconds()} сек")
    except Exception as ex:
        print(f"Конфигурация:          Ошибка чтения ({ex})")

    try:
        from apps.windows.telemetry.sqlite import TelemetryStorage
        storage = TelemetryStorage.get_instance(read_only=True)
        db_path = storage.db_path
        print(f"База данных SQLite:    {db_path} (размер: {db_path.stat().st_size / 1024 / 1024:.2f} МБ)")
        stats = storage.get_storage_stats()
        print(f"Всего снимков (polls): {stats.get('snapshots_count', 0)}")
        print(f"Метрик процессов:      {stats.get('process_metrics_count', 0)}")
        print(f"Событий (events):      {stats.get('events_count', 0)}")
    except Exception as ex:
        print(f"База данных:           Недоступна ({ex})")

    print("=" * 60)
    return 0


def cmd_control(action: str) -> int:
    """Управляет службой через sc.exe / net.exe.

    Args:
        action: Действие ('start', 'stop', 'restart').

    Returns:
        int: Код возврата команды.
    """
    if action == 'start':
        print("Запуск службы AITelemetry...")
        res = subprocess.run(['net.exe', 'start', 'AITelemetry'])
        return res.returncode
    elif action == 'stop':
        print("Остановка службы AITelemetry...")
        res = subprocess.run(['net.exe', 'stop', 'AITelemetry'])
        return res.returncode
    elif action == 'restart':
        print("Перезапуск службы AITelemetry...")
        subprocess.run(['net.exe', 'stop', 'AITelemetry'])
        res = subprocess.run(['net.exe', 'start', 'AITelemetry'])
        return res.returncode
    return 1


def cmd_database() -> int:
    """Выводит детальную статистику таблиц SQLite."""
    try:
        from apps.windows.telemetry.sqlite import TelemetryStorage
        storage = TelemetryStorage.get_instance(read_only=True)
        stats = storage.get_storage_stats()
        print(json.dumps(stats, indent=2, ensure_ascii=False))
        return 0
    except Exception as ex:
        print(f"Ошибка чтения базы данных: {ex}")
        return 1


def cmd_diagnose() -> int:
    """Выполняет экспресс-диагностику системных метрик."""
    print("Выполнение глубокой диагностики системы...")
    try:
        from apps.windows.telemetry.collector import SystemCollector
        collector = SystemCollector()
        snapshot = collector.collect_snapshot(top_processes_limit=10)
        print(f"CPU: {snapshot.cpu.usage_percent:.1f}%")
        print(f"Память: {snapshot.memory.percent_used:.1f}% (Свободно: {snapshot.memory.available_mb / 1024:.2f} ГБ)")
        print(f"Количество процессов: {len(snapshot.processes)}")
        print("Диагностика успешно выполнена.")
        return 0
    except Exception as ex:
        print(f"Ошибка при диагностике: {ex}")
        return 1


def main() -> int:
    """Точка входа утилиты AITelemetryCtl."""
    parser = argparse.ArgumentParser(description='AITelemetry CLI Controller')
    subparsers = parser.add_subparsers(dest='command', help='Команды управления')

    subparsers.add_parser('status', help='Показать статус службы и БД')
    subparsers.add_parser('start', help='Запустить службу')
    subparsers.add_parser('stop', help='Остановить службу')
    subparsers.add_parser('restart', help='Перезапустить службу')
    subparsers.add_parser('database', help='Показать статистику базы данных')
    subparsers.add_parser('diagnose', help='Выполнить экспресс-диагностику')

    args = parser.parse_args()

    if not args.command or args.command == 'status':
        return cmd_status()
    elif args.command in ('start', 'stop', 'restart'):
        return cmd_control(args.command)
    elif args.command == 'database':
        return cmd_database()
    elif args.command == 'diagnose':
        return cmd_diagnose()
    return 0


if __name__ == '__main__':
    sys.exit(main())
