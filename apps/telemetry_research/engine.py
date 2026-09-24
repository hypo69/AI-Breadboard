# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Telemetry Research Analysis and Investigation Engine
# =============================================================================
# Description:
#   Движок глубокого аналитического исследования системной телеметрии:
#   расчет корреляционных связей между подсистемами, проверка гипотез
#   производительности и стабильности оборудования, формирование
#   структурированных рекомендаций и экспертных заключений.
#
# File: engine.py
# Project: ai-breadboard
# Package: apps.telemetry_research
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Аналитический исследовательский движок телеметрии."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from apps.windows.telemetry.research.analyzer import TelemetryResearcher
from apps.windows.telemetry.research.charts import TelemetryChartGenerator
from apps.windows.telemetry.research.extractor import TelemetryDataExtractor
from apps.windows.telemetry.research.models import (
    MetricPoint,
    TelemetryResearchReport,
)
from apps.telemetry_research.models import (
    CorrelationMatrixItem,
    DeepResearchReport,
    HypothesisResult,
    ResearchScenarioRequest,
)
from logger import logger


class TelemetryResearchEngine:
    """Координатор и процессор глубоких исследований данных телеметрии."""

    def __init__(
        self,
        researcher: Optional[TelemetryResearcher] = None,
        extractor: Optional[TelemetryDataExtractor] = None,
        chart_generator: Optional[TelemetryChartGenerator] = None,
    ) -> None:
        """Инициализирует исследовательский движок с DI зависимостями.

        Args:
            researcher: Базовый аналитический движок исследования телеметрии.
            extractor: Загрузчик и парсер логов телеметрии.
            chart_generator: Генератор спецификаций графиков и визуализаций.
        """
        self.extractor = extractor or TelemetryDataExtractor()
        self.researcher = researcher or TelemetryResearcher(extractor=self.extractor)
        self.chart_generator = chart_generator or TelemetryChartGenerator()

    def run_deep_research(
        self,
        scenario: Optional[ResearchScenarioRequest] = None,
    ) -> DeepResearchReport:
        """Выполняет полный цикл исследовательского анализа телеметрии.

        Args:
            scenario: Параметры исследовательского сценария и фильтрации.

        Returns:
            DeepResearchReport: Полный отчет глубокого исследования с корреляциями и гипотезами.
        """
        sc = scenario or ResearchScenarioRequest()
        source = sc.records if sc.records is not None else sc.source_path

        # Загрузка и первичная фильтрация записей
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

        # Выполнение базового статистического анализа
        base_report = self.researcher.analyze(filtered_records)

        # Извлечение синхронизированных временных рядов
        time_series_map = self.researcher._extract_time_series(filtered_records)

        # Генерация конфигураций графиков
        base_report.charts = self.chart_generator.generate_chart_configs(time_series_map, base_report)

        # Вычисление матрицы корреляций
        correlations = self._calculate_correlations(time_series_map)

        # Проверка аналитических гипотез
        hypotheses: List[HypothesisResult] = []
        if sc.enable_hypotheses_check:
            hypotheses = self._evaluate_hypotheses(base_report, time_series_map, correlations)

        # Формирование рекомендаций
        recommendations = self._generate_recommendations(base_report, hypotheses, correlations)

        # Формирование сводного заключения
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
        """Фильтрует записи по временному диапазону и составу подсистем.

        Args:
            records: Список сырых записей.
            start_time: Начало временного интервала.
            end_time: Конец временного интервала.
            subsystems: Список целевых подсистем.

        Returns:
            List[Dict[str, Any]]: Отфильтрованный список записей.
        """
        if not records:
            return []

        start_dt = self._parse_iso_time(start_time) if start_time else None
        end_dt = self._parse_iso_time(end_time) if end_time else None

        result: List[Dict[str, Any]] = []
        for r in records:
            # Проверка времени
            ts_str = r.get("timestamp") or r.get("time") or r.get("created_at")
            if ts_str and (start_dt or end_dt):
                rec_dt = self._parse_iso_time(str(ts_str))
                if rec_dt:
                    if start_dt and rec_dt < start_dt:
                        continue
                    if end_dt and rec_dt > end_dt:
                        continue

            # Проверка подсистем
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
        time_series_map: Dict[str, List[MetricPoint]],
    ) -> List[CorrelationMatrixItem]:
        """Вычисляет коэффициенты корреляции Пирсона между парами системных метрик.

        Args:
            time_series_map: Словарь временных рядов метрик.

        Returns:
            List[CorrelationMatrixItem]: Список рассчитанных корреляций.
        """
        keys = sorted(list(time_series_map.keys()))
        correlations: List[CorrelationMatrixItem] = []

        # Сравниваем пары метрик
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

                # Приводим к одинаковой длине (min length)
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
        time_series_map: Dict[str, List[MetricPoint]],
        correlations: List[CorrelationMatrixItem],
    ) -> List[HypothesisResult]:
        """Проверяет набор стандартных системных гипотез.

        Args:
            report: Базовый отчет телеметрии.
            time_series_map: Временные ряды метрик.
            correlations: Рассчитанные корреляции.

        Returns:
            List[HypothesisResult]: Список проверенных гипотез.
        """
        hypotheses: List[HypothesisResult] = []

        # 1. Гипотеза о терморегулировании и троттлинге CPU
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

        # 2. Гипотеза о дефиците оперативной памяти (RAM Pressure)
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

        # 3. Гипотеза о нестабильности периферийных или системных устройств
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

        # 4. Гипотеза о перегреве или перегрузке GPU
        gpu_temp = report.statistics.get("gpu_temp")
        gpu_load = report.statistics.get("gpu_load")
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
