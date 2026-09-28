"""Копия оригинального модуля psapi из apps/windows/api.

Обеспечивает FFI-обёртки для psapi.dll.
"""

from apps.windows.api.psapi import *  # noqa: F403,F401

__all__ = [name for name in dir() if not name.startswith('_')]
