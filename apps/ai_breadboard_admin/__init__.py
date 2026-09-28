"""Пакет микроприложения администратора AI Breadboard."""
from .router import init_router, router
from .src import AdminConfigManager, InstructionsManager, SourcesManager, UserAdminService
from .tui import run_admin_tui
__all__ = ['init_router', 'router', 'AdminConfigManager', 'InstructionsManager', 'SourcesManager', 'UserAdminService', 'run_admin_tui']