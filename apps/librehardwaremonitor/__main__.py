# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: LibreHardwareMonitor Standalone CLI Runner
# =============================================================================
# Description:
#   Точка входа CLI для LibreHardwareMonitor App (python -m apps.librehardwaremonitor).
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.librehardwaremonitor
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Точка входа CLI для LibreHardwareMonitor."""

from __future__ import annotations

import argparse
import json

from apps.librehardwaremonitor.core.lhm_service import LhmService


def main() -> None:
    """Точка входа CLI."""
    parser = argparse.ArgumentParser(description="LibreHardwareMonitor Diagnostic App")
    parser.add_argument("--sensors", action="store_true", help="Получить полное дерево датчиков через Web API")
    parser.add_argument("--summary", action="store_true", help="Вывести системную сводку ключевых показателей (CPU/GPU/RAM)")
    parser.add_argument("--metrics", action="store_true", help="Вывести плоский список всех датчиков с числовыми значениями")
    parser.add_argument("--find", nargs=2, metavar=("HARDWARE", "SENSOR"), help="Поиск значения сенсора (например: --find CPU 'CPU Package')")
    parser.add_argument("--launch", action="store_true", help="Запустить LibreHardwareMonitor.exe в фоновом режиме")
    parser.add_argument("--endpoint", type=str, default="http://localhost:8085/data.json", help="URL Web API LHM")
    parser.add_argument("--server", action="store_true", help="Запустить выделенный HTTP API сервер")
    parser.add_argument("--port", type=int, default=8126, help="Порт сервера (по умолчанию: 8126)")

    args = parser.parse_args()
    svc = LhmService(endpoint_url=args.endpoint)

    if args.launch:
        started = svc.start_process()
        if started:
            print("🚀 Процесс LibreHardwareMonitor успешно запущен / уже работает.")
        else:
            print(f"❌ Не удалось запустить LibreHardwareMonitor. Проверьте наличие {svc.binary_path}")
        return

    if args.server:
        import uvicorn
        from fastapi import FastAPI
        from apps.librehardwaremonitor.router import init_router
        app = FastAPI(title="LibreHardwareMonitor Server")
        app.include_router(init_router())
        print(f"🚀 Запуск сервера LHM на http://127.0.0.1:{args.port}")
        uvicorn.run(app, host="127.0.0.1", port=args.port)
        return

    if args.sensors:
        tree = svc.get_sensor_tree()
        print(json.dumps(tree, ensure_ascii=False, indent=2))
        return

    if args.metrics:
        metrics = svc.get_flattened_sensors()
        print(json.dumps(metrics, ensure_ascii=False, indent=2))
        return

    if args.find:
        hw_query, sens_query = args.find
        sensor = svc.find_sensor(hw_query, sens_query)
        if sensor:
            print(f"✅ Найдено: [{sensor['hardware_name']}] {sensor['sensor_category']} -> {sensor['sensor_name']}: {sensor['value_raw']}")
        else:
            print(f"❌ Датчик не найден по запросу: железо='{hw_query}', сенсор='{sens_query}'")
        return

    if args.summary:
        summary = svc.get_system_summary()
        print("=== СИСТЕМНАЯ СВОДКА LIBREHARDWAREMONITOR ===")
        if not summary["is_available"]:
            print("⚠️ Нет данных от LHM (сервер не запущен или пустой ответ).")
            return
        cpu = summary["cpu"]
        gpu = summary["gpu"]
        mem = summary["memory"]
        print(f"CPU: {cpu['name'] or 'Unknown'}")
        print(f"  • Температура: {cpu['temperature_package_c']} °C" if cpu['temperature_package_c'] is not None else "  • Температура: Н/Д")
        print(f"  • Загрузка:    {cpu['load_total_percent']} %" if cpu['load_total_percent'] is not None else "  • Загрузка:    Н/Д")
        print(f"GPU: {gpu['name'] or 'Unknown'}")
        print(f"  • Температура: {gpu['temperature_core_c']} °C" if gpu['temperature_core_c'] is not None else "  • Температура: Н/Д")
        print(f"  • Загрузка:    {gpu['load_core_percent']} %" if gpu['load_core_percent'] is not None else "  • Загрузка:    Н/Д")
        print(f"RAM:")
        print(f"  • Занято:      {mem['used_gb']} GB" if mem['used_gb'] is not None else "  • Занято:      Н/Д")
        print(f"  • Загрузка:    {mem['load_percent']} %" if mem['load_percent'] is not None else "  • Загрузка:    Н/Д")
        print(f"Всего сенсоров: {summary['total_sensors_count']}")
        return

    print("=== LIBRE HARDWARE MONITOR APP ===")
    print(f"Статус Web API ({svc.endpoint_url}): {'🟢 Доступен' if svc.is_running() else '⚪ Недоступен'}")
    if svc.is_binary_available():
        print(f"Исполняемый файл: 🟢 [FOUND] {svc.binary_path}")
    else:
        from apps.common.discovery import UtilityDiscovery
        guide = UtilityDiscovery().get_portable_guide("librehardwaremonitor")
        print(f"Исполняемый файл: 🔴 [{guide.badge_label}] (Не найден в /bin)")
        print(f"\n📢 ИНСТРУКЦИЯ ПО УСТАНОВКЕ PORTABLE ВЕРСИИ:")
        print(f"   • Официальный сайт: {guide.official_url}")
        print(f"   • Прямая ссылка:    {guide.download_url}")
        print(f"   • Путь назначения:  {guide.target_bin_path}")
        print(f"\n{guide.instruction_ru}")
    print("\nИспользуйте --summary, --metrics, --find <HW> <SENSOR>, --sensors или --server --port 8126")


if __name__ == "__main__":
    main()

