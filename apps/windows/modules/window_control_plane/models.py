# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Window Management Models
# =============================================================================
# Description:
#   Модели данных, перечисления и схемы Pydantic для Windows Window Management Control Plane.
#   Описывает 295 параметров управления окнами, DWM, панелью задач, дисплеями и политиками.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.window_control_plane.models import (
#         SettingCategory, WindowSettingDefinition, SettingApplyRequest
#     )
#
# File: models.py
# Project: ai-breadboard
# Package: apps.windows.modules.window_control_plane
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 18:00:00
# =============================================================================

from __future__ import annotations
"""Модели данных и схемы Pydantic для реестра управления окнами и оболочкой Windows."""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class SettingCategory(str, Enum):
    """15 категорий настроек Windows Window Management Control Plane."""
    FOCUS_ACTIVATION = "focus_activation"
    ANIMATIONS_VISUAL_EFFECTS = "animations_visual_effects"
    WINDOW_GEOMETRY_METRICS = "window_geometry_metrics"
    WINDOW_ARRANGEMENT_SNAP = "window_arrangement_snap"
    ALT_TAB_TASK_SWITCHING = "alt_tab_task_switching"
    VIRTUAL_DESKTOPS = "virtual_desktops"
    DWM_WINDOW_COMPOSITION = "dwm_window_composition"
    TASKBAR_APP_SWITCHING = "taskbar_app_switching"
    MOUSE_WINDOW_BEHAVIOUR = "mouse_window_behaviour"
    KEYBOARD_FOCUS_NAVIGATION = "keyboard_focus_navigation"
    ACCESSIBILITY_PRESENTATION = "accessibility_presentation"
    DISPLAY_MULTI_MONITOR = "display_multi_monitor"
    DESKTOP_EXPLORER = "desktop_explorer"
    THEME_WINDOW_METRICS = "theme_window_metrics"
    SHELL_POLICY_CONTROLS = "shell_policy_controls"


class SettingScope(str, Enum):
    """Область действия настройки."""
    USER = "user"
    MACHINE = "machine"
    SESSION = "session"
    WINDOW = "window"


class SettingValueType(str, Enum):
    """Тип значения параметра."""
    BOOLEAN = "bool"
    INTEGER = "int"
    DURATION_MS = "duration_ms"
    STRING = "str"
    ENUM = "enum"
    COLOR_HEX = "color_hex"
    FONT = "font"
    RECT = "rect"
    ACTION = "action"


class BackendType(str, Enum):
    """Тип исполняющего бэкенда для чтения и записи."""
    SYSTEM_PARAMETERS_INFO = "SystemParametersInfoW"
    DWM_API = "DwmApi"
    DISPLAY_CONFIG = "DisplayConfigApi"
    WIN32_API = "Win32Api"
    REGISTRY = "Registry"
    POLICY_GPO = "PolicyGPO"
    POLICY_CSP = "PolicyCSP"
    SHELL_SETTINGS = "ShellSettings"
    POWERSHELL = "PowerShell"
    UNSUPPORTED = "Unsupported"


class SupportStatus(str, Enum):
    """Статус поддержки и надежности управления."""
    SAFE = "Safe"
    ADMIN = "Admin"
    COMPAT = "Compat"
    UNSUPPORTED = "Unsupported"


class DocStatus(str, Enum):
    """Статус документированности механизма."""
    DOCUMENTED_API = "documented_api"
    POLICY = "policy"
    REGISTRY_COMPAT = "registry_compat"
    UNSUPPORTED = "unsupported"


class RiskLevel(str, Enum):
    """Уровень риска применения настройки."""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BackendResolverSpec(BaseModel):
    """Спецификация разрешения параметра через Win32 API / Registry / Policy."""
    backend: BackendType = Field(..., description="Основной исполняющий бэкенд")
    api_getter: Optional[str] = Field(None, description="Имя Win32 SPI/DWM getter константы или функции")
    api_setter: Optional[str] = Field(None, description="Имя Win32 SPI/DWM setter константы или функции")
    registry_hive: Optional[str] = Field(None, description="Ветка реестра (HKCU, HKLM)")
    registry_path: Optional[str] = Field(None, description="Путь в реестре Windows")
    registry_value: Optional[str] = Field(None, description="Имя параметра реестра")
    registry_type: Optional[str] = Field(None, description="Тип ключа реестра (REG_DWORD, REG_SZ, REG_BINARY)")
    gpo_path: Optional[str] = Field(None, description="Путь Group Policy / CSP политики")
    gpo_name: Optional[str] = Field(None, description="Имя ключа политики")
    settings_uri: Optional[str] = Field(None, description="URI страница в Windows Settings (ms-settings:...)")
    powershell_cmd: Optional[str] = Field(None, description="PowerShell команда чтения/изменения")


class WindowSettingDefinition(BaseModel):
    """Машинное описание системной настройки Window Management Control Plane."""
    id: str = Field(..., description="Уникальный системный идентификатор (например: window.focus.foreground_lock_timeout)")
    index: int = Field(..., description="Порядковый номер в каталоге (1..295)")
    name: str = Field(..., description="Английское наименование настройки")
    name_ru: str = Field(..., description="Русское наименование настройки")
    category: SettingCategory = Field(..., description="Категория настройки (одна из 15)")
    subcategory: str = Field(..., description="Подкатегория настройки")
    scope: SettingScope = Field(default=SettingScope.USER, description="Область действия настройки")
    value_type: SettingValueType = Field(default=SettingValueType.BOOLEAN, description="Тип данных параметра")
    unit: Optional[str] = Field(None, description="Единица измерения (ms, px, count, etc.)")
    min_val: Optional[Union[int, float]] = Field(None, description="Минимальное допустимое значение")
    max_val: Optional[Union[int, float]] = Field(None, description="Максимальное допустимое значение")
    allowed_values: Optional[List[Any]] = Field(None, description="Список допустимых значений для перечислений")
    default_value: Optional[Any] = Field(None, description="Значение по умолчанию в Windows")
    read_spec: Optional[BackendResolverSpec] = Field(None, description="Спецификация чтения текущего значения")
    write_spec: Optional[BackendResolverSpec] = Field(None, description="Спецификация записи нового значения")
    support_status: SupportStatus = Field(default=SupportStatus.SAFE, description="Статус поддержки (Safe, Admin, Compat, Unsupported)")
    doc_status: DocStatus = Field(default=DocStatus.DOCUMENTED_API, description="Статус документированности")
    risk: RiskLevel = Field(default=RiskLevel.SAFE, description="Уровень риска применения")
    requires_elevation: bool = Field(default=False, description="Требует ли прав Администратора (UAC)")
    requires_restart: bool = Field(default=False, description="Требует ли перезапуска Explorer / Windows")
    requires_dwm_restart: bool = Field(default=False, description="Требует ли перезапуска DWM")
    windows_versions: List[str] = Field(default_factory=lambda: ["Windows 10", "Windows 11"], description="Поддерживаемые версии ОС")
    description: str = Field(..., description="Английское описание")
    description_ru: str = Field(..., description="Русское описание параметра и его влияния на систему")

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование модели в словарь."""
        return self.model_dump()


class SettingValueResponse(BaseModel):
    """Результат чтения текущего значения настройки."""
    setting_id: str
    name: str
    name_ru: str
    category: str
    value: Any
    raw_value: Optional[Any] = None
    value_type: str
    unit: Optional[str] = None
    is_live: bool = True
    backend_used: str
    error: Optional[str] = None


class SettingPreviewResponse(BaseModel):
    """Результат симуляции изменения настройки (Dry-Run)."""
    setting_id: str
    name_ru: str
    current_value: Any
    new_value: Any
    is_valid: bool
    validation_error: Optional[str] = None
    risk: str
    requires_elevation: bool
    requires_restart: bool
    will_create_restore_point: bool
    planned_backend: str
    safety_summary: str


class SettingApplyRequest(BaseModel):
    """Запрос на изменение настройки."""
    value: Any = Field(..., description="Новое устанавливаемое значение")
    force: bool = Field(False, description="Принудительное применение даже при предупреждениях")
    create_restore_point: Optional[bool] = Field(None, description="Создавать ли точку восстановления Windows")
    custom_comment: Optional[str] = Field(None, description="Пользовательский комментарий для журнала аудита")


class SettingApplyResponse(BaseModel):
    """Результат применения изменения настройки."""
    change_id: str
    setting_id: str
    name_ru: str
    old_value: Any
    new_value: Any
    status: str
    success: bool
    requires_restart: bool
    restore_point_id: Optional[str] = None
    message: str
    applied_at: str
    error: Optional[str] = None


class BatchSettingItem(BaseModel):
    """Элемент пакета изменений."""
    setting_id: str
    value: Any


class BatchApplyRequest(BaseModel):
    """Запрос пакетного применения настроек."""
    settings: List[BatchSettingItem]
    create_restore_point: bool = True
    comment: Optional[str] = "Пакетная настройка Windows Window Management"


class BatchApplyResponse(BaseModel):
    """Результат пакетного применения."""
    batch_id: str
    total_requested: int
    successful_count: int
    failed_count: int
    results: List[SettingApplyResponse]
    restore_point_created: bool


class SettingRollbackRequest(BaseModel):
    """Запрос отката изменения."""
    change_id: str


class SettingRollbackResponse(BaseModel):
    """Результат отката изменения."""
    change_id: str
    setting_id: str
    rolled_back: bool
    restored_value: Any
    message: str


class ControlPlaneSummaryResponse(BaseModel):
    """Сводный отчет по каталогу Window Management Control Plane."""
    total_settings: int
    categories_count: int
    by_category: Dict[str, int]
    by_support_status: Dict[str, int]
    by_doc_status: Dict[str, int]
    by_risk: Dict[str, int]
    by_backend: Dict[str, int]
    system_platform: str
    windows_build: Optional[str] = None
