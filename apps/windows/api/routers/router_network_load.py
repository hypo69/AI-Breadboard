# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Api Routers - Router Network Load
# =============================================================================
# Description:
#   GET /api/v1/panel/network-load — комплексные метрики нагрузки сетевых
#   адаптеров (Ethernet, Wi-Fi, Bluetooth): скорости Rx/Tx, использование канала,
#   состояние беспроводных интерфейсов, IP/MAC и история трафика.
#
# Usage Examples:
#   Python API:
#     from apps.windows.api.routers.router_network_load import init_router
#     app.include_router(init_router())
#
# File: router_network_load.py
# Project: ai-breadboard
# Package: apps.windows.api.routers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 12:25:00
# =============================================================================

from __future__ import annotations
"""Роутер панели «Сетевые адаптеры (Ethernet / Wi-Fi / BT)»: комплексная телеметрия сети."""

import re
import subprocess
import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field

try:
    import psutil
except ImportError:
    psutil = None

from logger import logger
from apps.windows.modules.hardware.lhm_service import LhmService
from apps.windows.telemetry import SystemCollector
from apps.windows.telemetry.models import ProcessNetworkActivity

_collector: Optional[SystemCollector] = None


def get_collector() -> SystemCollector:
    """Получить или создать синглтон сборщика системной телеметрии.

    Returns:
        SystemCollector: Экземпляр системного коллектора.
    """
    global _collector
    if _collector is None:
        _collector = SystemCollector()
    return _collector

_last_net_io: Optional[Any] = psutil.net_io_counters() if psutil else None
_last_net_time: float = time.time() if psutil else 0.0
_net_history: List[Dict[str, Any]] = []
_MAX_HISTORY = 120


class NetworkAdapterInfo(BaseModel):
    """Информация об отдельном сетевом адаптере."""
    name: str = Field(..., description="Имя интерфейса (Ethernet, Wi-Fi, etc.)")
    adapter_type: str = Field(default="Ethernet", description="Тип адаптера: Ethernet, Wi-Fi, Virtual, Loopback")
    is_up: bool = Field(default=False, description="Подключен ли интерфейс")
    speed_mbps: Optional[int] = Field(default=None, description="Скорость линка, Mbps")
    ip_address: str = Field(default="", description="IPv4 адрес")
    mac_address: str = Field(default="", description="MAC адрес")
    bytes_recv_sec: float = Field(default=0.0, description="Скорость приема, байт/с")
    bytes_sent_sec: float = Field(default=0.0, description="Скорость отдачи, байт/с")


class WifiStatusInfo(BaseModel):
    """Состояние беспроводного адаптера Wi-Fi."""
    name: str = Field(default="Wi-Fi", description="Имя интерфейса")
    description: str = Field(default="", description="Модель контроллера Wi-Fi")
    state: str = Field(default="disconnected", description="Статус подключения")
    radio_status: str = Field(default="On", description="Состояние радиомодуля")
    ssid: str = Field(default="", description="Имя подключенной сети (SSID)")
    signal_percent: Optional[int] = Field(default=None, description="Уровень сигнала, %")
    channel: Optional[int] = Field(default=None, description="Канал Wi-Fi")


class BluetoothStatusInfo(BaseModel):
    """Состояние модуля и подключений Bluetooth."""
    name: str = Field(default="Bluetooth", description="Имя контроллера BT")
    status: str = Field(default="OK", description="Статус адаптера")
    devices_count: int = Field(default=0, description="Количество сопряженных/активных устройств")
    devices: List[str] = Field(default_factory=list, description="Список устройств")


class NetworkPoint(BaseModel):
    """Точка истории скорости сети для графика."""
    timestamp: str = Field(default="", description="Время замера")
    download_bytes_sec: float = Field(default=0.0, description="Скорость скачивания, байт/с")
    upload_bytes_sec: float = Field(default=0.0, description="Скорость отдачи, байт/с")


class NetworkLoadResponse(BaseModel):
    """Ответ GET /api/v1/panel/network-load."""
    status: str = Field(default="ok", description="Статус ответа")
    name: str = Field(default="Network Adapters", description="Основной активный сетевой адаптер")
    timestamp: str = Field(default="", description="Время снимка")
    download_bytes_sec: float = Field(default=0.0, description="Текущая скорость приема (Download), байт/с")
    upload_bytes_sec: float = Field(default=0.0, description="Текущая скорость отдачи (Upload), байт/с")
    download_total_bytes: int = Field(default=0, description="Всего принято байт с загрузки системы")
    upload_total_bytes: int = Field(default=0, description="Всего отправлено байт с загрузки системы")
    utilization_percent: float = Field(default=0.0, description="Оценочная загрузка канала, %")
    link_speed_mbps: Optional[int] = Field(default=1000, description="Скорость основного интерфейса, Mbps")
    adapters: List[NetworkAdapterInfo] = Field(default_factory=list, description="Список сетевых адаптеров")
    wifi: WifiStatusInfo = Field(default_factory=WifiStatusInfo, description="Данные Wi-Fi")
    bluetooth: BluetoothStatusInfo = Field(default_factory=BluetoothStatusInfo, description="Данные Bluetooth")
    history: List[NetworkPoint] = Field(default_factory=list, description="История скоростей")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Метаданные")


def _get_wifi_info() -> WifiStatusInfo:
    """Опрашивает Wi-Fi через netsh wlan show interfaces."""
    info = WifiStatusInfo()
    try:
        res = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True,
            text=True,
            timeout=1.5,
            encoding="utf-8",
            errors="ignore",
        )
        if res.returncode == 0 and res.stdout:
            out = res.stdout
            desc_m = re.search(r"Description\s*:\s*(.+)", out)
            if desc_m:
                info.description = desc_m.group(1).strip()
            state_m = re.search(r"State\s*:\s*(.+)", out)
            if state_m:
                info.state = state_m.group(1).strip()
            ssid_m = re.search(r"SSID\s*:\s*([^\r\n]+)", out)
            if ssid_m and not ssid_m.group(1).strip().startswith("BSSID"):
                info.ssid = ssid_m.group(1).strip()
            signal_m = re.search(r"Signal\s*:\s*(\d+)%", out)
            if signal_m:
                info.signal_percent = int(signal_m.group(1))
            radio_m = re.search(r"Radio status\s*:\s*Hardware\s*(\w+)\s*Software\s*(\w+)", out, re.IGNORECASE)
            if radio_m:
                info.radio_status = f"HW {radio_m.group(1)} / SW {radio_m.group(2)}"
    except Exception as e:
        logger.debug(f"[RouterNetworkLoad] Ошибка опроса Wi-Fi: {e}")
    return info


_cached_bt_info: Optional[BluetoothStatusInfo] = None
_cached_bt_time: float = 0.0
_BT_CACHE_TTL: float = 30.0


def _get_bluetooth_info() -> BluetoothStatusInfo:
    """Опрашивает статус контроллера и устройств Bluetooth через PowerShell с кэшированием."""
    global _cached_bt_info, _cached_bt_time
    now = time.time()
    if _cached_bt_info is not None and (now - _cached_bt_time < _BT_CACHE_TTL):
        return _cached_bt_info

    info = BluetoothStatusInfo()
    try:
        cmd = "Get-PnpDevice -Class Bluetooth | Where-Object { $_.Status -eq 'OK' } | Select-Object -ExpandProperty FriendlyName"
        res = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
            capture_output=True,
            text=True,
            timeout=5.0,
            encoding="utf-8",
            errors="ignore",
        )
        if res.returncode == 0 and res.stdout:
            lines = [line.strip() for line in res.stdout.strip().splitlines() if line.strip()]
            main_ctrl = next((l for l in lines if "intel" in l.lower() or "adapter" in l.lower() or "radio" in l.lower()), "Bluetooth Adapter")
            devs = [l for l in lines if not any(x in l.lower() for x in ("enumerator", "service", "gateway", "transport", "object push", "nap service", "sim access"))]
            info.name = main_ctrl
            info.devices_count = len(devs)
            info.devices = devs[:6]
            _cached_bt_info = info
            _cached_bt_time = now
    except Exception as e:
        logger.debug(f"[RouterNetworkLoad] Ошибка опроса Bluetooth: {e}")
        if _cached_bt_info is not None:
            return _cached_bt_info
    return info


def calculate_network_load() -> NetworkLoadResponse:
    """Собирает полный снимок нагрузки сети."""
    global _last_net_io, _last_net_time, _net_history

    now = time.time()
    current_io = psutil.net_io_counters() if psutil else None
    
    rx_sec = 0.0
    tx_sec = 0.0

    if current_io and _last_net_io and _last_net_time > 0:
        dt = max(0.2, now - _last_net_time)
        rx_sec = max(0.0, (current_io.bytes_recv - _last_net_io.bytes_recv) / dt)
        tx_sec = max(0.0, (current_io.bytes_sent - _last_net_io.bytes_sent) / dt)

    _last_net_io = current_io
    _last_net_time = now

    ts_str = time.strftime("%H:%M:%S")
    _net_history.append({"timestamp": ts_str, "download_bytes_sec": rx_sec, "upload_bytes_sec": tx_sec})
    if len(_net_history) > _MAX_HISTORY:
        _net_history.pop(0)

    # Собираем список сетевых адаптеров
    adapters_list: List[NetworkAdapterInfo] = []
    main_name = "Ethernet"
    main_speed = 1000

    if psutil:
        stats_map = psutil.net_if_stats()
        addrs_map = psutil.net_if_addrs()

        for if_name, stat in stats_map.items():
            if not stat.isup:
                continue
            is_virt = any(v in if_name.lower() for v in ("vethernet", "virtual", "hyper-v", "loopback", "wsl", "vmware", "box"))
            is_wifi = "wi-fi" in if_name.lower() or "wlan" in if_name.lower() or "wireless" in if_name.lower()
            atype = "Wi-Fi" if is_wifi else ("Virtual" if is_virt else "Ethernet")

            addrs = addrs_map.get(if_name, [])
            ip_val = next((str(a.address) for a in addrs if getattr(a.family, "name", "") == "AF_INET"), "")
            mac_val = next((str(a.address) for a in addrs if getattr(a.family, "name", "") == "AF_LINK"), "")

            if not is_virt and stat.speed > 0:
                main_name = f"{if_name} ({stat.speed} Mbps)"
                main_speed = stat.speed

            adapters_list.append(
                NetworkAdapterInfo(
                    name=if_name,
                    adapter_type=atype,
                    is_up=stat.isup,
                    speed_mbps=stat.speed if stat.speed > 0 else None,
                    ip_address=ip_val,
                    mac_address=mac_val,
                    bytes_recv_sec=rx_sec if not is_virt else 0.0,
                    bytes_sent_sec=tx_sec if not is_virt else 0.0,
                )
            )

    # Оценка утилизации канала (в процентах от скорости линка в байтах)
    max_bandwidth_bps = (main_speed * 1_000_000) / 8.0 if main_speed > 0 else 125_000_000.0
    utilization_pct = min(100.0, round(((rx_sec + tx_sec) / max_bandwidth_bps) * 100.0, 2))

    wifi_info = _get_wifi_info()
    bt_info = _get_bluetooth_info()

    hist_points = [
        NetworkPoint(
            timestamp=p["timestamp"],
            download_bytes_sec=p["download_bytes_sec"],
            upload_bytes_sec=p["upload_bytes_sec"],
        )
        for p in _net_history
    ]

    return NetworkLoadResponse(
        name=main_name,
        timestamp=ts_str,
        download_bytes_sec=rx_sec,
        upload_bytes_sec=tx_sec,
        download_total_bytes=current_io.bytes_recv if current_io else 0,
        upload_total_bytes=current_io.bytes_sent if current_io else 0,
        utilization_percent=utilization_pct,
        link_speed_mbps=main_speed,
        adapters=adapters_list,
        wifi=wifi_info,
        bluetooth=bt_info,
        history=hist_points,
        meta={"source": "psutil/netsh/pnp", "adapters_count": len(adapters_list)},
    )


def init_router() -> APIRouter:
    """Создаёт роутер сетевой телеметрии и активности процессов.

    Returns:
        APIRouter: Роутер с эндпоинтами панели /api/v1/panel/network-load и /api/v1/system/network-activity.
    """
    router = APIRouter(tags=["Network Load Panel"])

    @router.get("/api/v1/panel/network-load", response_model=NetworkLoadResponse)
    async def get_network_load() -> NetworkLoadResponse:
        """Возвращает текущие метрики нагрузки сети, Wi-Fi и Bluetooth."""
        try:
            return calculate_network_load()
        except Exception as e:
            logger.error(f"[RouterNetworkLoad] Ошибка вычисления сетевой нагрузки: {e}", exc_info=True)
            return NetworkLoadResponse(status="error", meta={"error": str(e)})

    @router.get("/api/v1/panel/network-activity", response_model=List[ProcessNetworkActivity])
    @router.get("/api/v1/system/network-activity", response_model=List[ProcessNetworkActivity])
    @router.get("/api/v1/tc/network-activity", response_model=List[ProcessNetworkActivity])
    async def get_process_network_activity_endpoint(
        limit: int = 100,
        only_internet: bool = False,
    ) -> List[ProcessNetworkActivity]:
        """Возвращает список активных сетевых соединений программ и процессов.

        Args:
            limit: Максимальное число записей в выдаче.
            only_internet: Фильтровать только внешние интернет-соединения.

        Returns:
            List[ProcessNetworkActivity]: Список объектов сетевой активности процессов.
        """
        try:
            collector = get_collector()
            return collector.get_process_network_activity(limit=limit, only_internet=only_internet)
        except Exception as exc:
            logger.error(f"[RouterNetworkLoad] Ошибка получения сетевой активности процессов: {exc}", exc_info=True)
            return []

    return router
