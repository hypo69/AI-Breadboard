# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: LibreHardwareMonitor Standalone Service
# =============================================================================
# Description:
#   Ядро интеграции с LibreHardwareMonitor: опрос Web REST JSON API (:8085/data.json),
#   разбор полного дерева сенсоров материнской платы, CPU, GPU, накопителей,
#   нормализация метрик и управление жизненным циклом процесса.
#
# File: lhm_service.py
# Project: ai-breadboard
# Package: apps.librehardwaremonitor.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Сервис интеграции с LibreHardwareMonitor."""

from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from apps.common.discovery import UtilityDiscovery
from src.logger import logger

DEFAULT_ENDPOINT = "http://localhost:8085/data.json"


def parse_sensor_value(raw_value: Optional[str]) -> Tuple[Optional[float], Optional[str]]:
    """
    Извлечь числовое значение и единицу измерения из строки LHM.

    Args:
        raw_value (Optional[str]): Исходная строка значения (например, '54.2 °C', '14 %').

    Returns:
        Tuple[Optional[float], Optional[str]]: Кортеж (числовое_значение, единица_измерения).
    """
    if not raw_value or not isinstance(raw_value, str):
        return None, None
    raw = raw_value.strip().replace(",", ".")
    match = re.match(r"^([-+]?[0-9]*\.?[0-9]+)\s*(.*)$", raw)
    if match:
        try:
            num = float(match.group(1))
            unit = match.group(2).strip() or None
            return num, unit
        except ValueError:
            return None, raw
    return None, raw


class LhmService:
    """Сервис для сбора метрик и управления LibreHardwareMonitor."""

    def __init__(self, binary_path: Optional[str] = None, endpoint_url: str = DEFAULT_ENDPOINT) -> None:
        """
        Инициализация сервиса LHM.

        Args:
            binary_path (Optional[str]): Путь к исполняемому файлу LibreHardwareMonitor.exe.
            endpoint_url (str): URL Web API endpoint LHM (по умолчанию: http://localhost:8085/data.json).
        """
        discovery = UtilityDiscovery()
        self.binary_path = binary_path or discovery.find_utility("librehardwaremonitor") or discovery.find_utility("lhm")
        self.endpoint_url = endpoint_url

    def is_running(self) -> bool:
        """
        Проверить доступность Web API сервера LHM.

        Returns:
            bool: True, если сервер отвечает со статусом 200, иначе False.
        """
        try:
            req = urllib.request.Request(self.endpoint_url, headers={"User-Agent": "AI-Breadboard"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def is_binary_available(self) -> bool:
        """
        Проверить наличие исполняемого файла LibreHardwareMonitor.exe.

        Returns:
            bool: True, если бинарный файл найден и существует на диске.
        """
        return self.binary_path is not None and os.path.isfile(self.binary_path)

    def start_process(self) -> bool:
        """
        Запустить процесс LibreHardwareMonitor в фоновом режиме.

        Returns:
            bool: True, если процесс успешно запущен или уже работает, иначе False.
        """
        if self.is_running():
            logger.info("LibreHardwareMonitor Web API уже запущен и доступен.")
            return True

        if not self.is_binary_available():
            logger.warning(f"Исполняемый файл LHM не найден по пути: {self.binary_path}")
            return False

        try:
            creationflags = 0
            if os.name == "nt":
                creationflags = getattr(subprocess, "DETACHED_PROCESS", 0x00000008)

            assert self.binary_path is not None
            subprocess.Popen(
                [self.binary_path],
                creationflags=creationflags,
                close_fds=True,
            )
            logger.info(f"Запущен процесс LibreHardwareMonitor: {self.binary_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при запуске LibreHardwareMonitor: {e}")
            return False

    def get_sensor_tree(self) -> Optional[Dict[str, Any]]:
        """
        Получить полное дерево данных сенсоров в формате JSON.

        Returns:
            Optional[Dict[str, Any]]: Распарсенное дерево словарей или None в случае ошибки.
        """
        try:
            req = urllib.request.Request(self.endpoint_url, headers={"User-Agent": "AI-Breadboard"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            logger.debug(f"Ошибка запроса к LHM Web API: {e}")
            return None

    def find_sensor(
        self,
        hardware_pattern: str,
        sensor_pattern: str,
        sensor_type_pattern: Optional[str] = None,
        tree: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Рекурсивный поиск конкретного сенсора в структуре LHM.

        Args:
            hardware_pattern (str): Подстрока имени оборудования или тип ('CPU', 'AMD', 'GPU', 'NVIDIA', 'Memory').
            sensor_pattern (str): Подстрока имени датчика (например, 'CPU Package', 'GPU Core').
            sensor_type_pattern (Optional[str]): Опциональная подстрока категории (например, 'Temperatures', 'Load').
            tree (Optional[Dict[str, Any]]): Дерево для поиска (если None, запрашивается из API).

        Returns:
            Optional[Dict[str, Any]]: Словарь с метаданными сенсора или None, если не найден.
        """
        data = tree if tree is not None else self.get_sensor_tree()
        if not data:
            return None

        flattened = self._flatten_node(data, current_hardware="")
        hw_pat = hardware_pattern.lower()
        sens_pat = sensor_pattern.lower()
        type_pat = sensor_type_pattern.lower() if sensor_type_pattern else None

        for item in flattened:
            hw_match = hw_pat in item["hardware_name"].lower() or hw_pat in item["hardware_type"].lower()
            sens_match = sens_pat in item["sensor_name"].lower()
            if hw_match and sens_match:
                if type_pat is None or type_pat in item["sensor_category"].lower():
                    return item
        return None

    def get_flattened_sensors(self, tree: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Преобразовать древовидную структуру LHM в плоский список сенсоров.

        Args:
            tree (Optional[Dict[str, Any]]): Дерево LHM (если None, запрашивается из API).

        Returns:
            List[Dict[str, Any]]: Список всех обнаруженных датчиков с нормализованными значениями.
        """
        data = tree if tree is not None else self.get_sensor_tree()
        if not data:
            return []
        return self._flatten_node(data, current_hardware="")

    def _flatten_node(
        self,
        node: Any,
        current_hardware: str = "",
        current_category: str = "",
        current_hardware_type: str = "other",
    ) -> List[Dict[str, Any]]:
        """Рекурсивный обход узлов дерева LHM для формирования плоского списка."""
        results: List[Dict[str, Any]] = []

        if isinstance(node, dict):
            text = node.get("Text", "")
            image_url = node.get("ImageURL", "")
            value_raw = node.get("Value")
            sensor_id = node.get("id")

            hardware_name = current_hardware
            hardware_type = current_hardware_type
            category = current_category

            # Если узел является заголовком или корневым контейнером "Sensor"
            if text == "Sensor" or str(value_raw).strip() == "Value":
                children = node.get("Children", [])
                for child in children:
                    results.extend(self._flatten_node(child, hardware_name, category, hardware_type))
                return results

            categories = (
                "Temperatures", "Load", "Clocks", "Voltages", "Powers", "Fans",
                "Controls", "Levels", "Data", "Throughput", "Factors", "Times"
            )

            if text in categories:
                category = text
            elif image_url:
                img_lower = image_url.lower()
                # Исключаем узел компьютера верхнего уровня и прозрачные иконки датчиков
                if not any(x in img_lower for x in ("computer", "desktop", "transparent")):
                    hardware_name = text
                    if "cpu" in img_lower or "processor" in img_lower:
                        hardware_type = "cpu"
                    elif "nvidia" in img_lower or "gpu" in img_lower or "ati" in img_lower or "radeon" in img_lower or ("intel" in img_lower and ("arc" in text.lower() or "graphics" in text.lower() or "uhd" in text.lower())):
                        hardware_type = "gpu"
                    elif "ram" in img_lower or "memory" in img_lower:
                        hardware_type = "memory"
                    elif "hdd" in img_lower or "ssd" in img_lower or "drive" in img_lower or "nvme" in img_lower:
                        hardware_type = "storage"
                    elif "mainboard" in img_lower or "motherboard" in img_lower:
                        hardware_type = "mainboard"
                    elif "nic" in img_lower or "net" in img_lower or "wifi" in img_lower:
                        hardware_type = "network"

            # Если у узла есть непустое Value — это конечный сенсор
            if value_raw is not None and str(value_raw).strip() not in ("", "Value"):
                val_num, unit = parse_sensor_value(str(value_raw))
                results.append({
                    "id": sensor_id,
                    "hardware_name": hardware_name or "System",
                    "hardware_type": hardware_type,
                    "sensor_category": category or "General",
                    "sensor_name": text,
                    "value_raw": str(value_raw),
                    "value_num": val_num,
                    "unit": unit,
                })

            children = node.get("Children", [])
            for child in children:
                results.extend(self._flatten_node(child, hardware_name, category, hardware_type))

        elif isinstance(node, list):
            for item in node:
                results.extend(self._flatten_node(item, current_hardware, current_category, current_hardware_type))

        return results

    def get_system_summary(self, tree: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Собрать краткую сводку ключевых системных метрик (CPU/GPU/RAM).

        Args:
            tree (Optional[Dict[str, Any]]): Дерево LHM (если None, запрашивается из API).

        Returns:
            Dict[str, Any]: Краткая сводка основных температур и загрузок.
        """
        sensors = self.get_flattened_sensors(tree=tree)
        summary: Dict[str, Any] = {
            "is_available": len(sensors) > 0,
            "cpu": {
                "name": None,
                "temperature_package_c": None,
                "load_total_percent": None,
            },
            "gpu": {
                "name": None,
                "temperature_core_c": None,
                "load_core_percent": None,
            },
            "memory": {
                "used_gb": None,
                "load_percent": None,
            },
            "total_sensors_count": len(sensors),
        }

        for s in sensors:
            hw = s["hardware_name"]
            hw_type = s["hardware_type"]
            cat = s["sensor_category"].lower()
            name = s["sensor_name"].lower()
            num = s["value_num"]

            # CPU
            if hw_type == "cpu" or any(k in hw.lower() for k in ("intel core", "ryzen", "threadripper", "xeon")):
                if summary["cpu"]["name"] is None or summary["cpu"]["name"] == "System":
                    summary["cpu"]["name"] = hw

                if cat == "temperatures" and any(k in name for k in ("package", "tctl", "cpu total", "core max", "cpu core")):
                    if summary["cpu"]["temperature_package_c"] is None or "package" in name:
                        summary["cpu"]["temperature_package_c"] = num

                if cat == "load" and any(k in name for k in ("total", "cpu total")):
                    summary["cpu"]["load_total_percent"] = num

            # GPU
            if hw_type == "gpu" or any(k in hw.lower() for k in ("nvidia", "geforce", "radeon", "intel arc", "uhd graphics")):
                if summary["gpu"]["name"] is None or summary["gpu"]["name"] == "System":
                    summary["gpu"]["name"] = hw

                if cat == "temperatures" and any(k in name for k in ("gpu core", "core", "hot spot", "temperature")):
                    if summary["gpu"]["temperature_core_c"] is None or "core" in name:
                        summary["gpu"]["temperature_core_c"] = num

                if cat == "load" and ("core" in name or "gpu core" in name or "d3d 3d" in name):
                    if summary["gpu"]["load_core_percent"] is None or "gpu core" in name or "core" in name:
                        summary["gpu"]["load_core_percent"] = num

            # RAM
            if hw_type == "memory" or any(k in hw.lower() for k in ("memory", "ram")):
                if cat == "load" and name == "memory":
                    summary["memory"]["load_percent"] = num
                if cat == "data" and "used" in name and "gpu" not in name and "d3d" not in name:
                    summary["memory"]["used_gb"] = num

        return summary
