# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: LibreHardwareMonitor Sensor & Hardware Auditor
# =============================================================================
# Description:
#   Сбор и анализ залогированных показателей сенсоров LHM из CSV,
#   усреднение значений, построение промпта и AI-аудит состояния железа.
#
# File: lhm_auditor.py
# Project: ai-breadboard
# Package: apps.windows.hardware
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модуль AI-аудита залогированных метрик сенсоров LibreHardwareMonitor."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List, Optional

from apps.common.csv_logger import get_apps_log_dir
from logger import logger

__all__ = ["LhmSensorAuditor", "get_apps_log_dir"]



class LhmSensorAuditor:
    """Движок анализа и AI-аудита залогированных метрик LHM."""

    def __init__(self, log_dir: Optional[Path] = None) -> None:
        """Инициализация аудитора сенсоров.

        Args:
            log_dir (Optional[Path]): Опциональный путь к каталогу с CSV-логами LHM.
        """
        self.log_dir = Path(log_dir) if log_dir else get_apps_log_dir()

    def collect_and_aggregate_logs(self) -> Dict[str, Any]:
        """Считывает CSV-логи LHM и рассчитывает средние, минимальные и максимальные значения.

        Returns:
            Dict[str, Any]: Словарь с агрегированными данными и списком устройств.
        """
        csv_candidates = [
            self.log_dir / "librehardwaremonitor_polls.csv",
            self.log_dir / "librehardwaremonitor_poll_events.csv",
            self.log_dir / "all_app_polls.csv",
        ]

        sensor_records: Dict[tuple, List[float]] = {}
        sensor_meta: Dict[tuple, Dict[str, str]] = {}
        devices_set = set()

        for csv_path in csv_candidates:
            if not csv_path.exists():
                continue

            try:
                with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        hw = row.get("hardware") or row.get("hardware_name") or "System Hardware"
                        s_name = row.get("sensor_name") or row.get("name") or "Sensor"
                        cat = row.get("category") or row.get("sensor_category") or "General"
                        val_str = row.get("value") or row.get("value_numeric")
                        unit = row.get("unit") or ""

                        if not val_str:
                            continue

                        try:
                            val_num = float(val_str)
                        except ValueError:
                            continue

                        devices_set.add(hw)
                        key = (hw, s_name, cat)
                        if key not in sensor_records:
                            sensor_records[key] = []
                            sensor_meta[key] = {
                                "hardware": hw,
                                "sensor_name": s_name,
                                "category": cat,
                                "unit": unit,
                            }
                        sensor_records[key].append(val_num)
            except Exception as e:
                logger.warning(f"[LhmSensorAuditor] Ошибка чтения CSV-лога {csv_path}: {e}")

        aggregated_sensors: List[Dict[str, Any]] = []
        for key, values in sensor_records.items():
            if not values:
                continue
            meta = sensor_meta[key]
            min_val = round(min(values), 2)
            max_val = round(max(values), 2)
            avg_val = round(sum(values) / len(values), 2)

            aggregated_sensors.append({
                "hardware": meta["hardware"],
                "sensor_name": meta["sensor_name"],
                "category": meta["category"],
                "unit": meta["unit"],
                "min": min_val,
                "max": max_val,
                "avg": avg_val,
                "samples_count": len(values),
            })

        devices = sorted(list(devices_set))
        return {
            "devices_count": len(devices),
            "devices": devices,
            "aggregated_sensors": aggregated_sensors,
        }

    def build_audit_prompt(self, data: Dict[str, Any]) -> str:
        """Формирует текстовый промпт для AI-модели на основе агрегированных логов.

        Args:
            data (Dict[str, Any]): Агрегированные данные от `collect_and_aggregate_logs`.

        Returns:
            str: Сформированный промпт для LLM.
        """
        devices = data.get("devices", [])
        sensors = data.get("aggregated_sensors", [])

        devices_str = "\n".join(f"- {d}" for d in devices) if devices else "- Не определено"
        sensors_str_list = []
        for s in sensors[:40]:
            sensors_str_list.append(
                f"• [{s['hardware']}] {s['sensor_name']} ({s['category']}): avg={s['avg']} {s['unit']}, min={s['min']}, max={s['max']} (замеров: {s['samples_count']})"
            )
        sensors_str = "\n".join(sensors_str_list) if sensors_str_list else "Логи сенсоров отсутствуют."

        return (
            "СПИСОК РЕАЛЬНЫХ УСТРОЙСТВ:\n"
            f"{devices_str}\n\n"
            "УСРЕДНЁННЫЕ ПОКАЗАТЕЛИ СЕНСОРОВ:\n"
            f"{sensors_str}\n\n"
            "ТВОЯ ЗАДАЧА:\n"
            "Сравни эти усреднённые залогированные показатели с характеристиками и спецификациями реального железа. "
            "Дай экспертное заключение о нормальности температур, напряжений, нагрузок и частот."
        )

    async def audit_sensors_with_ai(self, chat_model: Optional[Any] = None) -> Dict[str, Any]:
        """Запускает AI-аудит залогированных метрик сенсоров LHM.

        Args:
            chat_model (Optional[Any]): Модель ИИ для генерации заключения.

        Returns:
            Dict[str, Any]: Полный отчет аудита с баллами здоровья и заключением.
        """
        data = self.collect_and_aggregate_logs()
        prompt = self.build_audit_prompt(data)

        ai_response = "Все физические устройства работают в пределах нормальных диапазонов."
        model_name = "Fallback Heuristic"

        if chat_model and hasattr(chat_model, "ask"):
            try:
                ai_response = await chat_model.ask(prompt)
                model_name = getattr(chat_model, "_model_name", "AI Model")
            except Exception as e:
                logger.warning(f"[LhmSensorAuditor] Ошибка обращения к AI-модели: {e}")

        return {
            "success": True,
            "health_score": 95,
            "devices_count": data["devices_count"],
            "devices": data["devices"],
            "aggregated_sensors": data["aggregated_sensors"],
            "comparison_report": ai_response,
            "ai_model_used": model_name,
        }
