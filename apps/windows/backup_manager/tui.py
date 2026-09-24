# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Backup, Libraries & File History TUI
# =============================================================================
# Description:
#   Терминальный интерфейс (TUI) на базе библиотеки Rich для отображения
#   статуса библиотек Windows, службы File History, теневых копий VSS и хранилища.
#
# Examples:
#   >>> from apps.windows.backup_manager.tui import BackupManagerTUI
#   >>> tui = BackupManagerTUI()
#   >>> tui.render_dashboard()
#
# File: tui.py
# Project: ai-breadboard
# Package: apps.windows.backup_manager
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Терминальный интерфейс (Rich TUI) для Windows Backup Manager."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from apps.windows.backup_manager.core.health_checker import BackupHealthChecker


class BackupManagerTUI:
    """Консольный рендерер аудита библиотек и бэкапов Windows."""

    def __init__(self, checker: BackupHealthChecker | None = None) -> None:
        self.console = Console()
        self.checker = checker or BackupHealthChecker()

    def render_dashboard(self) -> None:
        """Рендеринг основного дашборда аудита в консоль."""
        report = self.checker.generate_report()

        # 1. Заголовочная панель с Health Score
        score = report.health_score
        score_color = "green" if score >= 80 else ("yellow" if score >= 60 else "red")

        header_text = Text()
        header_text.append("🛡️ Windows Backup, Libraries & File History Center\n", style="bold cyan")
        header_text.append(f"Индекс готовности защиты данных: ", style="bold")
        header_text.append(f"{score}/100\n", style=f"bold {score_color}")

        # Сводка службы
        svc = report.file_history.service_status.value
        svc_style = "green" if svc == "running" else "yellow"
        header_text.append(f"Служба fhsvc: ", style="dim")
        header_text.append(f"{svc.upper()} ({report.file_history.service_start_type}) | ", style=f"bold {svc_style}")

        cfg = "Настроена" if report.file_history.config.is_configured else "Не настроена"
        cfg_style = "green" if report.file_history.config.is_configured else "red"
        header_text.append(f"Конфигурация: ", style="dim")
        header_text.append(f"{cfg} | ", style=f"bold {cfg_style}")

        header_text.append(f"Библиотек Windows: ", style="dim")
        header_text.append(f"{report.libraries_count}\n", style="bold white")

        self.console.print(Panel(header_text, border_style="cyan", padding=(1, 2)))

        # 2. Таблица библиотек Windows
        lib_table = Table(title="📁 Системные Библиотеки Windows (.library-ms)", header_style="bold blue")
        lib_table.add_column("Имя Библиотеки", style="cyan", width=20)
        lib_table.add_column("Папок", justify="center", width=8)
        lib_table.add_column("Включенные директории", style="dim")
        lib_table.add_column("Статус", justify="center", width=12)

        for lib in report.libraries:
            status_text = "[green]✓ Доступны[/green]" if lib.all_folders_exist else "[yellow]⚠ Неполный[/yellow]"
            folders_str = "\n".join([f"• {f.path} ({f.free_space_gb or '—'} ГБ свободно)" for f in lib.folders]) if lib.folders else "[italic text-muted]Нет папок[/italic text-muted]"
            lib_table.add_row(lib.name, str(lib.folder_count), folders_str, status_text)

        self.console.print(lib_table)
        self.console.print()

        # 3. Таблица хранилища и теневых копий
        if report.storage_audit and report.storage_audit.target_exists:
            st_table = Table(title="💾 Хранилище Резервных Копий File History", header_style="bold green")
            st_table.add_column("Параметр", style="bold")
            st_table.add_column("Значение", style="white")

            st_table.add_row("Путь к хранилищу", report.storage_audit.target_path)
            st_table.add_row("Всего сохраненных версий", str(report.storage_audit.total_versions_found))
            st_table.add_row("Суммарный объем", f"{report.storage_audit.total_backup_size_mb} МБ")
            st_table.add_row("Свободное место на диске", f"{report.storage_audit.free_space_gb} ГБ / {report.storage_audit.total_space_gb} ГБ")
            st_table.add_row("Архивированные тома", ", ".join(report.storage_audit.drives_in_backup) or "Нет данных")

            self.console.print(st_table)
            self.console.print()

        # 4. Рекомендации
        if report.recommendations:
            rec_text = Text()
            for r in report.recommendations:
                rec_text.append(f"• {r}\n", style="yellow")
            self.console.print(Panel(rec_text, title="⚠️ Рекомендации по оптимизации защиты", border_style="yellow"))

    def render_rag_results(self, query: str, results: list) -> None:
        """Рендеринг результатов RAG поиска по истории файлов в консоль."""
        if not results:
            self.console.print(Panel(f"[yellow]По запросу '{query}' совпадений в истории не найдено.[/yellow]", title="🔍 Результаты RAG поиска"))
            return

        table = Table(title=f"🔍 Найдено {len(results)} совпадений по запросу: '{query}'", header_style="bold magenta")
        table.add_column("Файл / Путь", style="cyan", width=30)
        table.add_column("Дата версии", justify="center", width=20)
        table.add_column("Score", justify="right", width=8)
        table.add_column("Найденный фрагмент", style="white")

        for r in results:
            dt_str = r.version_timestamp.strftime("%Y-%m-%d %H:%M:%S") if getattr(r, "version_timestamp", None) else "—"
            score_str = f"{r.score:.4f}"
            snippet = r.text[:150] + ("..." if len(r.text) > 150 else "")
            table.add_row(r.original_path, dt_str, score_str, snippet)

        self.console.print(table)