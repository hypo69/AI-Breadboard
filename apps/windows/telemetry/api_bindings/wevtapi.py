"""Обертка для wevtapi API, переэкспорт из старого пакета.

Обеспечивает совместимость после миграции API‑обёрток в слой Telemetry.
"""

from apps.windows.api.wevtapi import *  # noqa: F403,F401

__all__ = [name for name in dir() if not name.startswith('_')]
