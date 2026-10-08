# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry Win32_Ffi - Nethelper
# =============================================================================
# Description:
#   Низкоуровневый интерфейс к IP Helper API (iphlpapi.dll) Windows.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.win32_ffi.nethelper import MIB_TCPROW_OWNER_PID
#
#     service = MIB_TCPROW_OWNER_PID()
#
# File: nethelper.py
# Project: ai-breadboard
# Package: apps.windows.telemetry.win32_ffi
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Низкоуровневый интерфейс к IP Helper API (iphlpapi.dll) Windows."""

import ctypes
import ctypes.wintypes as wintypes
import socket
import struct
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from logger import logger
AF_INET = 2
AF_INET6 = 23
TCP_TABLE_BASIC_LISTENER = 0
TCP_TABLE_BASIC_CONNECTIONS = 1
TCP_TABLE_BASIC_ALL = 2
TCP_TABLE_OWNER_PID_LISTENER = 3
TCP_TABLE_OWNER_PID_CONNECTIONS = 4
TCP_TABLE_OWNER_PID_ALL = 5
TCP_TABLE_OWNER_MODULE_LISTENER = 6
TCP_TABLE_OWNER_MODULE_CONNECTIONS = 7
TCP_TABLE_OWNER_MODULE_ALL = 8
UDP_TABLE_BASIC = 0
UDP_TABLE_OWNER_PID = 1
UDP_TABLE_OWNER_MODULE = 2
MIB_TCP_STATE_CLOSED = 1
MIB_TCP_STATE_LISTEN = 2
MIB_TCP_STATE_SYN_SENT = 3
MIB_TCP_STATE_SYN_RCVD = 4
MIB_TCP_STATE_ESTAB = 5
MIB_TCP_STATE_FIN_WAIT1 = 6
MIB_TCP_STATE_FIN_WAIT2 = 7
MIB_TCP_STATE_CLOSE_WAIT = 8
MIB_TCP_STATE_CLOSING = 9
MIB_TCP_STATE_LAST_ACK = 10
MIB_TCP_STATE_TIME_WAIT = 11
MIB_TCP_STATE_DELETE_TCB = 12
TCP_STATE_MAP = {MIB_TCP_STATE_CLOSED: 'CLOSED', MIB_TCP_STATE_LISTEN: 'LISTEN', MIB_TCP_STATE_SYN_SENT: 'SYN_SENT', MIB_TCP_STATE_SYN_RCVD: 'SYN_RCVD', MIB_TCP_STATE_ESTAB: 'ESTABLISHED', MIB_TCP_STATE_FIN_WAIT1: 'FIN_WAIT1', MIB_TCP_STATE_FIN_WAIT2: 'FIN_WAIT2', MIB_TCP_STATE_CLOSE_WAIT: 'CLOSE_WAIT', MIB_TCP_STATE_CLOSING: 'CLOSING', MIB_TCP_STATE_LAST_ACK: 'LAST_ACK', MIB_TCP_STATE_TIME_WAIT: 'TIME_WAIT', MIB_TCP_STATE_DELETE_TCB: 'DELETE_TCB'}
ERROR_INSUFFICIENT_BUFFER = 122

class MIB_TCPROW_OWNER_PID(ctypes.Structure):
    """Структура записи TCP соединения с PID."""
    _fields_ = [('dwState', wintypes.DWORD), ('dwLocalAddr', wintypes.DWORD), ('dwLocalPort', wintypes.DWORD), ('dwRemoteAddr', wintypes.DWORD), ('dwRemotePort', wintypes.DWORD), ('dwOwningPid', wintypes.DWORD)]

class MIB_UDPROW_OWNER_PID(ctypes.Structure):
    """Структура записи UDP сокета с PID."""
    _fields_ = [('dwLocalAddr', wintypes.DWORD), ('dwLocalPort', wintypes.DWORD), ('dwOwningPid', wintypes.DWORD)]

class MIB_IF_ROW2(ctypes.Structure):
    """Нативная структура MIB_IF_ROW2 из iphlpapi.dll."""
    _fields_ = [
        ('InterfaceLuid', ctypes.c_uint64),
        ('InterfaceIndex', wintypes.DWORD),
        ('InterfaceGuid', ctypes.c_byte * 16),
        ('Alias', ctypes.c_wchar * 257),
        ('Description', ctypes.c_wchar * 257),
        ('PhysicalAddressLength', wintypes.DWORD),
        ('PhysicalAddress', ctypes.c_byte * 32),
        ('PermanentPhysicalAddress', ctypes.c_byte * 32),
        ('Mtu', wintypes.DWORD),
        ('Type', wintypes.DWORD),
        ('TunnelType', ctypes.c_int),
        ('MediaType', ctypes.c_int),
        ('PhysicalMediumType', ctypes.c_int),
        ('AccessType', ctypes.c_int),
        ('DirectionType', ctypes.c_int),
        ('InterfaceAndOperStatusFlags', ctypes.c_byte),
        ('OperStatus', ctypes.c_int),
        ('AdminStatus', ctypes.c_int),
        ('MediaConnectState', ctypes.c_int),
        ('NetworkGuid', ctypes.c_byte * 16),
        ('ConnectionType', ctypes.c_int),
        ('TransmitLinkSpeed', ctypes.c_uint64),
        ('ReceiveLinkSpeed', ctypes.c_uint64),
        ('InOctets', ctypes.c_uint64),
        ('InUcastPkts', ctypes.c_uint64),
        ('InNUcastPkts', ctypes.c_uint64),
        ('InDiscards', ctypes.c_uint64),
        ('InErrors', ctypes.c_uint64),
        ('InUnknownProtos', ctypes.c_uint64),
        ('InUcastOctets', ctypes.c_uint64),
        ('InMulticastOctets', ctypes.c_uint64),
        ('InBroadcastOctets', ctypes.c_uint64),
        ('OutOctets', ctypes.c_uint64),
        ('OutUcastPkts', ctypes.c_uint64),
        ('OutNUcastPkts', ctypes.c_uint64),
        ('OutDiscards', ctypes.c_uint64),
        ('OutErrors', ctypes.c_uint64),
        ('OutUcastOctets', ctypes.c_uint64),
        ('OutMulticastOctets', ctypes.c_uint64),
        ('OutBroadcastOctets', ctypes.c_uint64),
        ('OutQLen', ctypes.c_uint64),
    ]

class MIB_IF_TABLE2(ctypes.Structure):
    """Таблица сетевых интерфейсов MIB_IF_TABLE2."""
    _fields_ = [
        ('NumEntries', wintypes.DWORD),
        ('Table', MIB_IF_ROW2 * 1),
    ]

class MIB_IPNETROW(ctypes.Structure):
    """Структура записи таблицы ARP (MIB_IPNETROW)."""
    _fields_ = [
        ('dwIndex', wintypes.DWORD),
        ('dwPhysAddrLen', wintypes.DWORD),
        ('bPhysAddr', ctypes.c_ubyte * 8),
        ('dwAddr', wintypes.DWORD),
        ('dwType', wintypes.DWORD),
    ]

class MIB_IPNETTABLE(ctypes.Structure):
    """Таблица записей ARP (MIB_IPNETTABLE)."""
    _fields_ = [
        ('dwNumEntries', wintypes.DWORD),
        ('table', MIB_IPNETROW * 1),
    ]

IP_NET_TYPE_MAP = {
    1: 'OTHER',
    2: 'INVALID',
    3: 'DYNAMIC',
    4: 'STATIC',
}

@dataclass
class NetworkSocketInfo:
    """Нормализованные данные о сетевом соединении/сокете."""
    protocol: str
    local_address: str
    local_port: int
    remote_address: str
    remote_port: int
    state: str
    pid: int

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь."""
        return {'protocol': self.protocol, 'local_address': self.local_address, 'local_port': self.local_port, 'remote_address': self.remote_address, 'remote_port': self.remote_port, 'state': self.state, 'pid': self.pid}

class IPHelperAPI:
    """Нативный интерфейс к iphlpapi.dll."""

    def __init__(self) -> None:
        """Инициализация функций iphlpapi.dll."""
        self._iphlpapi = ctypes.windll.iphlpapi
        self._GetExtendedTcpTable = self._iphlpapi.GetExtendedTcpTable
        self._GetExtendedTcpTable.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD), wintypes.BOOL, wintypes.ULONG, ctypes.c_int, wintypes.ULONG]
        self._GetExtendedTcpTable.restype = wintypes.DWORD
        self._GetExtendedUdpTable = self._iphlpapi.GetExtendedUdpTable
        self._GetExtendedUdpTable.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD), wintypes.BOOL, wintypes.ULONG, ctypes.c_int, wintypes.ULONG]
        self._GetExtendedUdpTable.restype = wintypes.DWORD

        # SendARP
        self._SendARP = getattr(self._iphlpapi, 'SendARP', None)
        if self._SendARP:
            self._SendARP.argtypes = [wintypes.ULONG, wintypes.ULONG, ctypes.c_void_p, ctypes.POINTER(wintypes.ULONG)]
            self._SendARP.restype = wintypes.DWORD

        # GetIpNetTable
        self._GetIpNetTable = getattr(self._iphlpapi, 'GetIpNetTable', None)
        if self._GetIpNetTable:
            self._GetIpNetTable.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.ULONG), wintypes.BOOL]
            self._GetIpNetTable.restype = wintypes.DWORD

        if hasattr(self._iphlpapi, 'GetIfTable2'):
            self._GetIfTable2 = self._iphlpapi.GetIfTable2
            self._GetIfTable2.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
            self._GetIfTable2.restype = wintypes.DWORD
            self._FreeMibTable = getattr(self._iphlpapi, 'FreeMibTable', None)
            if self._FreeMibTable:
                self._FreeMibTable.argtypes = [ctypes.c_void_p]
        else:
            self._GetIfTable2 = None

    @staticmethod
    def _ip_to_str(ip_int: int) -> str:
        """Преобразование сетевого порядка байт IP в строку."""
        try:
            return socket.inet_ntoa(struct.pack('<L', ip_int))
        except Exception:
            return '0.0.0.0'

    @staticmethod
    def _port_to_int(port_int: int) -> int:
        """Преобразование сетевого порядка байт порта в int."""
        return port_int >> 8 & 255 | (port_int & 255) << 8

    def get_adapter_statistics(self) -> List[Dict[str, Any]]:
        """Получение накопительной статистики по всем сетевым адаптерам через GetIfTable2.

        Returns:
            List[Dict[str, Any]]: Список словарей со статистикой интерфейсов.
        """
        if not self._GetIfTable2:
            return []
        p_table = ctypes.c_void_p()
        res = self._GetIfTable2(ctypes.byref(p_table))
        if res != 0 or not p_table:
            return []
        try:
            num_entries = ctypes.cast(p_table, ctypes.POINTER(wintypes.DWORD)).contents.value
            offset = ctypes.sizeof(wintypes.DWORD)
            row_size = ctypes.sizeof(MIB_IF_ROW2)
            base_addr = p_table.value or 0
            if not base_addr:
                return []
            stats: List[Dict[str, Any]] = []
            for i in range(num_entries):
                row_addr = base_addr + offset + i * row_size
                row = MIB_IF_ROW2.from_address(row_addr)
                name = row.Alias or row.Description or f'Interface_{row.InterfaceIndex}'
                stats.append({
                    'name': name,
                    'alias': row.Alias,
                    'description': row.Description,
                    'interface_index': row.InterfaceIndex,
                    'received_bytes': row.InOctets,
                    'sent_bytes': row.OutOctets,
                    'received_packets': row.InUcastPkts + row.InNUcastPkts,
                    'sent_packets': row.OutUcastPkts + row.OutNUcastPkts,
                    'received_discarded': row.InDiscards,
                    'received_errors': row.InErrors,
                    'outbound_discarded': row.OutDiscards,
                    'outbound_errors': row.OutErrors,
                    'transmit_speed_bps': row.TransmitLinkSpeed,
                    'receive_speed_bps': row.ReceiveLinkSpeed,
                    'oper_status': row.OperStatus,
                })
            return stats
        finally:
            if hasattr(self, '_FreeMibTable') and self._FreeMibTable and p_table:
                self._FreeMibTable(p_table)

    def get_tcp_connections(self) -> List[NetworkSocketInfo]:
        """Получение всех активных TCP соединений и слушающих портов с PID.

        Returns:
            List[NetworkSocketInfo]: Список соединений.
        """
        size = wintypes.DWORD(0)
        self._GetExtendedTcpTable(None, ctypes.byref(size), True, AF_INET, TCP_TABLE_OWNER_PID_ALL, 0)
        if size.value == 0:
            return []
        buf = (ctypes.c_byte * size.value)()
        res = self._GetExtendedTcpTable(buf, ctypes.byref(size), True, AF_INET, TCP_TABLE_OWNER_PID_ALL, 0)
        if res != 0:
            return []
        num_entries = ctypes.cast(buf, ctypes.POINTER(wintypes.DWORD)).contents.value
        row_size = ctypes.sizeof(MIB_TCPROW_OWNER_PID)
        offset = ctypes.sizeof(wintypes.DWORD)
        connections: List[NetworkSocketInfo] = []
        for i in range(num_entries):
            row_ptr = ctypes.byref(buf, offset + i * row_size)
            row = ctypes.cast(row_ptr, ctypes.POINTER(MIB_TCPROW_OWNER_PID)).contents
            state_str = TCP_STATE_MAP.get(row.dwState, f'STATE_{row.dwState}')
            local_ip = self._ip_to_str(row.dwLocalAddr)
            local_port = self._port_to_int(row.dwLocalPort)
            remote_ip = self._ip_to_str(row.dwRemoteAddr)
            remote_port = self._port_to_int(row.dwRemotePort) if row.dwState != MIB_TCP_STATE_LISTEN else 0
            connections.append(NetworkSocketInfo(protocol='TCP', local_address=local_ip, local_port=local_port, remote_address=remote_ip, remote_port=remote_port, state=state_str, pid=row.dwOwningPid))
        return connections

    def get_udp_sockets(self) -> List[NetworkSocketInfo]:
        """Получение всех UDP слушающих сокетов с привязкой к PID.

        Returns:
            List[NetworkSocketInfo]: Список UDP сокетов.
        """
        size = wintypes.DWORD(0)
        self._GetExtendedUdpTable(None, ctypes.byref(size), True, AF_INET, UDP_TABLE_OWNER_PID, 0)
        if size.value == 0:
            return []
        buf = (ctypes.c_byte * size.value)()
        res = self._GetExtendedUdpTable(buf, ctypes.byref(size), True, AF_INET, UDP_TABLE_OWNER_PID, 0)
        if res != 0:
            return []
        num_entries = ctypes.cast(buf, ctypes.POINTER(wintypes.DWORD)).contents.value
        row_size = ctypes.sizeof(MIB_UDPROW_OWNER_PID)
        offset = ctypes.sizeof(wintypes.DWORD)
        sockets_list: List[NetworkSocketInfo] = []
        for i in range(num_entries):
            row_ptr = ctypes.byref(buf, offset + i * row_size)
            row = ctypes.cast(row_ptr, ctypes.POINTER(MIB_UDPROW_OWNER_PID)).contents
            local_ip = self._ip_to_str(row.dwLocalAddr)
            local_port = self._port_to_int(row.dwLocalPort)
            sockets_list.append(NetworkSocketInfo(protocol='UDP', local_address=local_ip, local_port=local_port, remote_address='*.*.*.*', remote_port=0, state='LISTEN', pid=row.dwOwningPid))
        return sockets_list

    def send_arp(self, dest_ip: str, src_ip: Optional[str] = None) -> Optional[str]:
        """Отправка ARP-запроса через SendARP API Windows и получение MAC-адреса.

        Args:
            dest_ip: Целевой IPv4-адрес.
            src_ip: Исходный IPv4-адрес (опционально, 0 по умолчанию).

        Returns:
            Optional[str]: Отформатированный MAC-адрес (e.g. '00:1A:2B:3C:4D:5E') или None при отсутствии ответа.
        """
        if not getattr(self, '_SendARP', None):
            return None
        try:
            dest_addr = struct.unpack('<L', socket.inet_aton(dest_ip))[0]
            src_addr = struct.unpack('<L', socket.inet_aton(src_ip))[0] if src_ip else 0
            mac_buf = (ctypes.c_ubyte * 6)()
            mac_len = wintypes.ULONG(6)
            res = self._SendARP(dest_addr, src_addr, ctypes.byref(mac_buf), ctypes.byref(mac_len))
            if res == 0 and mac_len.value == 6:
                return ':'.join(f'{b:02X}' for b in mac_buf)
            return None
        except Exception as ex:
            logger.debug(f'SendARP error for {dest_ip}: {ex}')
            return None

    def get_ip_net_table(self) -> List[Dict[str, Any]]:
        """Получение таблицы ARP-записей соседей ядра Windows через GetIpNetTable.

        Returns:
            List[Dict[str, Any]]: Список записей ARP соседей (ip, mac, interface_index, type).
        """
        if not getattr(self, '_GetIpNetTable', None):
            return []
        try:
            size = wintypes.ULONG(0)
            self._GetIpNetTable(None, ctypes.byref(size), True)
            if size.value == 0:
                return []
            buf = (ctypes.c_byte * size.value)()
            res = self._GetIpNetTable(buf, ctypes.byref(size), True)
            if res != 0:
                return []
            num_entries = ctypes.cast(buf, ctypes.POINTER(wintypes.DWORD)).contents.value
            row_size = ctypes.sizeof(MIB_IPNETROW)
            offset = ctypes.sizeof(wintypes.DWORD)
            neighbors: List[Dict[str, Any]] = []
            for i in range(num_entries):
                row_ptr = ctypes.byref(buf, offset + i * row_size)
                row = ctypes.cast(row_ptr, ctypes.POINTER(MIB_IPNETROW)).contents
                ip = self._ip_to_str(row.dwAddr)
                if row.dwPhysAddrLen == 6:
                    mac = ':'.join(f'{b:02X}' for b in row.bPhysAddr[:6])
                else:
                    mac = ''
                net_type = IP_NET_TYPE_MAP.get(row.dwType, f'TYPE_{row.dwType}')
                if ip and ip != '0.0.0.0' and not ip.startswith('255.255.255') and not ip.startswith('224.') and net_type != 'INVALID':
                    neighbors.append({
                        'ip': ip,
                        'mac': mac,
                        'interface_index': row.dwIndex,
                        'type': net_type,
                    })
            return neighbors
        except Exception as ex:
            logger.debug(f'GetIpNetTable error: {ex}')
            return []