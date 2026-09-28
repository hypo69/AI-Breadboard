"""Обертка для wevtapi API, переэкспорт из старого пакета.

Обеспечивает совместимость после миграции API‑обёрток в слой Telemetry.
"""

from apps.windows.api.wevtapi import WevtAPI, ChannelMetadata, CHANNEL_DESCRIPTIONS  # noqa: F403,F401

# Явно указываем экспортируемые имена, чтобы импорт из wrapper‑модуля успешно находил WevtAPI
__all__ = ['WevtAPI', 'ChannelMetadata', 'CHANNEL_DESCRIPTIONS']

__all__ = [name for name in dir() if not name.startswith('_')]

