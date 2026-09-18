# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Defender Data Models
# =============================================================================
# Description:
#   Pydantic-модели данных для представления статуса Microsoft Defender,
#   правил Attack Surface Reduction (ASR), Controlled Folder Access (CFA),
#   аудита исключений, журнала угроз, событий безопасности и AI-диагностики.
#
# File: models.py
# Project: ai-breadboard
# Package: apps.windows_defender.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Pydantic-модели данных для Microsoft Defender Antivirus & Security Center."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ProtectionState(str, Enum):
    """Состояние компонента защиты."""
    ENABLED = "enabled"
    DISABLED = "disabled"
    AUDIT = "audit"
    WARN = "warn"
    UNKNOWN = "unknown"
    NOT_CONFIGURED = "not_configured"


class ScanType(str, Enum):
    """Тип антивирусного сканирования."""
    QUICK = "quick"
    FULL = "full"
    CUSTOM = "custom"
    OFFLINE = "offline"


class ThreatSeverity(str, Enum):
    """Уровень серьезности угрозы."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    SEVERE = "severe"
    UNKNOWN = "unknown"


class ExclusionRiskLevel(str, Enum):
    """Уровень риска для обнаруженного исключения из проверки."""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ServiceStatus(BaseModel):
    """Статус системной службы/процесса Defender."""
    name: str = Field(..., description="Имя процесса или службы (например, MsMpEng.exe)")
    display_name: str = Field(..., description="Человекочитаемое название")
    running: bool = Field(False, description="Признак активности процесса")
    pid: Optional[int] = Field(None, description="Идентификатор процесса (PID)")
    memory_mb: float = Field(0.0, description="Потребление оперативной памяти в МБ")
    description: str = Field("", description="Назначение компонента")


class DefenderStatus(BaseModel):
    """Комплексный статус состояния Microsoft Defender Antivirus."""
    antivirus_enabled: bool = Field(False, description="Включен ли антивирусный модуль")
    real_time_protection_enabled: bool = Field(False, description="Защита в реальном времени")
    behavior_monitor_enabled: bool = Field(False, description="Поведенческий анализ")
    ioav_protection_enabled: bool = Field(False, description="Проверка загружаемых файлов и вложений")
    on_access_protection_enabled: bool = Field(False, description="Проверка файлов при доступе")
    script_scanning_enabled: bool = Field(False, description="Сканирование скриптов (AMSI)")
    cloud_protection_enabled: bool = Field(False, description="Облачная защита (MAPS)")
    cloud_block_level: str = Field("Default", description="Уровень блокировки в облаке")
    tamper_protection_enabled: bool = Field(False, description="Защита от несанкционированного изменения (Tamper Protection)")
    pua_protection_enabled: bool = Field(False, description="Защита от потенциально нежелательного ПО (PUA)")
    controlled_folder_access_enabled: bool = Field(False, description="Контролируемый доступ к папкам (защита от Ransomware)")
    network_protection_enabled: bool = Field(False, description="Сетевая защита (Network Protection)")
    antivirus_signature_version: str = Field("", description="Версия антивирусных баз")
    antispyware_signature_version: str = Field("", description="Версия баз защиты от шпионского ПО")
    engine_version: str = Field("", description="Версия сканирующего движка Defender")
    product_version: str = Field("", description="Версия платформы клиента Defender")
    last_quick_scan_time: Optional[str] = Field(None, description="Время последнего быстрого сканирования")
    last_full_scan_time: Optional[str] = Field(None, description="Время последнего полного сканирования")
    last_update_time: Optional[str] = Field(None, description="Время последнего обновления сигнатур")
    services: List[ServiceStatus] = Field(default_factory=list, description="Статусы связанных служб")


class ASRRuleInfo(BaseModel):
    """Информация о правиле Attack Surface Reduction (ASR)."""
    guid: str = Field(..., description="Уникальный идентификатор правила GUID")
    name: str = Field(..., description="Название правила")
    description: str = Field(..., description="Подробное описание назначения правила")
    state: ProtectionState = Field(ProtectionState.NOT_CONFIGURED, description="Текущее состояние правила")
    category: str = Field("General", description="Категория (Office, Scripts, Email, Persistence, Drivers)")
    recommendation: str = Field("", description="Рекомендация по настройке безопасности")


class ControlledFolderAccessInfo(BaseModel):
    """Сведения о функции Controlled Folder Access (защита от Ransomware)."""
    enabled: bool = Field(False, description="Статус активности CFA")
    mode: ProtectionState = Field(ProtectionState.DISABLED, description="Режим (Disabled, Block, Audit)")
    protected_folders: List[str] = Field(default_factory=list, description="Список защищенных директорий")
    allowed_applications: List[str] = Field(default_factory=list, description="Список разрешенных исполняемых файлов")


class ExclusionItem(BaseModel):
    """Запись исключения из антивирусного сканирования."""
    type: str = Field(..., description="Тип исключения: path, extension, process")
    value: str = Field(..., description="Значение (путь, расширение файла или имя процесса)")
    risk_level: ExclusionRiskLevel = Field(ExclusionRiskLevel.SAFE, description="Оценка уровня риска")
    risk_reason: str = Field("", description="Обоснование риска (почему исключение подозрительно)")


class ExclusionsAuditReport(BaseModel):
    """Отчет об аудите исключений из проверки."""
    total_exclusions: int = Field(0, description="Общее число исключений")
    suspicious_count: int = Field(0, description="Количество подозрительных/опасных исключений")
    path_exclusions: List[ExclusionItem] = Field(default_factory=list, description="Исключения каталогов и файлов")
    extension_exclusions: List[ExclusionItem] = Field(default_factory=list, description="Исключения расширений")
    process_exclusions: List[ExclusionItem] = Field(default_factory=list, description="Исключения процессов")
    summary_recommendation: str = Field("", description="Итоговая рекомендация по исключениям")


class ThreatRecord(BaseModel):
    """Запись об обнаруженной угрозе."""
    threat_id: str = Field(..., description="Идентификатор угрозы")
    threat_name: str = Field(..., description="Имя угрозы (например, Trojan:Win32/Wacatac)")
    severity: ThreatSeverity = Field(ThreatSeverity.UNKNOWN, description="Уровень опасности")
    category: str = Field("", description="Категория угрозы (Trojan, Ransomware, PUA, Adware)")
    initial_detection_time: Optional[str] = Field(None, description="Время первого обнаружения")
    last_detection_time: Optional[str] = Field(None, description="Время последнего обнаружения")
    status: str = Field("Cleaned", description="Статус (Cleaned, Quarantined, Blocked, Active)")
    resources: List[str] = Field(default_factory=list, description="Затронутые файлы или ресурсы")
    remediation_path: str = Field("", description="Путь или действие по устранению")


class DefenderEventRecord(BaseModel):
    """Запись события из журнала Microsoft-Windows-Windows Defender/Operational."""
    event_id: int = Field(..., description="Идентификатор события Windows Event ID")
    timestamp: str = Field(..., description="Время фиксации события")
    level: str = Field("Information", description="Уровень (Information, Warning, Error, Critical)")
    message: str = Field(..., description="Текст сообщения события")
    category: str = Field("Operational", description="Категория события")
    details: Dict[str, Any] = Field(default_factory=dict, description="Дополнительные структурированные атрибуты")


class SuspiciousProcessChain(BaseModel):
    """Обнаруженная подозрительная цепочка процессов / индикатор бесфайловой активности."""
    parent_process: str = Field(..., description="Родительский процесс (например, winword.exe)")
    parent_pid: Optional[int] = Field(None, description="PID родительского процесса")
    child_process: str = Field(..., description="Дочерний процесс (например, powershell.exe)")
    child_pid: Optional[int] = Field(None, description="PID дочернего процесса")
    command_line: str = Field("", description="Командная строка запуска")
    severity: ThreatSeverity = Field(ThreatSeverity.HIGH, description="Степень подозрительности")
    reason: str = Field(..., description="Причина срабатывания детектора")


class ScanRequest(BaseModel):
    """Параметры запроса на запуск сканирования."""
    scan_type: ScanType = Field(ScanType.QUICK, description="Тип проверки (quick, full, custom, offline)")
    target_path: Optional[str] = Field(None, description="Целевой путь для custom-сканирования")


class ScanResponse(BaseModel):
    """Результат инициализации/выполнения сканирования."""
    success: bool = Field(..., description="Успешность выполнения команды")
    scan_type: ScanType = Field(..., description="Тип запущенного сканирования")
    message: str = Field(..., description="Информационное сообщение")
    output: str = Field("", description="Вывод утилиты MpCmdRun.exe или PowerShell")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class DefenderDiagnosticReport(BaseModel):
    """Итоговый диагностический отчет защищенности с AI-анализом."""
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    security_score: int = Field(..., ge=0, le=100, description="Индекс защищенности от 0 до 100")
    status_summary: str = Field(..., description="Краткое резюме состояния безопасности")
    critical_findings: List[str] = Field(default_factory=list, description="Критические уязвимости и риски")
    warnings: List[str] = Field(default_factory=list, description="Предупреждения и потенциальные слабые места")
    recommendations: List[str] = Field(default_factory=list, description="Конкретные шаги по усилению защиты")
    status: DefenderStatus = Field(..., description="Текущее состояние Defender")
    exclusions_audit: ExclusionsAuditReport = Field(..., description="Результаты аудита исключений")
    active_threats_count: int = Field(0, description="Количество активных угроз")
    quarantined_threats_count: int = Field(0, description="Количество угроз в карантине")
    suspicious_process_chains: List[SuspiciousProcessChain] = Field(default_factory=list, description="Подозрительные процессы")
