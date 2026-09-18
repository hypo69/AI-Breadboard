# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: GPU Driver Manager Data Models
# =============================================================================
# Description:
#   Pydantic-модели и перечисления для видеокарт, версий драйверов NVIDIA/AMD,
#   задач загрузки и параметров установки.
#
# File: models.py
# Project: ai-breadboard
# Package: apps.gpu_driver_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модели данных и структуры для сервиса управления видеодрайверами."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class VendorType(str, Enum):
    """Тип производителя графического адаптера."""
    NVIDIA = "NVIDIA"
    AMD = "AMD"
    INTEL = "INTEL"
    OTHER = "OTHER"


class DriverBranch(str, Enum):
    """Ветка / категория драйвера."""
    GAME_READY = "Game Ready (GRD)"
    STUDIO = "Studio Driver (SD)"
    PRODUCTION_BRANCH = "Production / Enterprise"
    ADRENALIN = "AMD Software: Adrenalin Edition"
    PRO_ENTERPRISE = "AMD Software: PRO Edition"
    OTHER = "Other"


class UpdateStatus(str, Enum):
    """Статус актуальности установленного драйвера."""
    UP_TO_DATE = "UP_TO_DATE"
    UPDATE_AVAILABLE = "UPDATE_AVAILABLE"
    NEWER_THAN_CATALOG = "NEWER_THAN_CATALOG"
    UNKNOWN = "UNKNOWN"


class TaskStatus(str, Enum):
    """Статус выполнения фоновой задачи (скачивание/установка)."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class GpuDevice(BaseModel):
    """Информация об обнаруженной видеокарте в операционной системе."""
    id: str = Field(description="Уникальный идентификатор устройства в системе")
    name: str = Field(description="Маркетинговое название видеокарты")
    vendor: VendorType = Field(default=VendorType.OTHER, description="Производитель GPU")
    pnp_device_id: Optional[str] = Field(default=None, description="PNP Device ID / PCI ID")
    driver_version_raw: str = Field(default="", description="Сырая системная версия драйвера из WMI/реестра")
    driver_version_formatted: str = Field(default="", description="Форматированная версия (например, 560.94 или 24.8.1)")
    driver_date: Optional[str] = Field(default=None, description="Дата выпуска текущего установленного драйвера")
    cuda_driver_version: Optional[str] = Field(default=None, description="Версия CUDA драйвера (для NVIDIA при наличии nvidia-smi)")
    status: str = Field(default="OK", description="Статус устройства в диспетчере устройств Windows")
    memory_mb: Optional[int] = Field(default=None, description="Объем видеопамяти в мегабайтах")


class DriverRelease(BaseModel):
    """Сведения о доступном релизе драйвера в каталоге."""
    version: str = Field(description="Версия драйвера (например, '572.70' или '24.12.1')")
    vendor: VendorType = Field(description="Производитель (NVIDIA / AMD)")
    branch: DriverBranch = Field(default=DriverBranch.GAME_READY, description="Ветка драйвера")
    release_date: str = Field(description="Дата официального релиза (YYYY-MM-DD)")
    os: str = Field(default="Windows 10/11 64-bit", description="Поддерживаемая операционная система")
    download_url: str = Field(description="Прямая или официальная ссылка для скачивания установщика")
    file_size_mb: Optional[float] = Field(default=None, description="Приблизительный размер дистрибутива в МБ")
    is_whql: bool = Field(default=True, description="Флаг сертификации Microsoft WHQL")
    release_notes_url: Optional[str] = Field(default=None, description="Ссылка на Release Notes / документацию")
    highlights: List[str] = Field(default_factory=list, description="Ключевые особенности и поддерживаемые игры/приложения")
    installer_filename: Optional[str] = Field(default=None, description="Имя скачиваемого файла")
    is_cached: bool = Field(default=False, description="Скачан ли уже дистрибутив на локальный диск")
    local_path: Optional[str] = Field(default=None, description="Локальный путь к скачанному установщику")


class GpuUpdateCheck(BaseModel):
    """Результат проверки актуальности драйверов для конкретного GPU."""
    device: GpuDevice = Field(description="Сведения об устройстве")
    installed_version: str = Field(description="Текущая установленная версия")
    latest_available_version: Optional[str] = Field(default=None, description="Последняя доступная версия в каталоге")
    latest_release_date: Optional[str] = Field(default=None, description="Дата релиза последней версии")
    status: UpdateStatus = Field(default=UpdateStatus.UNKNOWN, description="Статус актуальности")
    status_message: str = Field(default="", description="Человекочитаемое пояснение статуса на русском языке")
    available_releases_count: int = Field(default=0, description="Количество доступных для установки версий в каталоге")


class DownloadProgress(BaseModel):
    """Прогресс скачивания файла установщика."""
    task_id: str
    version: str
    vendor: VendorType
    url: str
    destination_file: str
    status: TaskStatus = TaskStatus.PENDING
    total_bytes: int = 0
    downloaded_bytes: int = 0
    percent: float = 0.0
    speed_mb_s: float = 0.0
    error_message: Optional[str] = None


class InstallOptions(BaseModel):
    """Параметры установки выбранной версии драйвера."""
    version: str = Field(description="Версия драйвера для установки")
    vendor: VendorType = Field(description="Производитель (NVIDIA / AMD)")
    clean_install: bool = Field(default=False, description="Выполнить чистую установку (сброс настроек профилей)")
    silent: bool = Field(default=False, description="Фоновая / тихая установка без диалоговых окон")
    create_restore_point: bool = Field(default=False, description="Создать точку восстановления Windows перед запуском")
    custom_installer_path: Optional[str] = Field(default=None, description="Пользовательский путь к установщику")


class InstallTask(BaseModel):
    """Состояние задачи установки драйвера."""
    task_id: str
    version: str
    vendor: VendorType
    status: TaskStatus = TaskStatus.PENDING
    options: InstallOptions
    installer_path: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    exit_code: Optional[int] = None
    logs: List[str] = Field(default_factory=list, description="Логи процесса установки")
    error_message: Optional[str] = None


class DriverServiceStatus(BaseModel):
    """Общий статус сервиса управления драйверами."""
    status: str = "online"
    service: str = "GPU Driver Manager"
    version: str = "1.0.0"
    detected_gpus_count: int = 0
    nvidia_releases_count: int = 0
    amd_releases_count: int = 0
    cached_installers_count: int = 0
    portable_tools: Dict[str, Any] = Field(default_factory=dict)
