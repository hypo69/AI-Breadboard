"""Wrapper module for apps.windows.api.netw.

Перенос импортов в пространство `apps.windows.telemetry.api_bindings`.
Только переэкспортирует всё из оригинального модуля, чтобы обеспечить совместимость.
"""

from apps.windows.api.netw import *  # noqa: F403,F401

# Экспортируем все публичные имена, если оригинальный модуль определил __all__
try:
    from apps.windows.api.netw import __all__ as _orig_all
    __all__ = list(_orig_all)
except ImportError:
    __all__ = []
