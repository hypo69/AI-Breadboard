# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Startup Core - Models
# =============================================================================
# Description:
#   Модели данных для приложения Windows Startup & Autorun Auditor.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.startup.core.models import StartupLocationType
#
#     service = StartupLocationType()
#
# File: models.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.startup.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 13:55:00
# =============================================================================

from __future__ import annotations
"""Модели данных для приложения Windows Startup & Autorun Auditor."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

class StartupLocationType(str, Enum):
    """Типы расположений автозагрузки в Windows."""
    REGISTRY_RUN = 'registry_run'
    REGISTRY_RUNONCE = 'registry_runonce'
    REGISTRY_POLICIES = 'registry_policies'
    STARTUP_FOLDER_USER = 'startup_folder_user'
    STARTUP_FOLDER_COMMON = 'startup_folder_common'
    SCHEDULED_TASK = 'scheduled_task'
    WINDOWS_SERVICE = 'windows_service'
    WINLOGON = 'winlogon'
    IFEO = 'ifeo'
    SHELL_EXTENSION = 'shell_extension'
    BOOT_EXECUTE = 'boot_execute'
    OTHER = 'other'

class RiskLevel(str, Enum):
    """Уровни риска для элементов автозагрузки."""
    CLEAN = 'clean'
    NOTICE = 'notice'
    WARNING = 'warning'
    SUSPICIOUS = 'suspicious'
    CRITICAL = 'critical'

class ItemCategory(str, Enum):
    """Категории программ автозагрузки."""
    SYSTEM_CORE = 'Системный компонент'
    HARDWARE_DRIVER = 'Драйвер / Утилита оборудования'
    KNOWN_APP = 'Известное приложение'
    UTILITY = 'Системная утилита'
    BACKGROUND_UPDATER = 'Фоновое обновление'
    SUSPICIOUS_SCRIPT = 'Подозрительный скрипт'
    BROKEN_ENTRY = 'Битая ссылка (файл не найден)'
    UNKNOWN = 'Неизвестно'

class StartupEntry(BaseModel):
    """Модель записи автозапуска Windows."""
    id: str = Field(description='Уникальный идентификатор записи')
    name: str = Field(description='Отображаемое имя записи')
    location_type: StartupLocationType = Field(default=StartupLocationType.OTHER, description='Тип расположения')
    location_path: str = Field(default='', description='Точный путь реестра или директории')
    command: str = Field(default='', description='Полная строка команды автозапуска')
    executable_path: str = Field(default='', description='Извлеченный абсолютный путь к исполняемому файлу')
    arguments: str = Field(default='', description='Аргументы командной строки')
    publisher: str = Field(default='Неизвестен', description='Издатель или разработчик файла')
    is_signed: bool = Field(default=False, description='Наличие действительной цифровой подписи')
    is_enabled: bool = Field(default=True, description='Статус активности (включен/отключен)')
    file_exists: bool = Field(default=True, description='Существует ли файл на диске')
    file_size_kb: float = Field(default=0.0, description='Размер файла в килобайтах')
    created_date: Optional[str] = Field(default=None, description='Дата создания или изменения файла')
    category: ItemCategory = Field(default=ItemCategory.UNKNOWN, description='Категория элемента')
    risk_level: RiskLevel = Field(default=RiskLevel.CLEAN, description='Уровень риска элемента')
    risk_reasons: List[str] = Field(default_factory=list, description='Причины присвоения уровня риска')
    boot_impact: str = Field(default='Низкое', description='Влияние на время загрузки системы (Низкое/Среднее/Высокое)')
    recommendation: str = Field(default='Оставить как есть', description='Рекомендация по оптимизации')

class LocationInfo(BaseModel):
    """Информация о сканируемой точке автозапуска."""
    location_type: StartupLocationType
    title_ru: str
    description_ru: str
    target_path: str
    items_count: int = 0
    is_writable: bool = False

class AuditSummary(BaseModel):
    """Сводка результатов аудита автозапуска."""
    total_entries: int = 0
    active_entries: int = 0
    disabled_entries: int = 0
    broken_entries: int = 0
    clean_count: int = 0
    notice_count: int = 0
    warning_count: int = 0
    suspicious_count: int = 0
    critical_count: int = 0
    health_score: int = Field(default=100, description='Индекс чистоты и безопасности автозапуска (0-100)')
    categories_breakdown: Dict[str, int] = Field(default_factory=dict)
    locations_breakdown: Dict[str, int] = Field(default_factory=dict)

class AuditReport(BaseModel):
    """Полный отчет аудита точек автозапуска."""
    timestamp: str
    hostname: str
    os_name: str
    scan_duration_ms: float
    summary: AuditSummary
    entries: List[StartupEntry]
    security_alerts: List[StartupEntry] = Field(default_factory=list)
    broken_items: List[StartupEntry] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

class ToggleRequest(BaseModel):
    """Запрос на включение / отключение элемента автозагрузки."""
    entry_id: str
    enable: bool

class ToggleResponse(BaseModel):
    """Ответ на операцию включения / отключения."""
    success: bool
    entry_id: str
    new_state: bool
    message: str

class StartupExplainRequest(BaseModel):
    """Запрос на AI-объяснение и аудит элемента автозапуска."""
    entry_id: Optional[str] = Field(default=None, description='ID элемента автозапуска')
    name: str = Field(default='', description='Имя программы')
    publisher: Optional[str] = Field(default='', description='Издатель/разработчик')
    executable_path: Optional[str] = Field(default='', description='Путь к исполняемому файлу')
    command: Optional[str] = Field(default='', description='Командная строка запуска')
    arguments: Optional[str] = Field(default='', description='Аргументы командной строки')
    location_type: Optional[str] = Field(default='', description='Точка автозапуска')
    location_path: Optional[str] = Field(default='', description='Путь в реестре или файловой системе')
    risk_level: Optional[str] = Field(default='clean', description='Текущий уровень риска')
    is_enabled: Optional[bool] = Field(default=True, description='Включен ли автозапуск')
    file_exists: Optional[bool] = Field(default=True, description='Существует ли файл на диске')
    is_signed: Optional[bool] = Field(default=False, description='Подписан ли файл цифровой подписью')
    boot_impact: Optional[str] = Field(default='Низкое', description='Оценка влияния на запуск')
    model: Optional[str] = Field(default=None, description='Опциональное имя конкретной модели')
    provider: Optional[str] = Field(default=None, description='Опциональный провайдер LLM')

class StartupExplainResponse(BaseModel):
    """Структурированный ответ AI-анализа программы автозапуска."""
    summary: str = Field(description='Краткое описание программы и её назначения')
    developer: str = Field(default='Неизвестен', description='Разработчик / принадлежность ПО')
    category: str = Field(default='Приложение', description='Категория ПО')
    security_verdict: str = Field(description='Оценка безопасности и легитимности')
    boot_impact_analysis: str = Field(description='Анализ влияния на скорость загрузки и ресурсы')
    startup_recommendation: str = Field(description='Рекомендация по автозагрузке (оставить/отключить/удалить)')
    action_steps: List[str] = Field(default_factory=list, description='Рекомендуемые действия для пользователя')

class StartupChangeItem(BaseModel):
    """Зафиксированное изменение в автозагрузке между снимками телеметрии."""
    change_type: str = Field(..., description='Тип изменения: added, removed, state_changed, path_changed, risk_changed, impact_changed')
    entry_id: str = Field(..., description='Идентификатор элемента автозапуска')
    name: str = Field(..., description='Имя программы / записи автозапуска')
    description: str = Field(..., description='Подробное описание изменения на русском языке')
    previous_value: Optional[Dict[str, Any]] = Field(default=None, description='Предыдущее состояние элемента')
    current_value: Optional[Dict[str, Any]] = Field(default=None, description='Новое состояние элемента')
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description='Временная метка обнаружения изменения')

class StartupArchiveEntry(BaseModel):
    """Запись архивного снимка автозапуска в телеметрии."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    archive_id: str = Field(..., description='Уникальный идентификатор архивного снимка')
    timestamp: str = Field(..., description='Время создания архивного снимка')
    total_entries: int = Field(default=0, description='Общее количество элементов автозапуска')
    health_score: int = Field(default=100, description='Индекс чистоты и безопасности')
    changes_count: int = Field(default=0, description='Количество зафиксированных изменений по сравнению с прошлым снимком')
    changes: List[StartupChangeItem] = Field(default_factory=list, description='Список зафиксированных изменений')
    report: Any = Field(..., description='Полный отчет аудита автозапуска')

class StartupRefreshResponse(BaseModel):
    """Ответ на асинхронный перезапуск сбора автозапуска и сохранение в телеметрию."""
    success: bool = Field(default=True, description='Успешность операции')
    archive_id: str = Field(default='', description='Идентификатор сохраненного снимка')
    timestamp: str = Field(default='', description='Время создания снимка')
    changes_count: int = Field(default=0, description='Количество обнаруженных изменений')
    changes: List[StartupChangeItem] = Field(default_factory=list, description='Список обнаруженных изменений')
    report: AuditReport = Field(..., description='Свежий отчет аудита автозапуска')
    message: str = Field(default='Снимок телеметрии успешно обновлен', description='Статусное сообщение')