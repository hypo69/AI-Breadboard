# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Process_Manager Core - Models
# =============================================================================
# Description:
#   Модели данных для процессов, групп приложений (Apps), фоновых служб (Background)
#   и системных процессов Windows (Windows processes).
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.process_manager.core.models import ProcessGroupItem, CategorizedProcessReport
#
#     group = ProcessGroupItem(name="chrome.exe", friendly_name="Google Chrome", instance_count=25)
#
# File: models.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.process_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 02:06:00
# =============================================================================

from __future__ import annotations
"""Модели данных для процессов и категоризированных групп Windows."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ProcessItem(BaseModel):
    """Информация о запущенном процессе."""
    pid: int
    name: str
    username: Optional[str] = None
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    num_threads: int = 1
    create_time: str = ''
    exe_path: Optional[str] = None
    command_line: Optional[str] = None
    has_window: bool = False
    window_title: Optional[str] = None


class ProcessGroupItem(BaseModel):
    """Группа связанных процессов/приложений (например, Google Chrome (25))."""
    category: str = Field(default='background', description='Категория: app, background, windows')
    name: str = Field(..., description='Имя исполняемого файла (например, chrome.exe)')
    friendly_name: str = Field(..., description='Отображаемое имя (например, Google Chrome)')
    icon: Optional[str] = Field(default=None, description='Иконка или CSS класс')
    instance_count: int = Field(default=1, description='Количество экземпляров/процессов в группе')
    total_cpu_percent: float = Field(default=0.0, description='Суммарная нагрузка на CPU (%)')
    total_memory_mb: float = Field(default=0.0, description='Суммарное использование памяти в МБ')
    total_threads: int = Field(default=1, description='Суммарное количество потоков')
    main_pid: int = Field(default=0, description='PID главного или оконного процесса')
    has_visible_window: bool = Field(default=False, description='Флаг наличия открытого видимого окна')
    window_titles: List[str] = Field(default_factory=list, description='Заголовки окон приложения')
    subprocesses: List[ProcessItem] = Field(default_factory=list, description='Список подпроцессов в группе')


class CategorizedProcessReport(BaseModel):
    """Сводный отчет о процессах хоста, разделенный на Apps, Background и Windows."""
    total_processes: int = 0
    apps_count: int = 0
    background_count: int = 0
    windows_count: int = 0
    total_memory_used_mb: float = 0.0
    apps: List[ProcessGroupItem] = Field(default_factory=list, description='Интерактивные приложения с окнами')
    background_processes: List[ProcessGroupItem] = Field(default_factory=list, description='Фоновые службы и процессы')
    windows_processes: List[ProcessGroupItem] = Field(default_factory=list, description='Системные процессы ядра Windows')
    timestamp: str = ''


class ProcessReport(BaseModel):
    """Сводный отчет о процессах хоста."""
    total_processes: int = 0
    total_threads: int = 0
    total_memory_used_mb: float = 0.0
    apps_count: int = 0
    background_count: int = 0
    windows_count: int = 0
    top_cpu_processes: List[ProcessItem] = Field(default_factory=list)
    top_memory_processes: List[ProcessItem] = Field(default_factory=list)
    processes: List[ProcessItem] = Field(default_factory=list)
    apps: List[ProcessGroupItem] = Field(default_factory=list)
    background_processes: List[ProcessGroupItem] = Field(default_factory=list)
    windows_processes: List[ProcessGroupItem] = Field(default_factory=list)
    timestamp: str = ''


class ProcessKillRequest(BaseModel):
    """Запрос на завершение процесса."""
    pid: int
    kill_tree: bool = False
    dry_run: bool = True
    confirmed_by_user: bool = False


__all__ = [
    'ProcessItem',
    'ProcessGroupItem',
    'CategorizedProcessReport',
    'ProcessReport',
    'ProcessKillRequest',
]
