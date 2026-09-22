# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Sensors Sensor Collector
# =============================================================================
# Description:
#   Сбор данных со всех доступных сенсоров (HardwareMonitor + LHM).
#
# File: sensors.py
# Project: ai-sensors
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Сбор данных со всех доступных сенсоров."""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional

from logger import logger

from utils.config import ConfigManager

# Импортируем из существующих модулей
try:
    from apps.windows.hardware.hardware_monitor import HardwareMonitor
    from apps.librehardwaremonitor.core.lhm_service import LhmService
    from apps.windows.telemetry.internet_speed import InternetSpeedSensor
except ImportError as e:
    logger.warning(f"Не удалось импортировать зависимости: {e}")
    HardwareMonitor = None
    LhmService = None
    InternetSpeedSensor = None


class SensorCollector:
    """Коллектор данных со всех сенсоров."""

    def __init__(self, config_manager: Optional[ConfigManager] = None) -> None:
        """Инициализирует коллектор сенсоров.

        Args:
            config_manager: Менеджер конфигурации для настройки сенсоров.
        """
        self.config_manager = config_manager
        self._hardware_monitor = HardwareMonitor() if HardwareMonitor else None
        self._lhm_service = LhmService() if LhmService else None
        self._internet_speed_sensor = InternetSpeedSensor() if InternetSpeedSensor else None

        self._lhm_available = False
        self._lhm_tree: Optional[Dict[str, Any]] = None

        # Кэш последних данных
        self._last_hardware_snapshot: Optional[Dict[str, Any]] = None
        self._last_lhm_data: Optional[Dict[str, Any]] = None

        self._lock = threading.Lock()

        # Пробуем запустить LHM если доступен
        self._init_lhm()

    def _init_lhm(self) -> None:
        """Инициализирует LHM если доступен."""
        if self._lhm_service is None:
            logger.warning("LhmService не доступен")
            return

        if self._lhm_service.is_binary_available():
            if self._lhm_service.start_process():
                time.sleep(2)  # Ждем запуска

        self._lhm_available = self._lhm_service.is_running()
        logger.info(f"LHM Web API доступен: {self._lhm_available}")

    def _get_hardware_data(self) -> Dict[str, Any]:
        """Получает данные от HardwareMonitor.

        Returns:
            Dict[str, Any]: ДанныеHardwareMonitor.
        """
        if self._hardware_monitor is None:
            return {}

        try:
            snapshot = self._hardware_monitor.get_snapshot(include_smart=True)
            return snapshot.to_dict()
        except Exception as e:
            logger.error(f"Ошибка получения данных от HardwareMonitor: {e}")
            return {}

    def _get_lhm_data(self) -> Dict[str, Any]:
        """Получает данные от LibreHardwareMonitor.

        Returns:
            Dict[str, Any]: Данные LHM или пустой словарь.
        """
        if self._lhm_service is None:
            return {}

        if not self._lhm_available:
            return {}

        try:
            # Обновляем дерево сенсоров
            self._lhm_tree = self._lhm_service.get_sensor_tree()
            if not self._lhm_tree:
                return {}

            # Получаем плоский список сенсоров
            sensors = self._lhm_service.get_flattened_sensors(self._lhm_tree)

            # Получаем краткую сводку
            summary = self._lhm_service.get_system_summary(self._lhm_tree)

            return {
                "available": True,
                "total_sensors_count": len(sensors),
                "sensors": sensors,
                "summary": summary,
            }
        except Exception as e:
            logger.error(f"Ошибка получения данных от LHM: {e}")
            self._lhm_available = False
            return {
                "available": False,
                "error": str(e),
            }

    def _get_internet_speed_data(self) -> Dict[str, Any]:
        """Получает данные о скорости интернета.

        Returns:
            Dict[str, Any]: Данные скорости интернета.
        """
        if self._internet_speed_sensor is None:
            return {"available": False, "error": "InternetSpeedSensor not available"}

        try:
            metrics = self._internet_speed_sensor.measure_internet_speed()
            return {
                "available": True,
                "ping_ms": metrics.get("ping_ms", 0.0),
                "download_mbps": metrics.get("download_mbps", 0.0),
                "upload_mbps": metrics.get("upload_mbps", 0.0),
                "dns_ms": metrics.get("dns_ms", 0.0),
            }
        except Exception as e:
            logger.error(f"Ошибка получения данных скорости интернета: {e}")
            return {"available": False, "error": str(e)}

    def _build_sensor_metrics(self, hardware_data: Dict[str, Any], internet_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Формирует метрики сенсоров для записи.

        Args:
            hardware_data: ДанныеHardwareMonitor.
            internet_data: Данные скорости интернета.

        Returns:
            List[Dict[str, Any]]: Список метрик сенсоров.
        """
        metrics = []

        # CPU
        if "cpu" in hardware_data:
            cpu = hardware_data["cpu"]
            metrics.append({
                "sensor_name": "CPU Utilization",
                "value": cpu.get("utilization_pct", 0),
                "unit": "%",
                "category": "load",
            })
            if "per_core_pct" in cpu:
                metrics.append({
                    "sensor_name": "CPU Per-Core",
                    "value": cpu["per_core_pct"],
                    "unit": "%",
                    "category": "load",
                })
            if "frequency_current_mhz" in cpu and cpu["frequency_current_mhz"]:
                metrics.append({
                    "sensor_name": "CPU Frequency",
                    "value": cpu["frequency_current_mhz"],
                    "unit": "MHz",
                    "category": "clocks",
                })

        # RAM
        if "memory" in hardware_data:
            ram = hardware_data["memory"]
            metrics.append({
                "sensor_name": "RAM Usage",
                "value": ram.get("utilization_pct", 0),
                "unit": "%",
                "category": "load",
            })
            if "swap_utilization_pct" in ram and ram["swap_utilization_pct"]:
                metrics.append({
                    "sensor_name": "Swap Usage",
                    "value": ram["swap_utilization_pct"],
                    "unit": "%",
                    "category": "load",
                })

        # GPU
        if "gpus" in hardware_data:
            for gpu in hardware_data["gpus"]:
                if "utilization_gpu_pct" in gpu and gpu["utilization_gpu_pct"] is not None:
                    metrics.append({
                        "sensor_name": f"GPU {gpu.get('index', 'N/A')} Utilization",
                        "value": gpu["utilization_gpu_pct"],
                        "unit": "%",
                        "category": "load",
                    })
                if "temperature_gpu_c" in gpu and gpu["temperature_gpu_c"] is not None:
                    metrics.append({
                        "sensor_name": f"GPU {gpu.get('index', 'N/A')} Temperature",
                        "value": gpu["temperature_gpu_c"],
                        "unit": "°C",
                        "category": "temperature",
                    })

        # Storage
        if "storage" in hardware_data:
            storage = hardware_data["storage"]
            if "partitions" in storage:
                for part in storage["partitions"]:
                    metrics.append({
                        "sensor_name": f"Disk {part.get('device', 'N/A')} Usage",
                        "value": part.get("utilization_pct", 0),
                        "unit": "%",
                        "category": "load",
                    })
            if "io_rates" in storage and storage["io_rates"]:
                io = storage["io_rates"]
                metrics.append({
                    "sensor_name": "Disk Read Rate",
                    "value": io.get("read_bytes_sec", 0),
                    "unit": "B/s",
                    "category": "throughput",
                })
                metrics.append({
                    "sensor_name": "Disk Write Rate",
                    "value": io.get("write_bytes_sec", 0),
                    "unit": "B/s",
                    "category": "throughput",
                })

        # Sensors (from HardwareMonitor)
        if "sensors" in hardware_data:
            for s in hardware_data["sensors"]:
                metrics.append({
                    "sensor_name": s.get("name", "Unknown"),
                    "value": s.get("value", 0),
                    "unit": s.get("unit", ""),
                    "category": s.get("category", "general"),
                })

        # Network
        if "network" in hardware_data:
            net = hardware_data["network"]
            metrics.append({
                "sensor_name": "Network Sent Rate",
                "value": net.get("bytes_sent_sec", 0),
                "unit": "B/s",
                "category": "throughput",
            })
            metrics.append({
                "sensor_name": "Network Received Rate",
                "value": net.get("bytes_recv_sec", 0),
                "unit": "B/s",
                "category": "throughput",
            })

        # Battery
        if "battery" in hardware_data:
            batt = hardware_data["battery"]
            if batt.get("has_battery", False) and batt.get("percent") is not None:
                metrics.append({
                    "sensor_name": "Battery Level",
                    "value": batt["percent"],
                    "unit": "%",
                    "category": "power",
                })

        # LHM sensors
        if self._last_lhm_data and self._last_lhm_data.get("available"):
            lhm_sensors = self._last_lhm_data.get("sensors", [])
            for s in lhm_sensors[:50]:  # Лимит для избежания слишком больших данных
                metrics.append({
                    "sensor_name": f"LHM {s.get('hardware_name', 'Unknown')} - {s.get('sensor_name', 'Unknown')}",
                    "value": s.get("value_num", 0),
                    "unit": s.get("unit", ""),
                    "category": s.get("sensor_category", "general"),
                })

        # Internet speed sensors
        if internet_data and internet_data.get("available"):
            metrics.append({
                "sensor_name": "Internet Ping",
                "value": internet_data.get("ping_ms", 0),
                "unit": "ms",
                "category": "network",
            })
            metrics.append({
                "sensor_name": "Internet Download Speed",
                "value": internet_data.get("download_mbps", 0),
                "unit": "Mbps",
                "category": "network",
            })
            metrics.append({
                "sensor_name": "Internet Upload Speed",
                "value": internet_data.get("upload_mbps", 0),
                "unit": "Mbps",
                "category": "network",
            })
            metrics.append({
                "sensor_name": "Internet DNS Resolution",
                "value": internet_data.get("dns_ms", 0),
                "unit": "ms",
                "category": "network",
            })

        return metrics

    def get_hardware_snapshot(self) -> Dict[str, Any]:
        """Получает полный снапшот аппаратного состояния.

        Returns:
            Dict[str, Any]: Снапшот с данными от всех сенсоров.
        """
        with self._lock:
            # Получаем данные от HardwareMonitor
            hardware_data = self._get_hardware_data()

            # Получаем данные от LHM
            lhm_data = self._get_lhm_data()
            self._last_lhm_data = lhm_data

            # Получаем данные от интернет-скорости
            internet_data = self._get_internet_speed_data()

            # Формируем метрики сенсоров
            sensor_metrics = self._build_sensor_metrics(hardware_data, internet_data)

            # Собираем финальный результат
            result = {
                "timestamp": f"{time.time():.6f}",
                "hardware_monitor": hardware_data if hardware_data else {},
                "libre_hardware_monitor": lhm_data if lhm_data else {},
                "internet_speed": internet_data if internet_data else {},
                "sensor_metrics": sensor_metrics,
            }

            self._last_hardware_snapshot = result
            return result

    def get_last_snapshot(self) -> Optional[Dict[str, Any]]:
        """Возвращает последний собранный снапшот.

        Returns:
            Optional[Dict[str, Any]]: Последний снапшот или None.
        """
        return self._last_hardware_snapshot
