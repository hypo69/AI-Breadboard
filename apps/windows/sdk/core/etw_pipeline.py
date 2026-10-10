# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Core - ETW Pipeline
# =============================================================================
# Description:
#   Конвейер сбора и инспекции системной телеметрии ETW и Performance Counters
#   (Sensors -> ETW / Performance Counters -> AITelemetry -> SQLite).
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.core.etw_pipeline import EtwTelemetryPipeline
#
#     pipeline = EtwTelemetryPipeline.get_instance()
#     sessions = await pipeline.get_active_etw_sessions()
#
# File: etw_pipeline.py
# Project: ai-breadboard
# Package: apps.windows.sdk.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 15:10:00
# =============================================================================

from __future__ import annotations
"""Конвейер сбора и инспекции системной телеметрии ETW и Performance Counters."""

import asyncio
import platform
import subprocess
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from logger import logger


class EtwSessionInfo(BaseModel):
    """Сведения об активной сессии трассировки ETW в режиме реального времени."""
    name: str
    type: str = 'Event Trace Session'
    status: str = 'Running'
    raw_output: str = ''


class DataCollectorSetInfo(BaseModel):
    """Сведения о наборе сборщиков данных (Data Collector Set)."""
    name: str
    type: str = 'Data Collector Set'
    status: str = 'Configured'


class EtwPipelineStatus(BaseModel):
    """Статус сквозного конвейера телеметрии."""
    pipeline_architecture: str = 'Sensors -> ETW / Performance Counters -> AITelemetry -> SQLite'
    is_windows: bool = True
    active_etw_sessions_count: int = 0
    collector_sets_count: int = 0
    active_sessions: List[EtwSessionInfo] = Field(default_factory=list)
    collector_sets: List[DataCollectorSetInfo] = Field(default_factory=list)


class EtwTelemetryPipeline:
    """Управление и диагностика конвейера ETW / Performance Counters."""

    _instance: Optional[EtwTelemetryPipeline] = None

    def __init__(self) -> None:
        self._is_win: bool = platform.system().lower() == 'windows'

    @classmethod
    def get_instance(cls) -> EtwTelemetryPipeline:
        """Получение синглтона конвейера ETW."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def get_active_etw_sessions(self) -> List[EtwSessionInfo]:
        """Получение списка активных сессий трассировки ETW через logman query -ets."""
        if not self._is_win:
            return [
                EtwSessionInfo(name='EventLog-System (Simulated)', status='Running'),
                EtwSessionInfo(name='Circular Kernel Context Logger (Simulated)', status='Running')
            ]

        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    ['logman.exe', 'query', '-ets'],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
            )
            output = result.stdout or ''
            sessions: List[EtwSessionInfo] = []
            lines = output.splitlines()
            start_parsing = False
            for line in lines:
                line_str = line.strip()
                if '--------------------------------' in line_str:
                    start_parsing = True
                    continue
                if start_parsing and line_str:
                    if 'Команда выполнена успешно' in line_str or 'The command completed successfully' in line_str:
                        continue
                    parts = line_str.split(maxsplit=1)
                    if parts:
                        sessions.append(EtwSessionInfo(name=parts[0], raw_output=line_str))
            return sessions
        except Exception as e:
            logger.warning(f'[EtwPipeline] Ошибка выполнения logman query -ets: {e}')
            return []

    async def get_collector_sets(self) -> List[DataCollectorSetInfo]:
        """Получение списка зарегистрированных Data Collector Sets через logman query."""
        if not self._is_win:
            return [DataCollectorSetInfo(name='System Diagnostics (Simulated)')]

        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    ['logman.exe', 'query'],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
            )
            output = result.stdout or ''
            collectors: List[DataCollectorSetInfo] = []
            lines = output.splitlines()
            start_parsing = False
            for line in lines:
                line_str = line.strip()
                if '--------------------------------' in line_str:
                    start_parsing = True
                    continue
                if start_parsing and line_str:
                    if 'Команда выполнена успешно' in line_str or 'The command completed successfully' in line_str:
                        continue
                    parts = line_str.split(maxsplit=1)
                    if parts:
                        collectors.append(DataCollectorSetInfo(name=parts[0]))
            return collectors
        except Exception as e:
            logger.warning(f'[EtwPipeline] Ошибка выполнения logman query: {e}')
            return []

    async def get_pipeline_status(self) -> EtwPipelineStatus:
        """Сводный статус конвейера телеметрии ETW."""
        sessions, collectors = await asyncio.gather(
            self.get_active_etw_sessions(),
            self.get_collector_sets(),
            return_exceptions=True
        )

        sess_list = sessions if isinstance(sessions, list) else []
        coll_list = collectors if isinstance(collectors, list) else []

        return EtwPipelineStatus(
            is_windows=self._is_win,
            active_etw_sessions_count=len(sess_list),
            collector_sets_count=len(coll_list),
            active_sessions=sess_list,
            collector_sets=coll_list
        )


__all__ = [
    'EtwSessionInfo',
    'DataCollectorSetInfo',
    'EtwPipelineStatus',
    'EtwTelemetryPipeline',
]
