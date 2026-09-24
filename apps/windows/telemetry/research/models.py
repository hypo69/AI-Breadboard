# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Telemetry Research and Visualization Models
# =============================================================================
# Description:
#   Pydantic модели данных для анализа, статистического профилирования
#   и генерации графиков из логов системной и аппаратной телеметрии.
#
# File: models.py
# Project: ai-breadboard
# Package: apps.windows.telemetry.research
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модели данных для исследования телеметрии и построения графиков."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MetricPoint(BaseModel):
    """Единичная точка временного ряда для метрики."""

    timestamp: str = Field(..., description="Временная метка точки (ISO-8601 или formatted)")
    value: float = Field(..., description="Числовое значение метрики")
    label: Optional[str] = Field(default=None, description="Опциональная подпись или тег")


class TimeSeriesDataset(BaseModel):
    """Набор данных временного ряда для графика."""

    name: str = Field(..., description="Имя метрики или серии данных")
    unit: str = Field(default="%", description="Единица измерения (%, MB, °C, MB/s, ops/s)")
    points: List[MetricPoint] = Field(default_factory=list, description="Список точек временного ряда")
    color: Optional[str] = Field(default=None, description="HEX-код цвета серии для визуализации")


class AnomalyEvent(BaseModel):
    """Зафиксированная аномалия или всплеск нагрузки в логах."""

    timestamp: str = Field(..., description="Время фиксации аномалии")
    metric: str = Field(..., description="Название метрики с аномалией")
    value: float = Field(..., description="Фактическое значение в момент всплеска")
    threshold: float = Field(..., description="Пороговое или нормальное значение")
    severity: str = Field(default="warning", description="Уровень критичности (info, warning, critical)")
    description: str = Field(..., description="Понятное описание выявленной проблемы")


class MetricStats(BaseModel):
    """Сводная описательная статистика по метрике (EDA)."""

    count: int = Field(default=0, description="Количество замеров")
    min_val: float = Field(default=0.0, description="Минимальное значение")
    max_val: float = Field(default=0.0, description="Максимальное значение")
    avg_val: float = Field(default=0.0, description="Среднее арифметическое значение")
    median_val: float = Field(default=0.0, description="Медианное значение")
    p95_val: float = Field(default=0.0, description="95-й перцентиль")
    std_dev: float = Field(default=0.0, description="Стандартное отклонение")
    unit: str = Field(default="%", description="Единица измерения")


class DeviceEventSummary(BaseModel):
    """Сводная информация по событиям устройств (флаппинг, отключения, сбои)."""

    total_events: int = Field(default=0, description="Всего событий устройств")
    error_count: int = Field(default=0, description="Количество событий со сбоями")
    by_category: Dict[str, int] = Field(default_factory=dict, description="Распределение по категориям устройств")
    by_event_type: Dict[str, int] = Field(default_factory=dict, description="Распределение по типам событий")
    flapping_devices: List[str] = Field(default_factory=list, description="Список устройств с частыми переподключениями")


class ChartConfig(BaseModel):
    """Конфигурация графика для фронтенда / Chart.js."""

    id: str = Field(..., description="Уникальный идентификатор графика")
    title: str = Field(..., description="Заголовок графика")
    chart_type: str = Field(default="line", description="Тип графика (line, bar, doughnut, radar, heatmap)")
    labels: List[str] = Field(default_factory=list, description="Подписи оси X (временные метки)")
    datasets: List[Dict[str, Any]] = Field(default_factory=list, description="Массив датасетов с данными и стилями")
    y_axis_label: str = Field(default="", description="Подпись оси Y")
    description: Optional[str] = Field(default=None, description="Описание или аналитические выводы по графику")


class TelemetryResearchReport(BaseModel):
    """Итоговый отчет исследования логов телеметрии."""

    report_id: str = Field(..., description="Идентификатор отчета исследования")
    generated_at: str = Field(..., description="Время формирования отчета")
    records_analyzed: int = Field(default=0, description="Количество проанализированных записей логов")
    time_window_start: Optional[str] = Field(default=None, description="Начало исследуемого временного окна")
    time_window_end: Optional[str] = Field(default=None, description="Окончание исследуемого временного окна")
    statistics: Dict[str, MetricStats] = Field(default_factory=dict, description="Статистические профили метрик")
    anomalies: List[AnomalyEvent] = Field(default_factory=list, description="Список выявленных аномалий")
    device_summary: DeviceEventSummary = Field(default_factory=DeviceEventSummary, description="Сводка событий устройств")
    charts: List[ChartConfig] = Field(default_factory=list, description="Список сгенерированных графиков")
    health_score: float = Field(default=100.0, description="Итоговый индекс здоровья системы (0-100)")
    summary_conclusions: List[str] = Field(default_factory=list, description="Ключевые аналитические выводы исследования")
