"""Backward compatibility wrapper for apps.trading_terminal."""
from apps.trading_terminal import TradingDeskEngine, render_ui, run_dashboard
from apps.trading_terminal.__main__ import main
__all__ = ['TradingDeskEngine', 'render_ui', 'run_dashboard', 'main']
if __name__ == '__main__':
    main()