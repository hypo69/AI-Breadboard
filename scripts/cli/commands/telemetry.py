# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Scripts Cli Commands - Telemetry
# =============================================================================
# Description:
#   Команды управления телеметрией и аудитом оборудования (telemetry).
#
# Usage Examples:
#   Python API:
#     from scripts.cli.commands.telemetry import register_telemetry_parser
#
#     res = register_telemetry_parser()
#
# File: telemetry.py
# Project: ai-breadboard
# Package: scripts.cli.commands
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:27:07
# =============================================================================

from __future__ import annotations
"""Команды управления телеметрией и аудитом оборудования (telemetry)."""

# -*- coding: utf-8 -*-
# Updated: 2026-10-01 09:30:00
"""Команды управления телеметрией и аудитом оборудования (telemetry)."""
import argparse


def register_telemetry_parser(subparsers: argparse._SubParsersAction) -> None:
    """Регистрация аргументов команды telemetry."""
    telemetry_parser = subparsers.add_parser('telemetry', help='System metrics 1Hz logging, hardware audit, drivers, and history archives')
    telemetry_subparsers = telemetry_parser.add_subparsers(dest='subcommand', help='Subcommands')
    telemetry_start = telemetry_subparsers.add_parser('start', help='Start 1Hz telemetry logging loop')
    telemetry_start.add_argument('--interval', '-i', type=float, default=1.0, help='Logging interval in seconds (default: 1.0)')
    telemetry_start.add_argument('--processes', '-p', type=int, default=20, help='Top processes limit (default: 20)')
    telemetry_subparsers.add_parser('status', help='View telemetry & hardware archives status')
    telemetry_init = telemetry_subparsers.add_parser('init-db', help='Initialize and verify SQLite database telemetry.db')
    telemetry_init.add_argument('--force', action='store_true', help='Force reinitialize structure')
    telemetry_init.add_argument('--db-path', type=str, default=None, help='Custom path to telemetry.db')
    telemetry_history = telemetry_subparsers.add_parser('history', help='View saved hardware archive snapshots')
    telemetry_history.add_argument('--limit', '-n', type=int, default=20, help='Limit snapshots count')
    telemetry_subparsers.add_parser('audit', help='Perform live deep hardware & driver audit with sensors')
    telemetry_subparsers.add_parser('changes', help='View hardware configuration changes timeline (Diff)')
    telemetry_subparsers.add_parser('archive', help='Force capture and archive current hardware state')
    telemetry_reboots = telemetry_subparsers.add_parser('reboots', help='Analyze Windows boot and shutdown causes (Reboot Analyzer)')
    telemetry_reboots.add_argument('--limit', '-n', type=int, default=10, help='Limit reboot sessions count (default: 10)')
    telemetry_reboots.add_argument('--json', action='store_true', help='Output in JSON format')
    telemetry_cleanup = telemetry_subparsers.add_parser('cleanup', help='Delete old telemetry records')
    telemetry_cleanup.add_argument('--days', '-d', type=int, default=7, help='Retention days (default: 7)')



def run_telemetry_command(args: argparse.Namespace) -> int:
    """Управление посекундным логированием системной телеметрии и процессами в SQLite."""
    from apps.windows.telemetry import HardwareHistoryManager, SystemCollector, TelemetryLoggerService
    history_mgr = HardwareHistoryManager()
    collector = SystemCollector()
    sub = args.subcommand
    if sub in ('init-db', 'init_db', 'build-db', 'init'):
        from apps.windows.telemetry.init_db import init_telemetry_database
        res = init_telemetry_database(
            db_path=getattr(args, 'db_path', None),
            force=getattr(args, 'force', False),
        )
        status_icon = '✅' if res['integrity_ok'] else '⚠️'
        print(f"\n{status_icon} База данных телеметрии: {res['db_path']}")
        print(f"   • Существует:     {res['exists']}")
        print(f"   • Вновь создана:  {res['created']}")
        print(f"   • Размер файла:   {res['size_mb']} МБ ({res['size_bytes']} байт)")
        print(f"   • Таблиц в схеме: {res['tables_count']}")
        print(f"   • Целостность:    {res['integrity_message']}\n")
        return 0 if res['integrity_ok'] else 1
    if sub == 'status':
        history_list = history_mgr.get_history(limit=5)
        latest = history_mgr.get_latest_archive()
        print('\n--- СТАТУС ТЕЛЕМЕТРИИ И АРХИВОВ ОБОРУДОВАНИЯ ---')
        print(f'Каталог архивов:        {history_mgr.archive_dir}')
        print(f'Всего архивных записей: {len(history_list)}')
        if latest:
            print(f'Последний архив:        {latest.archive_id} ({latest.timestamp})')
            print(f'Устройств в архиве:     {latest.devices_count}')
            print(f'Сводка:                 {latest.report.summary}')
        else:
            print('Архивные снимки:        Пока не созданы')
        print('------------------------------------------------\n')
        return 0
    if sub in ('history', 'list'):
        limit = getattr(args, 'limit', 20) or 20
        history_list = history_mgr.get_history(limit=limit)
        print(f'\n--- ПОСЛЕДНИЕ {len(history_list)} АРХИВОВ ОБОРУДОВАНИЯ ---')
        print(f"{'#ID АРХИВА':<32} | {'ВРЕМЯ (UTC)':<20} | {'УСТРОЙСТВ':<10} | {'ОШИБОК':<8} | {'ИЗМЕНЕНИЙ':<10}")
        print('-' * 90)
        for h in history_list:
            ts = h.get('timestamp', '')[:19].replace('T', ' ')
            print(f"{h.get('archive_id', ''):<32} | {ts:<20} | {h.get('devices_count', 0):<10} | {h.get('problem_devices_count', 0):<8} | {h.get('changes_count', 0):<10}")
        print('----------------------------------------------------------\n')
        return 0
    if sub == 'audit':
        print('\n[+] Запуск аудита аппаратного обеспечения, драйверов и сенсоров...')
        report = collector.get_hardware_audit()
        print(f'\n--- РЕЗУЛЬТАТЫ АУДИТА ОБОРУДОВАНИЯ ({report.devices_count} устройств) ---')
        print(f'Проблемных PnP: {report.problem_devices_count} | С устаревшими драйверами: {report.outdated_drivers_count}')
        print('-' * 110)
        print(f"{'УСТРОЙСТВО':<35} | {'КЛАСС':<12} | {'ДРАЙВЕР':<15} | {'ВЕРСИЯ':<15} | {'ДАТА / АКТУАЛЬНОСТЬ':<25}")
        print('-' * 110)
        for dev in report.devices[:25]:
            d_name = dev.name[:33]
            cls_name = dev.device_class[:10]
            drv_name = (dev.driver.name if dev.driver else 'N/A')[:13]
            drv_ver = (dev.driver.driver_version if dev.driver else 'N/A')[:13]
            curr = f"{dev.driver.driver_date or ''} ({dev.driver.currency_status})" if dev.driver else 'N/A'
            print(f'{d_name:<35} | {cls_name:<12} | {drv_name:<15} | {drv_ver:<15} | {curr[:25]:<25}')
        if len(report.devices) > 25:
            print(f'... и ещё {len(report.devices) - 25} устройств.')
        print('--------------------------------------------------------------------------------------------------------------\n')
        return 0
    if sub == 'changes':
        changes = history_mgr.get_change_timeline(limit=30)
        print(f'\n--- ТАЙМЛАЙН ИЗМЕНЕНИЙ ОБОРУДОВАНИЯ ({len(changes)} событий) ---')
        if not changes:
            print('Изменений аппаратной конфигурации пока не зафиксировано.')
        for c in changes:
            ts = c.timestamp[:19].replace('T', ' ')
            print(f'[{ts}] [{c.change_type.upper()}] {c.description}')
        print('-----------------------------------------------------------------\n')
        return 0
    if sub == 'archive':
        print('\n[+] Фиксация текущего снимка оборудования в архив...')
        entry = collector.archive_hardware_state(auto_diff=True)
        print(f'[OK] Создан архив: {entry.archive_id} (Устройств: {entry.devices_count}, Изменений: {entry.changes_count})\n')
        return 0
    if sub in ('reboots', 'reboot'):
        from apps.windows.telemetry.reboot_analyzer import WindowsRebootAnalyzer
        import json
        limit = getattr(args, 'limit', 10) or 10
        analyzer = WindowsRebootAnalyzer()
        report = analyzer.collect_reboot_history(limit=limit, persist_to_storage=True)
        if getattr(args, 'json', False):
            print(json.dumps(report.model_dump(), ensure_ascii=False, indent=2))
            return 0
        print('\n=== АНАЛИЗАТОР ПЕРЕЗАГРУЗОК И ВЫКЛЮЧЕНИЙ WINDOWS ===')
        print(f"Хост: {report.hostname} | Текущий запуск: {report.current_boot_time} (Аптайм: {report.current_uptime_human})")
        print(f"Статистика: {report.total_reboots_analyzed} перезапусков | Плановых: {report.planned_count} | Обновлений: {report.update_reboot_count} | Аварийных: {report.unexpected_count} | BSOD: {report.bsod_count}")
        print(f"Индекс надежности: {report.stability_score}%/100%\n")
        print('─' * 70)
        for s in report.sessions:
            print(f"[{s.shutdown_type.value}] Сессия: {s.boot_id}")
            print(f"  Запуск: {s.boot_time} | Предыдущий: {s.previous_boot_time or 'N/A'} | Аптайм сессии: {s.uptime_human or 'N/A'}")
            print(f"  Заключение: {s.conclusion}")
            if s.initiating_process:
                print(f"  Инициатор (1074): {s.initiating_process} (пользователь: {s.initiating_user or 'N/A'})")
            if s.reason_text:
                print(f"  Причина: {s.reason_text} (код: {s.reason_code or 'N/A'})")
            if s.bugcheck_code:
                print(f"  BSOD StopCode: {s.bugcheck_code}")
            if s.windows_update_kb:
                print(f"  Обновление: {s.windows_update_kb}")
            if s.evidence:
                print(f"  Улики: {' | '.join(s.evidence[:3])}")
            print('─' * 70)
        return 0
    if sub == 'start':
        interval = getattr(args, 'interval', 1.0)
        processes = getattr(args, 'processes', 20)
        print(f'\n[+] Запуск сервиса телеметрии с интервалом {interval}с, лимит процессов: {processes}...')
        try:
            service = TelemetryLoggerService(interval_sec=float(interval), top_processes=int(processes))
            service.start()
            print(f"[OK] Телеметрия запущена (PID: {(service._thread.ident if service._thread else 'N/A')})\n")
            return 0
        except Exception as e:
            print(f'[ERROR] Failed to start telemetry: {e}')
            return 1
    if sub == 'cleanup':
        days = getattr(args, 'days', 7)
        print(f'\n[+] Удаление архивов старше {days} дней...')
        try:
            removed = history_mgr.cleanup_old_archives(days=int(days))
            print(f'[OK] Удалено {removed} архивов\n')
            return 0
        except Exception as e:
            print(f'[ERROR] Failed to cleanup archives: {e}')
            return 1
    print(f'Неизвестная подкоманда telemetry: {sub}')
    return 1
