# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Telemetry Research Application CLI
# =============================================================================
# Description:
#   Консольный интерфейс для запуска исследовательского анализа логов
#   телеметрии, проверки гипотез и экспорта результатов (JSON/HTML/SVG).
#
# Examples:
#   py apps/telemetry_research/cli.py --source logs/telemetry --output report.html
#
# File: cli.py
# Project: ai-breadboard
# Package: apps.telemetry_research
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Консольный интерфейс приложения исследования телеметрии."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from apps.telemetry_research.engine import TelemetryResearchEngine
from apps.telemetry_research.models import ResearchScenarioRequest


def main() -> int:
    """Точка входа CLI для запуска глубокого исследования телеметрии."""
    parser = argparse.ArgumentParser(
        description="🔬 Комплексное исследование телеметрии и логов оборудования",
    )
    parser.add_argument(
        "--source",
        "-s",
        type=str,
        default=None,
        help="Путь к файлу логов или директории (по умолчанию: logs/telemetry)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Путь для сохранения отчета (HTML или JSON)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "html", "summary"],
        default="summary",
        help="Формат вывода результатов (по умолчанию: summary)",
    )

    args = parser.parse_args()

    engine = TelemetryResearchEngine()
    req = ResearchScenarioRequest(source_path=args.source)
    report = engine.run_deep_research(req)

    if args.format == "json":
        json_data = report.model_dump_json(indent=2)
        if args.output:
            Path(args.output).write_text(json_data, encoding="utf-8")
            print(f"JSON отчет успешно сохранен в: {args.output}")
        else:
            print(json_data)
        return 0

    if args.format == "html":
        html_content = engine.chart_generator.render_html_dashboard(report.base_report)
        out_path = args.output or "telemetry_research_report.html"
        Path(out_path).write_text(html_content, encoding="utf-8")
        print(f"HTML дашборд успешно сформирован: {out_path}")
        return 0

    # Summary формат
    print("\n" + "=" * 70)
    print(f"🔬 Отчет исследования телеметрии: {report.report_id}")
    print("=" * 70)
    print(f"Дата формирования: {report.generated_at}")
    print(f"Проанализировано записей: {report.base_report.records_analyzed}")
    print(f"Индекс здоровья системы: {report.base_report.health_score}/100")
    print(f"Обнаружено аномалий: {len(report.base_report.anomalies)}")

    print("\n--- Проверенные гипотезы ---")
    for h in report.hypotheses:
        status_icon = "⚠️ [ПОДТВЕРЖДЕНА]" if h.confirmed else "✅ [В НОРМЕ]"
        print(f"{status_icon} {h.title} (уверенность {h.confidence*100:.0f}%)")
        for ev in h.evidence:
            print(f"    • {ev}")

    print("\n--- Рекомендации ---")
    for rec in report.actionable_recommendations:
        print(f"  👉 {rec}")

    print("=" * 70 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
