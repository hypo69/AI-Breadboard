"""Консольный интерактивный интерфейс (TUI) для Google User Desktop."""
from __future__ import annotations

import asyncio
from typing import Any, List, Optional

from .src.state import GoogleUserDesktopState

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


def _render_account_table(state: GoogleUserDesktopState) -> Table:
    """Отрисовать таблицу информации об активном Google аккаунте.

    Args:
        state: Активный экземпляр состояния GoogleUserDesktopState.

    Returns:
        Table: Настроенная таблица Rich.
    """
    table = Table(expand=True, show_header=False, box=None, padding=(0, 1))
    table.add_column("Параметр", style="bold cyan", width=18)
    table.add_column("Значение", style="white")

    acc = state.get_active_account()
    status_color = "green" if acc.status == "active" else "red"
    table.add_row("Аккаунт", acc.name or "[dim]N/A[/dim]")
    table.add_row("Email", acc.email or "[dim]Не указан[/dim]")
    table.add_row("Тип авторизации", acc.account_type)
    table.add_row("Статус", f"[{status_color}]{acc.status.upper()}[/{status_color}]")
    table.add_row("По умолчанию", "ДА" if acc.is_default else "НЕТ")
    table.add_row("─" * 16, "─" * 30)
    table.add_row("Писем в почте", str(len(state._mail_cache)))
    table.add_row("Событий календаря", str(len(state._calendar_cache)))
    table.add_row("Google Docs/Sheets", str(len(state._docs_cache)))
    table.add_row("Файлов на Диске", str(len(state._drive_cache)))
    return table


def _render_mail_table(state: GoogleUserDesktopState) -> Table:
    """Отрисовать таблицу входящих писем Gmail.

    Args:
        state: Экземпляр состояния GoogleUserDesktopState.

    Returns:
        Table: Таблица со списком сообщений.
    """
    table = Table(
        title="📧 Входящие сообщения Gmail",
        expand=True,
        header_style="bold magenta",
        border_style="bright_black",
    )
    table.add_column("Отправитель", style="bold yellow", width=22)
    table.add_column("Тема", style="white", min_width=25)
    table.add_column("Дата", style="dim", width=18)

    msgs = state._mail_cache
    if not msgs:
        table.add_row("[dim]—[/dim]", "[dim]Сообщения отсутствуют или нет подключения[/dim]", "[dim]—[/dim]")
        return table

    for m in msgs[:8]:
        table.add_row(m.sender[:20], m.subject[:35], m.date[:16])
    return table


def _render_calendar_table(state: GoogleUserDesktopState) -> Table:
    """Отрисовать таблицу ближайших событий Календаря.

    Args:
        state: Экземпляр состояния GoogleUserDesktopState.

    Returns:
        Table: Таблица событий.
    """
    table = Table(
        title="📅 Предстоящие события Google Calendar",
        expand=True,
        header_style="bold green",
        border_style="bright_black",
    )
    table.add_column("Время", style="bold cyan", width=16)
    table.add_column("Событие", style="white", min_width=25)
    table.add_column("Локация", style="dim", width=15)

    events = state._calendar_cache
    if not events:
        table.add_row("[dim]—[/dim]", "[dim]Событий не найдено[/dim]", "[dim]—[/dim]")
        return table

    for e in events[:8]:
        table.add_row(e.start_time[:15] if e.start_time else "—", e.summary[:30], e.location[:15] or "—")
    return table


def render_ui(state: GoogleUserDesktopState) -> Any:
    """Скомпоновать полный Rich TUI макет дашборда Google User Desktop.

    Args:
        state: Экземпляр состояния.

    Returns:
        Any: Объект Layout библиотеки Rich.
    """
    if not RICH_AVAILABLE:
        return None

    layout = Layout()
    layout.split_column(
        Layout(name="header", size=4),
        Layout(name="main", ratio=1),
        Layout(name="footer", size=3),
    )
    layout["main"].split_row(
        Layout(name="left_panel", ratio=2),
        Layout(name="right_panel", ratio=3),
    )
    layout["right_panel"].split_column(
        Layout(name="mail", ratio=1),
        Layout(name="calendar", ratio=1),
    )

    acc = state.get_active_account()
    header_text = Text.assemble(
        ("GOOGLE USER DESKTOP WORKSPACE & SERVICES\n", "bold cyan"),
        ("Активный аккаунт: ", "dim"),
        (f"{acc.name} ({acc.email or 'без email'}) ", "bold yellow"),
        (f"| Статус: [{acc.status.upper()}] ", "bold green" if acc.status == "active" else "bold red"),
        (f"| Обновлено: {state.last_refreshed or 'никогда'}", "dim"),
    )
    layout["header"].update(Panel(header_text, border_style="cyan"))

    info_table = _render_account_table(state)
    layout["left_panel"].update(Panel(info_table, title="👤 Google Account Telemetry", border_style="blue"))

    mail_table = _render_mail_table(state)
    layout["mail"].update(Panel(mail_table, border_style="bright_black"))

    cal_table = _render_calendar_table(state)
    layout["calendar"].update(Panel(cal_table, border_style="bright_black"))

    footer_text = Text(
        " [Q] Quit  |  [S] Sync Services  |  Polling Interval: 5.0s",
        style="dim white",
    )
    layout["footer"].update(Panel(footer_text, border_style="bright_black"))

    return layout


async def run_google_desktop_dashboard(
    interval: float = 5.0, max_iterations: Optional[int] = None
) -> None:
    """Запустить интерактивный консольный дашборд.

    Args:
        interval: Частота обновления в секундах.
        max_iterations: Максимальное количество итераций (для тестов).
    """
    if not RICH_AVAILABLE:
        print("Библиотека Rich требуется для интерактивного терминального UI.")
        return

    console = Console()
    state = GoogleUserDesktopState()
    state.refresh_all(probe_network=True)
    iterations = 0

    with Live(render_ui(state), console=console, refresh_per_second=2, screen=True) as live:
        try:
            while True:
                probe_net = iterations % 3 == 0
                state.refresh_all(probe_network=probe_net)
                live.update(render_ui(state))
                iterations += 1
                if max_iterations and iterations >= max_iterations:
                    break
                await asyncio.sleep(interval)
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass
