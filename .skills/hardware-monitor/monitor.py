## \file .agents/skills/hardware-monitor/monitor.py
# -*- coding: utf-8 -*-
#! .venv/Scripts/python.exe
"""
Скрипт мониторинга оборудования через LibreHardwareMonitor
=========================================================

Опрашивает локальный сервер LibreHardwareMonitor (http://localhost:8085/data.json)
и выводит показатели температуры, мощности, напряжений и загрузки компонентов.
"""

import json
import sys
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional

DEFAULT_LHM_URL = "http://localhost:8085/data.json"


def fetch_lhm_data(url: str = DEFAULT_LHM_URL, timeout: float = 3.0) -> Optional[Dict[str, Any]]:
    """
    Получает JSON-данные от веб-сервера LibreHardwareMonitor.
    """
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "AI-Breadboard/HardwareMonitor"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        return None


def _traverse_tree(node: Dict[str, Any], path: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Рекурсивно обходит дерево сенсоров LHM.
    """
    if path is None:
        path = []

    results = []
    text = node.get("Text", "")
    val = node.get("Value", "")
    min_v = node.get("Min", "")
    max_v = node.get("Max", "")
    children = node.get("Children", [])

    current_path = path + [text] if text else path

    if val:
        results.append({
            "name": text,
            "path": current_path,
            "value": val,
            "min": min_v,
            "max": max_v,
        })

    for child in children:
        results.extend(_traverse_tree(child, current_path))

    return results


def get_all_sensors(url: str = DEFAULT_LHM_URL) -> List[Dict[str, Any]]:
    """Возвращает плоский список всех сенсоров."""
    data = fetch_lhm_data(url)
    if not data:
        return []
    return _traverse_tree(data)


def get_cpu_info(url: str = DEFAULT_LHM_URL) -> Dict[str, Any]:
    """Возвращает подробные метрики CPU (температуры, частоты, мощности, напряжения)."""
    sensors = get_all_sensors(url)
    cpu_data = {
        "model": "Unknown CPU",
        "temperatures": {},
        "clocks": {},
        "powers": {},
        "voltages": {},
        "load": {}
    }

    for s in sensors:
        path = s["path"]
        name = s["name"]
        val = s["value"]

        # Поиск информации о CPU
        if any("Core i" in p or "Intel" in p or "AMD" in p or "Ryzen" in p for p in path):
            if len(path) >= 3 and cpu_data["model"] == "Unknown CPU":
                cpu_data["model"] = path[2]

            if "Temperatures" in path and "TjMax" not in name:
                cpu_data["temperatures"][name] = {"value": val, "min": s["min"], "max": s["max"]}
            elif "Clocks" in path:
                cpu_data["clocks"][name] = val
            elif "Powers" in path:
                cpu_data["powers"][name] = val
            elif "Voltages" in path:
                cpu_data["voltages"][name] = val
            elif "Load" in path:
                cpu_data["load"][name] = val

    return cpu_data


def get_gpu_info(url: str = DEFAULT_LHM_URL) -> Dict[str, Any]:
    """Возвращает метрики GPU."""
    sensors = get_all_sensors(url)
    gpu_data = {
        "model": "Unknown GPU",
        "temperatures": {},
        "load": {},
        "clocks": {},
        "powers": {}
    }

    for s in sensors:
        path = s["path"]
        name = s["name"]
        val = s["value"]

        if any("NVIDIA" in p or "GeForce" in p or "Radeon" in p or "Intel Iris" in p or "Intel UHD" in p for p in path):
            if len(path) >= 3 and gpu_data["model"] == "Unknown GPU":
                gpu_data["model"] = path[2]

            if "Temperatures" in path:
                gpu_data["temperatures"][name] = {"value": val, "min": s["min"], "max": s["max"]}
            elif "Load" in path:
                gpu_data["load"][name] = val
            elif "Clocks" in path:
                gpu_data["clocks"][name] = val
            elif "Powers" in path:
                gpu_data["powers"][name] = val

    return gpu_data


def print_cpu_summary(cpu: Dict[str, Any]):
    """Форматированный вывод показателей CPU."""
    print(f"\n🖥️  Процессор: {cpu['model']}")
    print("-" * 50)
    print("🌡️  Температуры:")
    for k, v in cpu["temperatures"].items():
        print(f"   • {k:<20}: {v['value']:<10} (Min: {v['min']}, Max: {v['max']})")

    if cpu["powers"]:
        print("\n⚡ Мощность:")
        for k, v in cpu["powers"].items():
            print(f"   • {k:<20}: {v}")

    if cpu["clocks"]:
        print("\n⏱️  Частоты:")
        for k, v in list(cpu["clocks"].items())[:6]:
            print(f"   • {k:<20}: {v}")


def main():
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "all"

    cpu = get_cpu_info()
    gpu = get_gpu_info()

    if not cpu["temperatures"] and not gpu["temperatures"]:
        print("❌ Ошибка: Не удалось получить данные от LibreHardwareMonitor.")
        print("Убедитесь, что приложение LibreHardwareMonitor запущено и в меню включен веб-сервер:")
        print("  Options -> Remote Web Server -> Run (порт 8085)")
        sys.exit(1)

    if mode in ["--json", "-j"]:
        print(json.dumps({"cpu": cpu, "gpu": gpu}, indent=2, ensure_ascii=False))
        return

    if mode in ["cpu", "temp", "temperature"]:
        print_cpu_summary(cpu)
    elif mode == "gpu":
        print(f"\n🎮 Видеокарта: {gpu['model']}")
        print("-" * 50)
        print("🌡️  Температуры:")
        for k, v in gpu["temperatures"].items():
            print(f"   • {k:<20}: {v['value']:<10} (Min: {v['min']}, Max: {v['max']})")
        if gpu["load"]:
            print("\n📊 Загрузка:")
            for k, v in gpu["load"].items():
                print(f"   • {k:<20}: {v}")
    else:
        print_cpu_summary(cpu)
        if gpu["temperatures"]:
            print(f"\n🎮 Видеокарта: {gpu['model']}")
            print("-" * 50)
            print("🌡️  Температуры:")
            for k, v in gpu["temperatures"].items():
                print(f"   • {k:<20}: {v['value']:<10} (Min: {v['min']}, Max: {v['max']})")


if __name__ == "__main__":
    main()
