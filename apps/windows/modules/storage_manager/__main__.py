# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Storage_Manager -   Main  
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   CLI:
#     python -m apps.windows.modules.storage_manager.__main__
#   Python API:
#     from apps.windows.modules.storage_manager.__main__ import main
#
#     res = main()
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.windows.modules.storage_manager
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

import argparse
import asyncio
from logger import logger
from apps.windows.modules.storage_manager.core.manager import StorageManager
from apps.windows.modules.storage_manager.core.models import (
    DiskCloneRequest,
    DiskHashRequest,
    DiskImageCreateRequest,
    DiskImageRestoreRequest,
    SectorReadRequest,
)
from apps.windows.modules.storage_manager.tui import StorageManagerTUI


def main() -> None:
    """Обработка аргументов командной строки."""
    parser = argparse.ArgumentParser(description='Windows Storage & Raw Block Cloner')
    subparsers = parser.add_subparsers(dest='command', help='Подкоманды')

    # Сервер
    srv_p = subparsers.add_parser('server', help='Запуск выделенного REST API сервера')
    srv_p.add_argument('--port', type=int, default=8120, help='TCP порт')
    srv_p.add_argument('--host', type=str, default='127.0.0.1', help='IP адрес')

    # Дашборд / Список
    list_p = subparsers.add_parser('list', help='Список физических дисков и томов')
    list_p.add_argument('--json', action='store_true', help='Вывод в JSON')

    # Детальная инспекция диска
    info_p = subparsers.add_parser('info', help='Детальная геометрия и таблица разделов MBR/GPT')
    info_p.add_argument('disk_id', type=int, default=0, nargs='?', help='Номер PhysicalDrive')

    # Чтение секторов
    read_p = subparsers.add_parser('read', help='Прямое посекторное чтение')
    read_p.add_argument('disk_id', type=int, help='Номер PhysicalDrive')
    read_p.add_argument('--lba', type=int, default=0, help='Начальный LBA сектор')
    read_p.add_argument('--count', type=int, default=1, help='Количество секторов')

    # Клонирование диск-в-диск
    clone_p = subparsers.add_parser('clone', help='Посекторное клонирование физического диска')
    clone_p.add_argument('--source', type=int, required=True, help='ID исходного диска')
    clone_p.add_argument('--target', type=int, required=True, help='ID целевого диска')
    clone_p.add_argument('--mode', choices=['raw', 'smart'], default='raw', help='Режим клонирования')
    clone_p.add_argument('--dry-run', action='store_true', default=True, help='Режим симуляции (Dry-Run)')
    clone_p.add_argument('--force-system', action='store_true', help='Разрешить запись на системный диск')
    clone_p.add_argument('--confirm', action='store_true', help='Подтверждение деструктивной записи')

    # Создание raw-образа
    img_p = subparsers.add_parser('image', help='Создание raw-образа диска в файл')
    img_p.add_argument('--disk', type=int, required=True, help='ID диска')
    img_p.add_argument('--out', type=str, required=True, help='Путь к файлу образа (.img/.raw)')
    img_p.add_argument('--dry-run', action='store_true', default=True, help='Режим симуляции')

    # Восстановление из образа
    res_p = subparsers.add_parser('restore', help='Восстановление диска из raw-образа')
    res_p.add_argument('--disk', type=int, required=True, help='ID целевого диска')
    res_p.add_argument('--in', dest='in_file', type=str, required=True, help='Путь к файлу образа')
    res_p.add_argument('--dry-run', action='store_true', default=True, help='Режим симуляции')
    res_p.add_argument('--confirm', action='store_true', help='Подтверждение записи')

    # Расчет хеша
    hash_p = subparsers.add_parser('hash', help='Вычисление SHA-256 хеша секторов диска')
    hash_p.add_argument('disk_id', type=int, help='Номер PhysicalDrive')
    hash_p.add_argument('--lba', type=int, default=0, help='Начальный LBA')
    hash_p.add_argument('--count', type=int, default=2048, help='Количество секторов')

    # Флаги по умолчанию
    parser.add_argument('--mode', type=str, choices=['cli', 'server'], default='cli', help='Устаревший флаг режима')
    parser.add_argument('--json', action='store_true', help='Вывод отчета в формате JSON')

    args = parser.parse_args()
    mgr = StorageManager()
    tui = StorageManagerTUI(manager=mgr)

    if args.command == 'server' or args.mode == 'server':
        import uvicorn
        from fastapi import FastAPI
        from apps.windows.modules.storage_manager.router import init_router

        app = FastAPI(title='Windows Storage & Raw Cloner API', version='2.0.0')
        app.include_router(init_router())
        port = getattr(args, 'port', 8120)
        host = getattr(args, 'host', '127.0.0.1')
        logger.info(f"Запуск Storage Manager на http://{host}:{port}")
        uvicorn.run(app, host=host, port=port)
        return

    if args.command == 'info':
        tui.render_disk_info(args.disk_id)
        return

    if args.command == 'read':
        req = SectorReadRequest(disk_id=args.disk_id, start_lba=args.lba, sector_count=args.count)
        res = mgr.read_sectors(req)
        tui.render_hex_dump(res)
        return

    if args.command == 'clone':
        req = DiskCloneRequest(
            source_disk_id=args.source,
            target_disk_id=args.target,
            clone_mode=args.mode,
            dry_run=args.dry_run and not args.confirm,
            force_system_drive=args.force_system,
            confirmed_by_user=args.confirm,
        )
        task = asyncio.run(mgr.start_clone(req))
        tui.render_task_status(task)
        return

    if args.command == 'image':
        req = DiskImageCreateRequest(
            disk_id=args.disk,
            image_path=args.out,
            dry_run=args.dry_run,
        )
        task = asyncio.run(mgr.start_image_create(req))
        tui.render_task_status(task)
        return

    if args.command == 'restore':
        req = DiskImageRestoreRequest(
            disk_id=args.disk,
            image_path=args.in_file,
            dry_run=args.dry_run and not args.confirm,
            confirmed_by_user=args.confirm,
        )
        task = asyncio.run(mgr.start_image_restore(req))
        tui.render_task_status(task)
        return

    if args.command == 'hash':
        req = DiskHashRequest(disk_id=args.disk_id, start_lba=args.lba, sector_count=args.count)
        h_res = mgr.compute_hash(req)
        print(f"PhysicalDrive{h_res.disk_id} SHA-256 (LBA {h_res.start_lba}+{h_res.sector_count}): {h_res.hash_hex} ({h_res.duration_sec}s)")
        return

    # По умолчанию: дашборд
    if getattr(args, 'json', False):
        report = mgr.generate_report()
        print(report.model_dump_json(indent=2))
        return

    tui.render_dashboard()


if __name__ == '__main__':
    main()
