# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Registry Viewer Data Models
# =============================================================================
# Description:
#   Модели данных Pydantic для представления ключей, параметров, закладок
#   и результатов поиска по реестру Windows.
#
# File: models.py
# Project: ai-breadboard
# Package: apps.registry_viewer
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модели данных для приложения Windows Registry Viewer."""

from __future__ import annotations

from typing import Any, List, Optional
from pydantic import BaseModel, Field


class RegistryValueDTO(BaseModel):
    """Модель отдельного параметра (значения) реестра Windows."""
    name: str = Field(..., description="Имя параметра реестра (или '(Default)')")
    type_code: int = Field(..., description="Числовой код типа данных winreg")
    type_name: str = Field(..., description="Строковое название типа (например REG_SZ, REG_DWORD)")
    data: Any = Field(..., description="Значение параметра (строка, число, список или HEX)")
    size_bytes: int = Field(default=0, description="Приблизительный размер данных в байтах")


class RegistryKeyDetailsDTO(BaseModel):
    """Детальная информация о ключе реестра (подразделы и значения)."""
    hive: str = Field(..., description="Корневая ветка (например HKEY_LOCAL_MACHINE)")
    path: str = Field(..., description="Относительный путь ключа")
    full_path: str = Field(..., description="Полный путь в реестре")
    subkeys: List[str] = Field(default_factory=list, description="Список имен непосредственных подразделов")
    values: List[RegistryValueDTO] = Field(default_factory=list, description="Список параметров и их значений")
    subkeys_count: int = Field(default=0, description="Количество подразделов")
    values_count: int = Field(default=0, description="Количество параметров")


class BookmarkItem(BaseModel):
    """Модель быстрой системной закладки реестра."""
    id: str = Field(..., description="Уникальный идентификатор закладки")
    title: str = Field(..., description="Название закладки")
    hive: str = Field(..., description="Корневая ветка")
    path: str = Field(..., description="Путь к ветке реестра")
    description: str = Field(..., description="Пояснение назначения ветки")
    icon: str = Field(default="📁", description="Эмодзи-иконка закладки")


class SearchMatchItem(BaseModel):
    """Модель одного совпадения при поиске по реестру."""
    hive: str = Field(..., description="Корневая ветка")
    key_path: str = Field(..., description="Путь к ключу с совпадением")
    match_type: str = Field(..., description="Тип совпадения: key_name, value_name, value_data")
    matched_text: str = Field(..., description="Текст, в котором найдено совпадение")
    value_name: Optional[str] = Field(default=None, description="Имя параметра, если совпадение в значении")
    value_type: Optional[str] = Field(default=None, description="Тип параметра, если применимо")
    value_data: Optional[Any] = Field(default=None, description="Данные параметра, если применимо")


class SearchResponseDTO(BaseModel):
    """Ответ поискового запроса по реестру."""
    status: str = Field(default="ok", description="Статус выполнения запроса")
    hive: str = Field(..., description="Корневая ветка")
    path: str = Field(..., description="Базовый путь поиска")
    query: str = Field(..., description="Поисковая строка")
    total_found: int = Field(default=0, description="Количество найденных результатов")
    results: List[SearchMatchItem] = Field(default_factory=list, description="Список найденных совпадений")


class BackupMetadataDTO(BaseModel):
    """Метаданные точки резервного копирования (снимка) реестра."""
    backup_id: str = Field(..., description="Уникальный идентификатор бэкапа")
    timestamp: str = Field(..., description="Время создания в формате ISO")
    hive: str = Field(..., description="Корневая ветка")
    path: str = Field(..., description="Путь ветки реестра")
    operation: str = Field(..., description="Операция, вызвавшая бэкап (set_value, delete_value, delete_key и др.)")
    file_path: str = Field(..., description="Путь к JSON-файлу со снимком данных")
    reg_file_path: Optional[str] = Field(default=None, description="Путь к нативному .reg файлу")
    values_count: int = Field(default=0, description="Количество сохраненных параметров")


class RestoreBackupResponseDTO(BaseModel):
    """Результат операции восстановления из бэкапа."""
    status: str = Field(default="ok", description="Статус восстановления")
    backup_id: str = Field(..., description="Идентификатор восстановленного бэкапа")
    message: str = Field(..., description="Текстовое сообщение о результате")
    hive: str = Field(..., description="Корневая ветка")
    path: str = Field(..., description="Путь восстановленного раздела")


class SetValueRequestDTO(BaseModel):
    """Запрос на создание или изменение параметра реестра."""
    hive: str = Field(default="HKEY_LOCAL_MACHINE", description="Корневая ветка")
    path: str = Field(..., description="Путь к ключу")
    name: str = Field(default="", description="Имя параметра (пустое для значения по умолчанию)")
    type_name: str = Field(default="REG_SZ", description="Тип параметра (REG_SZ, REG_DWORD, REG_MULTI_SZ и т.д.)")
    data: Any = Field(..., description="Значение параметра")
    create_backup: bool = Field(default=True, description="Флаг создания резервной копии перед сохранением")


class DeleteValueRequestDTO(BaseModel):
    """Запрос на удаление параметра реестра."""
    hive: str = Field(default="HKEY_LOCAL_MACHINE", description="Корневая ветка")
    path: str = Field(..., description="Путь к ключу")
    name: str = Field(..., description="Имя удаляемого параметра")
    create_backup: bool = Field(default=True, description="Флаг создания резервной копии перед удалением")


class CreateKeyRequestDTO(BaseModel):
    """Запрос на создание нового раздела реестра."""
    hive: str = Field(default="HKEY_LOCAL_MACHINE", description="Корневая ветка")
    path: str = Field(..., description="Путь к создаваемому ключу")


class DeleteKeyRequestDTO(BaseModel):
    """Запрос на удаление раздела реестра."""
    hive: str = Field(default="HKEY_LOCAL_MACHINE", description="Корневая ветка")
    path: str = Field(..., description="Путь к удаляемому ключу")
    recursive: bool = Field(default=False, description="Удалять ли рекурсивно со всеми подразделами")
    create_backup: bool = Field(default=True, description="Флаг создания резервной копии перед удалением")


class EditOperationResultDTO(BaseModel):
    """Результат выполнения операции модификации реестра."""
    status: str = Field(default="ok", description="Статус операции")
    operation: str = Field(..., description="Тип операции")
    hive: str = Field(..., description="Корневая ветка")
    path: str = Field(..., description="Путь к ключу")
    backup: Optional[BackupMetadataDTO] = Field(default=None, description="Метаданные созданного бэкапа")
    message: str = Field(..., description="Информационное сообщение")

