# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules System_Checkpoints - Tui
# =============================================================================
# Description:
#   Rich TUI консольный интерфейс для управления контрольными точками и образами Windows.
#
# Usage Examples:
#   CLI:
#     python -m apps.windows.modules.system_checkpoints.tui
#   Python API:
#     from apps.windows.modules.system_checkpoints.tui import render_dashboard
#
#     res = render_dashboard()
#
# File: tui.py
# Project: ai-breadboard
# Package: apps.windows.modules.system_checkpoints
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Rich TUI консольный интерфейс для управления контрольными точками и образами Windows."""

import sys
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt

from apps.windows.system_checkpoints.models import CheckpointCreateRequest, CheckpointType
from apps.windows.system_checkpoints.core.checkpoint_coordinator import CheckpointCoordinator


def render_dashboard(coordinator: CheckpointCoordinator, console: Console) -> None:
    """Отрисовка главного дашборда системы контрольных точек."""
    health = coordinator.get_comprehensive_health()
    freshness = coordinator.get_freshness_report()

    console.clear()
    console.print(
        Panel(
            "[bold cyan]🛡️ Windows System Checkpoints & Recovery Manager[/bold cyan]\n"
            "[dim]Управление образами восстановления WIM, средой WinRE и точками восстановления VSS[/dim]",
            border_style="cyan",
        )
    )

    # Таблица трех механизмов
    mech_table = Table(title="🔧 Три механизма восстановления системы", expand=True)
    mech_table.add_column("Механизм", style="bold white")
    mech_table.add_column("Статус", style="bold")
    mech_table.add_column("Детали", style="dim")

    # WinRE
    winre = health.get("winre", {})
    w_enabled = winre.get("enabled", False)
    w_status = "[bold green]ВКЛЮЧЕНА[/bold green]" if w_enabled else "[bold red]ОТКЛЮЧЕНА[/bold red]"
    w_details = f"Расположение: {winre.get('location') or 'По умолчанию'} | BCD ID: {winre.get('bcd_id') or 'N/A'}"
    mech_table.add_row("1. Recovery Environment (WinRE)", w_status, w_details)

    # Restore Points
    sr = health.get("system_restore", {})
    sr_prot = sr.get("protection_enabled", False)
    sr_status = "[bold green]АКТИВНА[/bold green]" if sr_prot else "[bold yellow]ОТКЛЮЧЕНА[/bold yellow]"
    sr_details = f"Точек в наличии: {sr.get('restore_points_count', 0)}"
    mech_table.add_row("2. Restore Points (System Restore)", sr_status, sr_details)

    # System Images
    s_img = health.get("system_images", {})
    img_cnt = s_img.get("total_images_found", 0)
    img_status = f"[bold green]{img_cnt} обр.[/bold green]" if img_cnt > 0 else "[bold yellow]0 обр.[/bold yellow]"
    latest_img = s_img.get("latest_image")
    img_details = f"Последний: {latest_img.get('image_path') if latest_img else 'Не найден'}"
    mech_table.add_row("3. System Image (WIM/DISM)", img_status, img_details)

    console.print(mech_table)

    # Панель актуальности (Freshness & System Drift)
    fresh_style = "green" if freshness.freshness_level.value == "HIGH" else ("yellow" if freshness.freshness_level.value == "MEDIUM" else "red")
    drift_text = (
        f"• Возраст последнего образа: [bold]{freshness.age_days}[/bold] дней\n"
        f"• Изменившихся компонентов/KB: [bold]{freshness.drift.changed_components_count}[/bold]\n"
        f"• Новых программ: [bold]{freshness.drift.installed_apps_count}[/bold]\n"
        f"• Обновлено драйверов: [bold]{freshness.drift.updated_drivers_count}[/bold]\n\n"
        f"[bold]Актуальность:[/bold] [{fresh_style}]{freshness.freshness_label_ru}[/{fresh_style}]\n"
        f"[bold]Рекомендация:[/bold] {freshness.recommendation}"
    )
    console.print(
        Panel(
            drift_text,
            title=f"📊 Анализ актуальности образов (Health Score: {health.get('health_score')}/100)",
            border_style=fresh_style,
        )
    )


def run_interactive_tui() -> None:
    """Запуск интерактивного меню управления контрольными точками."""
    console = Console()
    coordinator = CheckpointCoordinator()

    while True:
        render_dashboard(coordinator, console)
        console.print("\n[bold yellow]Меню действий:[/bold yellow]")
        console.print("  [bold cyan]1[/bold cyan] - 🟢 Создать базовый эталонный образ (Baseline)")
        console.print("  [bold cyan]2[/bold cyan] - 🔴 Зафиксировать периодическую контрольную точку")
        console.print("  [bold cyan]3[/bold cyan] - 🟡 Создать точку перед обновлением (Pre-Update)")
        console.print("  [bold cyan]4[/bold cyan] - 🟠 Создать точку перед экспериментом (Pre-Experiment)")
        console.print("  [bold cyan]5[/bold cyan] - 📋 Просмотреть каталог сохраненных точек")
        console.print("  [bold cyan]6[/bold cyan] - 🔍 Инвентаризация WIM-образов на дисках")
        console.print("  [bold cyan]7[/bold cyan] - ⚙️ Управление средой WinRE")
        console.print("  [bold cyan]0[/bold cyan] - Выход")

        choice = Prompt.ask("\nВыберите действие", default="0")

        if choice == "0":
            console.print("[dim]Выход из менеджера контрольных точек.[/dim]")
            break
        elif choice == "1":
            title = Prompt.ask("Заголовок базового образа", default="Чистая настроенная Windows")
            desc = Prompt.ask("Описание", default="Драйверы, обновления, базовый софт")
            req = CheckpointCreateRequest(
                checkpoint_type=CheckpointType.BASELINE,
                title=title,
                description=desc,
                create_restore_point=True,
                create_wim_image=False,  # WIM через DISM требует длительного времени, по умолчанию SafeOps
            )
            res = coordinator.create_checkpoint(req)
            console.print(f"[bold green]{res.get('message')}[/bold green]")
            Prompt.ask("\nНажмите Enter для продолжения...")
        elif choice in ["2", "3", "4"]:
            c_type = CheckpointType.PERIODIC
            if choice == "3":
                c_type = CheckpointType.PRE_UPDATE
            elif choice == "4":
                c_type = CheckpointType.PRE_EXPERIMENT

            title = Prompt.ask("Заголовок контрольной точки", default="Контрольная точка системы")
            req = CheckpointCreateRequest(
                checkpoint_type=c_type,
                title=title,
                create_restore_point=True,
                create_wim_image=False,
            )
            res = coordinator.create_checkpoint(req)
            console.print(f"[bold green]{res.get('message')}[/bold green]")
            Prompt.ask("\nНажмите Enter для продолжения...")
        elif choice == "5":
            records = coordinator.load_catalog()
            c_table = Table(title="📋 Каталог контрольных точек системы", expand=True)
            c_table.add_column("ID", style="cyan")
            c_table.add_column("Дата", style="dim")
            c_table.add_column("Тип", style="bold")
            c_table.add_column("Название", style="white")

            for r in records:
                c_table.add_row(r.checkpoint_id, r.created_at, r.checkpoint_type.value, r.title)
            console.print(c_table)
            Prompt.ask("\nНажмите Enter для продолжения...")
        elif choice == "6":
            images = coordinator.image_manager.scan_recovery_images()
            i_table = Table(title="🔍 Обнаруженные WIM/ESD образы", expand=True)
            i_table.add_column("Путь", style="cyan")
            i_table.add_column("Размер (GB)", style="green")
            i_table.add_column("Дата", style="dim")
            i_table.add_column("Индексов", style="magenta")

            for img in images:
                i_table.add_row(img.image_path, str(img.file_size_gb), img.created_at, str(img.index_count))
            console.print(i_table)
            Prompt.ask("\nНажмите Enter для продолжения...")
        elif choice == "7":
            status = coordinator.winre_manager.get_status()
            console.print(Panel(str(status.to_dict()), title="WinRE Status"))
            Prompt.ask("\nНажмите Enter для продолжения...")


if __name__ == "__main__":
    run_interactive_tui()
