# -*- coding: utf-8 -*-
"""Команды управления миграциями базы данных SQLite (db)."""
from __future__ import annotations

import argparse


def register_db_parser(subparsers: argparse._SubParsersAction) -> None:
    """Регистрация аргументов команды db."""
    db_parser = subparsers.add_parser('db', help='Database migrations management')
    db_subparsers = db_parser.add_subparsers(dest='subcommand', help='Subcommands')
    db_subparsers.add_parser('status', help='Check database migration status')
    db_subparsers.add_parser('migrate', help='Apply all pending database migrations')
    db_create = db_subparsers.add_parser('create', help='Create new database migration')
    db_create.add_argument('db', help='Database name (e.g. users)')
    db_create.add_argument('name', help='Migration description name')
    db_create.add_argument('--py', action='store_true', help='Create python migration script')


def run_db_command(args: argparse.Namespace) -> int:
    """Управление миграциями и инспекция схем баз данных."""
    from src.db import get_migration_manager
    mgr = get_migration_manager()
    sub = args.subcommand
    if sub == 'status':
        status = mgr.get_status()
        print('\n--- DATABASE MIGRATION STATUS ---')
        for db_name, info in status.items():
            print(f"[{db_name}] Up-to-date: {info['is_up_to_date']} | Applied: {info['applied_count']} | Pending: {info['pending_count']}")
            if info['pending_migrations']:
                print(f"  Pending: {', '.join(info['pending_migrations'])}")
        print('---------------------------------\n')
        return 0
    if sub == 'migrate':
        print('Applying pending database migrations...')
        result = mgr.apply_all_pending()
        for db_name, res in result['databases'].items():
            status_tag = '[OK]' if res['success'] else '[ERROR]'
            print(f"  {status_tag} {db_name}: {res['message']} ({res['applied_count']} applied)")
        return 0 if result['success'] else 1
    if sub == 'create':
        path = mgr.create_migration(args.db, args.name, is_python=getattr(args, 'py', False))
        print(f'Created migration file: {path}')
        return 0
    print(f'Unknown db subcommand: {sub}')
    return 1
