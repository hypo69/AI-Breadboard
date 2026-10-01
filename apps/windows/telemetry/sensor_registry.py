# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry - Sensor Registry
# =============================================================================
# Description:
#   Реестр сенсоров и политика дедупликации.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.sensor_registry import SensorProvider
#
#     service = SensorProvider()
#
# File: sensor_registry.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Реестр сенсоров и политика дедупликации."""

# -*- coding: utf-8 -*-
# Updated: 2026-10-01 10:00:00
"""Реестр сенсоров и политика дедупликации.

Централизованный модуль для управления уникальностью sensor_id,
приоритетами провайдеров и дедупликацией показаний сенсоров.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timezone


class SensorProvider(Enum):
    """Приоритеты провайдеров сенсоров (выше значение = выше приоритет).
    
    Приоритеты распределены так:
    - Специализированные провайдеры (GPU_PROBER, WINDOWS_STORAGE) имеют высший приоритет для своих доменов
    - Универсальные коллекторы (SENSOR_COLLECTOR) имеют средний приоритет
    - Прямые вызовы утилит (NVIDIA_SMI_DIRECT) имеют низший приоритет (есть риск дублирования)
    """
    NVIDIA_SMI_DIRECT = 10      # Прямой вызов nvidia-smi в sensors.py (устарело, используется GPU_PROBER)
    GPU_PROBER = 40             # GpuProber - приоритет для GPU метрик
    ACPI_THERMAL = 20           # ACPI thermal zones через WMI
    HARDWARE_MONITOR = 35       # HardwareMonitor (агрегатор, использует GpuProber)
    SENSOR_COLLECTOR = 30       # SensorCollector.extract_sensor_readings() - агрегирует hardware_data
    WINDOWS_STORAGE = 45        # WindowsStorageSensor (SMART, temps) - приоритет для storage
    NETWORK_SENSOR = 25         # Network sensors через psutil
    INTERNET_SPEED = 55         # InternetSpeedSensor - приоритет для speedtest метрик


@dataclass
class SensorDefinition:
    """Определение сенсора с политикой дедупликации."""
    sensor_id: str
    category: str
    preferred_provider: SensorProvider
    description: str = ""
    unit: str = ""
    allow_multiple_sources: bool = False  # Если True, дубликаты разрешены с разными провайдерами
    dedup_window_seconds: float = 1.0     # Окно дедупликации по времени


class SensorRegistry:
    """Централизованный реестр сенсоров с политикой дедупликации."""
    
    # Реестр известных сенсоров с предпочтительными провайдерами
    _registry: Dict[str, SensorDefinition] = {}
    
    # Маппинг категорий на предпочтительные провайдеры
    _category_providers: Dict[str, SensorProvider] = {
        "temperature": SensorProvider.ACPI_THERMAL,
        "Temperatures": SensorProvider.ACPI_THERMAL,
        "gpu_temp": SensorProvider.GPU_PROBER,
        "gpu_load": SensorProvider.GPU_PROBER,
        "gpu_power": SensorProvider.GPU_PROBER,
        "gpu_fan": SensorProvider.GPU_PROBER,
        "cpu_temp": SensorProvider.ACPI_THERMAL,
        "cpu_load": SensorProvider.SENSOR_COLLECTOR,
        "Load": SensorProvider.SENSOR_COLLECTOR,  # CPU/RAM utilization
        "Clocks": SensorProvider.SENSOR_COLLECTOR,
        "network_throughput": SensorProvider.SENSOR_COLLECTOR,
        "network_bytes": SensorProvider.NETWORK_SENSOR,
        "Throughput": SensorProvider.SENSOR_COLLECTOR,
        "internet": SensorProvider.INTERNET_SPEED,
        "storage_temp": SensorProvider.WINDOWS_STORAGE,
        "storage_wear": SensorProvider.WINDOWS_STORAGE,
        "storage_usage": SensorProvider.SENSOR_COLLECTOR,
        "storage": SensorProvider.SENSOR_COLLECTOR,
    }
    
    # Паттерны дублирующихся sensor_id
    _duplicate_patterns: Dict[str, List[str]] = {
        # GPU метрики - собираются предпочтительно через GpuProber
        "gpu_.*": ["gpu_prober", "sensor_collector", "nvidia_smi_direct"],
        # CPU метрики
        "cpu_.*": ["acpi_thermal", "sensor_collector"],
        # Internet ping - дублируется в sensors.py и sensor_collector
        "internet_ping": ["internet_speed", "sensor_collector"],
        # Network throughput - дублируется в sensors.py и sensor_collector
        "network_.*_rate": ["network_sensor", "sensor_collector"],
    }
    
    @classmethod
    def register(cls, definition: SensorDefinition) -> None:
        """Регистрирует сенсор в реестре.
        
        Args:
            definition: Определение сенсора с политикой.
        """
        cls._registry[definition.sensor_id] = definition
    
    @classmethod
    def get_preferred_provider(cls, sensor_id: str, category: str) -> Optional[SensorProvider]:
        """Возвращает предпочтительный провайдер для данного сенсора.
        
        Args:
            sensor_id: Идентификатор сенсора.
            category: Категория сенсора.
            
        Returns:
            Preferred provider или None если не определен.
        """
        # 1. Проверяем явную регистрацию
        if sensor_id in cls._registry:
            return cls._registry[sensor_id].preferred_provider
        
        # 2. Определяем по специфическому паттерну sensor_id
        import re
        for pattern, providers in cls._duplicate_patterns.items():
            if re.match(pattern, sensor_id):
                # Возвращаем первый из списка как предпочтительный
                provider_name = providers[0].upper()
                try:
                    return SensorProvider[provider_name]
                except KeyError:
                    pass

        # 3. Проверяем по категории
        if category in cls._category_providers:
            return cls._category_providers[category]
        
        return None
    
    @classmethod
    def should_keep_sensor(
        cls,
        sensor_id: str,
        provider: SensorProvider,
        existing_sensors: List[Tuple[str, SensorProvider]]
    ) -> bool:
        """Определяет, нужно ли сохранить показание сенсора или отклонить как дубликат.
        
        Args:
            sensor_id: Идентификатор сенсора.
            provider: Провайдер, предоставивший показание.
            existing_sensors: Список уже собранных (sensor_id, provider) пар.
            
        Returns:
            True если сенсор нужно сохранить, False если это дубликат.
        """
        # Проверяем, есть ли уже такой sensor_id
        for existing_id, existing_provider in existing_sensors:
            if existing_id == sensor_id:
                # Дубликат найден - сравниваем приоритеты провайдеров
                preferred = cls.get_preferred_provider(sensor_id, "")
                if preferred:
                    # Сохраняем только от предпочтительного провайдера
                    return provider == preferred
                else:
                    # Нет явной политики - сохраняем от провайдера с высшим приоритетом
                    return provider.value > existing_provider.value
        
        # Дубликатов нет - сохраняем
        return True


class SensorDeduplicator:
    """Дедупликатор показаний сенсоров."""
    
    def __init__(self) -> None:
        """Инициализирует дедупликатор с пустым кешем."""
        self._seen: Dict[str, Tuple[float, SensorProvider, float]] = {}  # sensor_id -> (timestamp, provider, value)
    
    def add(
        self,
        sensor_id: str,
        provider: SensorProvider,
        value: float,
        timestamp: Optional[float] = None,
        dedup_window: float = 1.0
    ) -> bool:
        """Пытается добавить показание сенсора с проверкой на дубликаты.
        
        Args:
            sensor_id: Идентификатор сенсора.
            provider: Провайдер показания.
            value: Значение показания.
            timestamp: Временная метка (epoch seconds).
            dedup_window: Окно дедупликации в секундах.
            
        Returns:
            True если показание добавлено, False если отклонено как дубликат.
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).timestamp()
        
        # Проверяем наличие в кеше
        if sensor_id in self._seen:
            cached_ts, cached_provider, cached_value = self._seen[sensor_id]
            
            # Проверяем временное окно
            if abs(timestamp - cached_ts) < dedup_window:
                # В пределах окна - проверяем приоритеты
                preferred = SensorRegistry.get_preferred_provider(sensor_id, "")
                if preferred:
                    # Если текущий провайдер предпочтительнее - обновляем
                    if provider == preferred:
                        self._seen[sensor_id] = (timestamp, provider, value)
                        return True
                    else:
                        # Отклоняем
                        return False
                else:
                    # Сравниваем по значению приоритета
                    if provider.value > cached_provider.value:
                        self._seen[sensor_id] = (timestamp, provider, value)
                        return True
                    else:
                        return False
        
        # Нет дубликата или вне окна - добавляем
        self._seen[sensor_id] = (timestamp, provider, value)
        return True
    
    def get_unique(self) -> Dict[str, Tuple[SensorProvider, float]]:
        """Возвращает уникальные показания сенсоров.
        
        Returns:
            Словарь {sensor_id: (provider, value)}.
        """
        return {sid: (prov, val) for sid, (_, prov, val) in self._seen.items()}
    
    def clear(self) -> None:
        """Очищает кеш дедупликатора."""
        self._seen.clear()


def deduplicate_sensor_readings(
    readings: List[Dict],
    provider: SensorProvider = SensorProvider.SENSOR_COLLECTOR
) -> List[Dict]:
    """Дедуплицирует список показаний сенсоров.
    
    Args:
        readings: Список показаний с полями 'id' и 'value'.
        provider: Провайдер показаний.
        
    Returns:
        Дедуплицированный список показаний.
    """
    deduplicator = SensorDeduplicator()
    unique_readings: List[Dict] = []
    
    for reading in readings:
        sensor_id = reading.get('id', '')
        value = reading.get('value', 0.0)
        
        if deduplicator.add(sensor_id, provider, value):
            unique_readings.append(reading)
    
    return unique_readings
