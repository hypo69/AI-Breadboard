# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Taskbar - Models
# =============================================================================
# Description:
#   Модели данных для контроллера панели задач (TaskbarController), окон и Command Registry.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.taskbar.core.models import TaskbarSettings, WindowItem
#
# File: models.py
# Project: ai-breadboard
# Package: apps.windows.modules.taskbar.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 17:35:00
# =============================================================================

from __future__ import annotations
"""Модели данных для подсистемы управления панелью задач и окнами Windows."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WindowRect(BaseModel):
    """Геометрические координаты и размеры окна."""
    left: int = Field(0, description="Координата X левого верхнего угла")
    top: int = Field(0, description="Координата Y левого верхнего угла")
    right: int = Field(0, description="Координата X правого нижнего угла")
    bottom: int = Field(0, description="Координата Y правого нижнего угла")
    width: int = Field(0, description="Ширина окна в пикселях")
    height: int = Field(0, description="Высота окна в пикселях")


class WindowItem(BaseModel):
    """Информация об окне рабочего стола Windows."""
    hwnd: int = Field(..., description="Дескриптор окна (HWND)")
    title: str = Field("", description="Заголовок окна")
    process_id: int = Field(0, description="Идентификатор процесса (PID)")
    process_name: str = Field("", description="Имя исполняемого файла процесса")
    class_name: str = Field("", description="Имя класса окна Win32")
    is_visible: bool = Field(True, description="Флаг видимости окна")
    is_minimized: bool = Field(False, description="Флаг свернутого состояния (IsIconic)")
    is_maximized: bool = Field(False, description="Флаг развернутого состояния (IsZoomed)")
    is_foreground: bool = Field(False, description="Флаг активного окна на переднем плане")
    rect: WindowRect = Field(default_factory=WindowRect, description="Геометрия окна")


class WindowMoveRequest(BaseModel):
    """Запрос на перемещение и изменение размера окна."""
    x: int = Field(..., description="Новая координата X")
    y: int = Field(..., description="Новая координата Y")
    width: int = Field(..., description="Новая ширина окна")
    height: int = Field(..., description="Новая высота окна")


class WindowBatchActionRequest(BaseModel):
    """Запрос на выполнение пакетных действий над окнами."""
    action: str = Field(
        ...,
        description="Тип действия: minimize_all, restore_all, minimize_all_except, close_by_process"
    )
    target_hwnd: Optional[int] = Field(None, description="Целевой HWND (для minimize_all_except)")
    process_name: Optional[str] = Field(None, description="Имя процесса (для close_by_process)")


class TaskbarSettings(BaseModel):
    """Параметры и настройки панели задач Windows 10/11."""
    alignment: int = Field(1, description="Выравнивание значков: 0 - по левому краю, 1 - по центру (Win11)")
    search_mode: int = Field(1, description="Режим поиска: 0 - скрыт, 1 - только значок, 2 - поле поиска, 3 - кнопка поиска")
    widgets_visible: bool = Field(True, description="Отображение виджетов на панели задач")
    task_view_visible: bool = Field(True, description="Отображение кнопки Просмотра задач (Task View)")
    copilot_visible: bool = Field(False, description="Отображение кнопки Copilot на панели задач")
    auto_hide: bool = Field(False, description="Автоматическое скрытие панели задач")
    badges_enabled: bool = Field(True, description="Показ бейджей уведомлений на кнопках панели задач")
    combine_buttons: int = Field(0, description="Группировка кнопок: 0 - всегда группировать, 1 - при заполнении, 2 - никогда")
    small_icons: bool = Field(False, description="Использование мелких значков панели задач (Win10)")
    location: str = Field("bottom", description="Положение панели: bottom, top, left, right")


class TaskbarSettingsUpdate(BaseModel):
    """Запрос на частичное обновление параметров панели задач."""
    alignment: Optional[int] = Field(None, description="Выравнивание значков (0 - слева, 1 - по центру)")
    search_mode: Optional[int] = Field(None, description="Режим поиска (0 - скрыт, 1 - иконка, 2 - поле, 3 - кнопка)")
    widgets_visible: Optional[bool] = Field(None, description="Показывать виджеты")
    task_view_visible: Optional[bool] = Field(None, description="Показывать Task View")
    copilot_visible: Optional[bool] = Field(None, description="Показывать Copilot")
    auto_hide: Optional[bool] = Field(None, description="Автоскрытие панели задач")
    badges_enabled: Optional[bool] = Field(None, description="Показ бейджей")
    combine_buttons: Optional[int] = Field(None, description="Группировка кнопок (0, 1, 2)")
    restart_explorer: bool = Field(False, description="Перезапустить Explorer для немедленного применения")


class AppLaunchRequest(BaseModel):
    """Запрос на запуск приложения."""
    app_path: str = Field(..., description="Путь к исполняемому файлу или системная команда")
    arguments: Optional[str] = Field(None, description="Аргументы командной строки")
    working_dir: Optional[str] = Field(None, description="Рабочий каталог")
    admin: bool = Field(False, description="Запуск с повышенными привилегиями (UAC)")


class AppPinRequest(BaseModel):
    """Запрос на закрепление приложения на панели задач."""
    target_path: str = Field(..., description="Полный путь к исполняемому файлу (.exe) или ярлыку (.lnk)")


class PinnedAppItem(BaseModel):
    """Информация о закрепленном приложении панели задач."""
    name: str = Field(..., description="Название приложения")
    target_path: str = Field("", description="Путь к целевому исполняемому файлу")
    link_path: str = Field("", description="Путь к ярлыку закрепления")


class TaskbarProgressRequest(BaseModel):
    """Запрос на установку индикатора выполнения ITaskbarList3."""
    hwnd: int = Field(..., description="Дескриптор целевого окна")
    state: str = Field("normal", description="Режим: no_progress, indeterminate, normal, error, paused")
    completed: int = Field(0, description="Завершенный объем работы")
    total: int = Field(100, description="Общий объем работы")


class TaskbarOverlayRequest(BaseModel):
    """Запрос на установку значка бейджа/оверлея на кнопке окна."""
    hwnd: int = Field(..., description="Дескриптор целевого окна")
    icon_path: Optional[str] = Field(None, description="Путь к файлу .ico (опционально)")
    description: str = Field("", description="Текстовое описание бейджа")


class CommandExecutionRequest(BaseModel):
    """Универсальный запрос выполнения команды через Command Registry."""
    command: str = Field(..., description="Идентификатор команды (например, WINDOW.MINIMIZE, TASKBAR.SET_ALIGNMENT)")
    params: Dict[str, Any] = Field(default_factory=dict, description="Параметры команды (hwnd, value, x, y, app_path и т.д.)")
    confirmed_by_user: bool = Field(False, description="Флаг подтверждения для опасных или Restricted операций")


class CommandExecutionResponse(BaseModel):
    """Ответ универсального механизма выполнения команд."""
    status: str = Field(..., description="Статус выполнения: SUCCESS, DRY_RUN, REJECTED, ERROR")
    command_id: str = Field(..., description="Идентификатор команды")
    details: Dict[str, Any] = Field(default_factory=dict, description="Детали и возвращенные данные")
    message: str = Field("", description="Сообщение о статусе")


class TaskbarSummaryReport(BaseModel):
    """Сводный отчет о состоянии панели задач и открытых окон."""
    os_version: str = Field(..., description="Версия операционной системы")
    is_win11: bool = Field(True, description="Флаг операционной системы Windows 11")
    taskbar_rect: WindowRect = Field(default_factory=WindowRect, description="Габариты и позиция панели задач")
    settings: TaskbarSettings = Field(default_factory=TaskbarSettings, description="Текущие настройки панели задач")
    windows_count: int = Field(0, description="Общее число открытых окон верхнего уровня")
    visible_windows_count: int = Field(0, description="Число видимых окон с заголовками")
    foreground_window: Optional[WindowItem] = Field(None, description="Текущее активное окно")
    pinned_apps_count: int = Field(0, description="Количество закрепленных на панели приложений")
