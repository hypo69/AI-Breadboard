# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules System_Checkpoints - Models
# =============================================================================
# Description:
#   Модели данных для системы контрольных точек и образов восстановления Windows.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.system_checkpoints.models import CheckpointType
#
#     service = CheckpointType()
#
# File: models.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.system_checkpoints
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Модели данных для системы контрольных точек и образов восстановления Windows."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CheckpointType(str, Enum):
    """Типы контрольных точек системы."""
    BASELINE = "BASELINE"                # 🟢 Базовая (после чистой установки)
    POST_CONFIG = "POST_CONFIG"          # 🔵 После настройки (драйверы и софт)
    PRE_UPDATE = "PRE_UPDATE"            # 🟡 Перед крупным обновлением Windows/драйверов
    PRE_EXPERIMENT = "PRE_EXPERIMENT"    # 🟠 Перед экспериментом / установкой тестового ПО
    PERIODIC = "PERIODIC"                # 🔴 Периодическая (плановая по расписанию)
    CUSTOM = "CUSTOM"                    # ⚪ Пользовательская произвольная


class RecoveryMechanism(str, Enum):
    """Нативные механизмы восстановления Windows."""
    SYSTEM_IMAGE = "SYSTEM_IMAGE"        # WIM / DISM полный или инкрементальный образ
    WINRE_ENVIRONMENT = "WINRE"          # Среда восстановления Windows RE (reagentc)
    RESTORE_POINT = "RESTORE_POINT"      # Нативная точка восстановления (VSS/SystemRestore)


class FreshnessLevel(str, Enum):
    """Уровни актуальности образа восстановления."""
    HIGH = "HIGH"                        # 🟢 Высокая (образ свежий, <30 дней, мало изменений)
    MEDIUM = "MEDIUM"                    # 🟡 Средняя (30-90 дней или умеренные изменения)
    LOW = "LOW"                          # 🟠 Низкая (>90 дней или значительные изменения)
    CRITICAL_OUTDATED = "CRITICAL"       # 🔴 Критически устарел (>180 дней / кардинальный дрейф)
    UNKNOWN = "UNKNOWN"                  # ⚪ Нет данных (образы отсутствуют)


@dataclass
class SystemDriftMetrics:
    """Метрики дрейфа состояния системы с момента создания образа.

    Attributes:
        days_since_creation: Количество дней с момента фиксации снимка/образа.
        changed_components_count: Количество изменившихся системных компонентов / KB.
        installed_apps_count: Количество вновь установленных программ.
        updated_drivers_count: Количество обновленных/добавленных драйверов.
        recent_kbs: Список недавних KB-обновлений.
        recent_apps: Список недавно установленных программ.
    """
    days_since_creation: int = 0
    changed_components_count: int = 0
    installed_apps_count: int = 0
    updated_drivers_count: int = 0
    recent_kbs: List[str] = field(default_factory=list)
    recent_apps: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование метрик в словарь."""
        return {
            "days_since_creation": self.days_since_creation,
            "changed_components_count": self.changed_components_count,
            "installed_apps_count": self.installed_apps_count,
            "updated_drivers_count": self.updated_drivers_count,
            "recent_kbs": self.recent_kbs,
            "recent_apps": self.recent_apps,
        }


@dataclass
class FreshnessReport:
    """Отчет об актуальности образов восстановления и рекомендации.

    Attributes:
        last_image_name: Имя последнего найденного образа.
        last_image_date: Дата и время создания последнего образа.
        age_days: Возраст образа в днях.
        drift: Метрики дрейфа системы.
        freshness_level: Рассчитанный уровень актуальности.
        freshness_label_ru: Понятное текстовое описание актуальности на русском языке.
        recommendation: Рекомендация для администратора.
        can_restore_safely: Безопасно ли откатываться к данному образу.
    """
    last_image_name: Optional[str] = None
    last_image_date: Optional[str] = None
    age_days: int = 0
    drift: SystemDriftMetrics = field(default_factory=SystemDriftMetrics)
    freshness_level: FreshnessLevel = FreshnessLevel.UNKNOWN
    freshness_label_ru: str = "Образы отсутствуют"
    recommendation: str = "Создайте базовый эталонный образ восстановления."
    can_restore_safely: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование отчета в словарь."""
        return {
            "last_image_name": self.last_image_name,
            "last_image_date": self.last_image_date,
            "age_days": self.age_days,
            "drift": self.drift.to_dict(),
            "freshness_level": self.freshness_level.value,
            "freshness_label_ru": self.freshness_label_ru,
            "recommendation": self.recommendation,
            "can_restore_safely": self.can_restore_safely,
        }


@dataclass
class WinREStatus:
    """Статус среды восстановления Windows (WinRE).

    Attributes:
        enabled: Включена ли среда Windows RE.
        location: Путь к образу Winre.wim или раздела восстановления.
        bcd_id: GUID записи BCD для Windows RE.
        custom_image_location: Пользовательское расположение образа WinRE (если задано).
        is_staged: Подготовлен ли образ к интеграции.
        error: Текст ошибки при диагностике (если есть).
    """
    enabled: bool = False
    location: str = ""
    bcd_id: str = ""
    custom_image_location: str = ""
    is_staged: bool = False
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование статуса в словарь."""
        return {
            "enabled": self.enabled,
            "location": self.location,
            "bcd_id": self.bcd_id,
            "custom_image_location": self.custom_image_location,
            "is_staged": self.is_staged,
            "error": self.error,
        }


@dataclass
class SystemImageMetadata:
    """Метаданные файла системного WIM-образа.

    Attributes:
        image_path: Полный путь к файлу .wim или .esd.
        file_size_bytes: Размер файла в байтах.
        created_at: Дата создания или модификации файла.
        is_baseline: Является ли образ базовым эталонным.
        index_count: Количество индексов/снимков внутри WIM-файла.
        description: Описание содержимого образа.
        captured_drive: Буква захваченного диска (например, 'C:').
    """
    image_path: str
    file_size_bytes: int = 0
    created_at: str = ""
    is_baseline: bool = False
    index_count: int = 1
    description: str = ""
    captured_drive: str = "C:"

    @property
    def file_size_gb(self) -> float:
        """Размер файла в гигабайтах."""
        return round(self.file_size_bytes / (1024 ** 3), 2)

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование метаданных образа в словарь."""
        return {
            "image_path": self.image_path,
            "file_size_bytes": self.file_size_bytes,
            "file_size_gb": self.file_size_gb,
            "created_at": self.created_at,
            "is_baseline": self.is_baseline,
            "index_count": self.index_count,
            "description": self.description,
            "captured_drive": self.captured_drive,
        }


@dataclass
class SystemCheckpointRecord:
    """Запись в версионном каталоге контрольных точек системы.

    Attributes:
        checkpoint_id: Уникальный строковый идентификатор точки.
        checkpoint_type: Тип контрольной точки (BASELINE, POST_CONFIG, etc.).
        mechanisms: Список задействованных механизмов (Image, WinRE, RestorePoint).
        created_at: Дата и время фиксации.
        title: Название контрольной точки.
        description: Подробное описание причин создания.
        image_path: Путь к привязанному WIM-файлу (если есть).
        restore_point_seq: Номер нативной точки восстановления Windows (если есть).
        drift_at_creation: Зафиксированный дрейф на момент фиксации.
    """
    checkpoint_id: str
    checkpoint_type: CheckpointType
    mechanisms: List[RecoveryMechanism]
    created_at: str
    title: str
    description: str = ""
    image_path: Optional[str] = None
    restore_point_seq: Optional[int] = None
    drift_at_creation: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование записи каталога в словарь."""
        return {
            "checkpoint_id": self.checkpoint_id,
            "checkpoint_type": self.checkpoint_type.value,
            "mechanisms": [m.value for m in self.mechanisms],
            "created_at": self.created_at,
            "title": self.title,
            "description": self.description,
            "image_path": self.image_path,
            "restore_point_seq": self.restore_point_seq,
            "drift_at_creation": self.drift_at_creation,
        }


# --- Pydantic модели для запросов API ---

class CheckpointCreateRequest(BaseModel):
    """Модель запроса создания новой контрольной точки."""
    checkpoint_type: CheckpointType = Field(
        default=CheckpointType.PERIODIC,
        description="Тип контрольной точки (BASELINE, POST_CONFIG, PRE_UPDATE, PRE_EXPERIMENT, PERIODIC)"
    )
    title: str = Field(..., description="Краткий заголовок контрольной точки")
    description: str = Field(default="", description="Подробное описание состояния системы")
    create_restore_point: bool = Field(default=True, description="Создать нативную точку восстановления VSS")
    create_wim_image: bool = Field(default=False, description="Создать полный или инкрементальный WIM-образ")
    target_drive: str = Field(default="C:", description="Целевой системный диск для захвата")
    destination_dir: Optional[str] = Field(default=None, description="Каталог сохранения WIM-образа")


class WimImageCreateRequest(BaseModel):
    """Модель запроса создания WIM-образа через DISM."""
    image_name: str = Field(..., description="Имя создаваемого образа (без расширения или с .wim)")
    is_baseline: bool = Field(default=False, description="Пометить как эталонный базовый образ")
    source_drive: str = Field(default="C:", description="Буква исходного диска для захвата")
    destination_dir: Optional[str] = Field(default=None, description="Целевая директория")
    description: str = Field(default="", description="Описание образа")
    append_if_exists: bool = Field(default=True, description="Добавить как новый индекс, если файл уже существует")


class WinREActionRequest(BaseModel):
    """Модель запроса управления WinRE."""
    action: str = Field(..., description="Действие: 'enable', 'disable' или 'set_path'")
    custom_path: Optional[str] = Field(default=None, description="Кастомный путь для set_path")
