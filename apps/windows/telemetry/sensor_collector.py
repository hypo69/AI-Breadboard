# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Telemetry Hardware & Sensors Collector
# =============================================================================
# Description:
#   Сбор данных со всех доступных аппаратных датчиков и сетевых сенсоров
#   (HardwareMonitor + LhmService + InternetSpeedSensor) со структурированной
#   схемой данных: id, hardware_name, hardware_type, sensor_category,
#   sensor_name, unit, values: [{"num": float, "time": iso_str}].
#
# File: sensor_collector.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Сбор данных со всех доступных сенсоров и аппаратных провайдеров."""

from __future__ import annotations

import re
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    from src.logger.logger import logger
except ImportError:
    from logger import logger
from apps.windows.telemetry.telemetry_config import TelemetryConfigManager

try:
    from apps.windows.hardware.hardware_monitor import HardwareMonitor
    from apps.windows.hardware.lhm_service import LhmService
    from apps.windows.telemetry.internet_speed import InternetSpeedSensor
except ImportError as e:
    logger.warning(f"Не удалось импортировать зависимости сенсоров: {e}")
    HardwareMonitor = None
    LhmService = None
    InternetSpeedSensor = None


class SensorCollector:
    """Коллектор данных со всех сенсоров с нормализованной схемой датчиков."""

    def __init__(self, config_manager: Optional[TelemetryConfigManager] = None) -> None:
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

        # Пробуем инициализировать LHM если доступен
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
            Dict[str, Any]: Данные HardwareMonitor.
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
            self._lhm_tree = self._lhm_service.get_sensor_tree()
            if not self._lhm_tree:
                return {}

            sensors = self._lhm_service.get_flattened_sensors(self._lhm_tree)
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

    def extract_sensor_readings(
        self,
        hardware_data: Dict[str, Any],
        lhm_data: Dict[str, Any],
        internet_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Извлекает нормализованный список всех текущих показаний датчиков.

        Каждый элемент содержит: id, hardware_name, hardware_type, sensor_category,
        sensor_name, unit, value.

        Args:
            hardware_data: Данные HardwareMonitor.
            lhm_data: Данные LibreHardwareMonitor.
            internet_data: Данные скорости интернета.

        Returns:
            List[Dict[str, Any]]: Нормализованный список сенсоров.
        """
        readings: List[Dict[str, Any]] = []

        # 1. LibreHardwareMonitor сенсоры (если доступны - они первичны и детальны)
        if lhm_data and lhm_data.get("available") and "sensors" in lhm_data:
            for s in lhm_data.get("sensors", []):
                readings.append({
                    "id": s.get("id"),
                    "hardware_name": s.get("hardware_name", "System"),
                    "hardware_type": s.get("hardware_type", "cpu"),
                    "sensor_category": s.get("sensor_category", "General"),
                    "sensor_name": s.get("sensor_name", "Unknown"),
                    "unit": s.get("unit", ""),
                    "value": s.get("value_num", 0.0),
                })

        # 2. CPU (HardwareMonitor)
        if "cpu" in hardware_data:
            cpu = hardware_data["cpu"]
            cpu_name = cpu.get("model") or cpu.get("model_name") or "Intel Core Processor"
            readings.append({
                "id": "cpu_util_total",
                "hardware_name": cpu_name,
                "hardware_type": "cpu",
                "sensor_category": "Load",
                "sensor_name": "CPU Total",
                "unit": "%",
                "value": cpu.get("utilization_pct", 0.0),
            })
            if "per_core_pct" in cpu and isinstance(cpu["per_core_pct"], list):
                for idx, core_val in enumerate(cpu["per_core_pct"]):
                    readings.append({
                        "id": f"cpu_core_{idx}_load",
                        "hardware_name": cpu_name,
                        "hardware_type": "cpu",
                        "sensor_category": "Load",
                        "sensor_name": f"CPU Core #{idx}",
                        "unit": "%",
                        "value": core_val,
                    })
            if "frequency_current_mhz" in cpu and cpu["frequency_current_mhz"]:
                readings.append({
                    "id": "cpu_freq_current",
                    "hardware_name": cpu_name,
                    "hardware_type": "cpu",
                    "sensor_category": "Clocks",
                    "sensor_name": "CPU Core Frequency",
                    "unit": "MHz",
                    "value": cpu["frequency_current_mhz"],
                })

        # 3. RAM / Memory
        if "memory" in hardware_data:
            ram = hardware_data["memory"]
            readings.append({
                "id": "ram_util_pct",
                "hardware_name": "System Memory",
                "hardware_type": "memory",
                "sensor_category": "Load",
                "sensor_name": "Memory Used",
                "unit": "%",
                "value": ram.get("utilization_pct", 0.0),
            })
            if "swap_utilization_pct" in ram and ram["swap_utilization_pct"] is not None:
                readings.append({
                    "id": "swap_util_pct",
                    "hardware_name": "System Memory",
                    "hardware_type": "memory",
                    "sensor_category": "Load",
                    "sensor_name": "Swap Used",
                    "unit": "%",
                    "value": ram["swap_utilization_pct"],
                })

        # 4. GPU
        if "gpus" in hardware_data and isinstance(hardware_data["gpus"], list):
            for gpu in hardware_data["gpus"]:
                gpu_name = gpu.get("name", "GPU")
                gpu_idx = gpu.get("index", 0)
                if "temperature_gpu_c" in gpu and gpu["temperature_gpu_c"] is not None:
                    readings.append({
                        "id": f"gpu_{gpu_idx}_temp",
                        "hardware_name": gpu_name,
                        "hardware_type": "gpu",
                        "sensor_category": "Temperatures",
                        "sensor_name": "GPU Core Temperature",
                        "unit": "°C",
                        "value": gpu["temperature_gpu_c"],
                    })
                if "utilization_gpu_pct" in gpu and gpu["utilization_gpu_pct"] is not None:
                    readings.append({
                        "id": f"gpu_{gpu_idx}_load",
                        "hardware_name": gpu_name,
                        "hardware_type": "gpu",
                        "sensor_category": "Load",
                        "sensor_name": "GPU Core Load",
                        "unit": "%",
                        "value": gpu["utilization_gpu_pct"],
                    })

        # 5. Storage
        if "storage" in hardware_data:
            storage = hardware_data["storage"]
            if "partitions" in storage and isinstance(storage["partitions"], list):
                for part in storage["partitions"]:
                    dev = part.get("device", "Disk")
                    readings.append({
                        "id": f"storage_usage_{dev.replace(':', '').replace(chr(92), '')}",
                        "hardware_name": f"Storage ({dev})",
                        "hardware_type": "storage",
                        "sensor_category": "Load",
                        "sensor_name": f"Used Space {dev}",
                        "unit": "%",
                        "value": part.get("utilization_pct", 0.0),
                    })
            if "io_rates" in storage and storage["io_rates"]:
                io = storage["io_rates"]
                readings.append({
                    "id": "storage_read_rate",
                    "hardware_name": "Storage",
                    "hardware_type": "storage",
                    "sensor_category": "Throughput",
                    "sensor_name": "Disk Read Rate",
                    "unit": "B/s",
                    "value": io.get("read_bytes_sec", 0.0),
                })
                readings.append({
                    "id": "storage_write_rate",
                    "hardware_name": "Storage",
                    "hardware_type": "storage",
                    "sensor_category": "Throughput",
                    "sensor_name": "Disk Write Rate",
                    "unit": "B/s",
                    "value": io.get("write_bytes_sec", 0.0),
                })

        # 6. Network
        if "network" in hardware_data:
            net = hardware_data["network"]
            readings.append({
                "id": "network_sent_rate",
                "hardware_name": "Network",
                "hardware_type": "network",
                "sensor_category": "Throughput",
                "sensor_name": "Network Upload Speed",
                "unit": "B/s",
                "value": net.get("bytes_sent_sec", 0.0),
            })
            readings.append({
                "id": "network_recv_rate",
                "hardware_name": "Network",
                "hardware_type": "network",
                "sensor_category": "Throughput",
                "sensor_name": "Network Download Speed",
                "unit": "B/s",
                "value": net.get("bytes_recv_sec", 0.0),
            })

        # 7. Internet Speed
        if internet_data and internet_data.get("available"):
            readings.append({
                "id": "internet_ping",
                "hardware_name": "Internet",
                "hardware_type": "network",
                "sensor_category": "Latency",
                "sensor_name": "Internet Ping Latency",
                "unit": "ms",
                "value": internet_data.get("ping_ms", 0.0),
            })
            readings.append({
                "id": "internet_download_speed",
                "hardware_name": "Internet",
                "hardware_type": "network",
                "sensor_category": "Throughput",
                "sensor_name": "Internet Download Bandwidth",
                "unit": "Mbps",
                "value": internet_data.get("download_mbps", 0.0),
            })

        return readings

    def get_hardware_snapshot(self) -> Dict[str, Any]:
        """Получает полный снапшот аппаратного состояния со списком сенсоров.

        Returns:
            Dict[str, Any]: Снапшот со списком показаний сенсоров.
        """
        with self._lock:
            now_iso = datetime.now(timezone.utc).isoformat()
            hardware_data = self._get_hardware_data()
            lhm_data = self._get_lhm_data()
            self._last_lhm_data = lhm_data
            internet_data = self._get_internet_speed_data()

            sensor_readings = self.extract_sensor_readings(hardware_data, lhm_data, internet_data)

            # Формируем объекты с массивом values
            sensors_payload = []
            for r in sensor_readings:
                sensors_payload.append({
                    "id": r.get("id"),
                    "hardware_name": r.get("hardware_name"),
                    "hardware_type": r.get("hardware_type"),
                    "sensor_category": r.get("sensor_category"),
                    "sensor_name": r.get("sensor_name"),
                    "unit": r.get("unit"),
                    "values": [
                        {"num": r.get("value", 0.0), "time": now_iso}
                    ],
                })

            result = {
                "timestamp": now_iso,
                "sensors": sensors_payload,
                "hardware_monitor": hardware_data if hardware_data else {},
                "libre_hardware_monitor": lhm_data if lhm_data else {},
                "internet_speed": internet_data if internet_data else {},
            }

            self._last_hardware_snapshot = result
            return result

    def get_last_snapshot(self) -> Optional[Dict[str, Any]]:
        """Возвращает последний собранный снапшот.

        Returns:
            Optional[Dict[str, Any]]: Последний снапшот или None.
        """
        return self._last_hardware_snapshot
