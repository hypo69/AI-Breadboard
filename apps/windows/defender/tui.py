# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Defender Rich TUI Dashboard
# =============================================================================
# Description:
#   Консольный терминальный интерфейс (TUI) на базе библиотеки Rich
#   для интерактивного аудита Microsoft Defender, правил ASR, Controlled Folder Access,
#   опасных исключений, подозрительных процессов и AI-рекомендаций.
#
# File: tui.py
# Project: ai-breadboard
# Package: apps.windows.defender
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Терминальный интерфейс (Rich TUI) для Microsoft Defender Security Center."""

from __future__ import annotations

from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from apps.windows.defender.core.ai_diagnostician import AIDiagnostician
from apps.windows.defender.core.models import ExclusionRiskLevel, ProtectionState


class DefenderTUI:
    """Консольный визуализатор для Defender Security Center."""

    def __init__(self, diagnostician: Optional[AIDiagnostician] = None) -> None:
        """Инициализация консольного интерфейса.

        Args:
            diagnostician: Экземпляр AIDiagnostician.
        """
        self.console = Console()
        self.diag = diagnostician or AIDiagnostician()

    def render_dashboard(self) -> None:
        """Рендеринг основного дашборда безопасности в терминал."""
        rep = self.diag.generate_diagnostic_report()
        st = rep.status

        # 1. Заголовочная панель
        score = rep.security_score
        score_color = "green" if score >= 80 else ("yellow" if score >= 50 else "red")

        hdr = Text()
        hdr.append("🛡️  MICROSOFT DEFENDER ANTIVIRUS & SECURITY CENTER\n", style="bold cyan")
        hdr.append(f"Индекс защищенности системы: ", style="bold")
        hdr.append(f"{score}/100\n", style=f"bold {score_color}")
        hdr.append(f"Версия баз: {st.antivirus_signature_version or 'N/A'} | Движок: {st.engine_version or 'N/A'}\n", style="dim")
        hdr.append(f"Резюме: {rep.status_summary}", style="italic")

        self.console.print(Panel(hdr, border_style=score_color, title="[bold]Endpoint Security Telemetry[/bold]"))

        # 2. Таблица компонентов защиты
        comp_table = Table(title="Эшелоны и компоненты защиты Defender", header_style="bold magenta")
        comp_table.add_column("Компонент", style="cyan")
        comp_table.add_column("Статус", justify="center")
        comp_table.add_column("Описание")

        def _fmt_bool(val: bool) -> Text:
            return Text("✓ ВКЛЮЧЕНО", style="bold green") if val else Text("✗ ОТКЛЮЧЕНО", style="bold red")

        comp_table.add_row("Real-time Protection", _fmt_bool(st.real_time_protection_enabled), "Постоянная защита файловой системы в реальном времени")
        comp_table.add_row("Cloud-delivered Protection", _fmt_bool(st.cloud_protection_enabled), f"Облачная репутация и ML (Уровень: {st.cloud_block_level})")
        comp_table.add_row("Behavior Monitoring", _fmt_bool(st.behavior_monitor_enabled), "Поведенческий анализ активности и цепочек процессов")
        comp_table.add_row("IOAV File Protection", _fmt_bool(st.ioav_protection_enabled), "Проверка загружаемых из сети файлов и вложений")
        comp_table.add_row("Script Scanning (AMSI)", _fmt_bool(st.script_scanning_enabled), "Анализ сценариев PowerShell, VBScript, JScript через AMSI")
        comp_table.add_row("Tamper Protection", _fmt_bool(st.tamper_protection_enabled), "Защита настроек антивируса от модификации вредоносным ПО")
        comp_table.add_row("PUA Protection", _fmt_bool(st.pua_protection_enabled), "Блокировка потенциально нежелательных программ и рекламного ПО")
        comp_table.add_row("Controlled Folder Access", _fmt_bool(st.controlled_folder_access_enabled), "Защита пользовательских папок от Ransomware (вымогателей)")
        comp_table.add_row("Network Protection", _fmt_bool(st.network_protection_enabled), "Блокировка обращений к опасным и вредоносным веб-ресурсам")

        self.console.print(comp_table)

        # 3. Службы и фоновые процессы
        if st.services:
            svc_table = Table(title="Системные службы и процессы Defender", header_style="bold blue")
            svc_table.add_column("Процесс / Служба", style="cyan")
            svc_table.add_column("Название")
            svc_table.add_column("Статус", justify="center")
            svc_table.add_column("PID", justify="right")
            svc_table.add_column("Память", justify="right")

            for s in st.services:
                s_state = Text("АКТИВЕН", style="bold green") if s.running else Text("НЕ ЗАПУЩЕН", style="dim")
                pid_str = str(s.pid) if s.pid else "-"
                mem_str = f"{s.memory_mb} MB" if s.running else "-"
                svc_table.add_row(s.name, s.display_name, s_state, pid_str, mem_str)

            self.console.print(svc_table)

        # 4. Аудит исключений (если есть)
        exc_rep = rep.exclusions_audit
        if exc_rep.total_exclusions > 0:
            exc_table = Table(title=f"Аудит исключений ({exc_rep.total_exclusions} всего, {exc_rep.suspicious_count} подозрительных)", header_style="bold yellow")
            exc_table.add_column("Тип", style="cyan", width=12)
            exc_table.add_column("Значение исключения")
            exc_table.add_column("Риск", justify="center", width=12)
            exc_table.add_column("Обоснование риска")

            all_exc = exc_rep.path_exclusions + exc_rep.extension_exclusions + exc_rep.process_exclusions
            for itm in all_exc:
                risk_style = "green"
                if itm.risk_level in (ExclusionRiskLevel.CRITICAL, ExclusionRiskLevel.HIGH):
                    risk_style = "bold red"
                elif itm.risk_level == ExclusionRiskLevel.MEDIUM:
                    risk_style = "yellow"

                exc_table.add_row(itm.type.upper(), itm.value, Text(itm.risk_level.value.upper(), style=risk_style), itm.risk_reason)

            self.console.print(exc_table)

        # 5. Подозрительные процессы
        if rep.suspicious_process_chains:
            proc_table = Table(title="⚠️ Обнаруженные подозрительные цепочки процессов (Fileless индикаторы)", header_style="bold red")
            proc_table.add_column("Родитель", style="yellow")
            proc_table.add_column("Дочерний процесс", style="bold red")
            proc_table.add_column("PID", justify="right")
            proc_table.add_column("Причина срабатывания")

            for chain in rep.suspicious_process_chains:
                proc_table.add_row(
                    f"{chain.parent_process} (PID: {chain.parent_pid})",
                    chain.child_process,
                    str(chain.child_pid),
                    chain.reason,
                )
            self.console.print(proc_table)

        # 6. Рекомендации
        if rep.recommendations:
            rec_text = Text()
            for i, r in enumerate(rep.recommendations, 1):
                rec_text.append(f"  {i}. {r}\n", style="bold yellow")
            self.console.print(Panel(rec_text, title="[bold yellow]🎯 Рекомендации AI по усилению безопасности[/bold yellow]", border_style="yellow"))
