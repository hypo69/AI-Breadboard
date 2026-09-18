# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Backup, Libraries & File History Data Models
# =============================================================================
# Description:
#   Типизированные модели данных для представления библиотек Windows (.library-ms),
#   конфигурации службы File History (fhsvc), теневых копий VSS и аудита резервных копий.
#
# Examples:
#   >>> from apps.windows_backup_manager.core.models import WindowsLibrary
#   >>> lib = WindowsLibrary(name="Dev", path="...", folders=[])
#
# File: models.py
# Project: ai-breadboard
# Package: apps.windows_backup_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модели данных для приложения Windows Backup, Libraries & File History Manager."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ServiceState(str, Enum):
    """Состояние системной службы Windows."""
    RUNNING = "running"
    STOPPED = "stopped"
    PAUSED = "paused"
    START_PENDING = "start_pending"
    STOP_PENDING = "stop_pending"
    NOT_FOUND = "not_found"
    UNKNOWN = "unknown"


class LibraryFolder(BaseModel):
    """Описание физической папки, включенной в библиотеку Windows."""
    path: str = Field(description="Абсолютный путь к целевой папке на диске")
    exists: bool = Field(default=True, description="Существует ли путь физически на диске")
    is_default_save: bool = Field(default=False, description="Является ли папкой сохранения по умолчанию")
    drive_letter: Optional[str] = Field(default=None, description="Буква тома/диска")
    free_space_gb: Optional[float] = Field(default=None, description="Свободное место на диске (в ГБ)")


class WindowsLibrary(BaseModel):
    """Модель библиотеки Windows Shell (.library-ms)."""
    name: str = Field(description="Имя библиотеки (например, Documents, repos)")
    file_path: str = Field(description="Путь к XML-файлу .library-ms")
    owner_sid: Optional[str] = Field(default=None, description="SID владельца библиотеки")
    is_pinned: bool = Field(default=True, description="Закреплена ли библиотека в панели навигации")
    folder_count: int = Field(default=0, description="Количество включенных папок")
    folders: List[LibraryFolder] = Field(default_factory=list, description="Список папок библиотеки")
    all_folders_exist: bool = Field(default=True, description="Все ли папки физически доступны")


class CreateLibraryRequest(BaseModel):
    """Запрос на создание новой библиотеки или обновление существующей."""
    name: str = Field(description="Имя создаваемой библиотеки")
    folders: List[str] = Field(description="Список путей к папкам, которые войдут в библиотеку")
    is_pinned: bool = Field(default=True, description="Закрепить библиотеку в проводнике")


class AddFolderToLibraryRequest(BaseModel):
    """Запрос на добавление папки в существующую библиотеку."""
    folder_path: str = Field(description="Абсолютный путь к добавляемой папке")
    is_default_save: bool = Field(default=False, description="Сделать ли папкой сохранения по умолчанию")


class FileHistoryConfigInfo(BaseModel):
    """Сведения о конфигурации Истории Файлов Windows."""
    is_configured: bool = Field(description="Настроена ли История Файлов для текущего пользователя")
    config_file_path: Optional[str] = Field(default=None, description="Путь к файлу Config.xml")
    target_drive_letter: Optional[str] = Field(default=None, description="Буква целевого диска бэкапов")
    target_url: Optional[str] = Field(default=None, description="Целевой путь назначения бэкапа")
    target_name: Optional[str] = Field(default=None, description="Метка тома целевого хранилища")
    backup_interval_seconds: Optional[int] = Field(default=3600, description="Интервал создания копий в секундах")
    retention_policy: Optional[str] = Field(default="Forever", description="Политика хранения версий")
    last_backup_time: Optional[datetime] = Field(default=None, description="Время последнего успешного резервного копирования")


class FileHistoryStatus(BaseModel):
    """Общий статус подсистемы File History."""
    service_status: ServiceState = Field(description="Состояние службы fhsvc")
    service_start_type: str = Field(default="Manual", description="Тип запуска службы (Manual, Auto, Disabled)")
    config: FileHistoryConfigInfo = Field(description="Конфигурация пользователя")
    fhexec_available: bool = Field(default=True, description="Доступна ли системная утилита fhexec.exe")


class FileVersionRecord(BaseModel):
    """Запись об отдельной сохраненной версии файла в хранилище истории."""
    original_relative_path: str = Field(description="Оригинальный относительный путь")
    backup_file_path: str = Field(description="Полный путь к файлу копии в хранилище")
    version_timestamp: Optional[datetime] = Field(default=None, description="Временная метка версии")
    size_bytes: int = Field(default=0, description="Размер версии в байтах")


class StorageBackupAudit(BaseModel):
    """Отчет об аудите хранилища резервных копий."""
    target_path: str = Field(description="Путь к корню хранилища бэкапов")
    target_exists: bool = Field(description="Доступен ли целевой диск/каталог")
    total_versions_found: int = Field(default=0, description="Общее число найденных версий файлов")
    total_backup_size_bytes: int = Field(default=0, description="Суммарный объем резервных копий")
    total_backup_size_mb: float = Field(default=0.0, description="Суммарный объем в МБ")
    free_space_gb: Optional[float] = Field(default=None, description="Свободное место на диске хранилища (в ГБ)")
    total_space_gb: Optional[float] = Field(default=None, description="Общий объем диска хранилища (в ГБ)")
    drives_in_backup: List[str] = Field(default_factory=list, description="Диски, найденные в структуре бэкапа")
    sample_versions: List[FileVersionRecord] = Field(default_factory=list, description="Примеры последних версий")


class VssSnapshot(BaseModel):
    """Снимок тома VSS (Volume Shadow Copy)."""
    snapshot_id: str = Field(description="Идентификатор снимка (GUID)")
    original_volume: str = Field(description="Исходный том (например, C:\\)")
    creation_time: Optional[str] = Field(default=None, description="Время создания снимка")
    shadow_volume_path: Optional[str] = Field(default=None, description="Путь к теневому устройству тома")


class BackupHealthReport(BaseModel):
    """Сводный отчет о состоянии всех механизмов резервного копирования Windows."""
    timestamp: datetime = Field(default_factory=datetime.now, description="Время формирования отчета")
    libraries_count: int = Field(description="Количество настроенных библиотек Windows")
    libraries: List[WindowsLibrary] = Field(default_factory=list, description="Список библиотек")
    file_history: FileHistoryStatus = Field(description="Статус службы и конфига File History")
    storage_audit: Optional[StorageBackupAudit] = Field(default=None, description="Аудит целевого хранилища")
    vss_snapshots: List[VssSnapshot] = Field(default_factory=list, description="Список теневых копий томов")
    health_score: int = Field(default=100, description="Общий индекс готовности бэкапов (0-100)")
    recommendations: List[str] = Field(default_factory=list, description="Рекомендации по улучшению защиты данных")


class FileHistoryRAGSyncRequest(BaseModel):
    """Запрос на синхронизацию/индексацию истории файлов в RAG."""
    target_path: Optional[str] = Field(default=None, description="Опциональный путь к каталогу бэкапов File History")
    chunk_size: int = Field(default=500, ge=100, le=4000, description="Размер чанка в символах")
    chunk_overlap: int = Field(default=50, ge=0, le=1000, description="Перекрытие чанков")
    force_rebuild: bool = Field(default=False, description="Принудительная полная переиндексация с нуля")


class FileHistoryRAGSearchRequest(BaseModel):
    """Запрос на семантический поиск по архивам Истории файлов Windows."""
    query: str = Field(..., min_length=1, description="Поисковый запрос")
    top_k: int = Field(default=5, ge=1, le=50, description="Количество возвращаемых результатов")
    min_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Минимальный порог релевантности")
    date_from: Optional[datetime] = Field(default=None, description="Начальная дата снимка версии")
    date_to: Optional[datetime] = Field(default=None, description="Конечная дата снимка версии")
    path_pattern: Optional[str] = Field(default=None, description="Фильтр по подстроке пути или имени файла")
    drive_filter: Optional[str] = Field(default=None, description="Фильтр по букве диска (например, 'C')")


class FileHistoryRAGSearchResult(BaseModel):
    """Элемент результата поиска по архиву Истории файлов."""
    chunk_id: str = Field(description="Идентификатор фрагмента")
    original_path: str = Field(description="Оригинальный относительный путь к файлу")
    backup_file_path: str = Field(description="Физический путь к файлу резервной копии")
    version_timestamp: Optional[datetime] = Field(default=None, description="Дата и время сохранения этой версии")
    score: float = Field(description="Коэффициент сходства / релевантности (0.0 - 1.0)")
    text: str = Field(description="Текстовое содержимое найденного фрагмента")
    chunk_index: int = Field(default=0, description="Индекс чанка в файле")


class FileHistoryVersionSummary(BaseModel):
    """Сводка по версиям конкретного документа."""
    original_path: str = Field(description="Оригинальный путь к файлу")
    total_versions: int = Field(description="Количество сохраненных версий")
    versions: List[FileVersionRecord] = Field(default_factory=list, description="Список всех найденных снимков")


class FileHistoryRAGStatus(BaseModel):
    """Текущее состояние и метрики RAG индекса Истории файлов Windows."""
    index_dir: str = Field(description="Каталог хранения индекса")
    total_files_indexed: int = Field(default=0, description="Количество проиндексированных версий файлов")
    total_chunks: int = Field(default=0, description="Общее число текстовых чанков в индексе")
    dimension: int = Field(default=0, description="Размерность вектора TF-IDF")
    last_sync_time: Optional[datetime] = Field(default=None, description="Время последней синхронизации")
    is_ready: bool = Field(default=False, description="Готов ли индекс для поиска")