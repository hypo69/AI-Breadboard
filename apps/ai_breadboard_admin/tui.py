# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI Breadboard Admin TUI Dashboard
# =============================================================================
# Description:
#   Интерактивный терминальный интерфейс (TUI) на базе Rich для мониторинга
#   системных настроек AI Breadboard, конфигурации RAG, провайдеров и пользователей.
#
# Examples:
#   >>> from apps.ai_breadboard_admin.tui import run_admin_tui
#   >>> await run_admin_tui()
#
# File: tui.py
# Project: AI-Breadboard
# Package: apps.ai_breadboard_admin
# Module: tui
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, List

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from apps.ai_breadboard_admin.src import (
    AdminConfigManager,
    InstructionsManager,
    UserAdminService,
)

config_mgr = AdminConfigManager()
instructions_mgr = InstructionsManager()
user_svc = UserAdminService()


def _render_system_panel(rag_mode: str, search_engine: str) -> Panel:
    """Отрисовка панели системных настроек.

    Args:
        rag_mode (str): Текущий режим RAG.
        search_engine (str): Выбранный поисковый движок.

    Returns:
        Panel: Виджет панели с параметрами системы.
    """
    info = Text()
    info.append("Режим RAG: ", style="bold cyan")
    info.append(f"{rag_mode}\n", style="bold green")

    info.append("Веб-поиск: ", style="bold cyan")
    info.append(f"{search_engine}\n", style="bold yellow")

    info.append("Конфигурация: ", style="bold cyan")
    info.append(f"{config_mgr.config_path.name}\n", style="white")

    return Panel(info, title="[bold]Системные параметры[/bold]", border_style="blue")


def _render_users_table(users: List[Dict[str, Any]]) -> Table:
    """Отрисовка таблицы пользователей системы.

    Args:
        users (List[Dict[str, Any]]): Список пользователей.

    Returns:
        Table: Таблица пользователей.
    """
    table = Table(title="Пользователи платформы", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="dim", width=4)
    table.add_column("Имя", style="cyan")
    table.add_column("Email", style="white")
    table.add_column("Роль", style="green")
    table.add_column("Статус", style="yellow")

    for u in users[:10]:
        status_text = "Активен" if u.get("is_active") == 1 else "Заблокирован"
        role_text = "Admin" if u.get("is_admin") == 1 or u.get("role") == "admin" else "User"
        table.add_row(
            str(u.get("id", "")),
            str(u.get("name", "")),
            str(u.get("email", "")),
            role_text,
            status_text,
        )

    return table


def _render_instructions_panel(chat_inst: Dict[str, str], narrator_inst: Dict[str, str]) -> Panel:
    """Отрисовка панели состояния системных инструкций.

    Args:
        chat_inst (Dict[str, str]): Данные инструкции чата.
        narrator_inst (Dict[str, str]): Данные инструкции диктора.

    Returns:
        Panel: Панель со статусом файлов инструкций.
    """
    info = Text()
    info.append("Инструкция чата:\n", style="bold cyan")
    chat_len = len(chat_inst.get("content", ""))
    info.append(f"  Файл: {chat_inst.get('file')} ({chat_len} симв.)\n", style="white")

    info.append("Инструкция диктора:\n", style="bold cyan")
    narr_len = len(narrator_inst.get("content", ""))
    info.append(f"  Файл: {narrator_inst.get('file')} ({narr_len} симв.)\n", style="white")

    return Panel(info, title="[bold]Системные инструкции[/bold]", border_style="green")


async def run_admin_tui(interval: float = 3.0) -> None:
    """Запуск интерактивного терминального интерфейса администратора.

    Args:
        interval (float): Интервал обновления данных в секундах.
    """
    console = Console()
    layout = Layout()

    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3),
    )

    layout["header"].update(
        Panel(
            Text("⚙️ AI Breadboard Administration Dashboard", style="bold white", justify="center"),
            style="bold blue",
        )
    )

    layout["main"].split_row(
        Layout(name="left"),
        Layout(name="right"),
    )

    layout["footer"].update(
        Panel(
            Text("Панель администратора активна | Нажмите Ctrl+C для выхода", style="white", justify="center"),
            style="bold yellow",
        )
    )

    try:
        with Live(layout, refresh_per_second=2, console=console):
            while True:
                rag_cfg = config_mgr.get_rag_config()
                search_cfg = config_mgr.get_web_search_config()
                users_data = user_svc.get_users_list()
                chat_inst = instructions_mgr.get_instruction("chat")
                narr_inst = instructions_mgr.get_instruction("narrator")

                left_layout = Layout()
                left_layout.split_column(
                    Layout(_render_system_panel(rag_cfg.get("mode", ""), search_cfg.get("engine", "")), size=6),
                    Layout(_render_instructions_panel(chat_inst, narr_inst)),
                )
                layout["left"].update(left_layout)

                layout["right"].update(
                    Layout(_render_users_table(users_data.get("users", [])))
                )

                await asyncio.sleep(interval)
    except asyncio.CancelledError:
        console.print("[yellow]Завершение работы TUI...[/yellow]")
    except Exception as ex:
        console.print(f"[red]Ошибка TUI:[/red] {ex}")


__all__ = ["run_admin_tui"]
