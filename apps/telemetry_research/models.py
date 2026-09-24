# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Telemetry Research Application Data Models
# =============================================================================
# Description:
#   Схемы данных Pydantic для приложения исследования телеметрии:
#   параметры сценариев исследования, результаты проверки гипотез,
#   матрица корреляций между метриками и расширенный аналитический отчет.
#
# File: models.py
# Project: ai-breadboard
# Package: apps.telemetry_research
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Схемы данных Pydantic для приложения глубокого исследования телеметрии."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# Повторное использование базовых моделей из подсистемы телеметрии (REUSE)
from apps.windows.telemetry.research.models import (
    AnomalyEvent,
    ChartConfig,
    DeviceEventSummary,
    MetricPoint,
    MetricStats,
    TelemetryResearchReport,
    TimeSeriesDataset,
)


class ResearchScenarioRequest(BaseModel):
    """Параметры запроса для проведения исследовательского сценария."""

    source_path: Optional[str] = Field(
        default=None,
        description="Путь к файлу логов, директории или шаблону поиска",
    )
    records: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Массив сырых записей телеметрии, переданный напрямую",
    )
    start_time: Optional[str] = Field(
        default=None,
        description="Начало временного интервала фильтрации (ISO 8601)",
    )
    end_time: Optional[str] = Field(
        default=None,
        description="Конец временного интервала фильтрации (ISO 8601)",
    )
    subsystems: Optional[List[str]] = Field(
        default=None,
        description="Список исследуемых подсистем (cpu, ram, gpu, disk, network, devices, sensors)",
    )
    cpu_anomaly_threshold: float = Field(
        default=90.0,
        description="Порог загрузки CPU (%) для детекции аномалий",
    )
    temp_anomaly_threshold: float = Field(
        default=85.0,
        description="Порог температуры (°C) для детекции перегрева",
    )
    enable_hypotheses_check: bool = Field(
        default=True,
        description="Флаг активации автоматической проверки системных гипотез",
    )


class CorrelationMatrixItem(BaseModel):
    """Элемент матрицы корреляции между парой метрик."""

    metric_a: str = Field(description="Идентификатор первой метрики")
    metric_b: str = Field(description="Идентификатор второй метрики")
    coefficient: float = Field(description="Коэффициент корреляции Пирсона (-1.0 ... 1.0)")
    sample_size: int = Field(description="Число общих точек временного ряда")
    interpretation: str = Field(description="Текстовая интерпретация взаимосвязи")


class HypothesisResult(BaseModel):
    """Результат проверки аналитической гипотезы о поведении системы."""

    hypothesis_id: str = Field(description="Уникальный идентификатор гипотезы")
    title: str = Field(description="Краткое название гипотезы")
    description: str = Field(description="Подробная формулировка гипотезы")
    confirmed: bool = Field(description="Подтверждена ли гипотеза на основе собранных данных")
    confidence: float = Field(description="Уровень уверенности (0.0 - 1.0)")
    evidence: List[str] = Field(default_factory=list, description="Список подтверждающих или опровергающих фактов")
    recommendation: Optional[str] = Field(default=None, description="Практическая рекомендация по устранению проблемы")


class DeepResearchReport(BaseModel):
    """Расширенный отчет глубокого исследования телеметрии."""

    report_id: str = Field(description="Уникальный идентификатор отчета исследования")
    generated_at: str = Field(description="Время формирования отчета (ISO 8601)")
    base_report: TelemetryResearchReport = Field(description="Базовый отчет статистического анализа телеметрии")
    correlations: List[CorrelationMatrixItem] = Field(
        default_factory=list,
        description="Матрица корреляций между ключевыми системными метриками",
    )
    hypotheses: List[HypothesisResult] = Field(
        default_factory=list,
        description="Результаты автоматической проверки гипотез производительности",
    )
    investigation_summary: str = Field(description="Сводное экспертное заключение исследования")
    actionable_recommendations: List[str] = Field(
        default_factory=list,
        description="Список практических рекомендаций по оптимизации и обслуживанию системы",
    )
