# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry - Sensor Collector
# =============================================================================
# Description:
#   Сбор данных со всех доступных сенсоров и аппаратных провайдеров.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.sensor_collector import SensorCollector
#
#     service = SensorCollector()
#
# File: sensor_collector.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 07:00:00
# =============================================================================

from __future__ import annotations
"""Сбор данных со всех доступных сенсоров и аппаратных провайдеров."""

import re
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
try:
    from logger import logger
except ImportError:
    from logger import logger
from .telemetry_config import TelemetryConfigManager
from .sensor_registry import SensorDeduplicator, SensorProvider
try:
    from apps.windows.modules.hardware.hardware_monitor import HardwareMonitor
    from apps.windows.modules.hardware.lhm_service import LhmService
    from .internet_speed import InternetSpeedSensor
except ImportError as e:
    logger.warning(f'Не удалось импортировать зависимости сенсоров: {e}')
    HardwareMonitor = None
    LhmService = None
    InternetSpeedSensor = None

class SensorCollector:
    """Коллектор данных со всех сенсоров с нормализованной схемой датчиков."""

    def __init__(
        self,
        config_manager: Optional[TelemetryConfigManager] = None,
        lhm_service: Optional[Any] = None,
    ) -> None:
        """Инициализирует коллектор сенсоров.

        Args:
            config_manager: Менеджер конфигурации для настройки сенсоров.
            lhm_service: Сервис LibreHardwareMonitor (опционально).
        """
        self.config_manager = config_manager
        self._lhm_service = lhm_service or (LhmService() if LhmService else None)
        self._hardware_monitor = HardwareMonitor() if HardwareMonitor else None
        self._internet_speed_sensor = InternetSpeedSensor() if InternetSpeedSensor else None
        self._last_hardware_snapshot: Optional[Dict[str, Any]] = None
        self._lock = threading.Lock()

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
            logger.error(f'Ошибка получения данных от HardwareMonitor: {e}')
            return {}

    def _get_internet_speed_data(self) -> Dict[str, Any]:
        """Получает данные о скорости интернета и задержке через FAST.com.

        Returns:
            Dict[str, Any]: Данные скорости интернета (download, upload, ping, bufferbloat, loaded latency).
        """
        if self._internet_speed_sensor is None:
            return {'available': False, 'error': 'InternetSpeedSensor not available'}
        try:
            metrics = self._internet_speed_sensor.measure_internet_speed()
            return {
                'available': metrics.get('available', True),
                'ping_ms': metrics.get('ping_ms', 0.0),
                'download_mbps': metrics.get('download_mbps', 0.0),
                'upload_mbps': metrics.get('upload_mbps', 0.0),
                'latency_unloaded_ms': metrics.get('latency_unloaded_ms', metrics.get('ping_ms', 0.0)),
                'latency_loaded_ms': metrics.get('latency_loaded_ms', 0.0),
                'bufferbloat_ms': metrics.get('bufferbloat_ms', 0.0),
                'provider': metrics.get('provider', 'fast.com'),
                'server': metrics.get('server', ''),
                'ip': metrics.get('ip', ''),
                'isp': metrics.get('isp', ''),
            }
        except Exception as e:
            logger.error(f'Ошибка получения данных скорости интернета: {e}')
            return {'available': False, 'error': str(e)}

    def _detect_provider(self, sensor_id: str, category: str, hardware_type: str) -> SensorProvider:
        """Определяет провайдера сенсора на основе его ID, категории и источника.
        
        Args:
            sensor_id: Идентификатор сенсора.
            category: Категория сенсора (Temperatures, Load, etc.).
            hardware_type: Тип оборудования (cpu, gpu, etc.).
            
        Returns:
            SensorProvider: Провайдер сенсора.
        """
        # GPU sensors from GpuProber
        if sensor_id.startswith('gpu_') and ('_temp' in sensor_id or '_load' in sensor_id):
            return SensorProvider.GPU_PROBER
        
        # Storage sensors
        if sensor_id.startswith('disk_') or sensor_id.startswith('storage_'):
            return SensorProvider.WINDOWS_STORAGE
        
        # Internet speed sensors
        if sensor_id.startswith('internet_'):
            return SensorProvider.INTERNET_SPEED
        
        # Network sensors
        if sensor_id.startswith('net_'):
            return SensorProvider.NETWORK_SENSOR
        
        # CPU/RAM utilization from sensor_collector
        if sensor_id in ('cpu_util_total', 'ram_util_pct', 'swap_util_pct'):
            return SensorProvider.SENSOR_COLLECTOR
        
        if sensor_id.startswith('cpu_core_') and '_load' in sensor_id:
            return SensorProvider.SENSOR_COLLECTOR
        
        if sensor_id.startswith('cpu_freq'):
            return SensorProvider.SENSOR_COLLECTOR
        
        # OneDrive sensors
        if sensor_id.startswith('onedrive_'):
            return SensorProvider.SENSOR_COLLECTOR
        
        # Network rates
        if sensor_id in ('network_sent_rate', 'network_recv_rate'):
            return SensorProvider.SENSOR_COLLECTOR
        
        # Storage usage
        if sensor_id.startswith('storage_usage_') or sensor_id in ('storage_read_rate', 'storage_write_rate'):
            return SensorProvider.SENSOR_COLLECTOR
        
        # Default based on category
        if category in ('Temperatures', 'temperature'):
            return SensorProvider.ACPI_THERMAL
        
        return SensorProvider.SENSOR_COLLECTOR

    def extract_sensor_readings(
        self, hardware_data: Dict[str, Any], *args: Any, internet_data: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """Извлекает нормализованный список всех текущих показаний датчиков с дедупликацией.

        Каждый элемент содержит: id, hardware_name, hardware_type, sensor_category,
        sensor_name, unit, value, _provider.

        Args:
            hardware_data: Данные HardwareMonitor.
            *args: Опциональные extra_sensors_data и/или internet_data.
            internet_data: Данные скорости интернета (если переданы явно).

        Returns:
            List[Dict[str, Any]]: Нормализованный и дедуплицированный список сенсоров.
        """
        extra_sensors_data = None
        if len(args) == 1:
            if isinstance(args[0], dict) and ("ping_ms" in args[0] or "download_mbps" in args[0] or "available" in args[0]):
                internet_data = args[0]
            else:
                extra_sensors_data = args[0]
        elif len(args) >= 2:
            extra_sensors_data = args[0]
            internet_data = args[1]

        raw_readings: List[Dict[str, Any]] = []

        # Дополнительные внешние сенсоры
        if extra_sensors_data and isinstance(extra_sensors_data, dict) and "sensors" in extra_sensors_data:
            for s in extra_sensors_data["sensors"]:
                if isinstance(s, dict):
                    sensor_id = s.get("id", s.get("sensor_name", "sensor"))
                    category = s.get("sensor_category", "Metric")
                    hardware_type = s.get("hardware_type", "sensor")
                    provider = self._detect_provider(str(sensor_id), category, hardware_type)
                    raw_readings.append({
                        "id": sensor_id,
                        "hardware_name": s.get("hardware_name", "Hardware"),
                        "hardware_type": hardware_type,
                        "sensor_category": category,
                        "sensor_name": s.get("sensor_name", "Sensor"),
                        "unit": s.get("unit", ""),
                        "value": s.get("value_num", s.get("value", 0.0)),
                        "_provider": provider,
                    })
        
        if 'cpu' in hardware_data:
            cpu = hardware_data['cpu']
            cpu_name = cpu.get('model') or cpu.get('model_name') or 'Intel Core Processor'
            raw_readings.append({
                'id': 'cpu_util_total',
                'hardware_name': cpu_name,
                'hardware_type': 'cpu',
                'sensor_category': 'Load',
                'sensor_name': 'CPU Total',
                'unit': '%',
                'value': cpu.get('utilization_pct', 0.0),
                '_provider': SensorProvider.SENSOR_COLLECTOR
            })
            if 'per_core_pct' in cpu and isinstance(cpu['per_core_pct'], list):
                for idx, core_val in enumerate(cpu['per_core_pct']):
                    raw_readings.append({
                        'id': f'cpu_core_{idx}_load',
                        'hardware_name': cpu_name,
                        'hardware_type': 'cpu',
                        'sensor_category': 'Load',
                        'sensor_name': f'CPU Core #{idx}',
                        'unit': '%',
                        'value': core_val,
                        '_provider': SensorProvider.SENSOR_COLLECTOR
                    })
            if 'frequency_current_mhz' in cpu and cpu['frequency_current_mhz']:
                raw_readings.append({
                    'id': 'cpu_freq_current',
                    'hardware_name': cpu_name,
                    'hardware_type': 'cpu',
                    'sensor_category': 'Clocks',
                    'sensor_name': 'CPU Core Frequency',
                    'unit': 'MHz',
                    'value': cpu['frequency_current_mhz'],
                    '_provider': SensorProvider.SENSOR_COLLECTOR
                })
        
        if 'memory' in hardware_data:
            ram = hardware_data['memory']
            raw_readings.append({
                'id': 'ram_util_pct',
                'hardware_name': 'System Memory',
                'hardware_type': 'memory',
                'sensor_category': 'Load',
                'sensor_name': 'Memory Used',
                'unit': '%',
                'value': ram.get('utilization_pct', 0.0),
                '_provider': SensorProvider.SENSOR_COLLECTOR
            })
            if 'swap_utilization_pct' in ram and ram['swap_utilization_pct'] is not None:
                raw_readings.append({
                    'id': 'swap_util_pct',
                    'hardware_name': 'System Memory',
                    'hardware_type': 'memory',
                    'sensor_category': 'Load',
                    'sensor_name': 'Swap Used',
                    'unit': '%',
                    'value': ram['swap_utilization_pct'],
                    '_provider': SensorProvider.SENSOR_COLLECTOR
                })
        
        # GPU metrics: temperature and load are already collected via GpuProber
        # in HardwareMonitor, so we normalize them here without re-probing
        if 'gpus' in hardware_data and isinstance(hardware_data['gpus'], list):
            for gpu in hardware_data['gpus']:
                gpu_name = gpu.get('name', 'GPU')
                gpu_idx = gpu.get('index', 0)
                # GPU temperature - use hardware_data from GpuProber
                if 'temperature_gpu_c' in gpu and gpu['temperature_gpu_c'] is not None:
                    raw_readings.append({
                        'id': f'gpu_{gpu_idx}_temp',
                        'hardware_name': gpu_name,
                        'hardware_type': 'gpu',
                        'sensor_category': 'Temperatures',
                        'sensor_name': 'GPU Core Temperature',
                        'unit': '°C',
                        'value': gpu['temperature_gpu_c'],
                        '_provider': SensorProvider.GPU_PROBER
                    })
                # GPU load
                if 'utilization_gpu_pct' in gpu and gpu['utilization_gpu_pct'] is not None:
                    raw_readings.append({
                        'id': f'gpu_{gpu_idx}_load',
                        'hardware_name': gpu_name,
                        'hardware_type': 'gpu',
                        'sensor_category': 'Load',
                        'sensor_name': 'GPU Core Load',
                        'unit': '%',
                        'value': gpu['utilization_gpu_pct'],
                        '_provider': SensorProvider.GPU_PROBER
                    })
        
        if 'storage' in hardware_data:
            storage = hardware_data['storage']
            if 'partitions' in storage and isinstance(storage['partitions'], list):
                for part in storage['partitions']:
                    dev = part.get('device', 'Disk')
                    raw_readings.append({
                        'id': f"storage_usage_{dev.replace(':', '').replace(chr(92), '')}",
                        'hardware_name': f'Storage ({dev})',
                        'hardware_type': 'storage',
                        'sensor_category': 'Load',
                        'sensor_name': f'Used Space {dev}',
                        'unit': '%',
                        'value': part.get('utilization_pct', 0.0),
                        '_provider': SensorProvider.SENSOR_COLLECTOR
                    })
            if 'io_rates' in storage and storage['io_rates']:
                io = storage['io_rates']
                raw_readings.append({
                    'id': 'storage_read_rate',
                    'hardware_name': 'Storage',
                    'hardware_type': 'storage',
                    'sensor_category': 'Throughput',
                    'sensor_name': 'Disk Read Rate',
                    'unit': 'B/s',
                    'value': io.get('read_bytes_sec', 0.0),
                    '_provider': SensorProvider.SENSOR_COLLECTOR
                })
                raw_readings.append({
                    'id': 'storage_write_rate',
                    'hardware_name': 'Storage',
                    'hardware_type': 'storage',
                    'sensor_category': 'Throughput',
                    'sensor_name': 'Disk Write Rate',
                    'unit': 'B/s',
                    'value': io.get('write_bytes_sec', 0.0),
                    '_provider': SensorProvider.SENSOR_COLLECTOR
                })
        
        # Network metrics: aggregated throughput rates
        # Note: Detailed per-interface stats are collected by _probe_network_sensors() in sensors.py
        if 'network' in hardware_data:
            net = hardware_data['network']
            raw_readings.append({
                'id': 'network_sent_rate',
                'hardware_name': 'Network',
                'hardware_type': 'network',
                'sensor_category': 'Throughput',
                'sensor_name': 'Network Upload Speed',
                'unit': 'B/s',
                'value': net.get('bytes_sent_sec', 0.0),
                '_provider': SensorProvider.SENSOR_COLLECTOR
            })
            raw_readings.append({
                'id': 'network_recv_rate',
                'hardware_name': 'Network',
                'hardware_type': 'network',
                'sensor_category': 'Throughput',
                'sensor_name': 'Network Download Speed',
                'unit': 'B/s',
                'value': net.get('bytes_recv_sec', 0.0),
                '_provider': SensorProvider.SENSOR_COLLECTOR
            })
        
        # Internet speed metrics
        if internet_data and internet_data.get('available'):
            raw_readings.append({
                'id': 'internet_download_speed',
                'hardware_name': 'Internet',
                'hardware_type': 'network',
                'sensor_category': 'Throughput',
                'sensor_name': 'Internet Download Bandwidth',
                'unit': 'Mbps',
                'value': internet_data.get('download_mbps', 0.0),
                '_provider': SensorProvider.INTERNET_SPEED
            })
            raw_readings.append({
                'id': 'internet_upload_speed',
                'hardware_name': 'Internet',
                'hardware_type': 'network',
                'sensor_category': 'Throughput',
                'sensor_name': 'Internet Upload Bandwidth',
                'unit': 'Mbps',
                'value': internet_data.get('upload_mbps', 0.0),
                '_provider': SensorProvider.INTERNET_SPEED
            })
            raw_readings.append({
                'id': 'internet_ping',
                'hardware_name': 'Internet',
                'hardware_type': 'network',
                'sensor_category': 'Throughput',
                'sensor_name': 'Internet Ping Latency',
                'unit': 'ms',
                'value': internet_data.get('ping_ms', 0.0),
                '_provider': SensorProvider.INTERNET_SPEED
            })
            raw_readings.append({
                'id': 'internet_bufferbloat',
                'hardware_name': 'Internet',
                'hardware_type': 'network',
                'sensor_category': 'Throughput',
                'sensor_name': 'Internet Bufferbloat',
                'unit': 'ms',
                'value': internet_data.get('bufferbloat_ms', 0.0),
                '_provider': SensorProvider.INTERNET_SPEED
            })
            raw_readings.append({
                'id': 'internet_latency_loaded',
                'hardware_name': 'Internet',
                'hardware_type': 'network',
                'sensor_category': 'Throughput',
                'sensor_name': 'Internet Loaded Latency',
                'unit': 'ms',
                'value': internet_data.get('latency_loaded_ms', 0.0),
                '_provider': SensorProvider.INTERNET_SPEED
            })
        
        # Дедупликация базовых показаний по приоритету провайдера
        deduplicator = SensorDeduplicator()
        unique_readings: List[Dict[str, Any]] = []
        
        for reading in raw_readings:
            sensor_id = str(reading.get('id', ''))
            value = reading.get('value', 0.0)
            provider = reading.get('_provider', SensorProvider.SENSOR_COLLECTOR)
            
            if deduplicator.add(sensor_id, provider, value):
                unique_readings.append(reading)

        # Обогащение из LibreHardwareMonitor (добавляются ТОЛЬКО сенсоры, отсутствующие в базовом пуле CIM/WMI)
        if self._lhm_service and self._lhm_service.is_running():
            try:
                lhm_items = self._lhm_service.get_flattened_sensors()
                existing_ids = {str(r.get('id', '')) for r in unique_readings}
                for item in lhm_items:
                    hw_name = item.get("hardware_name", "Hardware")
                    hw_type = item.get("hardware_type", "sensor")
                    cat = item.get("sensor_category", "General")
                    s_name = item.get("sensor_name", "Sensor")
                    
                    if "Distance to TjMax" in s_name:
                        continue
                        
                    val_num = item.get("value_num")
                    if val_num is None:
                        continue
                        
                    vraw = str(item.get("value_raw") or "").lower()
                    unit = ""
                    if "°c" in vraw or "c" in vraw:
                        unit = "°C"
                    elif "%" in vraw:
                        unit = "%"
                    elif "rpm" in vraw:
                        unit = "RPM"
                    elif "v" in vraw and "w" not in vraw:
                        unit = "V"
                    elif "w" in vraw:
                        unit = "W"
                    elif "mhz" in vraw:
                        unit = "MHz"
                    elif "b/s" in vraw:
                        unit = "B/s"
                    elif "gb" in vraw:
                        unit = "GB"

                    clean_hw = re.sub(r'[^a-zA-Z0-9]+', '_', hw_name.lower()).strip('_')
                    clean_name = re.sub(r'[^a-zA-Z0-9]+', '_', s_name.lower()).strip('_')
                    sid = f"lhm_{clean_hw}_{clean_name}"

                    # Пропускаем, если такой датчик уже есть или это дубликат общей нагрузки CPU/RAM
                    if sid in existing_ids or (cat == "Load" and "total" in clean_name and any("util_total" in eid for eid in existing_ids)):
                        continue

                    existing_ids.add(sid)
                    unique_readings.append({
                        'id': sid,
                        'hardware_name': hw_name,
                        'hardware_type': hw_type,
                        'sensor_category': cat,
                        'sensor_name': s_name,
                        'unit': unit,
                        'value': float(val_num),
                        '_provider': SensorProvider.LHM_ENRICHED,
                    })
            except Exception as lhm_err:
                logger.debug(f'Ошибка обогащения сенсорами LHM: {lhm_err}')
        
        return unique_readings

    def get_hardware_snapshot(self) -> Dict[str, Any]:
        """Получает полный снапшот аппаратного состояния со списком сенсоров.

        Returns:
            Dict[str, Any]: Снапшот со списком показаний сенсоров.
        """
        with self._lock:
            now_iso = datetime.now(timezone.utc).isoformat()
            hardware_data = self._get_hardware_data()
            internet_data = self._get_internet_speed_data()
            sensor_readings = self.extract_sensor_readings(hardware_data, internet_data)
            sensors_payload = []
            for r in sensor_readings:
                sensors_payload.append({'id': r.get('id'), 'hardware_name': r.get('hardware_name'), 'hardware_type': r.get('hardware_type'), 'sensor_category': r.get('sensor_category'), 'sensor_name': r.get('sensor_name'), 'unit': r.get('unit'), 'values': [{'num': r.get('value', 0.0), 'time': now_iso}]})
            result = {'timestamp': now_iso, 'sensors': sensors_payload, 'hardware_monitor': hardware_data if hardware_data else {}, 'internet_speed': internet_data if internet_data else {}}
            self._last_hardware_snapshot = result
            return result

    def get_last_snapshot(self) -> Optional[Dict[str, Any]]:
        """Возвращает последний собранный снапшот.

        Returns:
            Optional[Dict[str, Any]]: Последний снапшот или None.
        """
        return self._last_hardware_snapshot

    def collect_all_sensors(self) -> List[Dict[str, Any]]:
        """Собирает показания всех доступных датчиков.

        Returns:
            List[Dict[str, Any]]: Список прочитанных сенсоров.
        """
        with self._lock:
            hardware_data = self._get_hardware_data()
            internet_data = self._get_internet_speed_data()
            return self.extract_sensor_readings(hardware_data, internet_data)

    def collect_lhm_cpu_readings(self) -> List[Dict[str, Any]]:
        """Извлекает нормализованные показания температур ядер CPU и Package из LHM.

        Returns:
            List[Dict[str, Any]]: Список показаний датчиков температур.
        """
        from apps.windows.modules.hardware.lhm_service import LhmService
        lhm = self._lhm_service or LhmService()
        items = lhm.get_flattened_sensors()
        results: List[Dict[str, Any]] = []
        core_idx = 0
        for item in items:
            if item.get("hardware_type") != "cpu" or item.get("sensor_category") != "Temperatures":
                continue
            name = item.get("sensor_name", "")
            if "Distance to TjMax" in name:
                continue
            val = item.get("value_num")
            if val is None:
                continue
            if "Package" in name:
                results.append({
                    "id": "cpu_package_temp",
                    "hardware_name": item.get("hardware_name", "CPU"),
                    "hardware_type": "cpu",
                    "sensor_category": "Temperatures",
                    "sensor_name": name,
                    "unit": "°C",
                    "value": val,
                    "value_num": val,
                })
            elif "Core" in name:
                results.append({
                    "id": f"cpu_core_{core_idx}_temp",
                    "hardware_name": item.get("hardware_name", "CPU"),
                    "hardware_type": "cpu",
                    "sensor_category": "Temperatures",
                    "sensor_name": name,
                    "unit": "°C",
                    "value": val,
                    "value_num": val,
                })
                core_idx += 1
        return results
