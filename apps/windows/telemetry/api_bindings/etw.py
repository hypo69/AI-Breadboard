"""Эмуляция модуля etw: переэкспорт из старого пакета.

Этот файл обеспечивает совместимость после миграции API-обёрток в слой Telemetry.
"""

from apps.windows.api.etw import *  # noqa: F403,F401

__all__ = [name for name in dir() if not name.startswith('_')]
