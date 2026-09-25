# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Hardware Monitor
# =============================================================================
# Description:
#   Монитор аппаратных ресурсов реального времени для Windows. Собирает
#   детальные метрики по CPU, оперативной памяти, видеокартам (GPU),
#   накопителям (включая I/O и SMART), датчикам материнской платы
#   (температуры, кулеры, напряжения), сети и питанию.
#
# Examples:
#   >>> from apps.windows.hardware.hardware_monitor import HardwareMonitor
#   >>> monitor = HardwareMonitor()
#   >>> snapshot = monitor.get_snapshot()
#   >>> print(f"CPU Load: {snapshot.cpu.utilization_pct}%")
#
# File: hardware_monitor.py
# Project: ai-breadboard
# Package: apps.windows.hardware
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модуль аппаратного мониторинга реального времени для Windows."""

from __future__ import annotations

import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import psutil

from logger import logger
from apps.windows.hardware.gpu_prober import GpuDeviceTelemetry, GpuProber
from apps.windows.telemetry.sensors import get_hardware_sensors


@dataclass
class CpuMetrics:
    """Метрики центрального процессора (CPU)."""
    model_name: str
    physical_cores: int
    logical_cores: int
    utilization_pct: float
    per_core_pct: List[float] = field(default_factory=list)
    frequency_current_mhz: Optional[float] = None
    frequency_min_mhz: Optional[float] = None
    frequency_max_mhz: Optional[float] = None
    interrupts_per_sec: Optional[int] = None
    ctx_switches_per_sec: Optional[int] = None


@dataclass
class MemoryMetrics:
    """Метрики оперативной памяти и файла подкачки (RAM & Swap)."""
    total_gb: float
    used_gb: float
    free_gb: float
    available_gb: float
    utilization_pct: float
    swap_total_gb: float
    swap_used_gb: float
    swap_free_gb: float
    swap_utilization_pct: float


@dataclass
class GpuMetrics:
    """Метрики графического адаптера (GPU)."""
    index: int
    name: str
    vendor: str
    driver_version: str
    temperature_gpu_c: Optional[float] = None
    temperature_memory_c: Optional[float] = None
    utilization_gpu_pct: Optional[float] = None
    utilization_memory_pct: Optional[float] = None
    memory_used_mb: Optional[float] = None
    memory_total_mb: Optional[float] = None
    power_draw_w: Optional[float] = None
    power_limit_w: Optional[float] = None
    fan_speed_pct: Optional[float] = None
    throttle_reasons: List[str] = field(default_factory=list)


@dataclass
class DiskPartitionMetrics:
    """Метрики логического раздела накопителя."""
    device: str
    mountpoint: str
    fstype: str
    total_gb: float
    used_gb: float
    free_gb: float
    utilization_pct: float


@dataclass
class DiskIoMetrics:
    """Метрики скорости ввода-вывода накопителей."""
    read_bytes_sec: float
    write_bytes_sec: float
    read_count_sec: float
    write_count_sec: float


@dataclass
class StorageMetrics:
    """Сводные метрики подсистемы хранения данных."""
    partitions: List[DiskPartitionMetrics] = field(default_factory=list)
    io_rates: Optional[DiskIoMetrics] = None
    smart_drives: List[SmartDriveInfo] = field(default_factory=list)


@dataclass
class SensorMetrics:
    """Метрики аппаратных датчиков (температуры, кулеры, напряжения)."""
    sensor_id: str
    name: str
    category: str
    value: float
    unit: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None


@dataclass
class NetworkMetrics:
    """Метрики сетевых интерфейсов и скорости передачи данных."""
    bytes_sent_sec: float
    bytes_recv_sec: float
    packets_sent_sec: float
    packets_recv_sec: float
    active_connections_count: int
    interface_count: int


@dataclass
class BatteryMetrics:
    """Метрики аккумулятора и электропитания."""
    has_battery: bool
    percent: Optional[float] = None
    power_plugged: Optional[bool] = None
    seconds_left: Optional[int] = None


@dataclass
class HardwareSnapshot:
    """Полный слепок аппаратного состояния системы."""
    timestamp: str
    cpu: CpuMetrics
    memory: MemoryMetrics
    gpus: List[GpuMetrics]
    storage: StorageMetrics
    sensors: List[SensorMetrics]
    network: NetworkMetrics
    battery: BatteryMetrics
    status_summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование снимка в словарь."""
        return asdict(self)


class HardwareMonitor:
    """Менеджер мониторинга аппаратных компонентов и датчиков в реальном времени."""

    def __init__(self) -> None:
        """Инициализация монитора с внутренними счетчиками для дифференциальных метрик."""
        self._gpu_prober = GpuProber()
        self._last_poll_time: float = time.time()
        self._last_disk_io = self._get_raw_disk_io()
        self._last_net_io = self._get_raw_net_io()

        # Инициализируем первый опрос psutil CPU для достоверных последующих замеров
        try:
            psutil.cpu_percent(interval=None, percpu=True)
        except Exception:
            pass

    def _get_raw_disk_io(self) -> Optional[Any]:
        """Получение сырых счетчиков дискового I/O."""
        try:
            return psutil.disk_io_counters()
        except Exception:
            return None

    def _get_raw_net_io(self) -> Optional[Any]:
        """Получение сырых счетчиков сетевого I/O."""
        try:
            return psutil.net_io_counters()
        except Exception:
            return None

    def get_cpu_metrics(self) -> CpuMetrics:
        """Сбор текущих метрик процессора."""
        model_name = "Windows Processor"
        try:
            if os.name == "nt":
                model_name = os.environ.get("PROCESSOR_IDENTIFIER", "x86/x64 Processor")
        except Exception:
            pass

        phys_cores = psutil.cpu_count(logical=False) or 1
        logic_cores = psutil.cpu_count(logical=True) or 1

        per_core = []
        overall_pct = 0.0
        try:
            per_core = psutil.cpu_percent(interval=None, percpu=True)
            overall_pct = sum(per_core) / len(per_core) if per_core else psutil.cpu_percent(interval=None)
        except Exception as e:
            logger.debug(f"Ошибка получения загрузки CPU: {e}")

        freq_cur = freq_min = freq_max = None
        try:
            freq = psutil.cpu_freq()
            if freq:
                freq_cur = round(freq.current, 1)
                freq_min = round(freq.min, 1) if freq.min > 0 else None
                freq_max = round(freq.max, 1) if freq.max > 0 else None
        except Exception:
            pass

        interrupts = ctx_switches = None
        try:
            stats = psutil.cpu_stats()
            if stats:
                interrupts = stats.interrupts
                ctx_switches = stats.ctx_switches
        except Exception:
            pass

        return CpuMetrics(
            model_name=model_name,
            physical_cores=phys_cores,
            logical_cores=logic_cores,
            utilization_pct=round(overall_pct, 1),
            per_core_pct=[round(x, 1) for x in per_core],
            frequency_current_mhz=freq_cur,
            frequency_min_mhz=freq_min,
            frequency_max_mhz=freq_max,
            interrupts_per_sec=interrupts,
            ctx_switches_per_sec=ctx_switches,
        )

    def get_memory_metrics(self) -> MemoryMetrics:
        """Сбор текущих метрик оперативной памяти и файла подкачки."""
        vm = psutil.virtual_memory()
        swap = psutil.swap_memory()

        return MemoryMetrics(
            total_gb=round(vm.total / (1024**3), 2),
            used_gb=round(vm.used / (1024**3), 2),
            free_gb=round(vm.free / (1024**3), 2),
            available_gb=round(vm.available / (1024**3), 2),
            utilization_pct=round(vm.percent, 1),
            swap_total_gb=round(swap.total / (1024**3), 2),
            swap_used_gb=round(swap.used / (1024**3), 2),
            swap_free_gb=round(swap.free / (1024**3), 2),
            swap_utilization_pct=round(swap.percent, 1),
        )

    def get_gpu_metrics(self) -> List[GpuMetrics]:
        """Сбор телеметрии графических ускорителей (GPU)."""
        metrics: List[GpuMetrics] = []
        try:
            gpus = self._gpu_prober.probe_all()
            for g in gpus:
                metrics.append(
                    GpuMetrics(
                        index=g.index,
                        name=g.name,
                        vendor=g.vendor,
                        driver_version=g.driver_version,
                        temperature_gpu_c=g.temperature_gpu_c,
                        temperature_memory_c=g.temperature_memory_c,
                        utilization_gpu_pct=g.utilization_gpu_pct,
                        utilization_memory_pct=g.utilization_memory_pct,
                        memory_used_mb=g.memory_used_mb,
                        memory_total_mb=g.memory_total_mb,
                        power_draw_w=g.power_draw_w,
                        power_limit_w=g.power_limit_w,
                        fan_speed_pct=g.fan_speed_pct,
                        throttle_reasons=g.throttle_reasons,
                    )
                )
        except Exception as e:
            logger.debug(f"Ошибка опроса GPU: {e}")
        return metrics

    def get_storage_metrics(self, include_smart: bool = True) -> StorageMetrics:
        """Сбор данных о дисках, скоростях ввода-вывода и SMART."""
        partitions: List[DiskPartitionMetrics] = []
        try:
            for part in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    partitions.append(
                        DiskPartitionMetrics(
                            device=part.device,
                            mountpoint=part.mountpoint,
                            fstype=part.fstype,
                            total_gb=round(usage.total / (1024**3), 2),
                            used_gb=round(usage.used / (1024**3), 2),
                            free_gb=round(usage.free / (1024**3), 2),
                            utilization_pct=round(usage.percent, 1),
                        )
                    )
                except (PermissionError, OSError):
                    continue
        except Exception as e:
            logger.debug(f"Ошибка получения разделов дисков: {e}")

        # Расчет дифференциальных скоростей I/O
        io_rates = None
        now = time.time()
        time_delta = max(0.1, now - self._last_poll_time)
        current_disk_io = self._get_raw_disk_io()

        if current_disk_io and self._last_disk_io:
            read_bytes_sec = max(0.0, (current_disk_io.read_bytes - self._last_disk_io.read_bytes) / time_delta)
            write_bytes_sec = max(0.0, (current_disk_io.write_bytes - self._last_disk_io.write_bytes) / time_delta)
            read_count_sec = max(0.0, (current_disk_io.read_count - self._last_disk_io.read_count) / time_delta)
            write_count_sec = max(0.0, (current_disk_io.write_count - self._last_disk_io.write_count) / time_delta)
            io_rates = DiskIoMetrics(
                read_bytes_sec=round(read_bytes_sec, 1),
                write_bytes_sec=round(write_bytes_sec, 1),
                read_count_sec=round(read_count_sec, 1),
                write_count_sec=round(write_count_sec, 1),
            )
        self._last_disk_io = current_disk_io

        smart_drives: List[SmartDriveInfo] = []
        if include_smart:
            try:
                smart_drives = self._smart_prober.scan_drives()
            except Exception as e:
                logger.debug(f"Ошибка получения SMART данных: {e}")

        return StorageMetrics(
            partitions=partitions,
            io_rates=io_rates,
            smart_drives=smart_drives,
        )

    def get_sensor_metrics(self) -> List[SensorMetrics]:
        """Сбор температур, частот кулеров и напряжений."""
        sensors: List[SensorMetrics] = []
        try:
            raw_sensors = get_hardware_sensors()
            for s in raw_sensors:
                sensors.append(
                    SensorMetrics(
                        sensor_id=s.sensor_id,
                        name=s.name,
                        category=s.category,
                        value=s.value,
                        unit=s.unit,
                        min_value=s.min_value,
                        max_value=s.max_value,
                    )
                )
        except Exception as e:
            logger.debug(f"Ошибка получения датчиков: {e}")
        return sensors

    def get_network_metrics(self) -> NetworkMetrics:
        """Сбор метрик сетевого ввода-вывода и количества соединений."""
        now = time.time()
        time_delta = max(0.1, now - self._last_poll_time)
        current_net_io = self._get_raw_net_io()

        sent_sec = recv_sec = psent_sec = precv_sec = 0.0
        if current_net_io and self._last_net_io:
            sent_sec = max(0.0, (current_net_io.bytes_sent - self._last_net_io.bytes_sent) / time_delta)
            recv_sec = max(0.0, (current_net_io.bytes_recv - self._last_net_io.bytes_recv) / time_delta)
            psent_sec = max(0.0, (current_net_io.packets_sent - self._last_net_io.packets_sent) / time_delta)
            precv_sec = max(0.0, (current_net_io.packets_recv - self._last_net_io.packets_recv) / time_delta)
        self._last_net_io = current_net_io

        conn_count = 0
        try:
            conn_count = len(psutil.net_connections(kind="inet"))
        except Exception:
            pass

        if_count = 0
        try:
            if_count = len(psutil.net_if_addrs())
        except Exception:
            pass

        return NetworkMetrics(
            bytes_sent_sec=round(sent_sec, 1),
            bytes_recv_sec=round(recv_sec, 1),
            packets_sent_sec=round(psent_sec, 1),
            packets_recv_sec=round(precv_sec, 1),
            active_connections_count=conn_count,
            interface_count=if_count,
        )

    def get_battery_metrics(self) -> BatteryMetrics:
        """Сбор данных о батарее и электропитании."""
        try:
            battery = psutil.sensors_battery()
            if battery:
                return BatteryMetrics(
                    has_battery=True,
                    percent=round(battery.percent, 1),
                    power_plugged=battery.power_plugged,
                    seconds_left=battery.secsleft if battery.secsleft > 0 else None,
                )
        except Exception:
            pass
        return BatteryMetrics(has_battery=False)

    def get_summary(self, snapshot: Optional[HardwareSnapshot] = None) -> Dict[str, Any]:
        """Формирование сводного статуса здоровья оборудования."""
        snap = snapshot or self.get_snapshot(include_smart=False)
        warnings: List[str] = []
        criticals: List[str] = []

        # Проверка CPU
        if snap.cpu.utilization_pct >= 95.0:
            criticals.append(f"Критическая загрузка CPU: {snap.cpu.utilization_pct}%")
        elif snap.cpu.utilization_pct >= 85.0:
            warnings.append(f"Высокая загрузка CPU: {snap.cpu.utilization_pct}%")

        # Проверка RAM
        if snap.memory.utilization_pct >= 95.0:
            criticals.append(f"Критическое заполнение RAM: {snap.memory.utilization_pct}%")
        elif snap.memory.utilization_pct >= 85.0:
            warnings.append(f"Высокое заполнение RAM: {snap.memory.utilization_pct}%")

        # Проверка дисков
        for part in snap.storage.partitions:
            if part.utilization_pct >= 95.0:
                criticals.append(f"Диск {part.mountpoint} переполнен ({part.utilization_pct}%, свободно {part.free_gb} GB)")
            elif part.utilization_pct >= 90.0:
                warnings.append(f"Мало места на диске {part.mountpoint} ({part.utilization_pct}%)")

        # Проверка GPU температур
        for gpu in snap.gpus:
            if gpu.temperature_gpu_c and gpu.temperature_gpu_c >= 88.0:
                criticals.append(f"Перегрев {gpu.name}: {gpu.temperature_gpu_c}°C")
            elif gpu.temperature_gpu_c and gpu.temperature_gpu_c >= 80.0:
                warnings.append(f"Повышенная температура {gpu.name}: {gpu.temperature_gpu_c}°C")

        # Проверка SMART
        for d in snap.storage.smart_drives:
            if d.health_status == "FAILING":
                criticals.append(f"Угроза отказа накопителя {d.device} ({d.model}): SMART FAILING")

        status = "CRITICAL" if criticals else ("WARNING" if warnings else "HEALTHY")
        return {
            "status": status,
            "critical_issues": criticals,
            "warning_issues": warnings,
            "metrics": {
                "cpu_utilization_pct": snap.cpu.utilization_pct,
                "ram_utilization_pct": snap.memory.utilization_pct,
                "gpu_count": len(snap.gpus),
                "disks_count": len(snap.storage.partitions),
                "sensors_count": len(snap.sensors),
            },
        }

    def get_snapshot(self, include_smart: bool = True) -> HardwareSnapshot:
        """Создание полного моментального снимка состояния оборудования."""
        cpu = self.get_cpu_metrics()
        memory = self.get_memory_metrics()
        gpus = self.get_gpu_metrics()
        storage = self.get_storage_metrics(include_smart=include_smart)
        sensors = self.get_sensor_metrics()
        network = self.get_network_metrics()
        battery = self.get_battery_metrics()

        # Фиксация времени опроса
        self._last_poll_time = time.time()

        snapshot = HardwareSnapshot(
            timestamp=datetime.now().isoformat(),
            cpu=cpu,
            memory=memory,
            gpus=gpus,
            storage=storage,
            sensors=sensors,
            network=network,
            battery=battery,
        )
        snapshot.status_summary = self.get_summary(snapshot)
        return snapshot


__all__ = [
    "BatteryMetrics",
    "CpuMetrics",
    "DiskIoMetrics",
    "DiskPartitionMetrics",
    "GpuMetrics",
    "HardwareMonitor",
    "HardwareSnapshot",
    "MemoryMetrics",
    "NetworkMetrics",
    "SensorMetrics",
    "StorageMetrics",
]
