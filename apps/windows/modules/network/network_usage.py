# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Network - Network Usage
# =============================================================================
# Description:
#   Многоуровневый коллектор сетевой телеметрии и исторического использования трафика Windows.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.network.network_usage import WindowsNetworkUsageCollector
#
#     service = WindowsNetworkUsageCollector()
#
# File: network_usage.py
# Project: ai-breadboard
# Package: apps.windows.modules.network
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Многоуровневый коллектор сетевой телеметрии и исторического использования трафика Windows."""

import json
import os
import subprocess
import time
from typing import Any, Dict, List, Optional
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False

from logger import logger
from apps.windows.telemetry.win32_ffi.nethelper import IPHelperAPI
from apps.windows.telemetry.models import (
    AppNetworkUsageItem,
    NetworkAdapterStatistics,
    NetworkPerformanceCounter,
    NetworkUsagePeriodReport,
)

class WindowsNetworkUsageCollector:
    """Коллектор сетевой статистики адаптеров, Performance Counters и использования трафика процессами."""

    def __init__(self) -> None:
        """Инициализация нативного IP Helper API и локального состояния снимков."""
        self._net_api = IPHelperAPI()
        self._last_process_io: Dict[int, Dict[str, Any]] = {}
        self._last_poll_time: float = time.time()

    def get_adapter_statistics(self) -> List[NetworkAdapterStatistics]:
        """Получить накопительную статистику сетевых адаптеров (ReceivedBytes, SentBytes, ошибки).

        Returns:
            List[NetworkAdapterStatistics]: Список объектов статистики адаптеров.
        """
        results: List[NetworkAdapterStatistics] = []
        try:
            native_stats = self._net_api.get_adapter_statistics()
            for s in native_stats:
                # Фильтруем нулевые отключенные интерфейсы если нужно, но сохраняем существующие
                if s.get('received_bytes', 0) > 0 or s.get('sent_bytes', 0) > 0:
                    results.append(NetworkAdapterStatistics(
                        name=s.get('name', 'Network Adapter'),
                        received_bytes=int(s.get('received_bytes', 0)),
                        sent_bytes=int(s.get('sent_bytes', 0)),
                        received_packets=int(s.get('received_packets', 0)),
                        sent_packets=int(s.get('sent_packets', 0)),
                        received_discarded=int(s.get('received_discarded', 0)),
                        received_errors=int(s.get('received_errors', 0)),
                        outbound_discarded=int(s.get('outbound_discarded', 0)),
                        outbound_errors=int(s.get('outbound_errors', 0)),
                    ))
        except Exception as ex:
            logger.debug(f'Нативный сбор статистики адаптеров через IP Helper не удался: {ex}')

        if not results and os.name == 'nt':
            results = self._get_adapter_statistics_powershell()
        return results

    def _get_adapter_statistics_powershell(self) -> List[NetworkAdapterStatistics]:
        """Fallback вызов PowerShell Get-NetAdapterStatistics.

        Returns:
            List[NetworkAdapterStatistics]: Результаты сбора через PowerShell.
        """
        results: List[NetworkAdapterStatistics] = []
        cmd = [
            'powershell', '-NoProfile', '-NonInteractive', '-Command',
            'Get-NetAdapterStatistics | Select-Object Name, ReceivedBytes, SentBytes, ReceivedPackets, SentPackets, ReceivedDiscarded, ReceivedErrors, OutboundDiscarded, OutboundErrors | ConvertTo-Json -Compress'
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout.strip())
                items = data if isinstance(data, list) else [data]
                for item in items:
                    results.append(NetworkAdapterStatistics(
                        name=item.get('Name', 'Adapter'),
                        received_bytes=int(item.get('ReceivedBytes') or 0),
                        sent_bytes=int(item.get('SentBytes') or 0),
                        received_packets=int(item.get('ReceivedPackets') or 0),
                        sent_packets=int(item.get('SentPackets') or 0),
                        received_discarded=int(item.get('ReceivedDiscarded') or 0),
                        received_errors=int(item.get('ReceivedErrors') or 0),
                        outbound_discarded=int(item.get('OutboundDiscarded') or 0),
                        outbound_errors=int(item.get('OutboundErrors') or 0),
                    ))
        except Exception as ex:
            logger.debug(f'PowerShell Get-NetAdapterStatistics не удался: {ex}')
        return results

    def get_performance_counters(self) -> List[NetworkPerformanceCounter]:
        """Получить текущую скорость по сетевым интерфейсам (Performance Counters).

        Returns:
            List[NetworkPerformanceCounter]: Список мгновенных скоростей передачи байт/сек.
        """
        counters: List[NetworkPerformanceCounter] = []
        if os.name == 'nt':
            cmd = [
                'powershell', '-NoProfile', '-NonInteractive', '-Command',
                "$rx = Get-Counter '\\Network Interface(*)\\Bytes Received/sec' -ErrorAction SilentlyContinue; "
                "$tx = Get-Counter '\\Network Interface(*)\\Bytes Sent/sec' -ErrorAction SilentlyContinue; "
                "$res = @(); "
                "if ($rx) { foreach ($sample in $rx.CounterSamples) { "
                "  $instance = $sample.InstanceName; "
                "  if ($instance -ne '_total') { "
                "    $txVal = 0.0; "
                "    if ($tx) { $match = $tx.CounterSamples | Where-Object { $_.InstanceName -eq $instance }; if ($match) { $txVal = $match.CookedValue } }; "
                "    $res += @{ interface = $instance; rx_rate = [math]::Round($sample.CookedValue, 2); tx_rate = [math]::Round($txVal, 2); total_rate = [math]::Round($sample.CookedValue + $txVal, 2) }; "
                "  } "
                "} }; "
                "$res | ConvertTo-Json -Compress"
            ]
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
                if res.returncode == 0 and res.stdout.strip():
                    data = json.loads(res.stdout.strip())
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        counters.append(NetworkPerformanceCounter(
                            interface_name=item.get('interface', 'Network Interface'),
                            bytes_recv_per_sec=float(item.get('rx_rate') or 0.0),
                            bytes_sent_per_sec=float(item.get('tx_rate') or 0.0),
                            bytes_total_per_sec=float(item.get('total_rate') or 0.0),
                        ))
            except Exception as ex:
                logger.debug(f'Ошибка сбора Performance Counters через PowerShell: {ex}')

        if not counters and PSUTIL_AVAILABLE:
            try:
                net_io = psutil.net_io_counters(pernic=True)
                for name, io in net_io.items():
                    counters.append(NetworkPerformanceCounter(
                        interface_name=name,
                        bytes_recv_per_sec=0.0,
                        bytes_sent_per_sec=0.0,
                        bytes_total_per_sec=0.0,
                    ))
            except Exception:
                pass
        return counters

    def get_app_network_usage(self, top_limit: int = 15) -> List[AppNetworkUsageItem]:
        """Получить атрибуцию сетевого трафика по приложениям и процессам.

        Args:
            top_limit: Максимальное число приложений в выдаче.

        Returns:
            List[AppNetworkUsageItem]: Потраченный сетевой трафик процессами.
        """
        app_map: Dict[str, Dict[str, Any]] = {}
        if PSUTIL_AVAILABLE:
            for proc in psutil.process_iter(attrs=['pid', 'name']):
                try:
                    pname = proc.info.get('name') or 'Unknown'
                    pid = proc.info.get('pid')
                    io = proc.io_counters()
                    rx = getattr(io, 'read_bytes', 0)
                    tx = getattr(io, 'write_bytes', 0)
                    # Группируем по имени исполняемого файла
                    key = pname.lower()
                    if key not in app_map:
                        app_map[key] = {
                            'process_name': pname,
                            'pids': [pid],
                            'rx_bytes': rx,
                            'tx_bytes': tx,
                        }
                    else:
                        app_map[key]['pids'].append(pid)
                        app_map[key]['rx_bytes'] += rx
                        app_map[key]['tx_bytes'] += tx
                except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                    continue

        total_system_bytes = sum((item['rx_bytes'] + item['tx_bytes'] for item in app_map.values())) or 1

        items: List[AppNetworkUsageItem] = []
        for key, item in app_map.items():
            tot = item['rx_bytes'] + item['tx_bytes']
            if tot == 0:
                continue
            pct = round((tot / total_system_bytes) * 100.0, 2)
            items.append(AppNetworkUsageItem(
                process_name=item['process_name'],
                pid=item['pids'][0] if item['pids'] else None,
                rx_bytes=item['rx_bytes'],
                tx_bytes=item['tx_bytes'],
                total_bytes=tot,
                rx_formatted=self._format_bytes(item['rx_bytes']),
                tx_formatted=self._format_bytes(item['tx_bytes']),
                share_percent=pct,
            ))

        items.sort(key=lambda x: x.total_bytes, reverse=True)
        return items[:top_limit]

    def get_traffic_period_summary(self, period_minutes: int = 1440) -> NetworkUsagePeriodReport:
        """Сформировать итоговый отчёт потребления сети за указанный период (например, 10 мин, 1 час, 24 часа).

        Args:
            period_minutes: Период отчета в минутах.

        Returns:
            NetworkUsagePeriodReport: Сводка использования сети для LLM/ai-diagnostics.
        """
        adapter_stats = self.get_adapter_statistics()
        perf_counters = self.get_performance_counters()
        top_apps = self.get_app_network_usage(top_limit=15)

        tot_rx = sum((a.received_bytes for a in adapter_stats))
        tot_tx = sum((a.sent_bytes for a in adapter_stats))
        if tot_rx == 0 and tot_tx == 0 and PSUTIL_AVAILABLE:
            net_io = psutil.net_io_counters()
            if net_io:
                tot_rx = net_io.bytes_recv
                tot_tx = net_io.bytes_sent

        period_desc = f"{period_minutes // 60} ч" if period_minutes >= 60 else f"{period_minutes} мин"
        tot_rx_fmt = self._format_bytes(tot_rx)
        tot_tx_fmt = self._format_bytes(tot_tx)
        tot_fmt = self._format_bytes(tot_rx + tot_tx)

        summary_lines = [
            f"За период ({period_desc}):",
            f"  - Получено (RX): {tot_rx_fmt}",
            f"  - Отправлено (TX): {tot_tx_fmt}",
            f"  - Суммарный трафик: {tot_fmt}",
            "Детализация по приложениям:",
        ]

        for app in top_apps[:7]:
            summary_lines.append(
                f"  • {app.process_name} — RX: {app.rx_formatted}, TX: {app.tx_formatted} ({app.share_percent}% от общего объёма)"
            )

        summary_text = "\n".join(summary_lines)

        return NetworkUsagePeriodReport(
            period_minutes=period_minutes,
            total_rx_bytes=tot_rx,
            total_tx_bytes=tot_tx,
            total_rx_formatted=tot_rx_fmt,
            total_tx_formatted=tot_tx_fmt,
            total_formatted=tot_fmt,
            adapter_stats=adapter_stats,
            performance_counters=perf_counters,
            top_apps=top_apps,
            summary_text=summary_text,
        )

    @staticmethod
    def _format_bytes(size_bytes: int | float) -> str:
        """Форматировать объем байтов в человекочитаемую строку.

        Args:
            size_bytes: Число байтов.

        Returns:
            str: Отформатированная строка (B, KB, MB, GB).
        """
        if size_bytes <= 0:
            return "0 B"
        units = ["B", "KB", "MB", "GB", "TB"]
        idx = 0
        val = float(size_bytes)
        while val >= 1024.0 and idx < len(units) - 1:
            val /= 1024.0
            idx += 1
        return f"{val:.2f} {units[idx]}"

