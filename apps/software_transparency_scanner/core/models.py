# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI Software Transparency Scanner Data Models
# =============================================================================
# Description:
#   Pydantic-модели данных для приложения AI Software Transparency Scanner:
#   программы, конфигурационные файлы, хранилища данных, сетевые соединения
#   и результаты AI-исследования через Gemini.
#
# File: models.py
# Project: ai-breadboard
# Package: apps.software_transparency_scanner.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модели данных для инвентаризатора и сканера прозрачности программного обеспечения."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EvidenceStatus(str, Enum):
    """Статус достоверности сведений."""
    LOCAL_OBSERVED = "observed"           # 🟢 Подтверждено локально
    DOCS_CONFIRMED = "docs_confirmed"     # 🔵 Подтверждено документацией
    AI_INFERENCE = "ai_inference"         # 🟡 Предположение Gemini
    UNKNOWN = "unknown"                   # ⚪ Неизвестно


class StorageCategory(str, Enum):
    """Категория хранилища данных программы."""
    CONFIG = "config"                     # Настройки пользователя
    CACHE = "cache"                       # Кэш и временные файлы
    LOGS = "logs"                         # Журналы работы
    DATABASE = "database"                 # База данных (sqlite, db)
    BINARIES = "binaries"                 # Исполняемые файлы и библиотеки
    REGISTRY = "registry"                 # Записи в реестре
    SECRETS = "secrets"                   # Файлы с ключами / токенами
    UNKNOWN = "unknown"                   # Прочие данные


class ConfigFile(BaseModel):
    """Описание обнаруженного конфигурационного файла."""
    path: str = Field(..., description="Абсолютный путь к файлу")
    display_path: str = Field(..., description="Путь с макросами окружения, например %APPDATA%\\...")
    filename: str = Field(..., description="Имя файла")
    format: str = Field(default="unknown", description="Формат файла: json, ini, yaml, xml, etc.")
    size_bytes: int = Field(default=0, description="Размер в байтах")
    last_modified: Optional[str] = Field(default=None, description="Дата последнего изменения ISO")
    purpose: str = Field(default="Настройки программы", description="Предполагаемое или подтвержденное назначение")
    is_sanitized: bool = Field(default=True, description="Были ли вырезаны/маскированы секреты")
    sample_content: Optional[str] = Field(default=None, description="Очищенный фрагмент конфигурации")
    status: EvidenceStatus = Field(default=EvidenceStatus.LOCAL_OBSERVED, description="Статус достоверности")


class StorageDirectory(BaseModel):
    """Описание обнаруженного каталога данных программы."""
    path: str = Field(..., description="Абсолютный путь к каталогу")
    display_path: str = Field(..., description="Путь с макросами окружения")
    category: StorageCategory = Field(default=StorageCategory.UNKNOWN, description="Тип хранимых данных")
    description: str = Field(default="", description="Описание назначения каталога")
    file_count: int = Field(default=0, description="Количество файлов в каталоге")
    total_size_bytes: int = Field(default=0, description="Общий размер файлов")
    status: EvidenceStatus = Field(default=EvidenceStatus.LOCAL_OBSERVED, description="Статус достоверности")


class NetworkEndpoint(BaseModel):
    """Описание сетевого соединения или обнаруженного домена."""
    domain_or_ip: str = Field(..., description="Доменное имя или IP-адрес")
    port: Optional[int] = Field(default=None, description="Сетевой порт")
    protocol: str = Field(default="HTTPS", description="Сетевой протокол")
    source: str = Field(default="observed", description="Источник детекции: active_socket, config, binary_scan")
    purpose: str = Field(default="Требуется исследование домена", description="Назначение соединения")
    documentation_source: Optional[str] = Field(default=None, description="Ссылка на документацию или источник")
    status: EvidenceStatus = Field(default=EvidenceStatus.LOCAL_OBSERVED, description="Статус достоверности")


class GeminiAppResearch(BaseModel):
    """Результаты аналитического исследования программы через Gemini."""
    app_name: str = Field(..., description="Название исследованной программы")
    summary: str = Field(default="", description="Назначение и функционал программы")
    config_purpose_explanation: str = Field(default="", description="Объяснение назначения конфигурационных файлов")
    data_storage_explanation: str = Field(default="", description="Описание того, какие данные сохраняются локально")
    network_activity_explanation: str = Field(default="", description="Назначение сетевых доменов и серверов")
    confirmed_facts: List[str] = Field(default_factory=list, description="Факты, подтвержденные официальной документацией")
    inferred_facts: List[str] = Field(default_factory=list, description="Логические предположения модели")
    unknown_aspects: List[str] = Field(default_factory=list, description="Неизвестные или требующие отдельной проверки сведения")
    confidence_level: str = Field(default="Высокий", description="Уровень уверенности: Высокий / Средний / Предположение")


class SoftwareItem(BaseModel):
    """Сводная карточка установленного программного обеспечения."""
    id: str = Field(..., description="Уникальный идентификатор записи (slug)")
    name: str = Field(..., description="Название программы")
    version: str = Field(default="Не указана", description="Версия ПО")
    publisher: str = Field(default="Неизвестен", description="Разработчик / Издатель")
    install_location: Optional[str] = Field(default=None, description="Путь установки (Program Files и т.д.)")
    executable_path: Optional[str] = Field(default=None, description="Главный исполняемый файл")
    architecture: str = Field(default="x64", description="Разрядность x64, x86 или ARM64")
    install_date: Optional[str] = Field(default=None, description="Дата установки")
    registry_key: Optional[str] = Field(default=None, description="Ветка реестра Windows")
    
    # Детальные компоненты прозрачности
    config_files: List[ConfigFile] = Field(default_factory=list, description="Обнаруженные конфигурационные файлы")
    data_directories: List[StorageDirectory] = Field(default_factory=list, description="Каталоги хранения данных")
    network_endpoints: List[NetworkEndpoint] = Field(default_factory=list, description="Сетевые взаимодействия и домены")
    windows_services: List[str] = Field(default_factory=list, description="Связанные службы Windows")
    
    # Исследование AI
    ai_research: Optional[GeminiAppResearch] = Field(default=None, description="Результаты исследования Gemini")


class ScanSummary(BaseModel):
    """Сводная статистика сканирования системы."""
    total_apps: int = Field(default=0, description="Всего обнаружено установленных программ")
    total_configs_found: int = Field(default=0, description="Всего найдено файлов конфигурации")
    total_network_domains: int = Field(default=0, description="Всего уникальных сетевых доменов/узлов")
    total_storage_bytes: int = Field(default=0, description="Суммарный объем отслеживаемых данных")
    scan_duration_sec: float = Field(default=0.0, description="Время выполнения сканирования в секундах")
    last_scan_time: Optional[str] = Field(default=None, description="Время последнего сканирования ISO")


class FullScanReport(BaseModel):
    """Полный отчет инвентаризации и аудита прозрачности ПО."""
    summary: ScanSummary = Field(..., description="Сводка сканирования")
    apps: List[SoftwareItem] = Field(default_factory=list, description="Список детальных карточек программ")


class ResearchRequest(BaseModel):
    """Запрос на AI-исследование конкретной программы."""
    app_id: str = Field(..., description="Идентификатор программы")
    force_refresh: bool = Field(default=False, description="Принудительное обновление через Gemini")
