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
    CorrelationMatrixItem,
    DeepResearchReport,
    DeviceEventSummary,
    HypothesisResult,
    MetricPoint,
    MetricStats,
    ResearchScenarioRequest,
    TelemetryResearchReport,
    TimeSeriesDataset,
)
from apps.windows.telemetry.research.extractor import TelemetryDataExtractor
from apps.windows.telemetry.research.charts import TelemetryChartGenerator



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

    def run_deep_research(
        self,
        scenario: Optional[ResearchScenarioRequest] = None,
        chart_generator: Optional[TelemetryChartGenerator] = None,
    ) -> DeepResearchReport:
        """Выполнить полный цикл исследовательского анализа телеметрии (с корреляциями и гипотезами)."""
        sc = scenario or ResearchScenarioRequest()
        source = sc.records if sc.records is not None else sc.source_path
        c_gen = chart_generator or TelemetryChartGenerator()

        raw_records = self.extractor.load_all_records(source)
        filtered_records = self._filter_records(
            records=raw_records,
            start_time=sc.start_time,
            end_time=sc.end_time,
            subsystems=sc.subsystems,
        )

        logger.info(
            f"Запуск исследования телеметрии: обработано {len(filtered_records)} записей "
            f"(из исходных {len(raw_records)})."
        )

        base_report = self.analyze(filtered_records)
        time_series_map = self._extract_time_series(filtered_records)
        base_report.charts = c_gen.generate_chart_configs(time_series_map, base_report)

        correlations = self._calculate_correlations(time_series_map)

        hypotheses: List[HypothesisResult] = []
        if sc.enable_hypotheses_check:
            hypotheses = self._evaluate_hypotheses(base_report, time_series_map, correlations)

        recommendations = self._generate_recommendations(base_report, hypotheses, correlations)
        summary = self._build_investigation_summary(base_report, hypotheses, len(filtered_records))

        report_id = f"deep_research_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        return DeepResearchReport(
            report_id=report_id,
            generated_at=now_iso,
            base_report=base_report,
            correlations=correlations,
            hypotheses=hypotheses,
            investigation_summary=summary,
            actionable_recommendations=recommendations,
        )

    def _filter_records(
        self,
        records: List[Dict[str, Any]],
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        subsystems: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Фильтрует записи по временному диапазону и составу подсистем."""
        if not records:
            return []

        start_dt = self._parse_iso_time(start_time) if start_time else None
        end_dt = self._parse_iso_time(end_time) if end_time else None

        result: List[Dict[str, Any]] = []
        for r in records:
            ts_str = r.get("timestamp") or r.get("time") or r.get("created_at")
            if ts_str and (start_dt or end_dt):
                rec_dt = self._parse_iso_time(str(ts_str))
                if rec_dt:
                    if start_dt and rec_dt < start_dt:
                        continue
                    if end_dt and rec_dt > end_dt:
                        continue

            if subsystems:
                match_subsystem = False
                for sub in subsystems:
                    sub_lower = sub.lower()
                    if sub_lower in r or any(sub_lower in str(k).lower() for k in r.keys()):
                        match_subsystem = True
                        break
                    if sub_lower == "devices" and ("device_instance_id" in r or "event_type" in r):
                        match_subsystem = True
                        break
                if not match_subsystem:
                    continue

            result.append(r)

        return result

    @staticmethod
    def _parse_iso_time(time_str: Optional[str]) -> Optional[datetime]:
        """Парсит строку даты и времени в ISO формате."""
        if not time_str:
            return None
        clean_str = time_str.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(clean_str)
        except Exception:
            return None

    def _calculate_correlations(
        self,
        time_series_map: Dict[str, TimeSeriesDataset],
    ) -> List[CorrelationMatrixItem]:
        """Вычисляет коэффициенты корреляции Пирсона между парами системных метрик."""
        keys = sorted(list(time_series_map.keys()))
        correlations: List[CorrelationMatrixItem] = []

        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                key_a = keys[i]
                key_b = keys[j]

                ds_a = time_series_map[key_a]
                ds_b = time_series_map[key_b]

                pts_a = ds_a.points if hasattr(ds_a, "points") else ds_a
                pts_b = ds_b.points if hasattr(ds_b, "points") else ds_b

                if not pts_a or not pts_b:
                    continue

                val_a = [p.value if hasattr(p, "value") else float(p[1] if isinstance(p, (list, tuple)) else p) for p in pts_a]
                val_b = [p.value if hasattr(p, "value") else float(p[1] if isinstance(p, (list, tuple)) else p) for p in pts_b]

                min_len = min(len(val_a), len(val_b))
                if min_len < 3:
                    continue

                slice_a = val_a[:min_len]
                slice_b = val_b[:min_len]

                coeff = self._pearson_correlation(slice_a, slice_b)
                if math.isnan(coeff):
                    continue

                interpretation = self._interpret_correlation(coeff, key_a, key_b)

                correlations.append(
                    CorrelationMatrixItem(
                        metric_a=key_a,
                        metric_b=key_b,
                        coefficient=round(coeff, 3),
                        sample_size=min_len,
                        interpretation=interpretation,
                    )
                )

        return sorted(correlations, key=lambda x: abs(x.coefficient), reverse=True)

    @staticmethod
    def _pearson_correlation(x: List[float], y: List[float]) -> float:
        """Вычисляет коэффициент линейной корреляции Пирсона для двух списков чисел."""
        n = len(x)
        if n == 0:
            return 0.0

        mean_x = sum(x) / n
        mean_y = sum(y) / n

        diff_prod = sum((x[k] - mean_x) * (y[k] - mean_y) for k in range(n))
        sq_diff_x = sum((x[k] - mean_x) ** 2 for k in range(n))
        sq_diff_y = sum((y[k] - mean_y) ** 2 for k in range(n))

        denominator = math.sqrt(sq_diff_x * sq_diff_y)
        if denominator == 0.0:
            return 0.0

        return diff_prod / denominator

    @staticmethod
    def _interpret_correlation(coeff: float, metric_a: str, metric_b: str) -> str:
        """Формирует текстовое объяснение коэффициента корреляции."""
        abs_c = abs(coeff)
        direction = "прямая" if coeff > 0 else "обратная"

        if abs_c >= 0.8:
            strength = f"Очень сильная {direction}"
        elif abs_c >= 0.6:
            strength = f"Заметная {direction}"
        elif abs_c >= 0.3:
            strength = f"Умеренная {direction}"
        else:
            strength = f"Слабая {direction}"

        return (
            f"{strength} связь между '{metric_a}' и '{metric_b}' (r={coeff:.2f}). "
            f"{'Изменения происходят синхронно.' if coeff > 0.5 else ''}"
        )

    def _evaluate_hypotheses(
        self,
        report: TelemetryResearchReport,
        time_series_map: Dict[str, TimeSeriesDataset],
        correlations: List[CorrelationMatrixItem],
    ) -> List[HypothesisResult]:
        """Проверяет набор стандартных системных гипотез."""
        hypotheses: List[HypothesisResult] = []

        # 1. Гипотеза о терморегулировании CPU
        cpu_temp_stats = report.statistics.get("cpu_temp")
        cpu_load_stats = report.statistics.get("cpu_load")
        h1_confirmed = False
        h1_evidence: List[str] = []
        h1_conf = 0.5

        if cpu_temp_stats and cpu_temp_stats.max_val >= 82.0:
            h1_confirmed = True
            h1_conf = 0.85
            h1_evidence.append(f"Пиковая температура CPU достигла {cpu_temp_stats.max_val}°C (порог 82°C)")
            if cpu_load_stats:
                h1_evidence.append(f"Средняя загрузка CPU составляла {cpu_load_stats.avg_val:.1f}%")
        else:
            h1_evidence.append("Температуры CPU находятся в пределах нормы (ниже 82°C)")

        hypotheses.append(
            HypothesisResult(
                hypothesis_id="H_CPU_THERMAL_STRESS",
                title="Термический стресс и перегрев CPU",
                description="Проверка риска троттлинга или деградации при высоких температурах процессора.",
                confirmed=h1_confirmed,
                confidence=h1_conf,
                evidence=h1_evidence,
                recommendation="Проверить термопасту, систему охлаждения и отсутствие пыли в радиаторах CPU."
                if h1_confirmed
                else "Температурный режим в норме.",
            )
        )

        # 2. Гипотеза о дефиците RAM
        ram_stats = report.statistics.get("ram_used_percent")
        h2_confirmed = False
        h2_evidence: List[str] = []
        h2_conf = 0.5

        if ram_stats and ram_stats.max_val >= 88.0:
            h2_confirmed = True
            h2_conf = 0.90
            h2_evidence.append(f"Пиковое потребление RAM составило {ram_stats.max_val}% (порог 88%)")
            h2_evidence.append(f"Средняя загрузка RAM: {ram_stats.avg_val:.1f}%")
        else:
            h2_evidence.append("Потребление RAM находится в безопасных пределах (ниже 88%)")

        hypotheses.append(
            HypothesisResult(
                hypothesis_id="H_RAM_PRESSURE",
                title="Дефицит оперативной памяти (RAM Pressure)",
                description="Анализ рисков нехватки оперативной памяти и повышенного использования файла подкачки.",
                confirmed=h2_confirmed,
                confidence=h2_conf,
                evidence=h2_evidence,
                recommendation="Закрыть неиспользуемые фоновые приложения или расширить объем ОЗУ."
                if h2_confirmed
                else "Памяти достаточно для текущей рабочей нагрузки.",
            )
        )

        # 3. Гипотеза о нестабильности оборудования
        dev_sum = report.device_summary
        h3_confirmed = dev_sum.error_count > 0 or len(dev_sum.flapping_devices) > 0
        h3_evidence: List[str] = []
        if h3_confirmed:
            if dev_sum.error_count > 0:
                h3_evidence.append(f"Зафиксировано {dev_sum.error_count} сбоев и ошибок оборудования в логах")
            if dev_sum.flapping_devices:
                h3_evidence.append(f"Обнаружен флаппинг устройств: {', '.join(dev_sum.flapping_devices)}")
        else:
            h3_evidence.append("Ошибок оборудования и флаппинга устройств в исследованный период не обнаружено")

        hypotheses.append(
            HypothesisResult(
                hypothesis_id="H_DEVICE_INSTABILITY",
                title="Нестабильность и сбои оборудования (Hardware Flapping)",
                description="Проверка наличия сбоящих шин, отваливающихся USB/PCI контроллеров или конфликтов драйверов.",
                confirmed=h3_confirmed,
                confidence=0.95 if h3_confirmed else 0.7,
                evidence=h3_evidence,
                recommendation="Проверить подключение кабелей, обновить драйверы сбоящих устройств или заменить порт."
                if h3_confirmed
                else "Оборудование работает стабильно.",
            )
        )

        # 4. Гипотеза о перегреве GPU
        gpu_temp = report.statistics.get("gpu_temp")
        h4_confirmed = False
        h4_evidence: List[str] = []
        if gpu_temp and gpu_temp.max_val >= 83.0:
            h4_confirmed = True
            h4_evidence.append(f"Пиковая температура GPU: {gpu_temp.max_val}°C")
        else:
            h4_evidence.append("Температура GPU в безопасной зоне")

        hypotheses.append(
            HypothesisResult(
                hypothesis_id="H_GPU_THERMAL",
                title="Термическая стабильность графического ускорителя (GPU)",
                description="Оценка температурных режимов графического чипа при нагрузке.",
                confirmed=h4_confirmed,
                confidence=0.85 if h4_confirmed else 0.6,
                evidence=h4_evidence,
                recommendation="Настроить кривую вентиляторов GPU или проверить вентиляцию корпуса."
                if h4_confirmed
                else "GPU работает в штатном тепловом режиме.",
            )
        )

        return hypotheses

    def _generate_recommendations(
        self,
        report: TelemetryResearchReport,
        hypotheses: List[HypothesisResult],
        correlations: List[CorrelationMatrixItem],
    ) -> List[str]:
        """Генерирует практические рекомендации на основе анализа."""
        recs: List[str] = []

        for h in hypotheses:
            if h.confirmed and h.recommendation:
                recs.append(f"[{h.title}]: {h.recommendation}")

        for anom in report.anomalies:
            if anom.severity in ("critical", "high"):
                recs.append(f"[Аномалия {anom.metric}]: {anom.description}")

        if not recs:
            recs.append("Система работает стабильно. Регулярно проводите профилактический аудит телеметрии.")

        return recs

    @staticmethod
    def _build_investigation_summary(
        report: TelemetryResearchReport,
        hypotheses: List[HypothesisResult],
        total_records: int,
    ) -> str:
        """Формирует текстовое резюме проведенного исследования."""
        confirmed_count = sum(1 for h in hypotheses if h.confirmed)
        return (
            f"Исследование завершено. Проанализировано {total_records} записей телеметрии. "
            f"Индекс здоровья системы: {report.health_score}/100. "
            f"Обнаружено аномалий: {len(report.anomalies)}. "
            f"Подтверждено проблемных гипотез: {confirmed_count} из {len(hypotheses)}."
        )

