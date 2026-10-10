# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Core Audits - Network Collector
# =============================================================================
# Description:
#   Коллектор аудита сетевой активности и открытых портов Windows.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.core.audits.network_collector import NetworkCollector
#
#     service = NetworkCollector()
#
# File: network_collector.py
# Project: ai-breadboard
# Package: apps.windows.sdk.core.audits
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Коллектор аудита сетевой активности и открытых портов Windows."""

# Updated: 2026-10-01 07:53:00
import json
import subprocess
import time
from typing import Any, Dict, List
import psutil
from logger import logger
from apps.windows.telemetry.win32_ffi.nethelper import IPHelperAPI
from apps.windows.sdk.core.models import AuditFinding, DomainAuditResult, RiskLevel

class NetworkCollector:
    """Коллектор фактов о сетевых адаптерах и подключениях."""

    def __init__(self) -> None:
        """Инициализация коллектора с поддержкой нативного IP Helper API."""
        self._net_api = IPHelperAPI()

    def collect(self) -> DomainAuditResult:
        """Сбор данных о сетевых соединениях и портах.

        Returns:
            DomainAuditResult: Результат аудита сети.
        """
        start_t = time.perf_counter()
        findings: List[AuditFinding] = []
        listening_ports = []
        established_conns = []
        suspicious_conns = []
        native_success = False
        try:
            tcp_sockets = self._net_api.get_tcp_connections()
            for s in tcp_sockets:
                if s.state == 'LISTEN':
                    listening_ports.append({'port': s.local_port, 'ip': s.local_address, 'pid': s.pid})
                    if s.local_port > 10000 and s.pid > 4:
                        try:
                            proc = psutil.Process(s.pid)
                            proc_name = proc.name().lower()
                            if proc_name not in ['svchost.exe', 'explorer.exe', 'system', 'services.exe', 'lsass.exe']:
                                suspicious_conns.append({'type': 'listening', 'port': s.local_port, 'process': proc.name(), 'pid': s.pid})
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                elif s.state == 'ESTABLISHED':
                    established_conns.append({'local': f'{s.local_address}:{s.local_port}', 'remote': f'{s.remote_address}:{s.remote_port}', 'pid': s.pid})
            native_success = len(tcp_sockets) > 0
        except Exception as ex:
            logger.debug(f'Нативный сбор IP Helper завершился с ошибкой: {ex}')
        if not native_success:
            try:
                conns = psutil.net_connections(kind='inet')
                for c in conns:
                    if c.status == psutil.CONN_LISTEN and c.laddr:
                        listening_ports.append({'port': c.laddr.port, 'ip': c.laddr.ip, 'pid': c.pid})
                        if c.laddr.port > 10000 and c.pid:
                            try:
                                proc = psutil.Process(c.pid)
                                if proc.name().lower() not in ['svchost.exe', 'explorer.exe', 'system']:
                                    suspicious_conns.append({'type': 'listening', 'port': c.laddr.port, 'process': proc.name(), 'pid': c.pid})
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                pass
                    elif c.status == psutil.CONN_ESTABLISHED and c.raddr:
                        established_conns.append({'local': f'{c.laddr.ip}:{c.laddr.port}', 'remote': f'{c.raddr.ip}:{c.raddr.port}', 'pid': c.pid})
            except Exception as e:
                logger.debug(f'Ошибка при сборе сетевых подключений через psutil: {e}')
        firewall_status = self._get_firewall_status()
        if firewall_status.get('firewall_enabled') is False:
            findings.append(AuditFinding(domain='network', category='firewall_disabled', title='Брандмауэр Windows отключен', description='Отключение встроенного брандмауэра повышает риск несанкционированного доступа.', severity=RiskLevel.CRITICAL, evidence=firewall_status))

        usage_report_summary = None
        adapter_stats_list = []
        try:
            from apps.windows.network.network_usage import WindowsNetworkUsageCollector
            usage_collector = WindowsNetworkUsageCollector()
            rep = usage_collector.get_traffic_period_summary(period_minutes=1440)
            usage_report_summary = rep.model_dump()
            adapter_stats_list = [a.model_dump() for a in rep.adapter_stats]
        except Exception as ex_usage:
            logger.debug(f'Failed to collect network usage report in NetworkCollector: {ex_usage}')

        metrics: Dict[str, Any] = {
            'listening_ports_count': len(listening_ports),
            'established_connections_count': len(established_conns),
            'suspicious_connections_count': len(suspicious_conns),
            'sample_listening_ports': listening_ports[:10],
            'suspicious_connections': suspicious_conns,
            'firewall_status': firewall_status,
            'network_usage_summary': usage_report_summary,
            'adapter_statistics': adapter_stats_list,
            'engine': 'Native IP Helper (iphlpapi.dll)' if native_success else 'psutil fallback',
        }
        duration_ms = (time.perf_counter() - start_t) * 1000
        result = DomainAuditResult(domain_name='network', title_ru='Сетевая телеметрия и порты', status='critical' if findings else 'ok', findings=findings, metrics=metrics, scan_duration_ms=round(duration_ms, 2))
        self._last_result = result
        return result

    def _get_firewall_status(self) -> Dict[str, Any]:
        """Получение статуса встроенного брандмауэра Windows через COM / PowerShell."""
        try:
            import win32com.client
            fw_policy = win32com.client.Dispatch('HNetCfg.FwPolicy2')
            domain_on = fw_policy.FirewallEnabled(1)
            private_on = fw_policy.FirewallEnabled(2)
            public_on = fw_policy.FirewallEnabled(4)
            is_enabled = any([domain_on, private_on, public_on])
            return {'firewall_enabled': is_enabled, 'profiles_enabled': sum([int(domain_on), int(private_on), int(public_on)]), 'total_profiles': 3, 'engine': 'COM HNetCfg.FwPolicy2'}
        except Exception:
            pass
        cmd = ['powershell', '-NoProfile', '-Command', 'Get-NetFirewallProfile -All | Select-Object Name, Enabled | ConvertTo-Json -Compress']
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout.strip())
                profiles = data if isinstance(data, list) else [data]
                enabled_count = sum((1 for p in profiles if p.get('Enabled') is True))
                return {'firewall_enabled': enabled_count > 0, 'profiles_enabled': enabled_count, 'total_profiles': len(profiles), 'engine': 'PowerShell NetSecurity'}
        except Exception as e:
            logger.debug(f'Ошибка при проверке брандмауэра: {e}')
        return {'firewall_enabled': True, 'engine': 'Default assumption'}
