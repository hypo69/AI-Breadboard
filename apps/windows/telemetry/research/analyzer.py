# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Telemetry Research and Statistical Analytics Engine
# =============================================================================
# Description:
#   Аналитический движок для исследования логов телеметрии: вычисление
#   описательной статистики, детектирование всплесков и аномалий, расчет
#   индекса здоровья системы и агрегация временных рядов.
#
# Examples:
#   >>> from apps.windows.telemetry.research.analyzer import TelemetryResearcher
#   >>> researcher = TelemetryResearcher()
#   >>> report = researcher.analyze(records)
#
# File: analyzer.py
# Project: ai-breadboard
# Package: apps.windows.telemetry.research
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Аналитический движок исследования логов телеметрии."""

from __future__ import annotations

import math
import statistics
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

from logger import logger
from apps.windows.telemetry.research.models import (
    AnomalyEvent,
    ChartConfig,
    DeviceEventSummary,
    MetricPoint,
    MetricStats,
    TelemetryResearchReport,
    TimeSeriesDataset,
)
from apps.windows.telemetry.research.extractor import TelemetryDataExtractor


class TelemetryResearcher:
    """Исследователь и аналитик логов системной и аппаратной телеметрии."""

    def __init__(self, extractor: Optional[TelemetryDataExtractor] = None) -> None:
        """Инициализация аналитического движка.

        Args:
            extractor: Экземпляр загрузчика данных телеметрии.
        """
        self.extractor = extractor or TelemetryDataExtractor()

    def analyze(
        self,
        source: Optional[Union[str, List[Dict[str, Any]]]] = None,
    ) -> TelemetryResearchReport:
        """Провести глубокое исследование логов телеметрии и сформировать отчет.

        Args:
            source: Источник данных (директория, путь к файлу или список записей).

        Returns:
            TelemetryResearchReport: Комплексный отчет исследования.
        """
        records = self.extractor.load_all_records(source)
        logger.info(f"Загружено {len(records)} записей телеметрии для исследования.")

        now_str = datetime.now(timezone.utc).isoformat()
        if not records:
            return TelemetryResearchReport(
                report_id=f"rep-{uuid.uuid4().hex[:8]}",
                generated_at=now_str,
                records_analyzed=0,
                health_score=100.0,
                summary_conclusions=["Логи телеметрии не содержат записей для анализа."],
            )

        # 1. Извлечение временных рядов метрик
        time_series = self._extract_time_series(records)

        # 2. Вычисление статистики EDA (min, max, avg, median, p95, std)
        stats_map: Dict[str, MetricStats] = {}
        for metric_name, ds in time_series.items():
            vals = [pt.value for pt in ds.points]
            if vals:
                stats_map[metric_name] = self._calculate_stats(vals, ds.unit)

        # 3. Анализ событий устройств (ошибки, флаппинг)
        device_summary = self._analyze_device_events(records)

        # 4. Поиск всплесков и аномалий
        anomalies = self._detect_anomalies(time_series, device_summary)

        # 5. Расчет индекса здоровья системы (Health Score)
        health_score = self._compute_health_score(stats_map, anomalies, device_summary)

        # 6. Формирование аналитических выводов
        conclusions = self._generate_conclusions(stats_map, anomalies, device_summary, health_score)

        # Временное окно
        ts_list = [r.get("timestamp") for r in records if r.get("timestamp")]
        start_time = ts_list[0] if ts_list else None
        end_time = ts_list[-1] if ts_list else None

        return TelemetryResearchReport(
            report_id=f"rep-{uuid.uuid4().hex[:8]}",
            generated_at=now_str,
            records_analyzed=len(records),
            time_window_start=start_time,
            time_window_end=end_time,
            statistics=stats_map,
            anomalies=anomalies,
            device_summary=device_summary,
            health_score=health_score,
            summary_conclusions=conclusions,
        )

    def _extract_time_series(self, records: List[Dict[str, Any]]) -> Dict[str, TimeSeriesDataset]:
        """Извлечь структурированные временные ряды из разнородных записей."""
        datasets: Dict[str, TimeSeriesDataset] = {
            "cpu_load": TimeSeriesDataset(name="CPU Load", unit="%", color="#3B82F6"),
            "ram_used_percent": TimeSeriesDataset(name="RAM Usage", unit="%", color="#10B981"),
            "gpu_load": TimeSeriesDataset(name="GPU Load", unit="%", color="#8B5CF6"),
            "cpu_temp": TimeSeriesDataset(name="CPU Temperature", unit="°C", color="#EF4444"),
            "gpu_temp": TimeSeriesDataset(name="GPU Temperature", unit="°C", color="#F59E0B"),
            "disk_read_mb_s": TimeSeriesDataset(name="Disk Read", unit="MB/s", color="#06B6D4"),
            "disk_write_mb_s": TimeSeriesDataset(name="Disk Write", unit="MB/s", color="#EC4899"),
            "net_recv_mb_s": TimeSeriesDataset(name="Network Recv", unit="MB/s", color="#6366F1"),
            "net_sent_mb_s": TimeSeriesDataset(name="Network Sent", unit="MB/s", color="#14B8A6"),
        }

        for r in records:
            ts = r.get("timestamp", "")

            # Извлечение из объектов SystemSnapshot / collector
            cpu = r.get("cpu") or {}
            if isinstance(cpu, dict):
                val = cpu.get("total_percent")
                if val is not None:
                    datasets["cpu_load"].points.append(MetricPoint(timestamp=ts, value=float(val)))
                temp = cpu.get("temperature_celsius")
                if temp is not None:
                    datasets["cpu_temp"].points.append(MetricPoint(timestamp=ts, value=float(temp)))

            mem = r.get("memory") or {}
            if isinstance(mem, dict):
                val = mem.get("percent")
                if val is not None:
                    datasets["ram_used_percent"].points.append(MetricPoint(timestamp=ts, value=float(val)))

            gpu = r.get("gpu") or {}
            if isinstance(gpu, dict):
                val = gpu.get("load_percent")
                if val is not None:
                    datasets["gpu_load"].points.append(MetricPoint(timestamp=ts, value=float(val)))
                temp = gpu.get("temperature_celsius")
                if temp is not None:
                    datasets["gpu_temp"].points.append(MetricPoint(timestamp=ts, value=float(temp)))

            # Диск I/O
            disk_io = r.get("disk_io") or {}
            if isinstance(disk_io, dict):
                rb = disk_io.get("read_bytes_per_sec", 0.0)
                wb = disk_io.get("write_bytes_per_sec", 0.0)
                if rb > 0:
                    datasets["disk_read_mb_s"].points.append(MetricPoint(timestamp=ts, value=round(rb / (1024 * 1024), 2)))
                if wb > 0:
                    datasets["disk_write_mb_s"].points.append(MetricPoint(timestamp=ts, value=round(wb / (1024 * 1024), 2)))

            # Прямые замеры сенсоров
            if "sensor_type" in r and "value" in r:
                st = str(r.get("sensor_type")).lower()
                val = float(r.get("value", 0.0))
                if "cpu" in st and "load" in st:
                    datasets["cpu_load"].points.append(MetricPoint(timestamp=ts, value=val))
                elif "cpu" in st and "temp" in st:
                    datasets["cpu_temp"].points.append(MetricPoint(timestamp=ts, value=val))
                elif "gpu" in st and "load" in st:
                    datasets["gpu_load"].points.append(MetricPoint(timestamp=ts, value=val))
                elif "ram" in st or "mem" in st:
                    datasets["ram_used_percent"].points.append(MetricPoint(timestamp=ts, value=val))

        # Оставляем только непустые датасеты
        return {k: ds for k, ds in datasets.items() if ds.points}

    def _calculate_stats(self, values: List[float], unit: str = "%") -> MetricStats:
        """Рассчитать описательную статистику по массиву значений."""
        if not values:
            return MetricStats(unit=unit)

        sorted_vals = sorted(values)
        n = len(sorted_vals)
        min_v = sorted_vals[0]
        max_v = sorted_vals[-1]
        avg_v = sum(sorted_vals) / n
        median_v = statistics.median(sorted_vals)
        
        # 95-й перцентиль
        p95_idx = int(math.ceil(0.95 * n)) - 1
        p95_v = sorted_vals[min(p95_idx, n - 1)]

        std_v = statistics.stdev(sorted_vals) if n > 1 else 0.0

        return MetricStats(
            count=n,
            min_val=round(min_v, 2),
            max_val=round(max_v, 2),
            avg_val=round(avg_v, 2),
            median_val=round(median_v, 2),
            p95_val=round(p95_v, 2),
            std_dev=round(std_v, 2),
            unit=unit,
        )

    def _analyze_device_events(self, records: List[Dict[str, Any]]) -> DeviceEventSummary:
        """Собрать агрегированную статистику по аппаратным событиям и сбоям."""
        summary = DeviceEventSummary()
        flapping_set = set()

        for r in records:
            # Проверяем, является ли запись событием устройства
            ev_type = r.get("event_type")
            dev_id = r.get("device_instance_id") or r.get("friendly_name")
            if not ev_type and not dev_id:
                continue

            summary.total_events += 1

            if ev_type:
                summary.by_event_type[ev_type] = summary.by_event_type.get(ev_type, 0) + 1

            cat = r.get("category") or r.get("device_class") or "Другое"
            summary.by_category[cat] = summary.by_category.get(cat, 0) + 1

            if r.get("has_problem") or r.get("problem_code", 0) > 0:
                summary.error_count += 1

            flap_count = r.get("flapping_count_in_window", 0)
            if flap_count > 0 and dev_id:
                flapping_set.add(f"{dev_id} (всплесков: {flap_count})")

        summary.flapping_devices = list(flapping_set)
        return summary

    def _detect_anomalies(
        self,
        time_series: Dict[str, TimeSeriesDataset],
        device_summary: DeviceEventSummary,
    ) -> List[AnomalyEvent]:
        """Обнаружить аномальные значения метрик и сбои оборудования."""
        anomalies: List[AnomalyEvent] = []

        # 1. Аномалии загрузки CPU (>90%)
        if "cpu_load" in time_series:
            for pt in time_series["cpu_load"].points:
                if pt.value >= 90.0:
                    anomalies.append(
                        AnomalyEvent(
                            timestamp=pt.timestamp,
                            metric="CPU Load",
                            value=pt.value,
                            threshold=90.0,
                            severity="critical" if pt.value >= 98.0 else "warning",
                            description=f"Пиковая нагрузка процессора достигла {pt.value}%",
                        )
                    )

        # 2. Аномалии памяти RAM (>90%)
        if "ram_used_percent" in time_series:
            for pt in time_series["ram_used_percent"].points:
                if pt.value >= 90.0:
                    anomalies.append(
                        AnomalyEvent(
                            timestamp=pt.timestamp,
                            metric="RAM Usage",
                            value=pt.value,
                            threshold=90.0,
                            severity="critical" if pt.value >= 95.0 else "warning",
                            description=f"Высокое потребление оперативной памяти: {pt.value}%",
                        )
                    )

        # 3. Аномалии температуры CPU (>80°C)
        if "cpu_temp" in time_series:
            for pt in time_series["cpu_temp"].points:
                if pt.value >= 80.0:
                    anomalies.append(
                        AnomalyEvent(
                            timestamp=pt.timestamp,
                            metric="CPU Temp",
                            value=pt.value,
                            threshold=80.0,
                            severity="critical" if pt.value >= 90.0 else "warning",
                            description=f"Перегрев процессора: {pt.value}°C",
                        )
                    )

        # 4. Аномалии устройств
        if device_summary.error_count > 0:
            anomalies.append(
                AnomalyEvent(
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    metric="Device Failures",
                    value=float(device_summary.error_count),
                    threshold=0.0,
                    severity="warning",
                    description=f"Зафиксировано {device_summary.error_count} сбоев в работе подключенных устройств",
                )
            )

        # Ограничиваем список аномалий последними 50 записями
        return anomalies[-50:]

    def _compute_health_score(
        self,
        stats_map: Dict[str, MetricStats],
        anomalies: List[AnomalyEvent],
        device_summary: DeviceEventSummary,
    ) -> float:
        """Рассчитать интегральный индекс здоровья системы от 0.0 до 100.0."""
        score = 100.0

        # Штраф за высокую среднюю нагрузку CPU
        if "cpu_load" in stats_map:
            avg_cpu = stats_map["cpu_load"].avg_val
            if avg_cpu > 70.0:
                score -= min(30.0, (avg_cpu - 70.0) * 1.0)

        # Штраф за память
        if "ram_used_percent" in stats_map:
            avg_ram = stats_map["ram_used_percent"].avg_val
            if avg_ram > 80.0:
                score -= min(25.0, (avg_ram - 80.0) * 1.25)

        # Штраф за перегрев
        if "cpu_temp" in stats_map:
            max_temp = stats_map["cpu_temp"].max_val
            if max_temp > 80.0:
                score -= min(20.0, (max_temp - 80.0) * 1.5)

        # Штраф за сбои устройств
        if device_summary.error_count > 0:
            score -= min(25.0, device_summary.error_count * 5.0)

        # Штраф за критические аномалии
        crit_count = sum(1 for a in anomalies if a.severity == "critical")
        score -= min(20.0, crit_count * 4.0)

        return max(0.0, round(score, 1))

    def _generate_conclusions(
        self,
        stats_map: Dict[str, MetricStats],
        anomalies: List[AnomalyEvent],
        device_summary: DeviceEventSummary,
        health_score: float,
    ) -> List[str]:
        """Сформировать текстовые выводы и рекомендации исследования."""
        conclusions = []

        if health_score >= 90.0:
            conclusions.append("Состояние системы стабильное: параметры утилизации ресурсов находятся в допустимых границах.")
        elif health_score >= 70.0:
            conclusions.append("Состояние системы удовлетворительное, но выявлены эпизодические пики нагрузки.")
        else:
            conclusions.append("Внимание: состояние системы деградировало из-за высокой утилизации ресурсов или сбоев оборудования.")

        if "cpu_load" in stats_map:
            cpu = stats_map["cpu_load"]
            conclusions.append(f"Процессор (CPU): средняя нагрузка {cpu.avg_val}%, пик {cpu.max_val}% (p95: {cpu.p95_val}%).")

        if "ram_used_percent" in stats_map:
            ram = stats_map["ram_used_percent"]
            conclusions.append(f"Оперативная память (RAM): среднее использование {ram.avg_val}%, максимум {ram.max_val}%.")

        if device_summary.error_count > 0:
            conclusions.append(f"Обнаружено {device_summary.error_count} аппаратных сбоев или проблемных устройств.")

        if device_summary.flapping_devices:
            conclusions.append(f"Нестабильные устройства (флаппинг): {', '.join(device_summary.flapping_devices)}.")

        return conclusions
