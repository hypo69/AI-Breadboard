# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Telemetry Chart and Visualization Generator
# =============================================================================
# Description:
#   Генератор интерактивных графиков, векторных SVG-диаграмм и автономных
#   HTML-дашбордов для визуализации результатов исследования телеметрии.
#
# Examples:
#   >>> from apps.windows.telemetry.research.charts import TelemetryChartGenerator
#   >>> generator = TelemetryChartGenerator()
#   >>> configs = generator.generate_chart_configs(time_series, report)
#   >>> html_page = generator.render_html_dashboard(report)
#
# File: charts.py
# Project: ai-breadboard
# Package: apps.windows.telemetry.research
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Генератор графиков и HTML/SVG визуализаций телеметрии."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from apps.windows.telemetry.research.models import (
    ChartConfig,
    DeviceEventSummary,
    MetricStats,
    TelemetryResearchReport,
    TimeSeriesDataset,
)


class TelemetryChartGenerator:
    """Генератор графиков и визуальных отчетов телеметрии."""

    def generate_chart_configs(
        self,
        time_series: Dict[str, TimeSeriesDataset],
        report: TelemetryResearchReport,
    ) -> List[ChartConfig]:
        """Сформировать стандартный набор конфигураций графиков для отчета.

        Args:
            time_series: Словарь извлеченных временных рядов.
            report: Отчет исследования.

        Returns:
            List[ChartConfig]: Список спецификаций графиков.
        """
        charts: List[ChartConfig] = []

        # 1. График утилизации ресурсов (CPU, RAM, GPU)
        res_keys = [k for k in ("cpu_load", "ram_used_percent", "gpu_load") if k in time_series]
        if res_keys:
            labels, datasets = self._merge_series_for_chart(time_series, res_keys)
            charts.append(
                ChartConfig(
                    id="chart_resource_utilization",
                    title="Утилизация ресурсов (CPU, RAM, GPU)",
                    chart_type="line",
                    labels=labels,
                    datasets=datasets,
                    y_axis_label="Загрузка (%)",
                    description="Динамика потребления вычислительных ресурсов системы во времени.",
                )
            )

        # 2. График температурного режима
        temp_keys = [k for k in ("cpu_temp", "gpu_temp") if k in time_series]
        if temp_keys:
            labels, datasets = self._merge_series_for_chart(time_series, temp_keys)
            charts.append(
                ChartConfig(
                    id="chart_temperatures",
                    title="Температурный профиль оборудования",
                    chart_type="line",
                    labels=labels,
                    datasets=datasets,
                    y_axis_label="Температура (°C)",
                    description="Мониторинг нагрева процессора и графического ускорителя.",
                )
            )

        # 3. График дискового ввода-вывода (I/O Throughput)
        disk_keys = [k for k in ("disk_read_mb_s", "disk_write_mb_s") if k in time_series]
        if disk_keys:
            labels, datasets = self._merge_series_for_chart(time_series, disk_keys)
            charts.append(
                ChartConfig(
                    id="chart_disk_io",
                    title="Пропускная способность дисковой подсистемы",
                    chart_type="line",
                    labels=labels,
                    datasets=datasets,
                    y_axis_label="Скорость (MB/s)",
                    description="Потоки чтения и записи на накопителях.",
                )
            )

        # 4. Распределение аппаратных событий по категориям
        if report.device_summary.by_category:
            cat_labels = list(report.device_summary.by_category.keys())
            cat_data = [report.device_summary.by_category[k] for k in cat_labels]
            charts.append(
                ChartConfig(
                    id="chart_device_events",
                    title="Распределение событий устройств",
                    chart_type="doughnut",
                    labels=cat_labels,
                    datasets=[
                        {
                            "label": "События",
                            "data": cat_data,
                            "backgroundColor": ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#06B6D4"],
                        }
                    ],
                    y_axis_label="Количество событий",
                    description="Структура активности и сбоев подключенного оборудования.",
                )
            )

        # 5. Сводная гистограмма статистических перцентилей (EDA)
        if report.statistics:
            stat_labels = list(report.statistics.keys())
            avg_vals = [report.statistics[k].avg_val for k in stat_labels]
            p95_vals = [report.statistics[k].p95_val for k in stat_labels]
            max_vals = [report.statistics[k].max_val for k in stat_labels]

            charts.append(
                ChartConfig(
                    id="chart_eda_stats",
                    title="Сравнительный профиль метрик (Avg, p95, Max)",
                    chart_type="bar",
                    labels=stat_labels,
                    datasets=[
                        {"label": "Среднее (Avg)", "data": avg_vals, "backgroundColor": "#3B82F6"},
                        {"label": "95-й перцентиль (p95)", "data": p95_vals, "backgroundColor": "#F59E0B"},
                        {"label": "Максимум (Max)", "data": max_vals, "backgroundColor": "#EF4444"},
                    ],
                    y_axis_label="Значение",
                    description="Сравнение типичных и пиковых нагрузок по ключевым показателям.",
                )
            )

        return charts

    def _merge_series_for_chart(
        self,
        time_series: Dict[str, TimeSeriesDataset],
        keys: List[str],
        max_points: int = 100,
    ) -> tuple[List[str], List[Dict[str, Any]]]:
        """Свести несколько временных рядов в синхронизированные списки для графика."""
        all_timestamps = set()
        for k in keys:
            for pt in time_series[k].points:
                all_timestamps.add(pt.timestamp)

        sorted_ts = sorted(list(all_timestamps))
        
        # Прореживание точек если выборка слишком велика
        if len(sorted_ts) > max_points:
            step = len(sorted_ts) // max_points
            sample_ts = sorted_ts[::step]
        else:
            sample_ts = sorted_ts

        # Форматирование подписей оси X
        labels = [self._format_ts_label(t) for t in sample_ts]

        datasets = []
        for k in keys:
            ds = time_series[k]
            pt_dict = {p.timestamp: p.value for p in ds.points}
            data_points = [pt_dict.get(t, None) for t in sample_ts]

            datasets.append(
                {
                    "label": f"{ds.name} ({ds.unit})",
                    "data": data_points,
                    "borderColor": ds.color or "#3B82F6",
                    "backgroundColor": (ds.color or "#3B82F6") + "22",
                    "fill": False,
                    "tension": 0.3,
                }
            )

        return labels, datasets

    @staticmethod
    def _format_ts_label(iso_ts: str) -> str:
        """Сформировать короткую человекочитаемую подпись времени."""
        try:
            dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
            return dt.strftime("%H:%M:%S")
        except Exception:
            return iso_ts.split("T")[-1][:8] if "T" in iso_ts else iso_ts[-8:]

    def render_svg_chart(self, chart: ChartConfig, width: int = 800, height: int = 400) -> str:
        """Сгенерировать автономный векторный SVG график.

        Args:
            chart: Конфигурация графика.
            width: Ширина SVG холста в пикселях.
            height: Высота SVG холста в пикселях.

        Returns:
            str: XML-строка с SVG графиком.
        """
        padding = 50
        graph_w = width - 2 * padding
        graph_h = height - 2 * padding

        lines_svg = []
        # Отрисовка рамки и сетки
        lines_svg.append(f'<rect width="{width}" height="{height}" fill="#1E293B" rx="8" />')
        lines_svg.append(f'<text x="{width//2}" y="30" fill="#F8FAFC" font-size="16" font-family="sans-serif" font-weight="bold" text-anchor="middle">{chart.title}</text>')

        # Собираем все числовые значения для масштаба
        all_vals = []
        for ds in chart.datasets:
            for v in ds.get("data", []):
                if v is not None and isinstance(v, (int, float)):
                    all_vals.append(v)

        max_v = max(all_vals) if all_vals else 100.0
        min_v = 0.0
        val_range = max(1.0, max_v - min_v)

        # Сетка по оси Y
        for i in range(5):
            y_pos = padding + graph_h - int((i / 4.0) * graph_h)
            grid_val = round(min_v + (i / 4.0) * val_range, 1)
            lines_svg.append(f'<line x1="{padding}" y1="{y_pos}" x2="{width-padding}" y2="{y_pos}" stroke="#334155" stroke-dasharray="4" />')
            lines_svg.append(f'<text x="{padding - 10}" y="{y_pos + 4}" fill="#94A3B8" font-size="11" font-family="sans-serif" text-anchor="end">{grid_val}</text>')

        # Линии графиков
        n_points = len(chart.labels)
        if n_points > 1:
            x_step = graph_w / (n_points - 1)
            for ds in chart.datasets:
                color = ds.get("borderColor", "#38BDF8")
                points_str = []
                for idx, v in enumerate(ds.get("data", [])):
                    if v is not None:
                        x = padding + idx * x_step
                        norm_y = (v - min_v) / val_range
                        y = padding + graph_h - (norm_y * graph_h)
                        points_str.append(f"{x:.1f},{y:.1f}")
                        lines_svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{color}" />')

                if points_str:
                    polyline = " ".join(points_str)
                    lines_svg.append(f'<polyline fill="none" stroke="{color}" stroke-width="2.5" points="{polyline}" />')

        content = "\n".join(lines_svg)
        return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">\n{content}\n</svg>'

    def render_html_dashboard(self, report: TelemetryResearchReport) -> str:
        """Сгенерировать автономный интерактивный HTML-дашборд с графиками.

        Args:
            report: Отчет исследования с графиками и статистикой.

        Returns:
            str: Полноценная HTML-страница с интерактивными графиками.
        """
        charts_json = json.dumps([c.model_dump() for c in report.charts], ensure_ascii=False)
        stats_json = json.dumps({k: s.model_dump() for k, s in report.statistics.items()}, ensure_ascii=False)

        score_color = "#10B981" if report.health_score >= 85 else ("#F59E0B" if report.health_score >= 60 else "#EF4444")

        anomalies_rows = ""
        for a in report.anomalies:
            badge_cls = "badge-danger" if a.severity == "critical" else "badge-warning"
            anomalies_rows += f"""
            <tr>
                <td><span class="badge {badge_cls}">{a.severity.upper()}</span></td>
                <td>{a.timestamp}</td>
                <td><strong>{a.metric}</strong></td>
                <td>{a.value} (порог: {a.threshold})</td>
                <td>{a.description}</td>
            </tr>
            """

        conclusions_list = "".join(f"<li>{c}</li>" for c in report.summary_conclusions)

        return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI-Breadboard: Исследование телеметрии #{report.report_id}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --bg: #0F172A;
            --surface: #1E293B;
            --surface-hover: #334155;
            --border: #475569;
            --text-main: #F8FAFC;
            --text-muted: #94A3B8;
            --primary: #38BDF8;
            --success: #10B981;
            --warning: #F59E0B;
            --danger: #EF4444;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text-main);
            padding: 24px;
            line-height: 1.5;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
            padding-bottom: 20px;
            margin-bottom: 24px;
        }}
        .health-card {{
            background: var(--surface);
            padding: 16px 24px;
            border-radius: 12px;
            border-left: 6px solid {score_color};
            text-align: center;
        }}
        .health-value {{
            font-size: 36px;
            font-weight: 800;
            color: {score_color};
        }}
        .grid-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .card {{
            background: var(--surface);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid var(--border);
        }}
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 24px;
            margin-bottom: 24px;
        }}
        .chart-container {{
            background: var(--surface);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid var(--border);
            position: relative;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 12px;
        }}
        th, td {{
            padding: 10px 14px;
            text-align: left;
            border-bottom: 1px solid var(--border);
            font-size: 14px;
        }}
        th {{ color: var(--text-muted); font-weight: 600; }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: bold;
        }}
        .badge-danger {{ background: rgba(239, 68, 68, 0.2); color: #F87171; }}
        .badge-warning {{ background: rgba(245, 158, 11, 0.2); color: #FBBF24; }}
        ul {{ padding-left: 20px; }}
        li {{ margin-bottom: 8px; }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>📊 Исследование телеметрии Windows</h1>
            <p style="color: var(--text-muted);">Отчет: {report.report_id} | Создан: {report.generated_at}</p>
        </div>
        <div class="health-card">
            <div style="font-size: 13px; color: var(--text-muted); text-transform: uppercase;">Индекс здоровья</div>
            <div class="health-value">{report.health_score}%</div>
        </div>
    </div>

    <div class="grid-cards">
        <div class="card">
            <h3 style="color: var(--primary); margin-bottom: 8px;">📋 Объем выборки</h3>
            <p><strong>Записей в логах:</strong> {report.records_analyzed}</p>
            <p><strong>Период:</strong> {report.time_window_start or 'N/A'} — {report.time_window_end or 'N/A'}</p>
        </div>
        <div class="card">
            <h3 style="color: var(--warning); margin-bottom: 8px;">⚠️ Аномалии и сбои</h3>
            <p><strong>Обнаружено аномалий:</strong> {len(report.anomalies)}</p>
            <p><strong>Ошибок устройств:</strong> {report.device_summary.error_count}</p>
        </div>
        <div class="card">
            <h3 style="color: var(--success); margin-bottom: 8px;">💡 Выводы исследования</h3>
            <ul>{conclusions_list}</ul>
        </div>
    </div>

    <h2 style="margin-bottom: 16px;">📈 Графики телеметрии</h2>
    <div class="charts-grid" id="chartsContainer"></div>

    <div class="card" style="margin-top: 24px;">
        <h2 style="margin-bottom: 12px;">🚨 Зафиксированные аномалии и выбросы</h2>
        {f"<table><thead><tr><th>Уровень</th><th>Время</th><th>Метрика</th><th>Значение</th><th>Описание</th></tr></thead><tbody>{anomalies_rows}</tbody></table>" if report.anomalies else "<p style='color: var(--text-muted);'>Аномалий за исследуемый период не выявлено.</p>"}
    </div>

    <script>
        const chartConfigs = {charts_json};
        const container = document.getElementById('chartsContainer');

        chartConfigs.forEach((cfg) => {{
            const wrapper = document.createElement('div');
            wrapper.className = 'chart-container';
            wrapper.innerHTML = `
                <h3 style="margin-bottom: 4px;">${{cfg.title}}</h3>
                <p style="color: var(--text-muted); font-size: 13px; margin-bottom: 16px;">${{cfg.description || ''}}</p>
                <canvas id="${{cfg.id}}"></canvas>
            `;
            container.appendChild(wrapper);

            const ctx = document.getElementById(cfg.id).getContext('2d');
            new Chart(ctx, {{
                type: cfg.chart_type,
                data: {{
                    labels: cfg.labels,
                    datasets: cfg.datasets
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {{
                        legend: {{ labels: {{ color: '#F8FAFC' }} }}
                    }},
                    scales: cfg.chart_type === 'doughnut' ? {{}} : {{
                        x: {{ ticks: {{ color: '#94A3B8' }}, grid: {{ color: '#334155' }} }},
                        y: {{ ticks: {{ color: '#94A3B8' }}, grid: {{ color: '#334155' }}, title: {{ display: true, text: cfg.y_axis_label, color: '#94A3B8' }} }}
                    }}
                }}
            }});
        }});
    </script>
</body>
</html>
"""
