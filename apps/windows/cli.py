# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows AI Diagnostic Center CLI
# =============================================================================
# Description:
#   Консольный интерфейс командной строки (CLI) для запуска аудита Windows,
#   расследования первопричин проблем и запуска автономного сервера.
#
# Examples:
#   >>> python -m apps.windows --mode full
#   >>> python -m apps.windows --investigate "высокая нагрузка CPU"
#
# File: cli.py
# Project: ai-breadboard
# Package: apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""CLI интерфейс для Windows AI Diagnostic & Administration Center."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from apps.windows.ai.diagnostician import WindowsAIDiagnostician
from apps.windows.ai.root_cause_analyzer import WindowsAIRootCauseAnalyzer
from apps.windows.core.root_cause_engine import RootCauseEngine


def print_banner() -> None:
    """Печать приветственного баннера."""
    print("=" * 70)
    print("   AI WINDOWS DIAGNOSTIC & ADMINISTRATION CENTER")
    print("   Аналитический центр аудита, безопасности и оптимизации Windows")
    print("=" * 70)


def format_health_summary(report_dict: dict) -> None:
    """Форматированный вывод сводки здоровья."""
    score = report_dict.get("health_score", {})
    print(f"\n[+] SYSTEM HEALTH SCORE: {score.get('score')}/100 ({score.get('status_label')})")
    print(f"    Критические проблемы: {score.get('critical_count')}")
    print(f"    Предупреждения:       {score.get('medium_count')}")
    print(f"    Безопасные действия:  {score.get('low_count')}")
    print(f"    Всего фактов/находок: {score.get('total_findings')}")
    print("-" * 70)

    domains = report_dict.get("domains", {})
    for d_name, d_val in domains.items():
        title = d_val.get("title_ru", d_name)
        status = d_val.get("status", "ok").upper()
        findings = d_val.get("findings", [])
        print(f"  * [{status:<8}] {title} ({len(findings)} заметок)")
        for f in findings[:2]:
            print(f"      - {f.get('title')}")


def main() -> None:
    """Главная функция CLI."""
    parser = argparse.ArgumentParser(description="AI Windows Diagnostic & Administration Center")
    parser.add_argument(
        "--mode",
        choices=["quick", "full", "security", "performance", "drivers", "clean", "postinstall", "inspector", "dashboard", "server"],
        default="quick",
        help="Режим аудита системы или запуск сервиса/инспектора",
    )
    parser.add_argument(
        "--inspector",
        action="store_true",
        help="Запустить интерактивный системный инспектор (System & Hardware Inspector)",
    )
    parser.add_argument(
        "--investigate",
        type=str,
        help="Расследовать причину проблемы по описанию симптома",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Вывести результат в формате JSON",
    )
    parser.add_argument(
        "--server",
        action="store_true",
        help="Запустить сервер FastAPI",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8105,
        help="Порт сервера FastAPI (по умолчанию: 8105)",
    )
    parser.add_argument(
        "--tui",
        action="store_true",
        help="Запустить интерактивный TUI интерфейс",
    )
    parser.add_argument(
        "--logs",
        action="store_true",
        help="Запустить интерактивный монитор системных логов в терминале (System Log Viewer)",
    )
    parser.add_argument(
        "--channel",
        type=str,
        default="System",
        help="Канал логов для монитора (по умолчанию: System)",
    )
    parser.add_argument(
        "--hardware",
        "--hw-monitor",
        action="store_true",
        dest="hardware_monitor",
        help="Запустить интерактивный TUI монитор оборудования (Hardware Monitor)",
    )
    parser.add_argument(
        "--hw-json",
        action="store_true",
        help="Вывести текущий слепок состояния оборудования в формате JSON",
    )

    parser.add_argument(
        "--providers",
        action="store_true",
        help="Отобразить статус всех аппаратных провайдеров и утилит в /bin",
    )
    parser.add_argument(
        "--cross-check",
        action="store_true",
        help="Запустить перекрестную проверку (cross-check) данных оборудования",
    )

    args = parser.parse_args()

    if args.providers:
        from apps.windows.hardware.registry import HardwareProviderRegistry
        reg = HardwareProviderRegistry()
        print("\n=== АППАРАТНЫЕ ПРОВАЙДЕРЫ WINDOWS DIAGNOSTIC ENGINE ===")
        for p in reg.get_all_providers():
            info = p.get_provider_info()
            status_symbol = "🟢" if info["status"] == "AVAILABLE" or info["status"] == "RUNNING" else "⚪"
            print(f"{status_symbol} [{info['tier_label']}] {info['name']}: {info['status']}")
            if info["binary_path"]:
                print(f"   Файл: {info['binary_path']}")
            print(f"   Возможности: {', '.join(info['capabilities'])}")
        return

    if args.cross_check:
        from apps.windows.hardware.cross_validator import CrossValidator
        validator = CrossValidator()
        report = validator.run_cross_check()
        print("\n=== РЕЗУЛЬТАТЫ КРОСС-ВАЛИДАЦИИ ОБОРУДОВАНИЯ ===")
        print(f"Уровень согласованности: {report.consensus_score_pct:.1f}%")
        print(f"Активные провайдеры: {', '.join(report.active_providers)}")
        if report.discrepancies:
            print("\n[!] Обнаружены расхождения:")
            for d in report.discrepancies:
                print(f" - [{d.severity}] {d.component} -> {d.parameter}: {d.sources} ({d.explanation})")
        else:
            print("✅ Все аппаратные данные согласованы между провайдерами.")
        return

    if args.hw_json:
        from apps.windows.hardware.hardware_monitor import HardwareMonitor
        monitor = HardwareMonitor()
        snap = monitor.get_snapshot(include_smart=True)
        print(json.dumps(snap.to_dict(), ensure_ascii=False, indent=2))
        return

    if args.hardware_monitor:
        from apps.windows.tui import run_hardware_monitor_dashboard
        try:
            asyncio.run(run_hardware_monitor_dashboard())
        except (KeyboardInterrupt, SystemExit):
            print("\n[!] Мониторинг оборудования остановлен.")
        return

    if args.inspector or args.mode in ("inspector", "dashboard"):
        from apps.windows.tui import run_system_inspector
        try:
            asyncio.run(run_system_inspector())
        except (KeyboardInterrupt, SystemExit):
            print("\n[!] Системный инспектор остановлен.")
        return

    if args.logs:
        from apps.windows.tui import run_log_dashboard
        asyncio.run(run_log_dashboard(channel=args.channel))
        return

    if args.tui:
        from apps.windows.tui import run_tui
        run_tui()
        return

    if args.server or args.mode == "server":
        import uvicorn
        from fastapi import FastAPI
        from apps.windows.router import init_router

        app = FastAPI(title="AI Windows Diagnostic Center")
        app.include_router(init_router())
        print_banner()
        print(f"[*] Запуск FastAPI сервера на http://127.0.0.1:{args.port}")
        uvicorn.run(app, host="127.0.0.1", port=args.port)
        return

    if not args.json:
        print_banner()

    if args.investigate:
        investigator = WindowsAIRootCauseAnalyzer()
        res = asyncio.run(investigator.analyze_incident(args.investigate))
        if args.json:
            print(json.dumps(res.to_dict(), ensure_ascii=False, indent=2))
        else:
            print(f"\n[?] Симптом: {res.symptom}")
            print(f"[!] Первопричина: {res.probable_root_cause} (Уверенность: {int(res.confidence_score * 100)}%)")
            print(f"\n[i] AI Объяснение:\n{res.ai_explanation}")
            if res.remediation_plan:
                print("\n[*] План устранения:")
                for a in res.remediation_plan:
                    print(f"    - [{a.risk.value.upper()}] {a.title}: {a.execution_command}")
        return

    # Запуск аудита
    diagnostician = WindowsAIDiagnostician()
    report = asyncio.run(diagnostician.diagnose_system(mode=args.mode))

    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        format_health_summary(report.to_dict())
        if report.ai_summary:
            print("\n[AI Заключение]:")
            print(report.ai_summary)


if __name__ == "__main__":
    main()
