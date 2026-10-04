# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Network -   Init  
# =============================================================================
# Description:
#   Network Analyzer Terminal standalone application.
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.modules.network
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 04:55:00
# =============================================================================

"""Network Analyzer Terminal standalone application."""

_LAZY_EXPORTS = {
    'init_router': ('apps.windows.modules.network.router', 'init_router'),
    'NetworkTerminalState': ('apps.windows.modules.network.tui', 'NetworkTerminalState'),
    'render_ui': ('apps.windows.modules.network.tui', 'render_ui'),
    'run_network_dashboard': ('apps.windows.modules.network.tui', 'run_network_dashboard'),
    'WindowsNetworkUsageCollector': ('apps.windows.modules.network.network_usage', 'WindowsNetworkUsageCollector'),
    'WindowsLanScanner': ('apps.windows.modules.network.lan_scanner', 'WindowsLanScanner'),
    'LanDevice': ('apps.windows.modules.network.lan_scanner', 'LanDevice'),
}

def __getattr__(name: str):
    """Ленивая динамическая загрузка модулей и символов пакета."""
    if name in _LAZY_EXPORTS:
        module_path, attr_name = _LAZY_EXPORTS[name]
        module = __import__(module_path, fromlist=[attr_name])
        attr = getattr(module, attr_name)
        globals()[name] = attr
        return attr
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    'NetworkTerminalState',
    'render_ui',
    'run_network_dashboard',
    'init_router',
    'WindowsNetworkUsageCollector',
    'WindowsLanScanner',
    'LanDevice',
]