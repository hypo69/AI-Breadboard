# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Storage_Manager - Tui
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.storage_manager.tui import StorageManagerTUI
#
#     service = StorageManagerTUI()
#
# File: tui.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.storage_manager
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from apps.windows.sdk.modules.storage_manager.core.manager import StorageManager
from apps.windows.sdk.modules.storage_manager.core.models import (
    DiskDetailedInfo,
    SectorReadResponse,
    StorageTaskStatus,
)


class StorageManagerTUI:
    """Консольный интерфейс отображения дисковых накопителей и низкоуровневых операций."""

    def __init__(self, manager: Optional[StorageManager] = None) -> None:
        """Инициализация TUI."""
        self.manager = manager or StorageManager()
        self.console = Console()

    def render_dashboard(self) -> None:
        """Отображение сводного дашборда дисков и томов."""
        report = self.manager.generate_report()

        disk_table = Table(title='Физические накопители (Physical Disks)', header_style='bold cyan')
        disk_table.add_column('Диск ID', justify='center')
        disk_table.add_column('Модель / Имя')
        disk_table.add_column('Шина (Bus)', justify='center')
        disk_table.add_column('Тип', justify='center')
        disk_table.add_column('Объем (GB)', justify='right')
        disk_table.add_column('Статус', justify='center')

        for d in report.disks:
            color = 'green' if 'healthy' in d.status.lower() or 'ok' in d.status.lower() else 'yellow'
            disk_table.add_row(
                str(d.disk_id),
                d.name,
                d.bus_type,
                d.media_type,
                f"{d.size_gb:.1f}",
                f"[{color}]{d.status}[/{color}]",
            )

        vol_table = Table(title='Логические тома (Volumes)', header_style='bold magenta')
        vol_table.add_column('Буква / Путь', justify='center')
        vol_table.add_column('Файловая система', justify='center')
        vol_table.add_column('Всего (GB)', justify='right')
        vol_table.add_column('Свободно (GB)', justify='right')
        vol_table.add_column('Занято %', justify='right')

        for v in report.volumes:
            use_color = 'green' if v.percent_used < 85 else ('yellow' if v.percent_used < 95 else 'bold red')
            vol_table.add_row(
                v.drive_letter or 'N/A',
                v.filesystem,
                f"{v.total_gb:.1f}",
                f"{v.free_gb:.1f}",
                f"[{use_color}]{v.percent_used}%[/{use_color}]",
            )

        self.console.print(Panel('[bold white]AI-Breadboard: Storage & Raw Block Cloner[/bold white]', style='blue'))
        self.console.print(disk_table)
        self.console.print(vol_table)

    def render_disk_info(self, disk_id: int) -> None:
        """Отображение подробной информации о диске, геометрии и разделах."""
        info: DiskDetailedInfo = self.manager.get_disk_detailed(disk_id)

        geom_table = Table(title=f"Физическая геометрия: {info.device_path}", header_style='bold cyan')
        geom_table.add_column('Параметр', style='dim')
        geom_table.add_column('Значение', style='bold white')

        geom_table.add_row('Устройство', info.device_path)
        geom_table.add_row('Модель', info.friendly_name)
        geom_table.add_row('Интерфейс (Bus)', info.bus_type)
        geom_table.add_row('Размер сектора', f"{info.geometry.bytes_per_sector} байт")
        geom_table.add_row('Всего секторов', f"{info.geometry.total_sectors:,}")
        geom_table.add_row('Общий объем', f"{info.geometry.disk_size_bytes / (1024**3):.2f} GB ({info.geometry.disk_size_bytes:,} bytes)")
        geom_table.add_row('Цилиндры / Дорожки', f"{info.geometry.cylinders} / {info.geometry.tracks_per_cylinder}")
        geom_table.add_row('Разметка', 'GPT' if info.headers and info.headers.has_valid_gpt else ('MBR' if info.headers and info.headers.has_valid_mbr else 'RAW'))

        parts_table = Table(title=f"Таблица разделов (Partitions)", header_style='bold green')
        parts_table.add_column('#', justify='center')
        parts_table.add_column('Стиль', justify='center')
        parts_table.add_column('Тип раздела')
        parts_table.add_column('Start LBA', justify='right')
        parts_table.add_column('End LBA', justify='right')
        parts_table.add_column('Размер (MB)', justify='right')
        parts_table.add_column('Загрузочный', justify='center')

        for p in info.partitions:
            parts_table.add_row(
                str(p.partition_number),
                p.partition_style,
                p.partition_type,
                f"{p.start_lba:,}",
                f"{p.end_lba:,}",
                f"{p.partition_length / (1024*1024):.1f}",
                "[green]Да[/green]" if p.is_bootable else "[dim]Нет[/dim]",
            )

        self.console.print(Panel(f"[bold cyan]Инспекция накопителя #{disk_id}[/bold cyan]"))
        self.console.print(geom_table)
        self.console.print(parts_table)

    def render_hex_dump(self, res: SectorReadResponse) -> None:
        """Отображение дампа прочитанных секторов."""
        self.console.print(Panel(
            f"[bold yellow]Дамп сектора: PhysicalDrive{res.disk_id} | LBA {res.start_lba} ({res.bytes_read} байт)[/bold yellow]\n\n"
            f"[bold white]HEX:[/bold white]\n{res.hex_dump}\n\n"
            f"[bold white]ASCII:[/bold white]\n{res.ascii_preview}"
        ))

    def render_task_status(self, task: StorageTaskStatus) -> None:
        """Отображение статуса фоновой задачи."""
        status_color = 'green' if task.status == 'completed' else ('red' if task.status == 'failed' else 'yellow')
        self.console.print(Panel(
            f"[bold cyan]Задача #{task.task_id} ({task.task_type})[/bold cyan]\n"
            f"Источник: [bold]{task.source}[/bold] -> Назначение: [bold]{task.destination}[/bold]\n"
            f"Статус: [{status_color}]{task.status.upper()}[/{status_color}] (Dry-Run: {task.dry_run})\n"
            f"Прогресс: [bold]{task.progress_percent}%[/bold] ({task.processed_bytes / (1024*1024):.1f} MB / {task.total_bytes / (1024*1024):.1f} MB)\n"
            f"Скорость: {task.speed_mb_s} MB/s | ETA: {task.eta_seconds or 0} сек"
        ))


__all__ = ['StorageManagerTUI']
