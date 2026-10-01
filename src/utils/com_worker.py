# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard UTILS - Com Worker Module
# =============================================================================
# Description:
#   Dedicated executor for COM/WMI operations.
#
# Usage Examples:
#   Python API:
#     from src.utils.com_worker import ComWorker
#
#     service = ComWorker()
#
# File: com_worker.py
# Project: ai-breadboard
# Package: src.utils
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

from __future__ import annotations
"""Dedicated executor for COM/WMI operations."""

import asyncio
import threading
import pythoncom
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Any, TypeVar, ParamSpec
T = TypeVar('T')
P = ParamSpec('P')

class ComWorker:
    """Worker for executing COM/WMI operations in a dedicated thread."""

    def __init__(self) -> None:
        """Initialize worker with a single dedicated thread."""
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='ComWorker')
        self._executor.submit(self._init_com)

    @staticmethod
    def _init_com() -> None:
        """Initialize COM for this thread."""
        pythoncom.CoInitialize()

    async def run(self, func: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
        """Execute a function in the dedicated COM-initialized thread."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, lambda: func(*args, **kwargs))
com_worker = ComWorker()