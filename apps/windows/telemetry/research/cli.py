# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Telemetry Research CLI
# =============================================================================
# Description:
#   Консольная утилита для сбора логов телеметрии, проведения исследования
#   и генерации отчетов с графиками (HTML / SVG / JSON).
#
# Examples:
#   >>> py apps/windows/telemetry/research/cli.py --source logs/telemetry --output dashboard.html
#
# File: cli.py
# Project: ai-breadboard
# Package: apps.windows.telemetry.research
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""CLI интерфейс для исследования логов телеметрии и построения графиков."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Добавляем корень проекта в sys.path при прямом запуске CLI
_root_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))

from logger import logger
from apps.windows.telemetry.research.analyzer import TelemetryResearcher
from apps.windows.telemetry.research.charts import TelemetryChartGenerator


from apps.windows.telemetry.research.models import ResearchScenarioRequest


def parse_args() -> argparse.Namespace:
    """Парсинг аргументов командной строки."""
    parser = argparse.ArgumentParser(
        description="AI-Breadboard: Исследование логов телеметрии и генерация графиков",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--source",
        "-s",
        type=str,
        default=None,
        help="Путь к файлу логов (.json, .jsonl) или директории с логами телеметрии",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Путь для сохранения результата (по умолчанию: telemetry_research_report.html)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["html", "json", "svg", "summary"],
        default="html",
        help="Формат вывода: html, json, svg, summary",
    )
    return parser.parse_args()


def main() -> int:
    """Точка входа CLI."""
    args = parse_args()

    researcher = TelemetryResearcher()
    chart_gen = TelemetryChartGenerator()

    logger.info(f"Запуск исследования логов телеметрии (источник: {args.source or 'системные директории по умолчанию'})...")
    
    if args.format == "summary":
        req = ResearchScenarioRequest(source_path=args.source)
        deep_report = researcher.run_deep_research(scenario=req, chart_generator=chart_gen)
        print("\n" + "=" * 70)
        print(f"🔬 Отчет исследования телеметрии: {deep_report.report_id}")
        print("=" * 70)
        print(f"Дата формирования: {deep_report.generated_at}")
        print(f"Проанализировано записей: {deep_report.base_report.records_analyzed}")
        print(f"Индекс здоровья системы: {deep_report.base_report.health_score}/100")
        print(f"Обнаружено аномалий: {len(deep_report.base_report.anomalies)}")

        print("\n--- Проверенные гипотезы ---")
        for h in deep_report.hypotheses:
            status_icon = "⚠️ [ПОДТВЕРЖДЕНА]" if h.confirmed else "✅ [В НОРМЕ]"
            print(f"{status_icon} {h.title} (уверенность {h.confidence*100:.0f}%)")
            for ev in h.evidence:
                print(f"    • {ev}")

        print("\n--- Рекомендации ---")
        for rec in deep_report.actionable_recommendations:
            print(f"  👉 {rec}")
        print("=" * 70 + "\n")
        return 0

    report = researcher.analyze(args.source)
    records = researcher.extractor.load_all_records(args.source)
    ts_map = researcher._extract_time_series(records)
    report.charts = chart_gen.generate_chart_configs(ts_map, report)

    out_path_str = args.output or ("telemetry_research_report.html" if args.format == "html" else "report.json")
    out_path = Path(out_path_str)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if args.format == "html":
        html_content = chart_gen.render_html_dashboard(report)
        out_path.write_text(html_content, encoding="utf-8")
        print(f"✅ HTML дашборд с графиками сохранен в: {out_path.resolve()}")
    elif args.format == "json":
        json_content = json.dumps(report.model_dump(), ensure_ascii=False, indent=2)
        out_path.write_text(json_content, encoding="utf-8")
        print(f"✅ JSON отчет сохранен в: {out_path.resolve()}")
    elif args.format == "svg":
        for chart in report.charts:
            svg_file = out_path.parent / f"{chart.id}.svg"
            svg_content = chart_gen.render_svg_chart(chart)
            svg_file.write_text(svg_content, encoding="utf-8")
            print(f"✅ SVG график сохранен в: {svg_file.resolve()}")

    print("\n--- Результаты исследования ---")
    print(f"Проанализировано записей: {report.records_analyzed}")
    print(f"Индекс здоровья системы (Health Score): {report.health_score}%")
    print(f"Обнаружено аномалий: {len(report.anomalies)}")
    print(f"Сгенерировано графиков: {len(report.charts)}")
    for conclusion in report.summary_conclusions:
        print(f" • {conclusion}")

    return 0



if __name__ == "__main__":
    sys.exit(main())
