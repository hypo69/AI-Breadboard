# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Security_Acl - Tui
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.security_acl.tui import SecurityAclTUI
#
#     service = SecurityAclTUI()
#
# File: tui.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.security_acl
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from apps.windows.sdk.modules.security_acl.core.manager import SecurityAclManager


class SecurityAclTUI:
    """Консольный интерфейс отображения безопасности и шифрования."""

    def __init__(self, manager: SecurityAclManager | None = None) -> None:
        self.manager = manager or SecurityAclManager()
        self.console = Console()

    def render_dashboard(self) -> None:
        """Отображение сводного дашборда безопасности."""
        report = self.manager.generate_report()

        bitlocker_text = "\n".join([
            f"[bold cyan]Том {b.drive_letter}:[/bold cyan] [{ 'green' if 'on' in b.protection_status.lower() else 'red'}]{b.protection_status}[/{ 'green' if 'on' in b.protection_status.lower() else 'red'}] "
            f"({b.conversion_status}, {b.encryption_method}, Протекторы: {', '.join(b.key_protector_types)})"
            for b in report.bitlocker_volumes
        ])

        panel = Panel(
            f"[bold white]BitLocker Drive Encryption:[/bold white]\n{bitlocker_text}\n\n"
            f"[bold white]EFS Support:[/bold white] {'Включен' if report.efs_enabled else 'Отключен'}\n"
            f"[bold white]UAC Level:[/bold white] {report.uac_level}",
            title='Windows Security, ACL & BitLocker Center',
            style='blue'
        )

        self.console.print(Panel('[bold white]AI-Breadboard: Windows Security & Access Control[/bold white]', style='blue'))
        self.console.print(panel)


__all__ = ['SecurityAclTUI']
