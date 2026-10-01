# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Backup_Manager -   Main  
# =============================================================================
# Description:
#   CLI запуск TUI дашборда Windows Backup Manager.
#
# Usage Examples:
#   CLI:
#     python -m apps.windows.modules.backup_manager.__main__
#   Python API:
#     from apps.windows.modules.backup_manager.__main__ import main
#
#     res = main()
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.windows.modules.backup_manager
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""CLI запуск TUI дашборда Windows Backup Manager."""

import sys
from apps.windows.modules.backup_manager.tui import BackupManagerTUI

def main() -> None:
    tui = BackupManagerTUI()
    tui.render_dashboard()
if __name__ == '__main__':
    main()