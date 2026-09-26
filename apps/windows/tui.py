# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows AI Diagnostic Center TUI
# =============================================================================
# Description:
#   Интерактивный терминальный интерфейс (TUI) на библиотеке Rich для
#   просмотра статуса здоровья Windows, результатов аудита и действий SafeOps.
#
# Examples:
#   >>> from apps.windows.tui import run_tui
#   >>> run_tui()
#
# File: tui.py
# Project: ai-breadboard
# Package: apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Интерактивный TUI интерфейс для Windows AI Diagnostic Center."""

from __future__ import annotations

import sys
from typing import Optional

try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.tree import Tree
    RICH_AVAILABLE = True
except ImportError:
    Console = None  # type: ignore
    Layout = None  # type: ignore
    Live = None  # type: ignore
    Panel = None  # type: ignore
    Table = None  # type: ignore
    Text = None  # type: ignore
    Tree = None  # type: ignore
    RICH_AVAILABLE = False

from apps.windows.core.models import FullAuditReport, RiskLevel
from apps.windows.core.root_cause_engine import RootCauseEngine


def render_dashboard(report: FullAuditReport, console: Console) -> None:
    """Отрисовка главного дашборда здоровья системы."""
    console.clear()
    
    score = report.health_score.score
    color = "green" if score >= 85 else "yellow" if score >= 60 else "red"

    # Заголовок
    header_text = Text(" AI WINDOWS DIAGNOSTIC & ADMINISTRATION CENTER ", style="bold white on blue")
    console.print(Panel(header_text, style="blue", expand=True))

    # Сводка индекса здоровья
    health_panel = Panel(
        f"[bold {color}]Индекс здоровья: {score}/100 ({report.health_score.status_label})[/]\n"
        f"Критические проблемы: [red]{report.health_score.critical_count}[/] | "
        f"Предупреждения: [yellow]{report.health_score.medium_count}[/] | "
        f"Безопасные действия: [green]{report.health_score.low_count}[/]",
        title="[bold]System Health Score[/bold]",
        border_style=color,
    )
    console.print(health_panel)

    # Таблица доменов
    table = Table(title="Результаты аудита 15 системных доменов", expand=True)
    table.add_column("Домен", style="cyan", ratio=2)
    table.add_column("Статус", justify="center", ratio=1)
    table.add_column("Находки / Рекомендации", ratio=5)

    for d_name, d_res in report.domains.items():
        status_style = "green" if d_res.status == "ok" else "red" if d_res.status == "critical" else "yellow"
        findings_text = ""
        if d_res.findings:
            findings_text = ", ".join([f.title for f in d_res.findings[:2]])
            if len(d_res.findings) > 2:
                findings_text += f" (ещё {len(d_res.findings) - 2}...)"
        else:
            findings_text = "[dim]Аномалий не обнаружено[/dim]"

        table.add_row(
            d_res.title_ru,
            f"[{status_style}]{d_res.status.upper()}[/{status_style}]",
            findings_text,
        )

    console.print(table)

    # Футер управления
    footer = Panel(
        "[bold cyan]Горячие клавиши:[/] [R] Обновить | [F] Полный аудит | [S] Безопасность | [P] Производительность | [Q] Выход",
        style="dim",
    )
    console.print(footer)


def run_tui() -> None:
    """Запуск интерактивного TUI цикла."""
    if Console is None:
        print("Библиотека rich не установлена. Запустите: pip install rich")
        sys.exit(1)

    console = Console()
    engine = RootCauseEngine()
    current_mode = "quick"

    report = engine.run_full_audit(mode=current_mode)
    render_dashboard(report, console)


async def run_log_dashboard(
    interval: float = 2.0,
    channel: str = "System",
    level: str = "",
    search: str = "",
    limit: int = 15,
    hours: int = 24,
) -> None:
    """Запуск интерактивного дашборда системных журналов в терминале (System Log Viewer)."""
    import asyncio
    import datetime
    from apps.windows.core.modules.log_discovery_engine import LogDiscoveryEngine

    discovery = LogDiscoveryEngine()
    level_display = level.capitalize() if level else "Все"
    title_header = f"Windows Logs Monitor (Канал/Файл: {channel} | Уровень: {level_display})"

    if Console is None:
        print(f"[System Log Center] {title_header}. Запуск базового цикла...")
        while True:
            events = discovery.read_source_events(channel, limit=limit, level=level, search=search, hours=hours)
            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Получено событий: {len(events)}")
            await asyncio.sleep(interval)

    from rich.live import Live

    console = Console()
    with Live(console=console, refresh_per_second=1) as live:
        while True:
            events = discovery.read_source_events(channel, limit=limit, level=level, search=search, hours=hours)
            table = Table(title=f"📜 Windows System Log Center — {channel} ({level_display})", expand=True)
            table.add_column("Время", style="cyan", width=19, no_wrap=True)
            table.add_column("Уровень", style="magenta", width=12)
            table.add_column("ID", style="green", width=8)
            table.add_column("Источник", style="yellow", width=22)
            table.add_column("Сообщение", style="white")

            for ev in events:
                lvl = str(ev.get("level") or "Info")
                lvl_style = "red" if "Crit" in lvl or "Err" in lvl else ("yellow" if "Warn" in lvl else "green")
                table.add_row(
                    str(ev.get("timestamp") or ""),
                    f"[{lvl_style}]{lvl}[/{lvl_style}]",
                    str(ev.get("event_id") or "0"),
                    str(ev.get("provider") or "-")[:20],
                    str(ev.get("message") or "-").replace("\r", " ").replace("\n", " ")[:80],
                )

            live.update(Panel(table, title=title_header, border_style="red" if level and "err" in level.lower() else "blue"))
            await asyncio.sleep(interval)


async def run_hardware_monitor_dashboard(interval: float = 1.0) -> None:
    """Запуск интерактивного TUI дашборда мониторинга аппаратных ресурсов в реальном времени."""
    import asyncio
    import datetime
    from apps.windows.hardware.hardware_monitor import HardwareMonitor

    monitor = HardwareMonitor()

    if Console is None:
        print("[Hardware Monitor] Запуск базового монитора оборудования (Rich не обнаружен)...")
        while True:
            snap = monitor.get_snapshot(include_smart=False)
            print(
                f"[{datetime.datetime.now().strftime('%H:%M:%S')}] "
                f"CPU: {snap.cpu.utilization_pct}% | "
                f"RAM: {snap.memory.used_gb}/{snap.memory.total_gb} GB ({snap.memory.utilization_pct}%) | "
                f"GPU: {len(snap.gpus)} шт | Диски: {len(snap.storage.partitions)} шт"
            )
            await asyncio.sleep(interval)

    from rich.live import Live
    from rich.columns import Columns

    console = Console()
    with Live(console=console, refresh_per_second=int(1 / max(0.2, interval))) as live:
        while True:
            snap = monitor.get_snapshot(include_smart=False)

            # 1. CPU & Memory Таблица
            cpu_ram_table = Table(title="💻 CPU & Память", expand=True)
            cpu_ram_table.add_column("Компонент", style="cyan")
            cpu_ram_table.add_column("Значение", style="green")
            cpu_ram_table.add_column("Нагрузка", style="yellow")

            cpu_color = "red" if snap.cpu.utilization_pct > 85 else "green"
            freq_str = f"{snap.cpu.frequency_current_mhz} MHz" if snap.cpu.frequency_current_mhz else "N/A"
            cpu_ram_table.add_row(
                "CPU (Всего)",
                f"{snap.cpu.physical_cores}C / {snap.cpu.logical_cores}T @ {freq_str}",
                f"[{cpu_color}]{snap.cpu.utilization_pct}%[/{cpu_color}]",
            )

            ram_color = "red" if snap.memory.utilization_pct > 85 else "green"
            cpu_ram_table.add_row(
                "RAM (ОЗУ)",
                f"{snap.memory.used_gb} GB / {snap.memory.total_gb} GB",
                f"[{ram_color}]{snap.memory.utilization_pct}%[/{ram_color}]",
            )

            swap_color = "red" if snap.memory.swap_utilization_pct > 80 else "cyan"
            cpu_ram_table.add_row(
                "Swap (Подкачка)",
                f"{snap.memory.swap_used_gb} GB / {snap.memory.swap_total_gb} GB",
                f"[{swap_color}]{snap.memory.swap_utilization_pct}%[/{swap_color}]",
            )

            # 2. GPU Таблица
            gpu_table = Table(title="🎮 Видеокарты (GPU)", expand=True)
            gpu_table.add_column("Имя", style="magenta")
            gpu_table.add_column("Температура", justify="center")
            gpu_table.add_column("GPU / VRAM", justify="center")
            gpu_table.add_column("Питание / Fan", justify="center")

            if snap.gpus:
                for g in snap.gpus:
                    temp_str = f"{g.temperature_gpu_c}°C" if g.temperature_gpu_c else "N/A"
                    t_style = "red" if g.temperature_gpu_c and g.temperature_gpu_c > 80 else "green"
                    vram_str = f"{round(g.memory_used_mb / 1024, 1)} / {round(g.memory_total_mb / 1024, 1)} GB" if g.memory_used_mb and g.memory_total_mb else "-"
                    gpu_util = f"{g.utilization_gpu_pct}%" if g.utilization_gpu_pct is not None else "-"
                    power_str = f"{g.power_draw_w} W" if g.power_draw_w else "-"
                    fan_str = f"{g.fan_speed_pct}%" if g.fan_speed_pct is not None else "-"
                    gpu_table.add_row(
                        f"{g.name[:24]}",
                        f"[{t_style}]{temp_str}[/{t_style}]",
                        f"{gpu_util} | {vram_str}",
                        f"{power_str} | {fan_str}",
                    )
            else:
                gpu_table.add_row("Дискретные GPU не обнаружены (WMI/Intel)", "-", "-", "-")

            # 3. Накопители Таблица
            disk_table = Table(title="💽 Диски и Накопители", expand=True)
            disk_table.add_column("Том", style="cyan")
            disk_table.add_column("ФС / Размер", style="white")
            disk_table.add_column("Занято / Свободно", style="yellow")
            disk_table.add_column("Загрузка", justify="center")

            for p in snap.storage.partitions:
                p_style = "red" if p.utilization_pct > 90 else "green"
                disk_table.add_row(
                    f"{p.mountpoint} ({p.device})",
                    f"{p.fstype} | {p.total_gb} GB",
                    f"{p.used_gb} GB / {p.free_gb} GB",
                    f"[{p_style}]{p.utilization_pct}%[/{p_style}]",
                )

            # Скорости ввода-вывода диска и сети
            io_table = Table(title="⚡ Сеть и Дисковый I/O", expand=True)
            io_table.add_column("Метрика", style="cyan")
            io_table.add_column("Скорость", style="green")

            if snap.storage.io_rates:
                io_table.add_row(
                    "Диск Чтение / Запись",
                    f"{round(snap.storage.io_rates.read_bytes_sec / (1024*1024), 2)} MB/s | {round(snap.storage.io_rates.write_bytes_sec / (1024*1024), 2)} MB/s",
                )
            io_table.add_row(
                "Сеть Прием / Отдача",
                f"{round(snap.network.bytes_recv_sec / 1024, 1)} KB/s | {round(snap.network.bytes_sent_sec / 1024, 1)} KB/s",
            )
            io_table.add_row("Активные соединения", f"{snap.network.active_connections_count} сокетов")
            if snap.battery.has_battery:
                ac_status = "Сеть подключена" if snap.battery.power_plugged else "Работа от батареи"
                io_table.add_row("Батарея", f"{snap.battery.percent}% ({ac_status})")

            # Сенсоры
            sensor_table = Table(title="🌡️ Датчики и Вентиляторы", expand=True)
            sensor_table.add_column("Датчик", style="cyan")
            sensor_table.add_column("Тип", style="magenta")
            sensor_table.add_column("Показание", style="green")

            if snap.sensors:
                for s in snap.sensors[:6]:
                    sensor_table.add_row(s.name[:25], s.category, f"{s.value} {s.unit}")
            else:
                sensor_table.add_row("Датчики WMI/LHM в спящем режиме", "-", "-")

            # Главный контейнер
            status_text = snap.status_summary.get("status", "HEALTHY")
            status_color = "green" if status_text == "HEALTHY" else ("yellow" if status_text == "WARNING" else "red")
            main_header = (
                f"🎛️ Windows Hardware Monitor | Статус: [{status_color}]{status_text}[/{status_color}] | "
                f"Время: {snap.timestamp[11:19]}"
            )

            col1 = Columns([cpu_ram_table, gpu_table], expand=True)
            col2 = Columns([disk_table, io_table], expand=True)
            main_panel = Panel(
                Text.from_markup(
                    f"{main_header}\n\n"
                ) + Columns([col1, col2, sensor_table], expand=True),
                title="[bold blue]AI BREADBOARD HARDWARE CENTER[/bold blue]",
                border_style=status_color,
            )

            live.update(main_panel)
            await asyncio.sleep(interval)


class SystemInspectorState:
    """Сессия состояния интерактивного системного инспектора."""

    def __init__(self, sort_by: str = "cpu", process_limit: int = 15) -> None:
        """Инициализация состояния сессии."""
        from apps.windows.telemetry import SystemCollector, SystemDiagnosticEngine
        self.collector = SystemCollector()
        self.diagnostician = SystemDiagnosticEngine()
        self.sort_by: str = sort_by
        self.process_limit: int = process_limit
        self.latest_snapshot = None
        self.latest_report = None
        self.hardware_tree_nodes = []

    async def refresh(self) -> None:
        """Сбор свежего моментального снимка телеметрии и эвристический анализ."""
        from apps.windows.telemetry import SystemDiagnosticReport
        self.latest_snapshot = await self.collector.get_snapshot(process_limit=self.process_limit)
        if not self.hardware_tree_nodes:
            self.hardware_tree_nodes = await self.collector.get_hardware_tree_async()

        score, anomalies, recommendations = self.diagnostician.evaluate_heuristics(self.latest_snapshot)
        self.latest_report = SystemDiagnosticReport(
            health_score=score,
            summary=f"System Health: {score}/100. Telemetry stream nominal.",
            anomalies=anomalies,
            recommendations=recommendations,
            ai_model_used="Heuristic Monitor",
        )


def _render_inspector_process_table(snapshot: Any, sort_by: str) -> Any:
    """Отрисовка таблицы активных процессов."""
    table = Table(
        title=f"Live Process Stream (Сортировка: {sort_by.upper()})",
        expand=True,
        header_style="bold cyan",
        border_style="bright_black",
    )
    table.add_column("PID", style="cyan", width=8, justify="right")
    table.add_column("Имя процесса", style="bold white", min_width=18)
    table.add_column("Статус", style="dim", width=10)
    table.add_column("CPU %", style="yellow", justify="right", width=8)
    table.add_column("RAM (MB)", style="green", justify="right", width=10)
    table.add_column("RAM %", style="dim green", justify="right", width=8)
    table.add_column("Потоки", style="magenta", justify="right", width=8)
    table.add_column("Дескрипторы", style="blue", justify="right", width=8)
    table.add_column("Пользователь", style="dim", width=12)

    for proc in snapshot.top_processes:
        cpu_style = "bold red" if proc.cpu_percent > 50 else ("yellow" if proc.cpu_percent > 20 else "white")
        table.add_row(
            str(proc.pid),
            proc.name,
            proc.status,
            f"[{cpu_style}]{proc.cpu_percent:.1f}%[/{cpu_style}]",
            f"{proc.memory_mb:.1f}",
            f"{proc.memory_percent:.1f}%",
            str(proc.num_threads),
            str(getattr(proc, "num_handles", 0) or 0),
            proc.username or "SYSTEM",
        )
    return table


def _render_inspector_hardware_tree(nodes: list, sensors: list) -> Any:
    """Отрисовка дерева оборудования в стиле AIDA64."""
    tree = Tree("[bold cyan]🖥️ Оборудование и датчики хоста[/bold cyan]")

    for node in nodes:
        branch = tree.add(f"[bold yellow]{node.category}[/bold yellow]: {node.name}")
        for k, v in node.properties.items():
            branch.add(f"[dim]{k}:[/dim] [white]{v}[/white]")

    if sensors:
        sensor_branch = tree.add("[bold red]🌡️ Активные датчики[/bold red]")
        for s in sensors:
            color = "red" if s.value >= 80 else ("yellow" if s.value >= 65 else "green")
            sensor_branch.add(f"{s.name}: [{color}]{s.value} {s.unit}[/{color}]")

    return tree


def render_inspector_ui(state: SystemInspectorState) -> Any:
    """Отрисовка интерфейса системного инспектора."""
    if not RICH_AVAILABLE or not state.latest_snapshot:
        return None

    snap = state.latest_snapshot
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=4),
        Layout(name="main", ratio=1),
        Layout(name="footer", size=3),
    )

    layout["main"].split_row(
        Layout(name="processes", ratio=3),
        Layout(name="hardware_side", ratio=2),
    )

    layout["hardware_side"].split_column(
        Layout(name="hardware", ratio=3),
        Layout(name="ai_copilot", ratio=2),
    )

    cpu_bar = f"CPU: {snap.cpu.total_percent}% ({snap.cpu.physical_cores}C/{snap.cpu.logical_cores}T)"
    ram_bar = f"RAM: {snap.memory.used_gb}/{snap.memory.total_gb} GB ({snap.memory.percent}%)"
    uptime_h = round(snap.uptime_seconds / 3600, 1)

    gpu_str = ", ".join([f"{g.name} ({g.memory_total_gb}GB)" for g in snap.gpus]) or "Integrated"
    header_text = Text.assemble(
        ("AI-BREADBOARD SYSTEM & HARDWARE INSPECTOR\n", "bold cyan"),
        (f"Host: {snap.hostname} | OS: {snap.os_name} | Uptime: {uptime_h}h | ", "dim"),
        (f"{cpu_bar} | {ram_bar} | GPU: {gpu_str}", "bold green"),
    )
    layout["header"].update(Panel(header_text, border_style="cyan"))

    proc_table = _render_inspector_process_table(snap, state.sort_by)
    layout["processes"].update(Panel(proc_table, border_style="blue"))

    hw_tree = _render_inspector_hardware_tree(state.hardware_tree_nodes, snap.sensors)
    layout["hardware"].update(Panel(hw_tree, title="AIDA64 Hardware & Sensor Tree", border_style="yellow"))

    rep = state.latest_report
    copilot_content = Text()
    if rep:
        health_color = "green" if rep.health_score >= 80 else ("yellow" if rep.health_score >= 60 else "red")
        copilot_content.append(f"System Health: {rep.health_score}/100\n", style=f"bold {health_color}")
        copilot_content.append(f"AI Engine: {rep.ai_model_used}\n\n", style="dim")
        if rep.anomalies:
            copilot_content.append("⚠️ Обнаруженные аномалии:\n", style="bold yellow")
            for a in rep.anomalies:
                copilot_content.append(f" • [{a.severity.upper()}] {a.title}: {a.description}\n", style="white")
        else:
            copilot_content.append("✅ Все аппаратные подсистемы работают в норме.\n", style="green")

        if rep.recommendations:
            copilot_content.append("\n💡 Рекомендации:\n", style="bold cyan")
            for r in rep.recommendations:
                copilot_content.append(f" • {r}\n", style="dim")

    layout["ai_copilot"].update(Panel(copilot_content, title="🤖 AI Performance Copilot", border_style="magenta"))

    footer_text = Text(" [Q] Выход  |  [S] Сортировка CPU/RAM  |  [D] AI Диагностика  |  Интервал: 1.0s", style="dim white")
    layout["footer"].update(Panel(footer_text, border_style="bright_black"))

    return layout


async def run_system_inspector(interval: float = 1.0, sort_by: str = "cpu", max_iterations: Optional[int] = None) -> None:
    """Запуск интерактивного системного инспектора процессов и оборудования."""
    import asyncio
    if not RICH_AVAILABLE or Console is None:
        print("Для запуска интерактивного TUI интерфейса требуется библиотека rich.")
        return

    console = Console()
    state = SystemInspectorState(sort_by=sort_by)
    await state.refresh()

    iterations = 0
    with Live(render_inspector_ui(state), console=console, refresh_per_second=4, screen=True) as live:
        try:
            while True:
                await state.refresh()
                live.update(render_inspector_ui(state))
                iterations += 1
                if max_iterations and iterations >= max_iterations:
                    break
                await asyncio.sleep(interval)
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass


__all__ = [
    "SystemInspectorState",
    "render_dashboard",
    "run_hardware_monitor_dashboard",
    "run_log_dashboard",
    "run_system_inspector",
    "run_tui",
]


if __name__ == "__main__":
    run_tui()


