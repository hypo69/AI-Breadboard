# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Network - Lan Scanner
# =============================================================================
# Description:
#   Модуль обнаружения и инспекции устройств в локальной сети (LAN Device Discovery).
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.network.lan_scanner import LanDevice
#
#     service = LanDevice()
#
# File: lan_scanner.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.network
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Модуль обнаружения и инспекции устройств в локальной сети (LAN Device Discovery)."""

import concurrent.futures
import ipaddress
import json
import os
import re
import socket
import struct
import subprocess
import time
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field

from logger import logger
from apps.windows.telemetry.win32_ffi.nethelper import IPHelperAPI

# Популярные OUI префиксы производителей сетевого оборудования и устройств
OUI_VENDOR_MAP: Dict[str, str] = {
    '00:0C:29': 'VMware',
    '00:50:56': 'VMware',
    '00:1C:42': 'Parallels',
    '00:15:5D': 'Microsoft Hyper-V',
    '00:1A:11': 'Google',
    'D8:3A:DD': 'Google / Nest',
    '54:60:09': 'Google',
    'F4:F5:DB': 'Google',
    '00:03:93': 'Apple',
    '00:17:F2': 'Apple',
    '00:1B:63': 'Apple',
    '00:1C:B3': 'Apple',
    '00:1E:52': 'Apple',
    '00:1F:5B': 'Apple',
    '00:1F:F3': 'Apple',
    '00:22:41': 'Apple',
    '00:23:12': 'Apple',
    '00:23:DF': 'Apple',
    '00:24:36': 'Apple',
    '00:25:00': 'Apple',
    '00:25:4B': 'Apple',
    '00:26:08': 'Apple',
    '00:26:4A': 'Apple',
    '00:26:B0': 'Apple',
    '00:CD:FE': 'Apple',
    '04:0C:CE': 'Apple',
    '04:15:52': 'Apple',
    '10:93:E9': 'Apple',
    '14:7D:DA': 'Apple',
    '18:65:90': 'Apple',
    '1C:91:48': 'Apple',
    '28:CF:E9': 'Apple',
    '30:90:AB': 'Apple',
    '38:F9:D3': 'Apple',
    '40:6c:8f': 'Apple',
    '44:00:10': 'Apple',
    '48:D7:05': 'Apple',
    '64:B0:A6': 'Apple',
    '70:35:60': 'Apple',
    '7C:D1:C3': 'Apple',
    '88:66:5A': 'Apple',
    'A4:83:E7': 'Apple',
    'AC:BC:32': 'Apple',
    'B8:78:2E': 'Apple',
    'BC:D1:1F': 'Apple',
    'C8:69:CD': 'Apple',
    'DC:A9:04': 'Apple',
    'F0:18:98': 'Apple',
    'F8:FF:C2': 'Apple',
    '00:12:FB': 'Samsung',
    '00:15:99': 'Samsung',
    '00:16:6C': 'Samsung',
    '00:17:C9': 'Samsung',
    '00:21:D1': 'Samsung',
    '00:23:D7': 'Samsung',
    '00:26:37': 'Samsung',
    '08:EE:8B': 'Samsung',
    '14:BB:6E': 'Samsung',
    '18:3B:D2': 'Samsung',
    '24:4B:03': 'Samsung',
    '34:BE:00': 'Samsung',
    '40:0E:85': 'Samsung',
    '50:85:69': 'Samsung',
    '58:C3:8B': 'Samsung',
    '60:AF:6D': 'Samsung',
    '70:2C:1F': 'Samsung',
    '84:25:DB': 'Samsung',
    '94:65:2D': 'Samsung',
    'A8:06:00': 'Samsung',
    'AC:5F:3E': 'Samsung',
    'C4:73:1E': 'Samsung',
    'DC:71:44': 'Samsung',
    'E8:03:9A': 'Samsung',
    'F4:7B:5E': 'Samsung',
    '00:04:4B': 'NVIDIA',
    '00:1A:80': 'NVIDIA',
    '48:B0:2D': 'NVIDIA',
    '00:0C:43': 'MediaTek / Ralink',
    '00:0E:8E': 'SparkLAN',
    '00:13:D4': 'ASUSTek Computer',
    '00:1B:FC': 'ASUSTek Computer',
    '04:D4:C4': 'ASUSTek Computer',
    '08:60:6E': 'ASUSTek Computer',
    '10:BF:48': 'ASUSTek Computer',
    '1C:87:2C': 'ASUSTek Computer',
    '2C:FD:A1': 'ASUSTek Computer',
    '30:5A:3A': 'ASUSTek Computer',
    '40:16:7E': 'ASUSTek Computer',
    '60:45:CB': 'ASUSTek Computer',
    'AC:22:0B': 'ASUSTek Computer',
    'D8:50:E6': 'ASUSTek Computer',
    'E0:3F:49': 'ASUSTek Computer',
    '00:1D:0F': 'TP-Link',
    '00:25:86': 'TP-Link',
    '14:CC:20': 'TP-Link',
    '18:A6:F7': 'TP-Link',
    '30:DE:4B': 'TP-Link',
    '50:C7:BF': 'TP-Link',
    '54:AF:97': 'TP-Link',
    '60:32:B1': 'TP-Link',
    '70:4F:57': 'TP-Link',
    '98:48:27': 'TP-Link',
    'AC:84:C6': 'TP-Link',
    'B0:95:75': 'TP-Link',
    'C0:06:C3': 'TP-Link',
    'C4:6E:1F': 'TP-Link',
    'D8:0D:17': 'TP-Link',
    'E4:C3:2A': 'TP-Link',
    'EC:08:6B': 'TP-Link',
    '00:0C:42': 'MikroTik',
    '2C:C8:1B': 'MikroTik',
    '48:8F:5A': 'MikroTik',
    '64:D1:54': 'MikroTik',
    '74:4D:28': 'MikroTik',
    'B8:69:F4': 'MikroTik',
    'CC:2D:E0': 'MikroTik',
    'D4:01:C3': 'MikroTik',
    'E4:8D:8C': 'MikroTik',
    '00:15:6D': 'Ubiquiti Networks',
    '04:18:D6': 'Ubiquiti Networks',
    '24:5A:4C': 'Ubiquiti Networks',
    '44:D9:E7': 'Ubiquiti Networks',
    '68:D7:9A': 'Ubiquiti Networks',
    '70:A7:41': 'Ubiquiti Networks',
    '78:8A:20': 'Ubiquiti Networks',
    '80:2A:A8': 'Ubiquiti Networks',
    'AC:8B:A9': 'Ubiquiti Networks',
    'B4:FB:E4': 'Ubiquiti Networks',
    'DC:9F:DB': 'Ubiquiti Networks',
    'F0:9F:C2': 'Ubiquiti Networks',
    '00:1E:8C': 'Keenetic / ZyXEL',
    '50:FF:20': 'Keenetic',
    '64:6E:97': 'Keenetic',
    'E8:37:7A': 'Keenetic',
    '00:08:22': 'InPro Comm (Keenetic/ZyXEL)',
    '00:18:E7': 'Cameo (D-Link)',
    '00:1E:58': 'D-Link',
    '14:D6:4D': 'D-Link',
    '1C:7E:E5': 'D-Link',
    '28:10:7B': 'D-Link',
    'B0:C5:54': 'D-Link',
    'C8:D3:A3': 'D-Link',
    'FC:75:16': 'D-Link',
    '00:0F:B5': 'Netgear',
    '00:14:6C': 'Netgear',
    '00:18:4D': 'Netgear',
    '00:1E:2A': 'Netgear',
    '20:4E:7F': 'Netgear',
    '28:C6:8E': 'Netgear',
    '44:94:FC': 'Netgear',
    '9C:3D:CF': 'Netgear',
    'A0:04:60': 'Netgear',
    'C0:3F:0E': 'Netgear',
    '00:11:32': 'Synology',
    '00:08:9B': 'QNAP',
    '00:1B:21': 'Intel',
    '00:1C:C0': 'Intel',
    '00:1E:64': 'Intel',
    '00:21:5C': 'Intel',
    '00:23:14': 'Intel',
    '00:24:D7': 'Intel',
    '00:27:0E': 'Intel',
    '34:13:E8': 'Intel',
    '3C:F8:62': 'Intel',
    '48:51:B7': 'Intel',
    '68:05:CA': 'Intel',
    '80:86:F2': 'Intel',
    '88:AE:DD': 'Intel',
    'A4:4C:C8': 'Intel',
    'B8:08:CF': 'Intel',
    'D8:BB:C1': 'Intel',
    'F8:63:3F': 'Intel',
    '00:E0:4C': 'Realtek',
    '52:54:00': 'QEMU / KVM Virtual NIC',
    'B8:27:EB': 'Raspberry Pi Foundation',
    'DC:A6:32': 'Raspberry Pi Foundation',
    'E4:5F:01': 'Raspberry Pi Foundation',
    '28:CD:C1': 'Raspberry Pi Foundation',
    'D8:3A:DD': 'Raspberry Pi Foundation',
    '24:0A:C4': 'Espressif Inc (ESP32/ESP8266)',
    '24:62:AB': 'Espressif Inc (ESP32/ESP8266)',
    '30:AE:A4': 'Espressif Inc (ESP32/ESP8266)',
    '84:F3:EB': 'Espressif Inc (ESP32/ESP8266)',
    'A4:CF:12': 'Espressif Inc (ESP32/ESP8266)',
    'AC:67:B2': 'Espressif Inc (ESP32/ESP8266)',
    'CC:50:E3': 'Espressif Inc (ESP32/ESP8266)',
    'DC:4F:22': 'Espressif Inc (ESP32/ESP8266)',
    '00:EC:0A': 'Xiaomi / Beijing Xiaomi',
    '04:CF:8C': 'Xiaomi',
    '18:F0:E4': 'Xiaomi',
    '28:6C:07': 'Xiaomi',
    '34:80:0D': 'Xiaomi',
    '50:64:2B': 'Xiaomi',
    '64:09:80': 'Xiaomi',
    '78:11:DC': 'Xiaomi',
    '7C:49:EB': 'Xiaomi',
    '88:C3:97': 'Xiaomi',
    'AC:F7:F3': 'Xiaomi',
    'C4:0B:D3': 'Xiaomi',
    'F0:18:98': 'Xiaomi',
    '00:1E:10': 'Huawei Technologies',
    '00:25:68': 'Huawei Technologies',
    '00:E0:FC': 'Huawei Technologies',
    '08:7A:4C': 'Huawei Technologies',
    '10:47:80': 'Huawei Technologies',
    '20:08:89': 'Huawei Technologies',
    '30:75:12': 'Huawei Technologies',
    '48:46:FB': 'Huawei Technologies',
    '70:7B:E8': 'Huawei Technologies',
    '84:DB:AC': 'Huawei Technologies',
    'BC:76:70': 'Huawei Technologies',
    '00:18:FE': 'Hewlett Packard',
    '00:21:5A': 'Hewlett Packard',
    '00:24:81': 'Hewlett Packard',
    '3C:D9:2B': 'Hewlett Packard',
    '9C:8E:99': 'Hewlett Packard',
    '00:14:22': 'Dell Inc',
    '00:18:8B': 'Dell Inc',
    '00:21:70': 'Dell Inc',
    '00:24:E8': 'Dell Inc',
    '18:03:73': 'Dell Inc',
    '34:17:EB': 'Dell Inc',
    'F8:DB:88': 'Dell Inc',
    '00:26:B9': 'Dell Inc',
    '00:1A:E8': 'Sony Corporation',
    '00:1D:BA': 'Sony Corporation',
    '00:24:8D': 'Sony Corporation',
    '70:9E:29': 'Sony Interactive (PlayStation)',
    '00:1C:62': 'LG Electronics',
    '00:1E:75': 'LG Electronics',
    '00:1F:6B': 'LG Electronics',
    '20:3D:66': 'LG Electronics',
    '00:50:F2': 'Microsoft',
    '28:18:78': 'Microsoft',
    '70:6E:6D': 'Microsoft (Xbox)',
}


class LanDevice(BaseModel):
    """Модель устройства, обнаруженного в локальной сети."""
    ip: str = Field(description='IPv4 или IPv6 адрес устройства')
    mac: Optional[str] = Field(default=None, description='MAC-адрес устройства (e.g. 00:11:22:33:44:55)')
    hostname: Optional[str] = Field(default=None, description='Разрешённое сетевое имя устройства')
    vendor: Optional[str] = Field(default=None, description='Производитель устройства по OUI MAC-адреса')
    interface_name: Optional[str] = Field(default=None, description='Имя локального адаптера, через который обнаружено устройство')
    state: str = Field(default='Online', description='Статус устройства (Reachable, Permanent, Stale, Online)')
    is_gateway: bool = Field(default=False, description='Является ли устройство шлюзом по умолчанию')
    is_local: bool = Field(default=False, description='Является ли адрес собственным IP текущего хоста')
    discovery_methods: List[str] = Field(default_factory=list, description='Методы обнаружения (arp_cache, arp_sweep, ssdp, mdns, netbios)')
    latency_ms: Optional[float] = Field(default=None, description='Задержка отклика в миллисекундах')
    extra: Dict[str, Any] = Field(default_factory=dict, description='Дополнительные атрибуты (SSDP server, friendly name и др.)')


class WindowsLanScanner:
    """Многопоточный сканер и коллектор устройств локальной сети Windows."""

    def __init__(self) -> None:
        """Инициализация нативного IP Helper API и локального состояния."""
        self._net_api = IPHelperAPI()
        self._cached_devices: List[LanDevice] = []
        self._last_scan_time: float = 0.0

    @staticmethod
    def lookup_vendor(mac: Optional[str]) -> Optional[str]:
        """Определение производителя устройства по префиксу MAC-адреса (OUI).

        Args:
            mac: MAC-адрес (e.g. '00:1A:2B:3C:4D:5E' или '00-1A-2B-3C-4D-5E').

        Returns:
            Optional[str]: Название производителя или None.
        """
        if not mac:
            return None
        clean_mac = mac.replace('-', ':').upper().strip()
        parts = clean_mac.split(':')
        if len(parts) >= 3:
            prefix = ':'.join(parts[:3])
            return OUI_VENDOR_MAP.get(prefix)
        return None

    def get_default_gateways(self) -> Set[str]:
        """Получение списка IP-адресов шлюзов по умолчанию.

        Returns:
            Set[str]: Множество IPv4 адресов шлюзов.
        """
        gateways: Set[str] = set()
        if os.name == 'nt':
            try:
                cmd = [
                    'powershell', '-NoProfile', '-NonInteractive', '-Command',
                    "Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Select-Object -ExpandProperty NextHop | ConvertTo-Json -Compress"
                ]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if res.returncode == 0 and res.stdout.strip():
                    data = json.loads(res.stdout.strip())
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        if isinstance(item, str) and item.strip() and item != '0.0.0.0':
                            gateways.add(item.strip())
            except Exception as ex:
                logger.debug(f'Ошибка получения шлюзов через PowerShell: {ex}')
        return gateways

    def get_local_interfaces_info(self) -> List[Dict[str, Any]]:
        """Получение активных IPv4 сетевых интерфейсов хоста и их подсетей.

        Returns:
            List[Dict[str, Any]]: Список интерфейсов с IP, маской и подсетью.
        """
        interfaces_info: List[Dict[str, Any]] = []
        try:
            import psutil
            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            for iface_name, addr_list in addrs.items():
                stat = stats.get(iface_name)
                if stat and not stat.isup:
                    continue
                for a in addr_list:
                    if str(a.family) in ('AddressFamily.AF_INET', '2'):
                        ip = a.address
                        netmask = a.netmask
                        if ip and not ip.startswith('127.') and not ip.startswith('169.254.'):
                            try:
                                if netmask:
                                    network = ipaddress.IPv4Network(f'{ip}/{netmask}', strict=False)
                                else:
                                    network = ipaddress.IPv4Network(f'{ip}/24', strict=False)
                                interfaces_info.append({
                                    'name': iface_name,
                                    'ip': ip,
                                    'netmask': netmask,
                                    'network': network,
                                    'cidr': str(network),
                                })
                            except Exception:
                                pass
        except Exception as ex:
            logger.debug(f'Ошибка получения локальных интерфейсов через psutil: {ex}')
        return interfaces_info

    @staticmethod
    def is_valid_host_ip(ip: Optional[str], mac: Optional[str] = None) -> bool:
        """Проверка, что IP-адрес принадлежит реальному сетевому узлу (а не broadcast или multicast).

        Args:
            ip: IPv4/IPv6 адрес.
            mac: Опциональный MAC-адрес.

        Returns:
            bool: True если это валидный хост.
        """
        if not ip or ip == '0.0.0.0':
            return False
        if ip.startswith('127.') or ip.startswith('169.254.') or ip.startswith('224.') or ip.startswith('239.') or ip.startswith('255.'):
            return False
        if ip.endswith('.255') or ip.endswith('.0'):
            return False
        if mac:
            clean_mac = mac.upper().replace('-', ':')
            if clean_mac in ('FF:FF:FF:FF:FF:FF', '00:00:00:00:00:00'):
                return False
        try:
            addr = ipaddress.ip_address(ip)
            if addr.is_multicast or addr.is_loopback or addr.is_unspecified or addr.is_reserved:
                return False
        except Exception:
            return False
        return True

    def get_neighbor_cache_devices(self) -> List[LanDevice]:
        """Получение известных соседних устройств из кеша ядра Windows (ARP/Neighbor Table).

        Returns:
            List[LanDevice]: Список устройств из кеша.
        """
        devices: List[LanDevice] = []
        seen_ips: Set[str] = set()
        gateways = self.get_default_gateways()
        local_ifaces = self.get_local_interfaces_info()
        local_ips = {iface['ip'] for iface in local_ifaces}

        # 1. Нативный вызов GetIpNetTable
        try:
            native_neighbors = self._net_api.get_ip_net_table()
            for n in native_neighbors:
                ip = n.get('ip')
                mac = n.get('mac')
                if not self.is_valid_host_ip(ip, mac) or ip in seen_ips:
                    continue
                seen_ips.add(ip)
                vendor = self.lookup_vendor(mac)
                devices.append(LanDevice(
                    ip=ip,
                    mac=mac,
                    vendor=vendor,
                    state=n.get('type', 'Dynamic'),
                    is_gateway=(ip in gateways),
                    is_local=(ip in local_ips),
                    discovery_methods=['arp_cache'],
                ))
        except Exception as ex:
            logger.debug(f'Нативное чтение ARP-таблицы не удалось: {ex}')

        # 2. PowerShell fallback: Get-NetNeighbor
        if not devices and os.name == 'nt':
            try:
                cmd = [
                    'powershell', '-NoProfile', '-NonInteractive', '-Command',
                    "Get-NetNeighbor -AddressFamily IPv4 | Where-Object { $_.State -ne 'Unreachable' -and $_.LinkLayerAddress -ne '' } | "
                    "Select-Object IPAddress, LinkLayerAddress, State, InterfaceAlias | ConvertTo-Json -Compress"
                ]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=6)
                if res.returncode == 0 and res.stdout.strip():
                    data = json.loads(res.stdout.strip())
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        ip = item.get('IPAddress')
                        mac = item.get('LinkLayerAddress')
                        if not self.is_valid_host_ip(ip, mac) or ip in seen_ips:
                            continue
                        seen_ips.add(ip)
                        vendor = self.lookup_vendor(mac)
                        devices.append(LanDevice(
                            ip=ip,
                            mac=mac,
                            vendor=vendor,
                            interface_name=item.get('InterfaceAlias'),
                            state=item.get('State', 'Reachable'),
                            is_gateway=(ip in gateways),
                            is_local=(ip in local_ips),
                            discovery_methods=['powershell_neighbor'],
                        ))
            except Exception as ex:
                logger.debug(f'PowerShell Get-NetNeighbor не удался: {ex}')

        return devices

    def probe_ip_arp(self, ip: str) -> Optional[Dict[str, Any]]:
        """Опрос одного IP-адреса через нативный SendARP Windows.

        Args:
            ip: Целевой IPv4-адрес.

        Returns:
            Optional[Dict[str, Any]]: Данные отклика (ip, mac, latency_ms) или None.
        """
        start = time.perf_counter()
        mac = self._net_api.send_arp(ip)
        elapsed_ms = round((time.perf_counter() - start) * 1000.0, 2)
        if mac:
            return {'ip': ip, 'mac': mac, 'latency_ms': elapsed_ms}
        return None

    def scan_subnet(
        self,
        subnet_cidr: Optional[str] = None,
        max_workers: int = 64,
        max_hosts: int = 254,
    ) -> List[LanDevice]:
        """Активное параллельное сканирование локальной подсети через SendARP.

        Args:
            subnet_cidr: CIDR подсети (например, '192.168.1.0/24'). Если не задан, сканируются все активные интерфейсы.
            max_workers: Размер пула потоков для параллельного опроса.
            max_hosts: Максимальное число хостов для сканирования одной подсети.

        Returns:
            List[LanDevice]: Список ответивших устройств.
        """
        targets: List[str] = []
        ifaces = self.get_local_interfaces_info()
        gateways = self.get_default_gateways()
        local_ips = {iface['ip'] for iface in ifaces}

        if subnet_cidr:
            try:
                net = ipaddress.IPv4Network(subnet_cidr, strict=False)
                hosts = [str(h) for h in net.hosts()][:max_hosts]
                targets.extend(hosts)
            except Exception as ex:
                logger.error(f'Невалидный CIDR подсети {subnet_cidr}: {ex}')
        else:
            for iface in ifaces:
                net = iface['network']
                # Ограничиваем сканирование максимум /24 сетью (254 хоста)
                hosts = [str(h) for h in net.hosts()][:max_hosts]
                targets.extend(hosts)

        discovered: List[LanDevice] = []
        if not targets:
            return discovered

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_ip = {executor.submit(self.probe_ip_arp, ip): ip for ip in targets}
            for future in concurrent.futures.as_completed(future_to_ip):
                try:
                    res = future.result()
                    if res:
                        ip = res['ip']
                        mac = res['mac']
                        vendor = self.lookup_vendor(mac)
                        discovered.append(LanDevice(
                            ip=ip,
                            mac=mac,
                            vendor=vendor,
                            state='Online',
                            is_gateway=(ip in gateways),
                            is_local=(ip in local_ips),
                            discovery_methods=['arp_sweep'],
                            latency_ms=res.get('latency_ms'),
                        ))
                except Exception as ex:
                    logger.debug(f'Ошибка потока сканирования ARP: {ex}')

        return discovered

    def discover_ssdp_devices(self, timeout: float = 1.2) -> List[Dict[str, Any]]:
        """Обнаружение смарт-устройств в сети через SSDP / UPnP M-SEARCH multicast.

        Args:
            timeout: Время ожидания ответов в секундах.

        Returns:
            List[Dict[str, Any]]: Список обнаруженных UPnP сервисов/устройств с IP и описанием.
        """
        ssdp_devices: List[Dict[str, Any]] = []
        ssdp_request = (
            'M-SEARCH * HTTP/1.1\r\n'
            'HOST: 239.255.255.250:1900\r\n'
            'MAN: "ssdp:discover"\r\n'
            'MX: 1\r\n'
            'ST: ssdp:all\r\n'
            '\r\n'
        ).encode('utf-8')

        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            sock.settimeout(timeout)
            sock.sendto(ssdp_request, ('239.255.255.250', 1900))

            seen_locations: Set[str] = set()
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    data, addr = sock.recvfrom(4096)
                    ip = addr[0]
                    text = data.decode('utf-8', errors='ignore')
                    server = ''
                    location = ''
                    usn = ''
                    for line in text.splitlines():
                        if line.lower().startswith('server:'):
                            server = line.split(':', 1)[1].strip()
                        elif line.lower().startswith('location:'):
                            location = line.split(':', 1)[1].strip()
                        elif line.lower().startswith('usn:'):
                            usn = line.split(':', 1)[1].strip()

                    key = f'{ip}_{server}_{location}'
                    if key not in seen_locations:
                        seen_locations.add(key)
                        ssdp_devices.append({
                            'ip': ip,
                            'server': server,
                            'location': location,
                            'usn': usn,
                        })
                except socket.timeout:
                    break
                except Exception:
                    break
        except Exception as ex:
            logger.debug(f'Ошибка SSDP discovery: {ex}')
        finally:
            if sock:
                try:
                    sock.close()
                except Exception:
                    pass

        return ssdp_devices

    @staticmethod
    def resolve_hostname(ip: str) -> Optional[str]:
        """Разрешение доменного имени или NetBIOS имени для IP-адреса.

        Args:
            ip: IPv4 адрес.

        Returns:
            Optional[str]: Разрешённое имя хоста или None.
        """
        try:
            # 1. Reverse DNS
            host_info = socket.gethostbyaddr(ip)
            if host_info and host_info[0]:
                name = host_info[0]
                if name != ip:
                    return name
        except Exception:
            pass

        # 2. NetBIOS Node Status Query (порт UDP 137)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(0.3)
            # NetBIOS Node Status query payload (Wildcard *)
            query = (
                b'\x80\x00'  # Transaction ID
                b'\x00\x00'  # Flags (Query)
                b'\x00\x01'  # Questions: 1
                b'\x00\x00\x00\x00\x00\x00'
                b'\x20'      # Length of name
                b'CKAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\x00'  # Encoded '*'
                b'\x00\x21'  # Type: NBSTAT
                b'\x00\x01'  # Class: IN
            )
            sock.sendto(query, (ip, 137))
            data, _ = sock.recvfrom(1024)
            sock.close()
            if len(data) > 57:
                num_names = data[56]
                if num_names > 0 and len(data) >= 57 + 18:
                    raw_name = data[57:57 + 15].decode('ascii', errors='ignore').strip()
                    if raw_name:
                        return raw_name
        except Exception:
            pass

        return None

    def enrich_devices_with_details(self, devices: List[LanDevice]) -> List[LanDevice]:
        """Параллельное обогащение списка устройств именами хостов и данными SSDP.

        Args:
            devices: Исходный список устройств.

        Returns:
            List[LanDevice]: Обогащённый список устройств.
        """
        if not devices:
            return []

        # Запускаем параллельное разрешение имён
        with concurrent.futures.ThreadPoolExecutor(max_workers=32) as executor:
            future_to_dev = {executor.submit(self.resolve_hostname, dev.ip): dev for dev in devices if not dev.hostname}
            for future in concurrent.futures.as_completed(future_to_dev):
                dev = future_to_dev[future]
                try:
                    name = future.result()
                    if name:
                        dev.hostname = name
                except Exception:
                    pass

        return devices

    def discover_devices(
        self,
        full_scan: bool = False,
        subnet_cidr: Optional[str] = None,
        include_ssdp: bool = True,
    ) -> List[LanDevice]:
        """Главный метод обнаружения устройств в локальной сети.

        Args:
            full_scan: Если True, запускает активный ARP-свип по подсетям. Если False, читает быстрый кеш ARP.
            subnet_cidr: Опциональный фильтр конкретной подсети (например, '192.168.1.0/24').
            include_ssdp: Если True, опрашивает UPnP/SSDP смарт-устройства.

        Returns:
            List[LanDevice]: Нормализованный и обогащённый список устройств.
        """
        device_map: Dict[str, LanDevice] = {}

        # 1. Добавляем собственный хост (локальные интерфейсы)
        local_ifaces = self.get_local_interfaces_info()
        gateways = self.get_default_gateways()
        for iface in local_ifaces:
            ip = iface['ip']
            hostname = socket.gethostname()
            device_map[ip] = LanDevice(
                ip=ip,
                hostname=hostname,
                interface_name=iface['name'],
                state='LocalHost',
                is_gateway=False,
                is_local=True,
                discovery_methods=['local_interface'],
            )

        # 2. Получаем кеш ARP соседей ядра
        cache_devices = self.get_neighbor_cache_devices()
        for d in cache_devices:
            if d.ip not in device_map:
                device_map[d.ip] = d
            else:
                existing = device_map[d.ip]
                if d.mac and not existing.mac:
                    existing.mac = d.mac
                if d.vendor and not existing.vendor:
                    existing.vendor = d.vendor
                for m in d.discovery_methods:
                    if m not in existing.discovery_methods:
                        existing.discovery_methods.append(m)

        # 3. При запросе full_scan — запускаем активный ARP-свип
        if full_scan:
            active_devices = self.scan_subnet(subnet_cidr=subnet_cidr)
            for d in active_devices:
                if d.ip not in device_map:
                    device_map[d.ip] = d
                else:
                    existing = device_map[d.ip]
                    if d.mac and not existing.mac:
                        existing.mac = d.mac
                    if d.vendor and not existing.vendor:
                        existing.vendor = d.vendor
                    if d.latency_ms is not None:
                        existing.latency_ms = d.latency_ms
                    for m in d.discovery_methods:
                        if m not in existing.discovery_methods:
                            existing.discovery_methods.append(m)

        # 4. Опрос SSDP смарт-устройств
        if include_ssdp:
            ssdp_list = self.discover_ssdp_devices(timeout=1.0)
            for item in ssdp_list:
                ip = item['ip']
                if ip in device_map:
                    dev = device_map[ip]
                    if 'ssdp' not in dev.discovery_methods:
                        dev.discovery_methods.append('ssdp')
                    dev.extra['ssdp_server'] = item.get('server')
                    dev.extra['ssdp_location'] = item.get('location')
                else:
                    device_map[ip] = LanDevice(
                        ip=ip,
                        state='Online',
                        is_gateway=(ip in gateways),
                        is_local=False,
                        discovery_methods=['ssdp'],
                        extra={'ssdp_server': item.get('server'), 'ssdp_location': item.get('location')},
                    )

        result_list = list(device_map.values())

        # 5. Обогащаем именами хостов и производителями
        self.enrich_devices_with_details(result_list)

        # Фильтруем по подсети, если запрошено
        if subnet_cidr:
            try:
                target_net = ipaddress.IPv4Network(subnet_cidr, strict=False)
                result_list = [d for d in result_list if ipaddress.IPv4Address(d.ip) in target_net]
            except Exception:
                pass

        # Сортировка: сначала шлюз, потом локальный хост, затем по IP адресу
        def sort_key(d: LanDevice):
            try:
                ip_num = int(ipaddress.IPv4Address(d.ip))
            except Exception:
                ip_num = 0
            priority = 0 if d.is_gateway else 1 if d.is_local else 2
            return (priority, ip_num)

        result_list.sort(key=sort_key)
        self._cached_devices = result_list
        self._last_scan_time = time.time()
        return result_list


__all__ = ['LanDevice', 'WindowsLanScanner', 'OUI_VENDOR_MAP']
