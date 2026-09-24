# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Backup, Libraries & File History Manager Entrypoint
# =============================================================================
# Description:
#   Точка входа запуска приложения из консоли:
#   python -m apps.windows.backup_manager
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.windows.backup_manager
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""CLI запуск TUI дашборда Windows Backup Manager."""

import sys
from apps.windows.backup_manager.tui import BackupManagerTUI


def main() -> None:
    tui = BackupManagerTUI()
    tui.render_dashboard()


if __name__ == "__main__":
    main()