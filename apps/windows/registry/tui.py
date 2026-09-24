# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Registry Viewer TUI Interface
# =============================================================================
# Description:
#   Консольный пользовательский интерфейс (TUI) на базе Rich для исследования,
#   просмотра закладок, параметров и результатов поиска в реестре Windows.
#
# File: tui.py
# Project: ai-breadboard
# Package: apps.windows.registry
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Консольный TUI интерфейс Windows Registry Viewer."""

from __future__ import annotations

from typing import List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich import box

from apps.windows.registry.models import (
    BookmarkItem,
    RegistryKeyDetailsDTO,
    SearchResponseDTO,
)
from apps.windows.registry.viewer import RegistryViewer


class RegistryViewerTUI:
    """TUI интерфейс для вывода информации о реестре Windows."""

    def __init__(self, viewer: Optional[RegistryViewer] = None) -> None:
        """Инициализация TUI консоли."""
        self.console = Console()
        self.viewer = viewer or RegistryViewer()

    def render_bookmarks(self, bookmarks: Optional[List[BookmarkItem]] = None) -> None:
        """Отобразить таблицу быстрых системных закладок."""
        items = bookmarks or self.viewer.get_bookmarks()
        table = Table(
            title="🗝️ Быстрые системные закладки реестра Windows",
            box=box.ROUNDED,
            header_style="bold magenta",
        )
        table.add_column("ID", style="cyan", width=22)
        table.add_column("Иконка / Название", style="bold white", width=36)
        table.add_column("Ветка", style="yellow", width=20)
        table.add_column("Путь к разделу", style="dim white")

        for bm in items:
            table.add_row(
                bm.id,
                f"{bm.icon} {bm.title}",
                bm.hive,
                bm.path,
            )

        self.console.print(table)
        self.console.print(
            "[dim]Используйте: [bold cyan]python -m apps.windows.registry --bookmark <id>[/bold cyan] для быстрого перехода.[/dim]\n"
        )

    def render_key_details(self, details: RegistryKeyDetailsDTO) -> None:
        """Отобразить детальную информацию о ключе, подразделы и параметры."""
        # Верхняя информационная панель
        info_panel = Panel(
            f"[bold green]Ветка:[/bold green] {details.hive}\n"
            f"[bold green]Путь:[/bold green] {details.path or '(Корневой раздел)'}\n"
            f"[bold green]Полный путь:[/bold green] [bold cyan]{details.full_path}[/bold cyan]\n"
            f"[bold green]Подразделов:[/bold green] {details.subkeys_count}  |  "
            f"[bold green]Параметров:[/bold green] {details.values_count}",
            title="📂 Просмотр раздела реестра Windows",
            border_style="bright_blue",
        )
        self.console.print(info_panel)

        # Таблица параметров (Values)
        if details.values:
            val_table = Table(
                title=f"📋 Параметры раздела ({len(details.values)})",
                box=box.SIMPLE_HEAVY,
                header_style="bold cyan",
            )
            val_table.add_column("Имя параметра", style="bold white", width=32)
            val_table.add_column("Тип", style="magenta", width=16)
            val_table.add_column("Данные / Значение", style="green")
            val_table.add_column("Размер", style="dim", justify="right", width=10)

            for val in details.values:
                # Цветовая подсветка типов
                type_style = "magenta"
                if "SZ" in val.type_name:
                    type_style = "green"
                elif "DWORD" in val.type_name or "QWORD" in val.type_name:
                    type_style = "cyan"
                elif "BINARY" in val.type_name:
                    type_style = "yellow"

                val_table.add_row(
                    val.name,
                    f"[{type_style}]{val.type_name}[/{type_style}]",
                    str(val.data),
                    f"{val.size_bytes} B",
                )
            self.console.print(val_table)
        else:
            self.console.print("[yellow]Параметры отсутствуют в данном ключе.[/yellow]")

        # Дерево подразделов (Subkeys)
        if details.subkeys:
            tree = Tree(f"📁 [bold blue]Подразделы ({len(details.subkeys)})[/bold blue]")
            display_limit = 40
            for sk in details.subkeys[:display_limit]:
                tree.add(f"[dim]📁[/dim] {sk}")
            if len(details.subkeys) > display_limit:
                tree.add(f"[italic dim]... и еще {len(details.subkeys) - display_limit} подразделов[/italic dim]")
            self.console.print(tree)
            self.console.print()

    def render_search_results(self, response: SearchResponseDTO) -> None:
        """Отобразить результаты поиска по реестру."""
        if not response.results:
            self.console.print(
                f"[yellow]По запросу '{response.query}' ничего не найдено в ветке {response.hive}\\{response.path}.[/yellow]"
            )
            return

        table = Table(
            title=f"🔍 Результаты поиска по запросу '{response.query}' (Найдено: {response.total_found})",
            box=box.ROUNDED,
            header_style="bold green",
        )
        table.add_column("Тип совпадения", style="cyan", width=16)
        table.add_column("Путь к ключу", style="bold white", width=40)
        table.add_column("Параметр / Текст", style="yellow", width=25)
        table.add_column("Данные", style="dim green")

        for item in response.results:
            match_type_label = {
                "key_name": "📁 Подраздел",
                "value_name": "📝 Имя параметра",
                "value_data": "💾 Значение",
            }.get(item.match_type, item.match_type)

            table.add_row(
                match_type_label,
                f"{item.hive}\\{item.key_path}",
                item.value_name or item.matched_text,
                str(item.value_data) if item.value_data is not None else "-",
            )

        self.console.print(table)
