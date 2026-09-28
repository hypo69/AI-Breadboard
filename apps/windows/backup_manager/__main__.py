"""CLI запуск TUI дашборда Windows Backup Manager."""
import sys
from apps.windows.backup_manager.tui import BackupManagerTUI

def main() -> None:
    tui = BackupManagerTUI()
    tui.render_dashboard()
if __name__ == '__main__':
    main()