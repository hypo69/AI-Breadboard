# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Cli
# =============================================================================
# Description:
#   CLI интерфейс для Windows AI Diagnostic & Administration Center.
#
# Usage Examples:
#   CLI:
#     python -m apps.windows.cli
#   Python API:
#     from apps.windows.cli import print_banner
#
#     res = print_banner()
#
# File: cli.py
# Project: ai-breadboard
# Package: apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 02:15:00
# =============================================================================

from __future__ import annotations
"""CLI интерфейс для Windows AI Diagnostic & Administration Center."""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

_project_root = str(Path(__file__).resolve().parents[2])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from apps.windows.ai.diagnostician import WindowsAIDiagnostician
from apps.windows.ai.root_cause_analyzer import WindowsAIRootCauseAnalyzer
from apps.windows.sdk.core.root_cause_engine import RootCauseEngine

def print_banner() -> None:
    """Печать приветственного баннера."""
    print('=' * 70)
    print('   AI WINDOWS DIAGNOSTIC & ADMINISTRATION CENTER')
    print('   Аналитический центр аудита, безопасности и оптимизации Windows')
    print('=' * 70)

def format_health_summary(report_dict: dict) -> None:
    """Форматированный вывод сводки здоровья."""
    score = report_dict.get('health_score', {})
    print(f"\n[+] SYSTEM HEALTH SCORE: {score.get('score')}/100 ({score.get('status_label')})")
    print(f"    Критические проблемы: {score.get('critical_count')}")
    print(f"    Предупреждения:       {score.get('medium_count')}")
    print(f"    Безопасные действия:  {score.get('low_count')}")
    print(f"    Всего фактов/находок: {score.get('total_findings')}")
    print('-' * 70)
    domains = report_dict.get('domains', {})
    for d_name, d_val in domains.items():
        title = d_val.get('title_ru', d_name)
        status = d_val.get('status', 'ok').upper()
        findings = d_val.get('findings', [])
        print(f'  * [{status:<8}] {title} ({len(findings)} заметок)')
        for f in findings[:2]:
            print(f"      - {f.get('title')}")

def main() -> None:
    """Главная функция CLI."""
    parser = argparse.ArgumentParser(description='AI Windows Diagnostic & Administration Center')
    parser.add_argument('--mode', choices=['quick', 'full', 'security', 'performance', 'drivers', 'clean', 'postinstall', 'inspector', 'dashboard', 'server'], default='quick', help='Режим аудита системы или запуск сервиса/инспектора')
    parser.add_argument('--inspector', action='store_true', help='Запустить интерактивный системный инспектор (System & Hardware Inspector)')
    parser.add_argument('--investigate', type=str, help='Расследовать причину проблемы по описанию симптома')
    parser.add_argument('--json', action='store_true', help='Вывести результат в формате JSON')
    parser.add_argument('--server', action='store_true', help='Запустить сервер FastAPI')
    parser.add_argument('--port', type=int, default=8105, help='Порт сервера FastAPI (по умолчанию: 8105)')
    parser.add_argument('--tui', action='store_true', help='Запустить интерактивный TUI интерфейс')
    parser.add_argument('--logs', action='store_true', help='Запустить интерактивный монитор системных логов в терминале (System Log Viewer)')
    parser.add_argument('--channel', type=str, default='System', help='Канал логов для монитора (по умолчанию: System)')
    parser.add_argument('--hardware', '--hw-monitor', action='store_true', dest='hardware_monitor', help='Запустить интерактивный TUI монитор оборудования (Hardware Monitor)')
    parser.add_argument('--hw-json', action='store_true', help='Вывести текущий слепок состояния оборудования в формате JSON')
    parser.add_argument('--reboots', action='store_true', help='Анализ причин перезагрузок и выключений ОС (Reboot Analyzer)')
    parser.add_argument('--reboot-limit', type=int, default=10, help='Количество сессий перезагрузки для анализа (по умолчанию: 10)')
    parser.add_argument('--providers', action='store_true', help='Отобразить статус всех аппаратных провайдеров и утилит в /bin')
    parser.add_argument('--cross-check', action='store_true', help='Запустить перекрестную проверку (cross-check) данных оборудования')
    parser.add_argument('--identity', action='store_true', help='Отобразить контекст безопасности и маркер доступа текущего пользователя')
    parser.add_argument('--explain-user', type=str, help='Сформировать полное досье субъекта безопасности (Principal) по имени или SID')
    parser.add_argument('--explain-pid', type=int, help='Исследовать контекст безопасности процесса (PID -> Token -> Account -> Groups -> Integrity -> Elevation)')
    parser.add_argument('--who-is-admin', action='store_true', help='Найти всех администраторов системы с цепочками путей вложенных групп')
    parser.add_argument('--who-can-logon-as-service', action='store_true', help='Найти аккаунты с правом входа в качестве службы (SeServiceLogonRight)')
    parser.add_argument('--who-can-rdp', action='store_true', help='Найти аккаунты с доступом к удаленному рабочему столу (RDP)')
    parser.add_argument('--orphaned-sids', action='store_true', help='Найти осиротевшие SID в профилях и правах безопасности')
    parser.add_argument('--identity-graph', action='store_true', help='Построить и отобразить полный Windows Identity Graph')
    # Windows Security Event Log
    parser.add_argument('--security-status', action='store_true', help='Отобразить статус журнала безопасности и политик аудита (Security Event Log)')
    parser.add_argument('--security-tail', action='store_true', help='Вывести последние события журнала Security в реальном времени')
    parser.add_argument('--security-search', type=int, help='Найти события по Event ID (например 4624, 4688)')
    parser.add_argument('--security-user', type=str, help='Найти события безопасности по имени пользователя')
    parser.add_argument('--security-process', type=str, help='Найти события создания процессов (Event 4688)')
    parser.add_argument('--security-failed-logons', action='store_true', help='Найти неудачные попытки входа в систему (Event 4625, 4771)')
    parser.add_argument('--security-collect', action='store_true', help='Запустить инкрементальный сбор событий из Security.evtx')
    parser.add_argument('--security-correlate', action='store_true', help='Выполнить корреляцию событий безопасности с телеметрией процессов и ресурсов')
    # Windows Event Log Catalog & Domains
    parser.add_argument('--logs-catalog', action='store_true', help='Отобразить каталог провайдеров и каналов Windows Event Log (7 доменов телеметрии)')
    parser.add_argument('--logs-domains', action='store_true', help='Сводная статистика по 7 доменам телеметрии Windows Event Log')
    parser.add_argument('--process-provenance', type=str, nargs='?', const='all', help='Построить граф происхождения процессов (User -> Process -> Parent -> Service -> Task)')
    parser.add_argument('--power-lifecycle', action='store_true', help='Реконструировать таймлайн жизненного цикла ОС (Boot -> Sleep -> Wake -> Shutdown -> Crash)')
    parser.add_argument('--sysmon-status', action='store_true', help='Проверить статус и конфигурацию Sysmon Observability Layer')
    parser.add_argument('--event-limit', type=int, default=25, help='Лимит событий для выборки (по умолчанию: 25)')
    args = parser.parse_args()

    if args.security_status or args.security_tail or args.security_search or args.security_user or args.security_process or args.security_failed_logons or args.security_collect or args.security_correlate:
        from apps.windows.telemetry.security_collector import WindowsSecurityCollector
        sec_collector = WindowsSecurityCollector()
        if args.security_status:
            status = sec_collector.check_access_and_audit()
            if args.json:
                print(json.dumps(status.model_dump(), ensure_ascii=False, indent=2))
                return
            acc_str = "🟢 Доступен" if status.accessible else f"🔴 Недоступен ({status.error})"
            print('\n=== СТАТУС ЖУРНАЛА БЕЗОПАСНОСТИ WINDOWS SECURITY ===')
            print(f"Канал Security:             {acc_str}")
            print(f"Всего событий в журнале ОС: {status.record_count:,}")
            print(f"Событий в telemetry.db:     {status.total_ingested_events:,}")
            print(f"Последний EventRecordID:    {status.last_record_id:,}")
            print(f"Аудит CommandLine (4688):   {'🟢 Включен' if status.command_line_audit_enabled else '⚪ Отключен'}")
            return
        if args.security_tail:
            events = sec_collector.get_live_tail(limit=args.event_limit)
            if args.json:
                print(json.dumps([e.model_dump() for e in events], ensure_ascii=False, indent=2))
                return
            print(f'\n=== ПОСЛЕДНИЕ {len(events)} СОБЫТИЙ SECURITY (LIVE TAIL) ===')
            for ev in reversed(events):
                print(f"  [{ev.timestamp}] Event {ev.event_id:<4} | {ev.message}")
            return
        if args.security_search:
            events = sec_collector.storage.get_security_events(event_id=args.security_search, limit=args.event_limit)
            if args.json:
                print(json.dumps(events, ensure_ascii=False, indent=2))
                return
            print(f'\n=== СОБЫТИЯ EVENT ID {args.security_search} ({len(events)} записей) ===')
            for ev in events:
                print(f"  [{ev.get('timestamp')}] ID {ev.get('event_id')} | {ev.get('message')}")
            return
        if args.security_user:
            events = sec_collector.storage.get_security_events(user=args.security_user, limit=args.event_limit)
            if args.json:
                print(json.dumps(events, ensure_ascii=False, indent=2))
                return
            print(f"\n=== СОБЫТИЯ БЕЗОПАСНОСТИ ПОЛЬЗОВАТЕЛЯ '{args.security_user}' ({len(events)} записей) ===")
            for ev in events:
                print(f"  [{ev.get('timestamp')}] Event {ev.get('event_id')} | {ev.get('message')}")
            return
        if args.security_process:
            events = sec_collector.storage.get_security_process_creations(process_name=args.security_process, limit=args.event_limit)
            if args.json:
                print(json.dumps(events, ensure_ascii=False, indent=2))
                return
            print(f"\n=== ЗАПУСКИ ПРОЦЕССА '{args.security_process}' (EVENT 4688) ({len(events)} записей) ===")
            for ev in events:
                print(f"  [{ev.get('timestamp')}] PID: {ev.get('process_id')} | User: {ev.get('subject_user')} | {ev.get('command_line') or ev.get('process_name')}")
            return
        if args.security_failed_logons:
            events = sec_collector.storage.get_security_failed_logons(limit=args.event_limit)
            if args.json:
                print(json.dumps(events, ensure_ascii=False, indent=2))
                return
            print(f'\n=== НЕУДАЧНЫЕ ПОПЫТКИ ВХОДА (EVENT 4625) ({len(events)} записей) ===')
            for ev in events:
                print(f"  [{ev.get('timestamp')}] User: {ev.get('target_user')} | IP: {ev.get('source_ip')} | {ev.get('message')}")
            return
        if args.security_collect:
            report = sec_collector.collect_incremental(batch_size=500, max_records=args.event_limit * 20, save_raw=False)
            if args.json:
                print(json.dumps(report.model_dump(), ensure_ascii=False, indent=2))
                return
            print('\n=== ИНКРЕМЕНТАЛЬНЫЙ СБОР СОБЫТИЙ SECURITY ===')
            print(f"Сохранено событий:       {report.total_events_ingested}")
            print(f"Последний EventRecordID: {report.last_record_id}")
            if report.events_by_id:
                print("Распределение по типам:")
                for eid, count in sorted(report.events_by_id.items(), key=lambda x: x[1], reverse=True)[:8]:
                    print(f"  Event {eid:<4}: {count} событий")
            return
        if args.security_correlate:
            corrs = sec_collector.correlate_security_with_telemetry(limit=args.event_limit)
            if args.json:
                print(json.dumps([c.model_dump() for c in corrs], ensure_ascii=False, indent=2))
                return
            print(f'\n=== КОРРЕЛЯЦИЯ СОБЫТИЙ БЕЗОПАСНОСТИ С ТЕЛЕМЕТРИЕЙ ({len(corrs)} цепочек) ===')
            for c in corrs:
                notes_str = "; ".join(c.notes) if c.notes else "нормальная активность"
                print(f"  * [{c.timestamp}] {c.event_type} | {c.user} -> {c.process_name} (PID {c.pid}) | {notes_str}")
            return

    if args.logs_catalog or args.logs_domains or args.process_provenance or args.power_lifecycle or args.sysmon_status:
        from apps.windows.telemetry.event_catalog import WindowsEventCatalogEngine
        catalog_engine = WindowsEventCatalogEngine()

        if args.logs_domains:
            summary = catalog_engine.get_domains_summary()
            if args.json:
                print(json.dumps(summary, ensure_ascii=False, indent=2))
                return
            print('\n=== СВОДКА 7 ДОМЕНОВ ТЕЛЕМЕТРИИ WINDOWS EVENT LOGS ===')
            print(f"Всего зарегистрировано провайдеров: {summary.get('total_registered_providers')}")
            print(f"Sysmon установлен: {'🟢 Да' if summary.get('sysmon_installed') else '⚪ Нет'}\n")
            for dom in summary.get('domains', []):
                print(f"  * {dom.get('title')} [{dom.get('status')}]")
                print(f"    Каналов: {dom.get('channels_count')} | Записей: {dom.get('total_records'):,} | Ключевые ID: {dom.get('key_events')}")
                print(f"    {dom.get('description')}\n")
            return

        if args.logs_catalog:
            catalog = catalog_engine.get_full_catalog()
            if args.json:
                from dataclasses import asdict
                print(json.dumps([asdict(c) for c in catalog], ensure_ascii=False, indent=2))
                return
            print(f'\n=== КАТАЛОГ ПРОВАЙДЕРОВ WINDOWS EVENT LOGS ({len(catalog)} провайдеров) ===')
            for entry in catalog:
                print(f"  [{entry.domain.value}] {entry.provider} -> {entry.channel}")
                print(f"    Объем: {entry.volume_rating} | Привилегии: {entry.privilege_required} | Записей: {entry.record_count:,}")
                print(f"    События: {list(entry.key_events.keys())}")
                print(f"    {entry.description}\n")
            return

        if args.process_provenance:
            target_proc = None if args.process_provenance == 'all' else args.process_provenance
            graph = catalog_engine.reconstruct_process_provenance(process_name=target_proc, limit=args.event_limit)
            if args.json:
                print(json.dumps(graph, ensure_ascii=False, indent=2))
                return
            print(f"\n=== ДЕРЕВО ПРОИСХОЖДЕНИЯ ПРОЦЕССОВ (PROVENANCE GRAPH) ===")
            print(f"Узлов: {graph.get('total_nodes')}, Связей: {graph.get('total_links')}\n")
            for node in graph.get('nodes', []):
                print(f"  * [{node.get('type')}] {node.get('name')} (PID {node.get('pid')}) | User: {node.get('user')}")
                if node.get('command_line'):
                    print(f"      CMD: {node.get('command_line')}")
            for link in graph.get('links', []):
                print(f"    -> {link.get('source')} ===[{link.get('relationship')}]===> {link.get('target')}")
            return

        if args.power_lifecycle:
            timeline = catalog_engine.reconstruct_power_lifecycle(hours=72)
            if args.json:
                print(json.dumps(timeline, ensure_ascii=False, indent=2))
                return
            print(f'\n=== ЖИЗНЕННЫЙ ЦИКЛ ПИТАНИЯ ОС (BOOT / SLEEP / CRASH / SHUTDOWN) ({len(timeline)} событий) ===')
            for item in timeline:
                print(f"  {item.get('icon')} [{item.get('timestamp')}] {item.get('phase'):<18} | Event {item.get('event_id')} ({item.get('provider')}) | {item.get('message')}")
            return

        if args.sysmon_status:
            status = catalog_engine.check_sysmon_status()
            if args.json:
                print(json.dumps(status, ensure_ascii=False, indent=2))
                return
            print('\n=== СТАТУС SYSMON OBSERVABILITY LAYER ===')
            inst_str = "🟢 Установлен" if status.get('installed') else "⚪ Не обнаружен"
            print(f"Статус службы:   {inst_str}")
            print(f"Канал логов:     {status.get('channel_name')}")
            print(f"Всего событий:   {status.get('record_count'):,}")
            print(f"Возможности:     {', '.join(status.get('capabilities', [])) or 'N/A'}")
            print(f"Рекомендации:    {status.get('recommended_config')}")
            return

    if args.reboots:
        from apps.windows.telemetry.reboot_analyzer import WindowsRebootAnalyzer
        analyzer = WindowsRebootAnalyzer()
        report = analyzer.collect_reboot_history(limit=args.reboot_limit, persist_to_storage=True)
        if args.json:
            print(json.dumps(report.model_dump(), ensure_ascii=False, indent=2))
            return
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
        return
    if args.providers:
        from apps.windows.hardware.registry import HardwareProviderRegistry
        reg = HardwareProviderRegistry()
        print('\n=== АППАРАТНЫЕ ПРОВАЙДЕРЫ WINDOWS DIAGNOSTIC ENGINE ===')
        for p in reg.get_all_providers():
            info = p.get_provider_info()
            status_symbol = '🟢' if info['status'] == 'AVAILABLE' or info['status'] == 'RUNNING' else '⚪'
            print(f"{status_symbol} [{info['tier_label']}] {info['name']}: {info['status']}")
            if info['binary_path']:
                print(f"   Файл: {info['binary_path']}")
            print(f"   Возможности: {', '.join(info['capabilities'])}")
        return
    if args.cross_check:
        from apps.windows.hardware.cross_validator import CrossValidator
        validator = CrossValidator()
        report = validator.run_cross_check()
        print('\n=== РЕЗУЛЬТАТЫ КРОСС-ВАЛИДАЦИИ ОБОРУДОВАНИЯ ===')
        print(f'Уровень согласованности: {report.consensus_score_pct:.1f}%')
        print(f"Активные провайдеры: {', '.join(report.active_providers)}")
        if report.discrepancies:
            print('\n[!] Обнаружены расхождения:')
            for d in report.discrepancies:
                print(f' - [{d.severity}] {d.component} -> {d.parameter}: {d.sources} ({d.explanation})')
    if args.identity:
        from apps.windows.sdk.modules.accounts_identity import get_accounts_identity_service, format_principal_tree
        srv = get_accounts_identity_service()
        cur_tok = srv.get_current_identity()
        if args.json:
            print(json.dumps(cur_tok.model_dump(), ensure_ascii=False, indent=2))
        else:
            principal = srv.explain(cur_tok.user_name)
            print("\n=== КОНТЕКСТ ТЕКУЩЕГО ПОЛЬЗОВАТЕЛЯ (IDENTITY) ===")
            print(format_principal_tree(principal))
        return

    if args.explain_user:
        from apps.windows.sdk.modules.accounts_identity import get_accounts_identity_service, format_principal_tree
        srv = get_accounts_identity_service()
        principal = srv.explain(args.explain_user)
        if args.json:
            print(json.dumps(principal.model_dump(), ensure_ascii=False, indent=2))
        else:
            print(f"\n=== ДОСЬЕ СУБЪЕКТА БЕЗОПАСНОСТИ: {args.explain_user} ===")
            print(format_principal_tree(principal))
        return

    if args.explain_pid is not None:
        from apps.windows.sdk.modules.accounts_identity import get_accounts_identity_service, format_pid_tree
        srv = get_accounts_identity_service()
        pid_info = srv.explain_pid(args.explain_pid)
        if args.json:
            print(json.dumps(pid_info, ensure_ascii=False, indent=2))
        else:
            print(f"\n=== ДОСЬЕ БЕЗОПАСНОСТИ ПРОЦЕССА PID {args.explain_pid} ===")
            print(format_pid_tree(pid_info))
        return

    if args.who_is_admin:
        from apps.windows.sdk.modules.accounts_identity import get_accounts_identity_service
        srv = get_accounts_identity_service()
        admins = srv.who_is_admin()
        if args.json:
            print(json.dumps(admins, ensure_ascii=False, indent=2))
        else:
            print("\n=== АДМИНИСТРАТОРЫ СИСТЕМЫ (WHO-IS-ADMIN) ===")
            for adm in admins:
                direct_badge = "[DIRECT]" if adm.get("is_direct") else "[NESTED]"
                path_str = " -> ".join(adm.get("path_to_admin", []))
                print(f" * {direct_badge} {adm.get('username')} ({adm.get('sid')})")
                print(f"     Цепочка прав: {path_str}")
        return

    if args.who_can_logon_as_service:
        from apps.windows.sdk.modules.accounts_identity import get_accounts_identity_service
        srv = get_accounts_identity_service()
        accounts = srv.who_can_logon_as_service()
        if args.json:
            print(json.dumps(accounts, ensure_ascii=False, indent=2))
        else:
            print("\n=== АККАУНТЫ С ПРАВОМ ВХОДА В КАЧЕСТВЕ СЛУЖБЫ (SeServiceLogonRight) ===")
            for acc in accounts:
                print(f" * {acc}")
        return

    if args.who_can_rdp:
        from apps.windows.sdk.modules.accounts_identity import get_accounts_identity_service
        srv = get_accounts_identity_service()
        accounts = srv.who_can_rdp()
        if args.json:
            print(json.dumps(accounts, ensure_ascii=False, indent=2))
        else:
            print("\n=== АККАУНТЫ С ПРАВОМ ДОСТУПА К RDP (SeRemoteInteractiveLogonRight) ===")
            for acc in accounts:
                print(f" * {acc}")
        return

    if args.orphaned_sids:
        from apps.windows.sdk.modules.accounts_identity import get_accounts_identity_service
        srv = get_accounts_identity_service()
        orphaned = srv.find_orphaned_sids()
        if args.json:
            print(json.dumps(orphaned, ensure_ascii=False, indent=2))
        else:
            print("\n=== ОСИРОТЕВШИЕ SID И ПРОФИЛИ (ORPHANED SIDS) ===")
            if not orphaned:
                print("✅ Осиротевших SID в системе не обнаружено.")
            for item in orphaned:
                print(f" * SID: {item.get('sid')} | Путь: {item.get('location')} | Статус: {item.get('state')}")
        return

    if args.identity_graph:
        from apps.windows.sdk.modules.accounts_identity import get_accounts_identity_service
        srv = get_accounts_identity_service()
        graph = srv.get_identity_graph()
        if args.json:
            print(json.dumps(graph.model_dump(), ensure_ascii=False, indent=2))
        else:
            print("\n=== WINDOWS IDENTITY GRAPH ===")
            print(f"Узлов (Nodes): {len(graph.nodes)} | Связей (Edges): {len(graph.edges)}")
            print("Сводка:")
            for k, v in graph.summary.items():
                print(f"  - {k}: {v}")
        return

    if args.hw_json:
        from apps.windows.hardware.hardware_monitor import HardwareMonitor
        monitor = HardwareMonitor()
        snap = monitor.get_snapshot(include_smart=True)
        print(json.dumps(snap.to_dict(), ensure_ascii=False, indent=2))
        return
    if args.hardware_monitor:
        from apps.windows.tui import run_hardware_monitor_dashboard
        try:
            asyncio.run(run_hardware_monitor_dashboard())
        except (KeyboardInterrupt, SystemExit):
            print('\n[!] Мониторинг оборудования остановлен.')
        return
    if args.inspector or args.mode in ('inspector', 'dashboard'):
        from apps.windows.tui import run_system_inspector
        try:
            asyncio.run(run_system_inspector())
        except (KeyboardInterrupt, SystemExit):
            print('\n[!] Системный инспектор остановлен.')
        return
    if args.logs:
        from apps.windows.tui import run_log_dashboard
        asyncio.run(run_log_dashboard(channel=args.channel))
        return
    if args.tui:
        from apps.windows.tui import run_tui
        run_tui()
        return
    if args.server or args.mode == 'server':
        import uvicorn
        from fastapi import FastAPI
        from apps.windows.router import init_router
        app = FastAPI(title='AI Windows Diagnostic Center')
        app.include_router(init_router())
        print_banner()
        print(f'[*] Запуск FastAPI сервера на http://127.0.0.1:{args.port}')
        uvicorn.run(app, host='127.0.0.1', port=args.port)
        return
    if not args.json:
        print_banner()
    if args.investigate:
        investigator = WindowsAIRootCauseAnalyzer()
        res = asyncio.run(investigator.analyze_incident(args.investigate))
        if args.json:
            print(json.dumps(res.to_dict(), ensure_ascii=False, indent=2))
        else:
            print(f'\n[?] Симптом: {res.symptom}')
            print(f'[!] Первопричина: {res.probable_root_cause} (Уверенность: {int(res.confidence_score * 100)}%)')
            print(f'\n[i] AI Объяснение:\n{res.ai_explanation}')
            if res.remediation_plan:
                print('\n[*] План устранения:')
                for a in res.remediation_plan:
                    print(f'    - [{a.risk.value.upper()}] {a.title}: {a.execution_command}')
        return
    diagnostician = WindowsAIDiagnostician()
    report = asyncio.run(diagnostician.diagnose_system(mode=args.mode))
    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        format_health_summary(report.to_dict())
        if report.ai_summary:
            print('\n[AI Заключение]:')
            print(report.ai_summary)
if __name__ == '__main__':
    main()