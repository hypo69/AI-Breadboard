# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Execution of an external Python script as a subpro
# =============================================================================
# Description:
#   Single entry point for all utility scripts and plugins:
#
# File: manage_tools.py
# Project: ai-breadboard
# Package: root
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

import header
from header import __root__
from src.skills import SkillRegistry

# =============================================================================
# UTF-8 Encoding Fix for Windows Console
# =============================================================================
# Windows console uses legacy encoding (CP1251) by default.
# Reconfigure stdout/stderr to use UTF-8 with replacement for invalid characters.
# This ensures Cyrillic characters in logs and messages are displayed correctly.

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# =============================================================================
# Environment Variables Loading
# =============================================================================
# Load environment variables from .env file located in project root.
# This allows secure storage of API keys and sensitive configuration.

load_dotenv(__root__ / '.env')

def _run_script(script_rel_path: str, extra_args: list[str] = []) -> int:
    """Execution of an external Python script as a subprocess.

    Invokes a Python interpreter with the target script and forwards any
    additional command-line arguments. The script runs in the project root
    directory, preserving the environment context.

    Args:
        script_rel_path (str): Path to the script file relative to project root.
                               Example: 'plugins/rag/tools/manage_knowledge.py'
        extra_args (list[str]): List of command-line arguments to pass to the script.
                               These are appended to the command after the script path.

    Returns:
        int: Exit code from the subprocess. 0 indicates success, non-zero indicates error.

    Examples:
        >>> _run_script('scripts/dev/update_docs.py', ['--force'])
        0
    """
    # Resolve the target script path from project root directory
    target_path = __root__ / script_rel_path

    # Validate that the script file exists before attempting execution
    if not target_path.exists():
        print(f"Error: script not found: {target_path}")
        return 1

    # Build command: python interpreter + script path + any extra arguments
    cmd = [sys.executable, str(target_path)]
    if extra_args:
        cmd.extend(extra_args)

    # Execute the script as a subprocess in the project root directory
    result = subprocess.run(cmd, cwd=str(__root__))
    return result.returncode

def run_knowledge_command(args: argparse.Namespace) -> int:
    """Delegation of knowledge base management commands to the dedicated tool.

    Routes knowledge management operations (extract, add, init) to the
    external knowledge management script located in plugins/rag/tools.

    Args:
        args (argparse.Namespace): Parsed command arguments containing:
            - subcommand (str): The specific knowledge operation to perform.
            - rest (list[str]): Additional arguments for the subcommand.

    Returns:
        int: Exit code from the delegated knowledge management script.

    Subcommands:
        extract: Extract knowledge from chat files
        add: Add new entries to the knowledge base
        init: Initialize the knowledge registry
    """
    sub = args.subcommand
    extra = getattr(args, 'rest', [])

    if sub in ('extract', 'add', 'init'):
        cmd_args = [sub] + extra
        return _run_script('plugins/rag/tools/manage_knowledge.py', cmd_args)

    print(f"Unknown knowledge subcommand: {sub}")
    return 1

def run_rag_command(args: argparse.Namespace) -> int:
    """Management of Retrieval-Augmented Generation (RAG) index operations.

    Provides direct access to RAG index lifecycle operations including
    rebuilding, reindexing, validation, and status checking.

    Args:
        args (argparse.Namespace): Parsed command arguments containing:
            - subcommand (str): The specific RAG operation to perform.

    Returns:
        int: Exit code indicating operation success (0) or failure (1).

    Subcommands:
        rebuild: Full reconstruction of the RAG index from source documents
        reindex: Incremental update of existing index
        validate: Verification of index integrity and document consistency
        status: Check whether the RAG index exists and is ready for use
    """
    sub = args.subcommand
    extra = getattr(args, 'rest', [])

    if sub == 'rebuild':
        extra = getattr(args, 'rest', [])
        try:
            from src.rag import build_rules_index
            index_path, docs_path = build_rules_index(*extra)
            print(f"RAG index rebuilt successfully: {index_path}, {docs_path}")
            return 0
        except TypeError:
            # If build_rules_index doesn't accept arguments, call without args
            from src.rag import build_rules_index
            index_path, docs_path = build_rules_index()
            print(f"RAG index rebuilt successfully: {index_path}, {docs_path}")
            return 0
        except Exception as e:
            print(f"Error rebuilding RAG: {e}")
            return 1
    if sub == 'status':
        try:
            from header import __root__
            idx_file = __root__ / 'tmp' / 'rag' / 'rules.index'
            print(f"Core RAG status: {'Ready' if idx_file.exists() else 'Not built'}")
            return 0
        except Exception as e:
            print(f"Error checking RAG status: {e}")
            return 1

    print(f"Unknown rag subcommand: {sub}")
    return 1

def run_docs_command(args: argparse.Namespace) -> int:
    """Delegation of documentation management operations to external scripts.

    Handles project documentation updates, generation, and maintenance through
    dedicated development scripts.

    Args:
        args (argparse.Namespace): Parsed command arguments containing:
            - subcommand (str): The documentation operation to perform.
            - rest (list[str]): Additional arguments for the operation.

    Returns:
        int: Exit code from the delegated documentation script.

    Subcommands:
        generate: Run API and scripts documentation generation
        update: Run documentation validity check on modified files
    """
    sub = args.subcommand
    extra = getattr(args, 'rest', [])

    if sub == 'generate':
        api_code = _run_script('scripts/docs/generate_api.py', extra)
        if api_code != 0:
            return api_code
        scripts_code = _run_script('scripts/dev/update_scripts_documentation.py', extra)
        return scripts_code

    if sub == 'update':
        return _run_script('scripts/dev/update_docs.py', extra)

    if sub == 'pdf':
        return _run_script('scripts/dev/export_pdf.py', extra)

    print(f"Unknown docs subcommand: {sub}")
    return 1

def run_skills_command(args: argparse.Namespace) -> int:
    """Unified skills catalog management for AI agents.

    Discovers, searches, and exports AI capabilities (skills) from
    the universal skills registry. Supports multiple discovery roots
    (.agents/skills, .gemini/skills).

    The SkillRegistry provides a portable interface for AI agents to
    understand available capabilities without hardcoding references.

    Args:
        args (argparse.Namespace): Parsed command arguments containing:
            - subcommand (str): The skills operation to perform.
            - query (str): Search terms for 'search' subcommand.
            - name (str): Skill name for 'show' and 'export' subcommands.
            - without_instructions (bool): Flag to exclude instructions when exporting.

    Returns:
        int: Exit code indicating operation success (0) or failure (1).

    Subcommands:
        list: Display all discovered skills with their descriptions
        search: Find skills matching query string by name or description
        show: Print full Markdown instructions for a specific skill
        export: Generate portable JSON contract for skill integration
    """
    registry = SkillRegistry()
    sub = args.subcommand
    lang = getattr(args, 'lang', None)

    if sub == 'list':
        for skill in registry.discover(lang=lang):
            print(f"{skill.name}\t{skill.get_description(lang) if lang else skill.description}")
        return 0

    if sub == 'search':
        for skill in registry.search(args.query, lang=lang):
            print(f"{skill.name}\t{skill.get_description(lang) if lang else skill.description}")
        return 0

    if sub in ('show', 'export'):
        try:
            if sub == 'show':
                skill = registry.get(args.name)
                print(skill.prompt())
            else:
                print(registry.export_json(args.name, include_instructions=not args.without_instructions, lang=lang))
            return 0
        except KeyError as error:
            print(f"Error: {error}")
            return 1

    print(f"Unknown skills subcommand: {sub}")
    return 1

def run_plugins_command(args: argparse.Namespace) -> int:
    """Plugin management and scaffolding commands.

    Args:
        args (argparse.Namespace): Command arguments.

    Returns:
        int: Exit code (0 on success, 1 on error).
    """
    sub = args.subcommand
    if sub == 'list':
        from plugins import load_plugins
        loaded = load_plugins()
        lang = getattr(args, 'lang', None)
        print("\n--- INSTALLED PLUGINS ---")
        for name, p in sorted(loaded.items()):
            t = p.get_title(lang) if lang else p.title
            d = p.get_description(lang) if lang else p.description
            status = "enabled" if p.enabled else "disabled"
            print(f"[{p.icon}] {name} ({t}) - {status}\n    {d}")
        print("-------------------------\n")
        return 0

    if sub == 'create':
        from scripts.dev.init_plugin import create_plugin
        create_plugin(
            name=args.name,
            title=getattr(args, 'title', '') or '',
            title_ru=getattr(args, 'title_ru', '') or '',
            description=getattr(args, 'description', '') or '',
            description_ru=getattr(args, 'description_ru', '') or '',
            category=getattr(args, 'category', 'general') or 'general',
            icon=getattr(args, 'icon', '🧩') or '🧩',
            scope=getattr(args, 'scope', 'system') or 'system',
        )
        return 0

    print(f"Unknown plugins subcommand: {sub}")
    return 1

def run_db_command(args: argparse.Namespace) -> int:
    """Database schema migration and inspection commands.

    Args:
        args (argparse.Namespace): Parsed command arguments containing:
            - subcommand (str): The db operation ('migrate', 'status', 'create').
            - name (str): Migration name (for create).
            - db (str): Database name.
            - py (bool): Flag for Python migration format.

    Returns:
        int: Exit code (0 on success, 1 on error).
    """
    from apps.helpdesk.db.migrations import get_migration_manager
    mgr = get_migration_manager()
    sub = args.subcommand

    if sub == 'status':
        status = mgr.get_status()
        print("\n--- DATABASE MIGRATION STATUS ---")
        for db_name, info in status.items():
            print(f"[{db_name}] Up-to-date: {info['is_up_to_date']} | Applied: {info['applied_count']} | Pending: {info['pending_count']}")
            if info['pending_migrations']:
                print(f"  Pending: {', '.join(info['pending_migrations'])}")
        print("---------------------------------\n")
        return 0

    if sub == 'migrate':
        print("Applying pending database migrations...")
        result = mgr.apply_all_pending()
        for db_name, res in result['databases'].items():
            status_tag = "[OK]" if res['success'] else "[ERROR]"
            print(f"  {status_tag} {db_name}: {res['message']} ({res['applied_count']} applied)")
        return 0 if result['success'] else 1

    if sub == 'create':
        path = mgr.create_migration(args.db, args.name, is_python=getattr(args, 'py', False))
        print(f"Created migration file: {path}")
        return 0

    print(f"Unknown db subcommand: {sub}")
    return 1

def run_network_command(args: argparse.Namespace) -> int:
    """Network capture and TShark analysis CLI commands.

    Args:
        args (argparse.Namespace): Parsed command arguments.

    Returns:
        int: Exit code (0 on success, 1 on error).
    """
    from src.network import TSharkWrapper, TrafficAnalyzer
    sub = args.subcommand
    wrapper = TSharkWrapper()

    if sub == 'status':
        print(f"TShark Available: {wrapper.is_available()}")
        print(f"TShark Binary Path: {wrapper.tshark_path or 'Not Found'}")
        return 0

    if sub == 'interfaces':
        if not wrapper.is_available():
            print("Error: TShark is not available on this host.")
            return 1
        ifaces = wrapper.list_interfaces()
        print("\n--- NETWORK CAPTURE INTERFACES ---")
        for iface in ifaces:
            print(f"[{iface.id}] {iface.name} - {iface.description}")
        print("----------------------------------\n")
        return 0

    if sub == 'analyze':
        pcap_file = getattr(args, 'file', '')
        if not pcap_file:
            print("Error: --file argument is required for PCAP analysis.")
            return 1
        if not wrapper.is_available():
            print("Error: TShark is not available on this host.")
            return 1
        packets = wrapper.read_pcap(pcap_file, display_filter=getattr(args, 'filter', '') or '')
        analyzer = TrafficAnalyzer()
        stats = analyzer.compute_stats(packets)
        heuristics = analyzer.detect_heuristics(packets)
        print("\n--- PCAP TRAFFIC REPORT ---")
        print(f"Total Packets: {stats.total_packets}")
        print(f"Total Volume: {stats.total_bytes} bytes")
        print(f"Protocol Distribution: {stats.protocol_distribution}")
        print(f"Top Sources: {stats.top_sources}")
        print(f"Top Destinations: {stats.top_destinations}")
        if heuristics:
            print("\nWarnings / Heuristics:")
            for h in heuristics:
                print(f"  [!] {h}")
        print("---------------------------\n")
        return 0

    print(f"Unknown network subcommand: {sub}")
    return 1

def run_sys_param_command(args: argparse.Namespace) -> int:
    """Управление параметрами системы и точками восстановления Windows.

    Args:
        args (argparse.Namespace): Аргументы команды CLI.

    Returns:
        int: Код возврата (0 - успешно, 1 - ошибка).
    """
    from apps.windows.core.system_param_manager import SafeSystemParamManager
    from apps.windows.core.system_restore import WindowsSystemRestoreManager

    restore_mgr = WindowsSystemRestoreManager()
    manager = SafeSystemParamManager(restore_manager=restore_mgr)
    sub = args.subcommand

    if sub == 'list':
        category = getattr(args, 'category', None)
        params = manager.list_parameters(category=category)
        print(f"\n{'ID':<25} | {'SENSITIVE':<10} | {'RISK':<9} | {'CURRENT VALUE':<20} | NAME")
        print("-" * 90)
        for p in params:
            sens_str = "YES [RP]" if p['is_sensitive'] else "NO"
            print(f"{p['param_id']:<25} | {sens_str:<10} | {p['risk'].upper():<9} | {str(p['current_value']):<20} | {p['name']}")
        print(f"\nВсего параметров: {len(params)}\n")
        return 0

    if sub == 'preview':
        param_id = getattr(args, 'param_id', '')
        val = getattr(args, 'value', '')
        res = manager.preview_change(param_id, val)
        if not res.get('success'):
            print(f"Ошибка: {res.get('error')}")
            return 1
        print(f"\n--- СИМУЛЯЦИЯ ИЗМЕНЕНИЯ ПАРАМЕТРА ---")
        print(f"Параметр:          {res['name']} ({res['param_id']})")
        print(f"Текущее значение:  {res['current_value']}")
        print(f"Новое значение:    {res['new_value']}")
        print(f"Чувствительный:    {'ДА' if res['is_sensitive'] else 'НЕТ'}")
        print(f"Уровень риска:     {res['risk'].upper()}")
        print(f"Точка восстан.:    {'БУДЕТ СОЗДАНА АВТОМАТИЧЕСКИ' if res['will_create_restore_point'] else 'Не требуется'}")
        if res.get('restore_point_description'):
            print(f"Описание точки:    {res['restore_point_description']}")
        print("------------------------------------\n")
        return 0

    if sub == 'set':
        param_id = getattr(args, 'param_id', '')
        val = getattr(args, 'value', '')
        if val.lower() == 'true':
            parsed_val = True
        elif val.lower() == 'false':
            parsed_val = False
        elif val.isdigit():
            parsed_val = int(val)
        else:
            parsed_val = val

        print(f"Применение изменения для '{param_id}' -> '{parsed_val}'...")
        res = manager.apply_change(param_id, parsed_val)
        if res.get('status') == 'SUCCESS':
            print(f"\n[OK] {res.get('message')}")
            if res.get('restore_point'):
                rp = res['restore_point']
                print(f"  [RP] Точка восстановления Windows: {rp.get('message', 'Создана')} (Статус: {rp.get('success')})")
            print(f"  Change ID: {res.get('change_id')}\n")
            return 0
        else:
            print(f"\n[ERROR] {res.get('message')}\n")
            return 1

    if sub == 'restore-points':
        points = restore_mgr.list_restore_points()
        status = restore_mgr.check_protection_status()
        print(f"\n--- ТОЧКИ ВОССТАНОВЛЕНИЯ WINDOWS ---")
        print(f"Защита системы (Диск C:): {'ВКЛЮЧЕНА' if status.get('system_protection_enabled') else 'ОТКЛЮЧЕНА / НЕДОСТУПНА'}")
        print(f"{'#':<6} | {'ДАТА СОЗДАНИЯ':<22} | {'ТИП':<20} | ОПИСАНИЕ")
        print("-" * 80)
        for pt in points:
            print(f"{pt['sequence_number']:<6} | {pt['creation_time']:<22} | {pt['restore_point_type']:<20} | {pt['description']}")
        print(f"\nВсего точек: {len(points)}\n")
        return 0

    if sub == 'create-rp':
        desc = getattr(args, 'description', '')
        if not desc:
            desc = "AI-Breadboard Manual Checkpoint"
        print(f"Создание точки восстановления Windows: '{desc}'...")
        res = restore_mgr.create_restore_point(desc)
        if res.get('success'):
            print(f"[OK] {res.get('message')}")
            return 0
        else:
            print(f"[ERROR] {res.get('message')}")
            return 1

    if sub == 'history':
        history = manager.get_history(limit=getattr(args, 'limit', 20))
        print(f"\n--- ЖУРНАЛ ИЗМЕНЕНИЙ ПАРАМЕТРОВ ---")
        for h in history:
            rb_tag = " [ROLLED BACK]" if h.get('rolled_back') else ""
            rp_tag = " [RP CREATED]" if h.get('restore_point') and h['restore_point'].get('success') else ""
            print(f"[{h.get('timestamp')}] {h.get('param_name')} ({h.get('param_id')}){rb_tag}{rp_tag}")
            print(f"   {h.get('old_value')} -> {h.get('new_value')} | Status: {h.get('status')} | ID: {h.get('change_id')}")
        print(f"\nВсего записей: {len(history)}\n")
        return 0

    if sub == 'rollback':
        cid = getattr(args, 'change_id', '')
        res = manager.rollback_change(cid)
        if res.get('status') == 'SUCCESS':
            print(f"[OK] {res.get('message')}")
            return 0
        else:
            print(f"[ERROR] {res.get('message')}")
            return 1

    print(f"Неизвестная подкоманда sys-param: {sub}")
    return 1


def run_telemetry_command(args: argparse.Namespace) -> int:
    """Управление посекундным логгированием системной телеметрии и процессами в SQLite.

    Args:
        args (argparse.Namespace): Аргументы команды CLI.

    Returns:
        int: Код возврата (0 - успешно, 1 - ошибка).
    """
    from apps.windows.telemetry import SystemCollector, TelemetryStorage, TelemetryLoggerService
    import time

    storage = TelemetryStorage()
    sub = args.subcommand

    if sub == 'status':
        stats = storage.get_storage_stats()
        print("\n--- СТАТУС БАЗЫ ДАННЫХ ТЕЛЕМЕТРИИ ---")
        print(f"Путь к базе данных:    {stats['db_path']}")
        print(f"Всего снимков системы: {stats['snapshots_count']}")
        print(f"Всего записей процессов:{stats['process_snapshots_count']}")
        print(f"Размер файла базы:     {stats['file_size_mb']} MB")
        print("-------------------------------------\n")
        return 0

    if sub == 'history':
        limit = getattr(args, 'limit', 20) or 20
        snaps = storage.get_snapshots(limit=limit)
        print(f"\n--- ПОСЛЕДНИЕ {len(snaps)} СНИМКОВ ТЕЛЕМЕТРИИ ---")
        print(f"{'#ID':<6} | {'ВРЕМЯ (UTC)':<20} | {'CPU %':<7} | {'RAM %':<7} | {'DISK R (KB/s)':<14} | {'DISK W (KB/s)':<14}")
        print("-" * 80)
        for s in snaps:
            r_kb = round(s.get('disk_read_bytes_sec', 0.0) / 1024, 1)
            w_kb = round(s.get('disk_write_bytes_sec', 0.0) / 1024, 1)
            ts = s.get('timestamp', '')[:19].replace('T', ' ')
            print(f"{s.get('id'):<6} | {ts:<20} | {s.get('cpu_total_percent', 0.0):<7.1f} | {s.get('memory_percent', 0.0):<7.1f} | {r_kb:<14.1f} | {w_kb:<14.1f}")
        print("------------------------------------------------\n")
        return 0

    if sub == 'cleanup':
        days = getattr(args, 'days', 7) or 7
        print(f"Очистка записей телеметрии старше {days} дней...")
        deleted = storage.cleanup_old_records(retention_days=days)
        print(f"[OK] Удалено устаревших снимков: {deleted}\n")
        return 0

    if sub == 'start':
        interval = float(getattr(args, 'interval', 1.0) or 1.0)
        procs_limit = int(getattr(args, 'processes', 20) or 20)
        collector = SystemCollector()

        print(f"\n[+] Запуск посекундного логгирования телеметрии в SQLite...")
        print(f"    Интервал: {interval} сек | Top-процессов: {procs_limit} | База: {storage.db_path}")
        print(f"    Нажмите Ctrl+C для остановки.\n")
        print(f"{'ВРЕМЯ':<10} | {'CPU %':<7} | {'RAM %':<7} | {'DISK READ':<12} | {'DISK WRITE':<12} | ТОП-1 ПРОЦЕСС")
        print("-" * 85)

        try:
            while True:
                t0 = time.time()
                snap = collector.get_snapshot(process_limit=procs_limit)
                snap_id = storage.save_snapshot(snap, top_n=procs_limit)

                now_str = time.strftime("%H:%M:%S")
                cpu = f"{snap.cpu.total_percent:.1f}%"
                ram = f"{snap.memory.percent:.1f}%"
                r_rate = f"{snap.disk_io.read_bytes_per_sec / (1024*1024):.2f} MB/s"
                w_rate = f"{snap.disk_io.write_bytes_per_sec / (1024*1024):.2f} MB/s"
                top_p = snap.top_processes[0].name if snap.top_processes else "N/A"
                top_p_cpu = f"({snap.top_processes[0].cpu_percent:.1f}%)" if snap.top_processes else ""

                print(f"{now_str:<10} | {cpu:<7} | {ram:<7} | {r_rate:<12} | {w_rate:<12} | {top_p} {top_p_cpu}")

                elapsed = time.time() - t0
                time.sleep(max(0.01, interval - elapsed))
        except KeyboardInterrupt:
            print("\n[!] Логгирование телеметрии остановлено пользователем.\n")
            return 0
        except Exception as e:
            print(f"\n[ERROR] Ошибка сбора телеметрии: {e}\n")
            return 1

    print(f"Неизвестная подкоманда telemetry: {sub}")
    return 1


def main() -> int:
    """Primary entry point for the universal CLI management system.

    Initializes the argument parser with all available command groups and
    dispatches incoming commands to their respective handlers.

    Returns:
        int: Exit code indicating overall command execution status:
            0 - Success (command executed properly)
            1 - Error (unknown command, missing arguments, or handler failure)

    Command Structure:
        manage_tools.py <command> [<subcommand>] [<args>]

    Available Commands:
        knowledge - Knowledge base extraction and management
        rag       - RAG index operations (rebuild, status)
        docs      - Documentation updates and generation
        skills    - Skills registry operations (list, search, show, export)
        assist    - Assistant process management
    """
    # Initialize the argument parser with program metadata and formatting options
    parser = argparse.ArgumentParser(
        prog='manage_tools.py',
        description='Universal CLI for managing ai-breadboard project tools',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  py manage_tools.py rag rebuild                          # rebuild RAG index
  py manage_tools.py knowledge extract --file chat.md     # extract knowledge
  py manage_tools.py skills list                          # list all available skills
'''
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # ==========================================================================
    # Knowledge Management Subparser
    # ==========================================================================
    # Commands for extracting, adding, and initializing knowledge base entries
    # from chat files and documentation sources.

    knowledge_parser = subparsers.add_parser('knowledge', help='Knowledge management')
    knowledge_subparsers = knowledge_parser.add_subparsers(dest='subcommand', help='Subcommands')
    knowledge_extract = knowledge_subparsers.add_parser('extract', help='Extract knowledge from chats')
    knowledge_extract.add_argument('rest', nargs=argparse.REMAINDER, help='Arguments')
    knowledge_add = knowledge_subparsers.add_parser('add', help='Add new entry to knowledge')
    knowledge_add.add_argument('rest', nargs=argparse.REMAINDER, help='Arguments')
    knowledge_subparsers.add_parser('init', help='Initialize knowledge registry')

    # ==========================================================================
    # RAG (Retrieval-Augmented Generation) Index Subparser
    # ==========================================================================
    # Commands for building, validating, and checking status of RAG indexes
    # used for semantic search and AI-powered knowledge retrieval.

    rag_parser = subparsers.add_parser('rag', help='RAG index management')
    rag_subparsers = rag_parser.add_subparsers(dest='subcommand', help='Subcommands')
    rag_rebuild = rag_subparsers.add_parser('rebuild', help='Full rebuild of RAG index')
    rag_rebuild.add_argument('rest', nargs=argparse.REMAINDER, help='Rebuild options')
    rag_subparsers.add_parser('reindex', help='Reindex knowledge base')
    rag_subparsers.add_parser('validate', help='Validate knowledge base files')
    rag_subparsers.add_parser('status', help='Check RAG index status')

    # ==========================================================================
    # Documentation Management Subparser
    # ==========================================================================
    # Commands for generating, updating, and maintaining project documentation
    # including auto-generated API docs and user guides.

    docs_parser = subparsers.add_parser('docs', help='Documentation management')
    docs_subparsers = docs_parser.add_subparsers(dest='subcommand', help='Subcommands')
    docs_generate = docs_subparsers.add_parser('generate', help='Generate and synchronize API and scripts documentation')
    docs_generate.add_argument('rest', nargs=argparse.REMAINDER, help='Additional generator options')
    docs_update = docs_subparsers.add_parser('update', help='Validate documentation validity of modified files')
    docs_update.add_argument('rest', nargs=argparse.REMAINDER, help='Additional validator options')
    docs_pdf = docs_subparsers.add_parser('pdf', help='Export project code and documentation into code.pdf and docs.pdf')
    docs_pdf.add_argument('rest', nargs=argparse.REMAINDER, help='PDF exporter options (--target all|docs|code, --output-dir, etc.)')

    # ==========================================================================
    # Skills Registry Subparser
    # ==========================================================================
    # Universal skills catalog for AI agents. Discovers capabilities from
    # .agents/skills and .gemini/skills directories and provides
    # portable JSON contracts for agent integration.

    skills_parser = subparsers.add_parser('skills', help='Universal skills registry')
    skills_subparsers = skills_parser.add_subparsers(dest='subcommand', help='Subcommands')
    skills_list = skills_subparsers.add_parser('list', help='List discovered skills')
    skills_list.add_argument('--lang', '-l', help='Language code (e.g. en, ru, es)')
    skills_search = skills_subparsers.add_parser('search', help='Search skills by name or description')
    skills_search.add_argument('query', help='Search terms')
    skills_search.add_argument('--lang', '-l', help='Language code for output (e.g. en, ru, es)')
    skills_show = skills_subparsers.add_parser('show', help='Print Markdown instructions')
    skills_show.add_argument('name', help='Skill name')
    skills_export = skills_subparsers.add_parser('export', help='Export a portable JSON skill contract')
    skills_export.add_argument('name', help='Skill name')
    skills_export.add_argument('--without-instructions', action='store_true', help='Exclude Markdown instructions')
    skills_export.add_argument('--lang', '-l', help='Language code for exported description')

    # ==========================================================================
    # Plugins Management Subparser
    # ==========================================================================
    plugins_parser = subparsers.add_parser('plugins', help='System and user plugins management and scaffolding')
    plugins_subparsers = plugins_parser.add_subparsers(dest='subcommand', help='Subcommands')
    plugins_list = plugins_subparsers.add_parser('list', help='List installed plugins')
    plugins_list.add_argument('--lang', '-l', help='Language code for localized title and description')
    plugins_create = plugins_subparsers.add_parser('create', help='Scaffold a new plugin')
    plugins_create.add_argument('name', help='Plugin name (e.g. audit_logger)')
    plugins_create.add_argument('--title', '-t', default='', help='English display title')
    plugins_create.add_argument('--title-ru', '-tru', default='', help='Russian display title')
    plugins_create.add_argument('--description', '-d', default='', help='English description')
    plugins_create.add_argument('--description-ru', '-ru', default='', help='Russian description')
    plugins_create.add_argument('--category', '-c', default='general', help='Plugin category')
    plugins_create.add_argument('--icon', '-i', default='🧩', help='Emoji icon')
    plugins_create.add_argument('--scope', '-s', default='system', choices=['system', 'user'], help='Plugin scope')

    # ==========================================================================
    # Database Migration Subparser
    # ==========================================================================
    db_parser = subparsers.add_parser('db', help='Database migrations management')
    db_subparsers = db_parser.add_subparsers(dest='subcommand', help='Subcommands')
    db_subparsers.add_parser('status', help='Check database migration status')
    db_subparsers.add_parser('migrate', help='Apply all pending database migrations')
    db_create = db_subparsers.add_parser('create', help='Create new database migration')
    db_create.add_argument('db', help='Database name (e.g. users)')
    db_create.add_argument('name', help='Migration description name')
    db_create.add_argument('--py', action='store_true', help='Create python migration script')

    # ==========================================================================
    # Network Traffic & TShark Subparser
    # ==========================================================================
    network_parser = subparsers.add_parser('network', help='Network traffic capture and TShark analysis')
    network_subparsers = network_parser.add_subparsers(dest='subcommand', help='Subcommands')
    network_subparsers.add_parser('status', help='Check TShark binary status')
    network_subparsers.add_parser('interfaces', help='List available network interfaces')
    network_analyze = network_subparsers.add_parser('analyze', help='Analyze PCAP file')
    network_analyze.add_argument('--file', '-f', required=True, help='Path to .pcap or .pcapng file')
    network_analyze.add_argument('--filter', '-Y', default='', help='Wireshark display filter')

    # ==========================================================================
    # System Parameters & Restore Points Subparser
    # ==========================================================================
    sys_param_parser = subparsers.add_parser('sys-param', help='Safe system parameter management & Windows restore points')
    sys_param_subparsers = sys_param_parser.add_subparsers(dest='subcommand', help='Subcommands')
    
    sys_param_list = sys_param_subparsers.add_parser('list', help='List system parameters')
    sys_param_list.add_argument('--category', '-c', help='Filter by category')
    
    sys_param_preview = sys_param_subparsers.add_parser('preview', help='Preview/dry-run parameter change')
    sys_param_preview.add_argument('param_id', help='Parameter ID (e.g. sec.uac_level)')
    sys_param_preview.add_argument('value', help='New parameter value')
    
    sys_param_set = sys_param_subparsers.add_parser('set', help='Apply parameter change safely (auto restore point)')
    sys_param_set.add_argument('param_id', help='Parameter ID (e.g. sec.uac_level)')
    sys_param_set.add_argument('value', help='New parameter value')
    
    sys_param_subparsers.add_parser('restore-points', help='List Windows restore points')
    
    sys_param_rp_create = sys_param_subparsers.add_parser('create-rp', help='Create Windows restore point manually')
    sys_param_rp_create.add_argument('description', nargs='?', default='AI-Breadboard Manual Checkpoint', help='Description')
    
    sys_param_history = sys_param_subparsers.add_parser('history', help='View parameter change history')
    sys_param_history.add_argument('--limit', '-n', type=int, default=20, help='Limit history items')
    
    sys_param_rollback = sys_param_subparsers.add_parser('rollback', help='Rollback parameter change')
    sys_param_rollback.add_argument('change_id', help='Change ID from history')

    # ==========================================================================
    # Telemetry SQLite Logger Subparser
    # ==========================================================================
    telemetry_parser = subparsers.add_parser('telemetry', help='System metrics 1Hz SQLite logging (CPU, RAM, Disk I/O, Top-20 procs)')
    telemetry_subparsers = telemetry_parser.add_subparsers(dest='subcommand', help='Subcommands')

    telemetry_start = telemetry_subparsers.add_parser('start', help='Start 1Hz telemetry logging loop')
    telemetry_start.add_argument('--interval', '-i', type=float, default=1.0, help='Logging interval in seconds (default: 1.0)')
    telemetry_start.add_argument('--processes', '-p', type=int, default=20, help='Top processes limit (default: 20)')

    telemetry_subparsers.add_parser('status', help='View telemetry SQLite database statistics')

    telemetry_history = telemetry_subparsers.add_parser('history', help='View recent telemetry snapshots')
    telemetry_history.add_argument('--limit', '-n', type=int, default=20, help='Limit snapshots count')

    telemetry_cleanup = telemetry_subparsers.add_parser('cleanup', help='Delete old telemetry records')
    telemetry_cleanup.add_argument('--days', '-d', type=int, default=7, help='Retention days (default: 7)')

    # ==========================================================================
    # Assistant CLI Subparser
    # ==========================================================================
    # Gateway to the main assistant CLI for process management including
    # start, stop, status queries, and provider configuration.

    assist_parser = subparsers.add_parser('assist', help='Assistant management (start, stop, status, providers, etc.)')
    assist_parser.add_argument('rest', nargs=argparse.REMAINDER, help='Arguments for assist CLI')

    # ==========================================================================
    # Command Dispatch
    # ==========================================================================
    # Parse arguments and route to the appropriate handler based on command type.

    args, unknown = parser.parse_known_args()

    # Calculate exact unconsumed trailing CLI arguments for sub-command delegation
    if args.command in ('knowledge', 'rag', 'docs', 'plugins', 'db', 'sys-param', 'telemetry') and getattr(args, 'subcommand', None):
        # Find index where subcommand appears in sys.argv
        argv_list = list(sys.argv[1:])
        if args.subcommand in argv_list:
            sub_idx = argv_list.index(args.subcommand)
            args.rest = argv_list[sub_idx + 1:]
        else:
            args.rest = unknown
    elif unknown:
        if hasattr(args, 'rest') and isinstance(args.rest, list):
            args.rest = args.rest + unknown
        else:
            args.rest = unknown

    # Display help when no command is provided
    if not args.command:
        parser.print_help()
        return 0

    # Special handling for 'assist' command - forwards to dedicated assist_cli
    if args.command == 'assist':
        from scripts.dev import assist_cli
        sys.argv = ['assist'] + getattr(args, 'rest', [])
        return assist_cli.main()

    # Display help when no subcommand is provided for commands that require one
    if not getattr(args, 'subcommand', ''):
        parser.print_help()
        return 0

    # Command-to-handler mapping for primary command groups
    dispatch = {
        'knowledge': run_knowledge_command,
        'rag': run_rag_command,
        'docs': run_docs_command,
        'skills': run_skills_command,
        'plugins': run_plugins_command,
        'db': run_db_command,
        'network': run_network_command,
        'sys-param': run_sys_param_command,
        'telemetry': run_telemetry_command,
    }

    # Resolve and execute the appropriate command handler
    handler = dispatch.get(args.command)
    if not handler:
        parser.print_help()
        return 1

    return handler(args)


if __name__ == '__main__':
    sys.exit(main())
