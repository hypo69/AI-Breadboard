# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Hardware - LHM Service
# =============================================================================
# Description:
#   Клиент веб-сервера LibreHardwareMonitor (http://127.0.0.1:8085/data.json):
#   проверка доступности, запуск bin/LibreHardwareMonitor/LibreHardwareMonitor.exe,
#   разбор дерева датчиков в плоский список.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.hardware.lhm_service import LhmService
#
#     sensors = LhmService().get_flattened_sensors()
#
# File: lhm_service.py
# Project: ai-breadboard
# Package: apps.windows.modules.hardware
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 02:20:00
# =============================================================================

from __future__ import annotations
"""Клиент веб-API LibreHardwareMonitor и разбор дерева датчиков."""

import json
import os
import re
import subprocess
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from logger import logger

DEFAULT_ENDPOINT = "http://127.0.0.1:8085/data.json"
_PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_BINARY = _PROJECT_ROOT / "bin" / "LibreHardwareMonitor" / "LibreHardwareMonitor.exe"

_NUM_RE = re.compile(r"-?\d+(?:[.,]\d+)?")
# Порядок важен: более специфичные ключи раньше общих.
_HARDWARE_ICONS = (
    ("cpu", "cpu"), ("nvidia", "gpu"), ("ati", "gpu"), ("gpu", "gpu"),
    ("ram", "memory"), ("memory", "memory"), ("hdd", "storage"), ("ssd", "storage"),
    ("nvme", "storage"), ("mainboard", "mainboard"), ("nic", "network"),
)


def parse_sensor_value(raw: Any) -> Optional[float]:
    """Извлекает число из строки значения LHM (``"55,0 °C"`` -> ``55.0``).

    Args:
        raw: Сырое значение узла (строка вида «45.0 °C»).

    Returns:
        Optional[float]: Число или None, если число в строке отсутствует.
    """
    match = _NUM_RE.search(str(raw or ""))
    return float(match.group(0).replace(",", ".")) if match else None


def _hardware_type(image_url: str) -> str:
    """Определяет тип оборудования по иконке узла; пустая строка — не оборудование."""
    icon = (image_url or "").lower()
    for key, kind in _HARDWARE_ICONS:
        if key in icon:
            return kind
    return ""


class LhmService:
    """Доступ к датчикам LibreHardwareMonitor через его веб-сервер."""

    def __init__(self, binary_path: Optional[str] = None, endpoint_url: str = DEFAULT_ENDPOINT) -> None:
        """Инициализирует сервис.

        Args:
            binary_path: Путь к LibreHardwareMonitor.exe (по умолчанию bin/LibreHardwareMonitor).
            endpoint_url: URL data.json веб-сервера LHM.
        """
        self.binary_path = str(binary_path or DEFAULT_BINARY)
        self.endpoint_url = endpoint_url

    def is_running(self) -> bool:
        """Проверяет, отвечает ли веб-сервер LHM."""
        try:
            req = urllib.request.Request(self.endpoint_url, headers={"User-Agent": "AI-Breadboard"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def is_binary_available(self) -> bool:
        """Проверяет наличие LibreHardwareMonitor.exe на диске."""
        return os.path.isfile(self.binary_path)

    def start_process(self) -> bool:
        """Запускает LHM в фоне (если ещё не запущен).

        Returns:
            bool: True, если сервер уже работает или процесс запущен.
        """
        if self.is_running():
            return True
        if not self.is_binary_available():
            logger.warning(f"Исполняемый файл LHM не найден: {self.binary_path}")
            return False
        try:
            flags = getattr(subprocess, "DETACHED_PROCESS", 0) if os.name == "nt" else 0
            subprocess.Popen([self.binary_path], creationflags=flags, close_fds=True, cwd=str(Path(self.binary_path).parent))
            logger.info(f"Запущен процесс LibreHardwareMonitor: {self.binary_path}")
            return True
        except Exception as exc:
            logger.error(f"Ошибка запуска LibreHardwareMonitor: {exc}")
            return False

    def get_sensor_tree(self) -> Optional[Dict[str, Any]]:
        """Возвращает дерево датчиков data.json.

        Returns:
            Optional[Dict[str, Any]]: Дерево или None, если сервер недоступен (задокументированный возврат).
        """
        try:
            req = urllib.request.Request(self.endpoint_url, headers={"User-Agent": "AI-Breadboard"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            logger.debug(f"Ошибка запроса к LHM Web API: {exc}")
            return None

    def get_flattened_sensors(self, tree: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Преобразует дерево LHM в плоский список датчиков.

        Args:
            tree: Готовое дерево (если None — запрашивается у сервера).

        Returns:
            List[Dict[str, Any]]: Датчики с полями hardware_name, hardware_type,
            sensor_category, sensor_name, value_raw, value_num. Пустой список, если данных нет.
        """
        tree = tree if tree is not None else self.get_sensor_tree()
        if not tree:
            return []
        result: List[Dict[str, Any]] = []
        self._walk(tree, hardware=("System", ""), category="General", out=result)
        return result

    def _walk(self, node: Any, hardware: tuple, category: str, out: List[Dict[str, Any]]) -> None:
        """Рекурсивный обход дерева: оборудование -> группа -> датчик."""
        if not isinstance(node, dict):
            return
        text = str(node.get("Text") or "").strip()
        children = node.get("Children") or []
        kind = _hardware_type(str(node.get("ImageURL") or ""))
        if kind and children:
            hardware = (text, kind)
        elif children and hardware[1]:
            category = text or category
        if not children:
            value_raw = str(node.get("Value") or "").strip()
            value_num = parse_sensor_value(value_raw)
            if text and value_num is not None and hardware[1]:
                out.append({
                    "hardware_name": hardware[0], "hardware_type": hardware[1],
                    "sensor_category": category, "sensor_name": text,
                    "value_raw": value_raw, "value_num": value_num,
                })
            return
        for child in children:
            self._walk(child, hardware, category, out)

    def find_sensor(self, hardware_pattern: str, sensor_pattern: str,
                    sensor_type_pattern: Optional[str] = None,
                    tree: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Ищет первый датчик по подстрокам (без учёта регистра).

        Returns:
            Optional[Dict[str, Any]]: Датчик или None, если не найден (задокументированный возврат).
        """
        for item in self.get_flattened_sensors(tree):
            if hardware_pattern.lower() not in f"{item['hardware_name']} {item['hardware_type']}".lower():
                continue
            if sensor_pattern.lower() not in item["sensor_name"].lower():
                continue
            if sensor_type_pattern and sensor_type_pattern.lower() not in item["sensor_category"].lower():
                continue
            return item
        return None

    def get_system_summary(self, tree: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Краткая сводка: температуры и загрузка CPU, число датчиков."""
        sensors = self.get_flattened_sensors(tree)
        temps = [s["value_num"] for s in sensors if s["hardware_type"] == "cpu" and "temperature" in s["sensor_category"].lower()]
        total = next((s["value_num"] for s in sensors if s["hardware_type"] == "cpu"
                      and s["sensor_category"].lower() == "load" and "total" in s["sensor_name"].lower()), None)
        return {
            "is_available": bool(sensors),
            "total_sensors_count": len(sensors),
            "cpu": {"temperature_max_c": max(temps) if temps else None, "load_total_percent": total},
        }


__all__ = ["DEFAULT_ENDPOINT", "DEFAULT_BINARY", "LhmService", "parse_sensor_value"]
