"""CLI-запуск Enterprise Knowledge Platform."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from apps.enterprise_knowledge.engine import EnterpriseKnowledgeEngine
from apps.enterprise_knowledge.storage import KnowledgeStore


def main() -> None:
    """Разбор аргументов командной строки и запуск выбранного режима."""
    parser = argparse.ArgumentParser(
        description="Enterprise Knowledge Platform - Unified Enterprise Knowledge Platform",
    )
    parser.add_argument(
        "--mode",
        choices=["tui", "server", "status"],
        default="server",
        help="Режим выполнения (по умолчанию: server)",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Хост сервера (для режима server)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8181,
        help="Порт сервера (для режима server)",
    )

    args = parser.parse_args()

    if args.mode == "status":
        store = KnowledgeStore()
        status_info = {
            "service": "enterprise_knowledge",
            "db_path": str(store.db_path),
            "status": "ok",
        }
        print(json.dumps(status_info, indent=2, ensure_ascii=False))
        return

    if args.mode == "server":
        import uvicorn
        from fastapi import FastAPI
        from apps.enterprise_knowledge.router import init_router

        app = FastAPI(title="Enterprise Knowledge Platform API")
        app.include_router(init_router())
        print(f"Запуск автономного сервера Enterprise Knowledge Platform на https://{args.host}:{args.port}/helpdesk")
        uvicorn.run(app, host=args.host, port=args.port, ssl_certfile=".certs/localhost+2.pem", ssl_keyfile=".certs/localhost+2-key.pem")
        return

    # По умолчанию: Интерактивный TUI
    asyncio.run(run_enterprise_knowledge_tui())


async def run_enterprise_knowledge_tui(interval: float = 3.0) -> None:
    """Запуск интерактивного терминального интерфейса Enterprise Knowledge Platform."""
    from rich.console import Console
    from rich.layout import Layout
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    console = Console()
    layout = Layout()

    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3),
    )

    layout["header"].update(
        Panel(
            Text("🏢 Enterprise Knowledge Platform", style="bold white", justify="center"),
            style="bold blue",
        )
    )

    layout["main"].split_row(
        Layout(name="left"),
        Layout(name="right"),
    )

    layout["footer"].update(
        Panel(
            Text("Панель Enterprise Knowledge Platform активна | Нажмите Ctrl+C для выхода", style="white", justify="center"),
            style="bold yellow",
        )
    )

    try:
        with Live(layout, refresh_per_second=2, console=console):
            while True:
                store = KnowledgeStore()
                
                # Get employee count
                with store._connect() as connection:
                    employee_count = connection.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
                    fact_count = connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
                    source_count = connection.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
                
                left_layout = Layout()
                left_layout.split_column(
                    Layout(_render_system_panel(employee_count, fact_count, source_count), size=8),
                )
                layout["left"].update(left_layout)

                layout["right"].update(
                    Layout(_render_facts_table(store))
                )

                await asyncio.sleep(interval)
    except asyncio.CancelledError:
        console.print("[yellow]Завершение работы TUI...[/yellow]")
    except Exception as ex:
        console.print(f"[red]Ошибка TUI:[/red] {ex}")


def _render_system_panel(employee_count: int, fact_count: int, source_count: int) -> Panel:
    """Отрисовка панели системных настроек."""
    info = Text()
    info.append("Сотрудники: ", style="bold cyan")
    info.append(f"{employee_count}\n", style="bold green")

    info.append("Факты: ", style="bold cyan")
    info.append(f"{fact_count}\n", style="bold yellow")

    info.append("Источники: ", style="bold cyan")
    info.append(f"{source_count}\n", style="bold magenta")

    return Panel(info, title="[bold]Enterprise Knowledge Platform[/bold]", border_style="blue")


def _render_facts_table(store: KnowledgeStore) -> Table:
    """Отрисовка таблицы последних фактов."""
    table = Table(title="Последние факты", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="dim", width=10)
    table.add_column("Сотрудник", style="cyan")
    table.add_column("Предикат", style="white")
    table.add_column("Объект", style="green")
    table.add_column("Статус", style="yellow")

    with store._connect() as connection:
        facts = connection.execute(
            "SELECT f.fact_id, e.name, f.predicate, f.object_value, f.status "
            "FROM facts f LEFT JOIN employees e ON e.employee_id=f.employee_id "
            "ORDER BY f.created_at DESC LIMIT 10"
        ).fetchall()

        for f in facts:
            table.add_row(
                f["fact_id"][:10],
                str(f["name"] or "N/A"),
                f["predicate"],
                str(f["object_value"])[:30],
                f["status"],
            )

    return table


if __name__ == "__main__":
    main()
