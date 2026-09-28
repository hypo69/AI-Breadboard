"""Интерактивный TUI дашборд для визуализации и управления Dead Letter Queue (DLQ)."""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any, Optional

# Обеспечение импорта локальных модулей
sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage import DLQStorage

try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    Console = Any
    Layout = Any
    Live = Any
    Panel = Any
    Table = Any
    Text = Any
    RICH_AVAILABLE = False


def _build_summary_panel(storage: DLQStorage) -> Panel:
    """Сформировать сводную панель метрик DLQ очереди.

    Args:
        storage: Экземпляр хранилища DLQStorage.

    Returns:
        Panel: Панель Rich со статистикой.
    """
    stats = storage.get_stats()
    total = stats.get("TOTAL", 0)
    pending = stats.get("PENDING", 0)
    retrying = stats.get("RETRYING", 0)
    resolved = stats.get("RESOLVED", 0)
    failed = stats.get("FAILED", 0)

    summary_text = Text()
    summary_text.append(f"Всего записей: {total}  │  ", style="bold white")
    summary_text.append(f"Ожидают (PENDING): {pending}  │  ", style="bold yellow")
    summary_text.append(f"Повтор (RETRYING): {retrying}  │  ", style="bold cyan")
    summary_text.append(f"Решено (RESOLVED): {resolved}  │  ", style="bold green")
    summary_text.append(f"Сбои (FAILED): {failed}", style="bold red")

    return Panel(summary_text, title="📊 Статистика DLQ", border_style="blue")


def _build_table(storage: DLQStorage, limit: int = 20) -> Table:
    """Сформировать таблицу текущих сообщений в очереди.

    Args:
        storage: Экземпляр хранилища DLQStorage.
        limit: Лимит отображаемых строк.

    Returns:
        Table: Компонент таблицы Rich.
    """
    table = Table(expand=True, show_header=True, header_style="bold magenta", box=None)
    table.add_column("ID", style="bold cyan", width=6)
    table.add_column("Источник", style="yellow", width=18)
    table.add_column("Ошибка / Traceback", style="bold red", ratio=2)
    table.add_column("Retry", style="magenta", width=6, justify="center")
    table.add_column("Статус", style="bold green", width=12, justify="center")
    table.add_column("Создано", style="dim white", width=19)

    messages = storage.list_all(limit=limit)
    if not messages:
        table.add_row("-", "N/A", "[dim]Очередь DLQ пуста. Ошибок не обнаружено.[/dim]", "0", "[green]CLEAN[/green]", "-")
        return table

    for msg in messages:
        status = msg["status"]
        if status == "RESOLVED":
            status_markup = f"[bold green]{status}[/bold green]"
        elif status == "RETRYING":
            status_markup = f"[bold cyan]{status}[/bold cyan]"
        elif status == "FAILED":
            status_markup = f"[bold red]{status}[/bold red]"
        else:
            status_markup = f"[bold yellow]{status}[/bold yellow]"

        err_msg = msg["error_message"]
        truncated_err = err_msg[:75] + ("..." if len(err_msg) > 75 else "")

        table.add_row(
            str(msg["id"]),
            msg["source"],
            truncated_err,
            str(msg["retry_count"]),
            status_markup,
            str(msg["created_at"]),
        )

    return table


def render_dlq_dashboard(storage: Optional[DLQStorage] = None) -> Layout:
    """Скомпоновать полный макет TUI дашборда.

    Args:
        storage: Экземпляр хранилища DLQStorage.

    Returns:
        Layout: Объект макета Rich.
    """
    store = storage or DLQStorage()
    layout = Layout()
    layout.split(
        Layout(name="header", size=3),
        Layout(name="summary", size=3),
        Layout(name="body", ratio=1),
        Layout(name="footer", size=3),
    )

    header_panel = Panel(
        Text("🚨 Dead Letter Queue (DLQ) — Terminal User Interface", style="bold cyan", justify="center"),
        border_style="cyan",
    )
    footer_panel = Panel(
        Text("Команды CLI: py .agents/skills/dlq/scripts/manager.py [push|list|retry|purge|tui] | Ctrl+C для выхода", style="dim white", justify="center"),
        border_style="dim",
    )

    layout["header"].update(header_panel)
    layout["summary"].update(_build_summary_panel(store))
    layout["body"].update(Panel(_build_table(store), title="📋 Записи очереди (Последние)", border_style="white"))
    layout["footer"].update(footer_panel)

    return layout


def run_dlq_tui(refresh_interval: float = 2.0, once: bool = False, storage: Optional[DLQStorage] = None) -> None:
    """Запустить интерактивный TUI дашборд в режиме реального времени.

    Args:
        refresh_interval: Интервал обновления экрана в секундах.
        once: Запустить только один кадр и завершить (для тестов и отладки).
        storage: Пользовательский объект DLQStorage.
    """
    if not RICH_AVAILABLE:
        print("Ошибка: Библиотека 'rich' не установлена. Установите её через `pip install rich`.")
        return

    console = Console()
    store = storage or DLQStorage()

    if once:
        console.print(render_dlq_dashboard(store))
        return

    console.clear()
    try:
        with Live(render_dlq_dashboard(store), refresh_per_second=1 / refresh_interval, console=console) as live:
            while True:
                time.sleep(refresh_interval)
                live.update(render_dlq_dashboard(store))
    except KeyboardInterrupt:
        console.print("\n[yellow]Мониторинг TUI DLQ завершен.[/yellow]")


if __name__ == "__main__":
    once_flag = "--once" in sys.argv
    run_dlq_tui(once=once_flag)
