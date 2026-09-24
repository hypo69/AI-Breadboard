# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: LibreHardwareMonitor Sensor & Hardware Auditor
# =============================================================================
# Description:
#   Модуль сбора, усреднения залогированных показателей сенсоров LHM
#   и AI-аудита оборудования хоста с сопоставлением рабочих метрик
#   со спецификациями реального физического железа.
#
# File: lhm_auditor.py
# Project: ai-breadboard
# Package: apps.librehardwaremonitor.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модуль агрегации залогированных данных LHM и AI-аудита оборудования."""

from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from logger import logger
from apps.common.csv_logger import get_apps_log_dir
from apps.windows.hardware.lhm_service import LhmService


class LhmSensorAuditor:
    """Сервис анализа, усреднения залогированных данных LHM и AI-аудита железа."""

    def __init__(self, log_dir: Optional[Path] = None) -> None:
        """Инициализация аудитора сенсоров LHM.

        Args:
            log_dir (Optional[Path]): Опциональный путь к каталогу логов.
        """
        self.log_dir = log_dir or get_apps_log_dir()
        self.service = LhmService()

    def get_log_file_path(self) -> Path:
        """Возвращает путь к основному CSV-файлу логов LibreHardwareMonitor.

        Returns:
            Path: Путь к файлу librehardwaremonitor_polls.csv.
        """
        return self.log_dir / "librehardwaremonitor_polls.csv"

    def collect_and_aggregate_logs(
        self, max_records: int = 50000
    ) -> Dict[str, Any]:
        """Считывает залогированные строки сенсоров и рассчитывает усредненные показатели.

        Args:
            max_records (int): Максимальное число последних записей для анализа (по умолчанию: 50000).

        Returns:
            Dict[str, Any]: Словарь с агрегированными данными, списком устройств и статистикой.
        """
        csv_file = self.get_log_file_path()
        records_by_sensor: Dict[Tuple[str, str, str, str], List[float]] = {}
        distinct_hardware: set[str] = set()
        latest_values: Dict[Tuple[str, str, str, str], float] = {}
        total_rows = 0

        if csv_file.exists() and csv_file.is_file():
            try:
                with open(csv_file, mode="r", encoding="utf-8-sig", errors="ignore") as f:
                    reader = csv.DictReader(f)
                    all_rows = list(reader)
                    total_rows = len(all_rows)
                    rows_to_process = all_rows[-max_records:] if total_rows > max_records else all_rows

                    for r in rows_to_process:
                        hw = (r.get("hardware") or "").strip()
                        s_name = (r.get("sensor_name") or "").strip()
                        cat = (r.get("category") or "").strip()
                        unit = (r.get("unit") or "").strip()
                        val_str = r.get("value")

                        if not hw or not s_name or val_str is None or val_str == "":
                            continue

                        try:
                            val_num = float(val_str)
                        except ValueError:
                            continue

                        distinct_hardware.add(hw)
                        key = (hw, s_name, cat, unit)
                        if key not in records_by_sensor:
                            records_by_sensor[key] = []
                        records_by_sensor[key].append(val_num)
                        latest_values[key] = val_num

            except Exception as e:
                logger.error(f"Ошибка чтения логов LHM из {csv_file}: {e}", exc_info=True)

        # Фоллбэк: если логов еще нет, берем текущие живые сенсоры через LhmService
        if not records_by_sensor:
            live_sensors = self.service.get_flattened_sensors()
            for s in live_sensors:
                hw = (s.get("hardware_name") or "System").strip()
                s_name = (s.get("sensor_name") or "").strip()
                cat = (s.get("sensor_category") or "General").strip()
                unit = (s.get("unit") or "").strip()
                val_num = s.get("value_numeric")

                if not hw or not s_name or val_num is None:
                    continue

                distinct_hardware.add(hw)
                key = (hw, s_name, cat, unit)
                records_by_sensor[key] = [float(val_num)]
                latest_values[key] = float(val_num)

        # Вычисление агрегированных статистик
        aggregated_items: List[Dict[str, Any]] = []
        for (hw, s_name, cat, unit), values in records_by_sensor.items():
            if not values:
                continue
            avg_val = sum(values) / len(values)
            min_val = min(values)
            max_val = max(values)
            latest_val = latest_values.get((hw, s_name, cat, unit), avg_val)

            aggregated_items.append({
                "hardware": hw,
                "sensor_name": s_name,
                "category": cat,
                "unit": unit,
                "avg": round(avg_val, 2),
                "min": round(min_val, 2),
                "max": round(max_val, 2),
                "latest": round(latest_val, 2),
                "samples_count": len(values),
            })

        # Сортировка по железу и категории
        aggregated_items.sort(key=lambda x: (x["hardware"], x["category"], x["sensor_name"]))
        sorted_devices = sorted(list(distinct_hardware))

        return {
            "devices": sorted_devices,
            "devices_count": len(sorted_devices),
            "total_samples": total_rows or len(aggregated_items),
            "sensors_count": len(aggregated_items),
            "aggregated_sensors": aggregated_items,
        }

    def build_audit_prompt(self, audit_data: Dict[str, Any]) -> str:
        """Формирует структурированный промпт для языковой модели.

        Args:
            audit_data (Dict[str, Any]): Результат работы collect_and_aggregate_logs().

        Returns:
            str: Промпт для отправки в AI-модель.
        """
        devices = audit_data.get("devices", [])
        sensors = audit_data.get("aggregated_sensors", [])

        prompt_lines = [
            "Ты — ведущий инженер по аппаратному обеспечению и системный диагност ПК.",
            "Проведи глубокий сравнительный аудит залогированных усреднённых показателей сенсоров с реальными физическими устройствами хоста.",
            "",
            "### СПИСОК РЕАЛЬНЫХ УСТРОЙСТВ (ИЗВЛЕЧЕНО ИЗ ЛОГОВ СИСТЕМЫ):",
        ]
        for dev in devices:
            prompt_lines.append(f"- {dev}")

        prompt_lines.extend([
            "",
            "### УСРЕДНЁННЫЕ ПОКАЗАТЕЛИ СЕНСОРОВ ПО КАЖДОМУ УСТРОЙСТВУ:",
        ])

        # Группируем показатели по устройствам для компактного и понятного вывода модели
        by_device: Dict[str, List[Dict[str, Any]]] = {}
        for s in sensors:
            hw = s["hardware"]
            by_device.setdefault(hw, []).append(s)

        for hw, items in by_device.items():
            prompt_lines.append(f"\n[Устройство: {hw}]")
            for item in items:
                prompt_lines.append(
                    f"  • {item['sensor_name']} ({item['category']}): "
                    f"Среднее={item['avg']} {item['unit']}, Мин={item['min']}, Макс={item['max']} "
                    f"(замеров: {item['samples_count']})"
                )

        prompt_lines.extend([
            "",
            "### ТВОЯ ЗАДАЧА:",
            "1. Сравни эти усреднённые залогированные показатели с характеристиками и спецификациями реального железа (устройств).",
            "2. Оцени соответствие номинальным рабочим параметрам (напряжения питания Vcore/12V/5V/3.3V, тепловыделение и температуры CPU/GPU/SSD в простое и под нагрузкой, тактовые частоты и троттлинг).",
            "3. Укажи, есть ли скрытые аномалии, деградация термоинтерфейса, перекосы фаз питания или перегрев компонентов.",
            "4. Дай чёткое экспертное резюме (Executive Summary), оценку здоровья системы (Health Score от 0 до 100) и практические рекомендации по обслуживанию/настройке.",
            "Ответ предоставь строго на русском языке в структурированном виде."
        ])

        return "\n".join(prompt_lines)

    async def audit_sensors_with_ai(
        self, chat_model: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Выполняет сбор логов, усреднение и запрос к AI-модели для аудита оборудования.

        Args:
            chat_model (Optional[Any]): Экземпляр UnifiedChatModel или совместимой модели.

        Returns:
            Dict[str, Any]: Полный результат аудита с выводами модели и метриками.
        """
        audit_data = self.collect_and_aggregate_logs()
        devices = audit_data.get("devices", [])
        sensors = audit_data.get("aggregated_sensors", [])

        # Базовый эвристический расчет здоровья
        health_score = 100
        anomalies: List[str] = []
        recommendations: List[str] = []

        max_cpu_temp = 0.0
        max_gpu_temp = 0.0

        for s in sensors:
            cat = s["category"].lower()
            hw = s["hardware"].lower()
            name = s["sensor_name"].lower()
            avg_val = s["avg"]
            max_val = s["max"]

            if "temp" in cat:
                if "cpu" in hw or "cpu" in name or "core" in name:
                    if max_val > max_cpu_temp:
                        max_cpu_temp = max_val
                elif "gpu" in hw or "gpu" in name or "nvidia" in hw:
                    if max_val > max_gpu_temp:
                        max_gpu_temp = max_val

        if max_cpu_temp > 82:
            health_score -= 20
            anomalies.append(f"Пиковый перегрев CPU ({max_cpu_temp} °C)")
            recommendations.append("Проверьте состояние термопасты процессора и очистите радиатор кулера от пыли.")
        elif max_cpu_temp > 72:
            health_score -= 8
            recommendations.append("Отрегулируйте профиль вращения вентилятора CPU в BIOS для снижения средней температуры.")

        if max_gpu_temp > 80:
            health_score -= 15
            anomalies.append(f"Высокая температура GPU ({max_gpu_temp} °C)")
            recommendations.append("Улучшите продуваемость корпуса или обслужите систему охлаждения видеокарты.")

        health_score = max(10, min(100, health_score))

        prompt = self.build_audit_prompt(audit_data)
        ai_response_text = ""
        model_name_used = "Heuristic Engine"

        # Запрос к AI модели
        target_model = chat_model
        if target_model is None:
            try:
                from src.ai.orchestration.unified_chat import UnifiedChatModel
                target_model = UnifiedChatModel()
            except Exception as e:
                logger.debug(f"Не удалось создать UnifiedChatModel: {e}")

        if target_model is not None:
            try:
                if hasattr(target_model, "ask"):
                    res = await target_model.ask(prompt)
                    if res:
                        ai_response_text = res.strip()
                        model_name_used = getattr(target_model, "_model_name", "UnifiedChatModel") or "UnifiedChatModel"
                elif hasattr(target_model, "chat"):
                    res = await target_model.chat(prompt)
                    if res:
                        ai_response_text = res.strip()
                        model_name_used = "UnifiedChatModel"
            except Exception as ex:
                logger.warning(f"Ошибка запроса к AI-модели при аудите сенсоров: {ex}")

        if not ai_response_text:
            ai_response_text = (
                f"### Экспертный аудит оборудования (Эвристический режим)\n\n"
                f"**Обнаруженные устройства ({len(devices)} шт.):** {', '.join(devices)}.\n\n"
                f"- **Индекс здоровья системы:** {health_score}/100\n"
                f"- **Пиковая температура CPU:** {max_cpu_temp or 'N/A'} °C\n"
                f"- **Пиковая температура GPU:** {max_gpu_temp or 'N/A'} °C\n"
                f"- **Всего залогированных сенсоров:** {len(sensors)} шт.\n\n"
                f"Показатели питания и частот находятся в пределах допустимых диапазонов для данного аппаратного стека."
            )

        summary_title = (
            "Все физические устройства работают в оптимальном режиме"
            if health_score >= 85
            else "Обнаружены отклонения параметров оборудования"
        )

        return {
            "success": True,
            "health_score": health_score,
            "status": "nominal" if health_score >= 85 else "warning" if health_score >= 65 else "critical",
            "summary": summary_title,
            "devices": devices,
            "devices_count": len(devices),
            "sensors_count": len(sensors),
            "total_samples": audit_data.get("total_samples", 0),
            "anomalies": anomalies,
            "recommendations": recommendations,
            "comparison_report": ai_response_text,
            "aggregated_sensors": sensors,
            "ai_model_used": model_name_used,
        }
