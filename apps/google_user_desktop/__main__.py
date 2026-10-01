# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Google_User_Desktop -   Main  
# =============================================================================
# Description:
#   Точка входа CLI для Google User Desktop.
#
# Usage Examples:
#   CLI:
#     python -m apps.google_user_desktop.__main__
#   Python API:
#     from apps.google_user_desktop.__main__ import main
#
#     res = main()
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.google_user_desktop
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Точка входа CLI для Google User Desktop."""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace

from .src.state import GoogleUserDesktopState
from .tui import run_google_desktop_dashboard


def _load_config() -> SimpleNamespace:
    """Загрузить конфигурацию приложения из config.json.

    Returns:
        SimpleNamespace: Пространство имен загруженной конфигурации.
    """
    config_path = Path(__file__).parent / 'config.json'
    from src.utils.jjson import j_loads_ns

    return j_loads_ns(config_path) if config_path.exists() else SimpleNamespace()


def _get_server_mode(config: SimpleNamespace) -> str:
    """Извлечь режим сервера ('dedicated' или 'shared') из конфигурации.

    Args:
        config: Пространство имен конфигурации.

    Returns:
        str: 'dedicated' или 'shared'.
    """
    server_val = getattr(config, 'server', None)
    if isinstance(server_val, str):
        return server_val.strip().lower()
    if isinstance(server_val, SimpleNamespace):
        dedicated_val = getattr(server_val, 'dedicated', None)
        if dedicated_val is not None:
            return 'dedicated' if dedicated_val in (True, 'true', 'True', 1) else 'shared'
        mode = getattr(server_val, 'mode', getattr(server_val, 'type', 'dedicated'))
        return str(mode).strip().lower()
    if isinstance(server_val, dict):
        if 'dedicated' in server_val:
            return 'dedicated' if server_val['dedicated'] in (True, 'true', 'True', 1) else 'shared'
        mode = server_val.get('mode') or server_val.get('type', 'dedicated')
        return str(mode).strip().lower()
    return 'dedicated'


def _run_standalone_server(
    host: str = '127.0.0.1', port: int = 8106, reload: bool = False, workers: int = 1
) -> None:
    """Запустить Google User Desktop как standalone FastAPI сервер.

    Args:
        host: Сетевой адрес сервера.
        port: Сетевой порт.
        reload: Автоперезагрузка при изменениях кода.
        workers: Количество рабочих процессов Uvicorn.
    """
    try:
        import uvicorn
        from fastapi import FastAPI
        from .routers.router import init_router

        print('[Google User Desktop] Запуск standalone FastAPI сервера...')
        print(f'  Хост: {host}')
        print(f'  Порт: {port}')
        print(f'  Перезагрузка: {reload}')
        print(f'  Воркеры: {workers}')
        print(
            f"\n  Доступен по адресу: http://{(host if host != '0.0.0.0' else 'localhost')}:{port}"
        )
        print(
            f"  Документация API (Swagger): http://{(host if host != '0.0.0.0' else 'localhost')}:{port}/docs\n"
        )
        app = FastAPI(
            title='Google User Desktop Workspace',
            description='Единое приложение управления Google Mail, Calendar, Docs/Sheets & Drive',
            version='1.0.0',
        )
        app.include_router(init_router())
        uvicorn.run(app, host=host, port=port, reload=reload, workers=workers, log_level='info')
    except ImportError as e:
        print(f'[ERROR] Не удалось импортировать необходимые модули: {e}')
        print('[INFO] Убедитесь, что uvicorn и fastapi установлены.')
        sys.exit(1)
    except Exception as e:
        print(f'[ERROR] Ошибка сервера: {e}')
        sys.exit(1)


def main() -> None:
    """Разобрать аргументы командной строки CLI и выполнить запрошенную операцию."""
    parser = argparse.ArgumentParser(
        description='AI Breadboard Google User Desktop Workspace & Diagnostics'
    )
    parser.add_argument(
        '--mode',
        '-m',
        type=str,
        choices=['dashboard', 'server', 'status', 'mail', 'calendar', 'docs', 'drive'],
        default='dashboard',
        help='Режим работы приложения (по умолчанию: dashboard)',
    )
    parser.add_argument(
        '--status',
        '-s',
        action='store_true',
        help='Вывести краткую сводку по состоянию и выйти',
    )
        # Формы Google Forms
    parser.add_argument('--create-form', action='store_true', help='Создать новую форму')
    parser.add_argument('--title', type=str, default='', help='Заголовок формы (для создания/обновления)')
    parser.add_argument('--description', type=str, default='', help='Описание формы (опционально)')
    parser.add_argument('--update-form', action='store_true', help='Выполнить batchUpdate для формы')
    parser.add_argument('--form-id', type=str, default='', help='ID формы для операций')
    parser.add_argument('--requests', type=str, default='[]', help='JSON массив запросов batchUpdate')
    parser.add_argument('--publish-form', action='store_true', help='Опубликовать форму (включить ответы)')
    parser.add_argument('--close-form', action='store_true', help='Закрыть форму (отключить ответы)')
    parser.add_argument('--form-responses', action='store_true', help='Получить ответы формы')
    parser.add_argument('--limit', type=int, default=20, help='Лимит записей (для ответов)')

    parser.add_argument(
        '--calendar', action='store_true', help='Вывести ближайшие события Календаря и выйти'
    )
    parser.add_argument(
        '--docs', action='store_true', help='Вывести список недавно измененных Google Docs и выйти'
    )
    parser.add_argument(
        '--drive', action='store_true', help='Вывести список файлов Google Drive и выйти'
    )
    parser.add_argument(
        '--limit', type=int, default=20, help='Максимальное количество возвращаемых записей (default: 20)'
    )
    parser.add_argument('--json', action='store_true', help='Форматировать вывод в формате JSON')
    parser.add_argument(
        '--account', type=str, default='', help='Указать имя активного Google аккаунта'
    )
    parser.add_argument(
        '--host', type=str, default='127.0.0.1', help='Хост FastAPI сервера (default: 127.0.0.1)'
    )
    parser.add_argument(
        '--port', '-p', type=int, default=0, help='Порт FastAPI сервера (default: 8106)'
    )
    parser.add_argument(
        '--reload', action='store_true', help='Включить автоперезагрузку для сервера разработки'
    )
    parser.add_argument(
        '--workers', type=int, default=1, help='Количество воркеров Uvicorn (default: 1)'
    )
    args = parser.parse_args()

    config = _load_config()
    state = GoogleUserDesktopState(account_name=args.account or None)

    if args.status or args.mode == 'status':
        summary = state.refresh_all(probe_network=False)
        if args.json:
            print(json.dumps(summary, indent=2, ensure_ascii=False))
        else:
            print('========================================')
            print('  Google User Desktop Workspace Overview')
            print('========================================')
            acc = summary['account']
            print(f"  Активный аккаунт: {acc['name']} ({acc['email'] or 'нет email'})")
            print(f"  Статус аккаунта:  {acc['status'].upper()}")
            print(f"  Тип авторизации:  {acc['type']}")
            print(f"  Сообщений Gmail:  {summary['mail_count']}")
            print(f"  Событий Календаря:{summary['calendar_events_count']}")
            print(f"  Google Docs:      {summary['docs_count']}")
            print(f"  Файлов на Диске:  {summary['drive_files_count']}")
            print('========================================')
        return
    # Обработка команд Google Forms
    if args.create_form:
        summary = state.create_form(title=args.title, description=args.description or None)
        if args.json:
            print(json.dumps(summary.__dict__, ensure_ascii=False, indent=2))
        else:
            print(f"Создана форма '{summary.title}' (ID: {summary.form_id})")
        return
    if args.update_form:
        try:
            requests = json.loads(args.requests)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Неверный JSON в параметре --requests: {e}")
            return
        state.update_form(form_id=args.form_id, requests=requests)
        print(f"Форма {args.form_id} обновлена")
        return
    if args.publish_form:
        state.publish_form(form_id=args.form_id)
        print(f"Форма {args.form_id} опубликована")
        return
    if args.close_form:
        state.close_form(form_id=args.form_id)
        print(f"Форма {args.form_id} закрыта")
        return
    if args.form_responses:
        responses = state.get_form_responses(form_id=args.form_id, limit=args.limit)
        if args.json:
            print(json.dumps(responses, ensure_ascii=False, indent=2))
        else:
            print(f"Получено {len(responses)} ответов формы {args.form_id}")
            for resp in responses:
                print(resp)
        return
    if args.mail or args.mode == 'mail':
        msgs = state.fetch_mail_messages(max_results=args.limit)
        if args.json:
            print(
                json.dumps(
                    [
                        {
                            'id': m.id,
                            'subject': m.subject,
                            'sender': m.sender,
                            'date': m.date,
                            'snippet': m.snippet,
                        }
                        for m in msgs
                    ],
                    indent=2,
                    ensure_ascii=False,
                )
            )
        else:
            print(f'--- Входящие сообщения Gmail ({len(msgs)}) ---')
            for m in msgs:
                print(f'[{m.date[:16]}] {m.sender[:25]} | {m.subject}')
        return

    if args.calendar or args.mode == 'calendar':
        events = state.fetch_calendar_events(max_results=args.limit)
        if args.json:
            print(
                json.dumps(
                    [
                        {
                            'id': e.id,
                            'summary': e.summary,
                            'start': e.start_time,
                            'end': e.end_time,
                            'location': e.location,
                        }
                        for e in events
                    ],
                    indent=2,
                    ensure_ascii=False,
                )
            )
        else:
            print(f'--- События Google Calendar ({len(events)}) ---')
            for e in events:
                print(f'[{e.start_time[:16]}] {e.summary} ({e.location or "Нет локации"})')
        return

    if args.docs or args.mode == 'docs':
        docs = state.fetch_documents(page_size=args.limit)
        if args.json:
            print(
                json.dumps(
                    [
                        {
                            'id': d.id,
                            'name': d.name,
                            'mime_type': d.mime_type,
                            'modified': d.modified_time,
                        }
                        for d in docs
                    ],
                    indent=2,
                    ensure_ascii=False,
                )
            )
        else:
            print(f'--- Документы Google Docs ({len(docs)}) ---')
            for d in docs:
                print(f'[{d.modified_time[:16]}] {d.name} ({d.mime_type})')
        return

    if args.drive or args.mode == 'drive':
        files = state.fetch_drive_files(page_size=args.limit)
        if args.json:
            print(
                json.dumps(
                    [
                        {
                            'id': f.id,
                            'name': f.name,
                            'size': f.size_bytes,
                            'modified': f.modified_time,
                        }
                        for f in files
                    ],
                    indent=2,
                    ensure_ascii=False,
                )
            )
        else:
            print(f'--- Файлы Google Drive ({len(files)}) ---')
            for f in files:
                print(f'[{f.modified_time[:16]}] {f.name} ({f.size_bytes} байт)')
        return

    if args.mode == 'server':
        server_cfg = getattr(config, 'server', SimpleNamespace())
        server_mode = _get_server_mode(config)
        effective_host = (
            args.host if args.host != '127.0.0.1' else getattr(server_cfg, 'host', '127.0.0.1')
        )
        effective_port = args.port if args.port > 0 else getattr(server_cfg, 'port', 8106)
        effective_reload = args.reload if args.reload else False
        effective_workers = (
            args.workers if args.workers != 1 else getattr(server_cfg, 'workers', 1)
        )
        if server_mode == 'shared' and args.port == 0:
            print("[Google User Desktop] Приложение настроено в режиме сервера 'shared'.")
            print(f'[Google User Desktop] Маршруты API обслуживаются через главный сервер (http://{effective_host}:8000).')
        _run_standalone_server(
            host=effective_host,
            port=effective_port,
            reload=effective_reload,
            workers=effective_workers,
        )
        return

    try:
        asyncio.run(run_google_desktop_dashboard())
    except KeyboardInterrupt:
        print('\n[Google User Desktop] Завершено пользователем.')
        sys.exit(0)


if __name__ == '__main__':
    main()
