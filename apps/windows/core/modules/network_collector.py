# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Network & Connection Intelligence Collector
# =============================================================================
# Description:
#   Сбор активных TCP/UDP соединений, открытых портов (Listening Ports),
#   сетевых адаптеров и сопоставление сетевой активности с процессами (PID).
#   Использует нативный IP Helper API (iphlpapi.dll) с fallback на psutil.
#
# Examples:
#   >>> from apps.windows.core.modules.network_collector import NetworkCollector
#   >>> collector = NetworkCollector()
#   >>> result = collector.collect()
#
# File: network_collector.py
# Project: ai-breadboard
# Package: apps.windows.core.modules
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Коллектор аудита сетевой активности и открытых портов Windows."""

from __future__ import annotations

import json
import subprocess
import time
from typing import Any, Dict, List

import psutil

from src.logger import logger
from apps.windows.api.nethelper import IPHelperAPI
from apps.windows.core.models import AuditFinding, DomainAuditResult, RiskLevel
from apps.common.csv_logger import AppCsvLogger


class NetworkCollector:
    """Коллектор фактов о сетевых адаптерах и подключениях."""

    def __init__(self) -> None:
        """Инициализация коллектора с поддержкой нативного IP Helper API и CSV логгирования."""
        self._net_api = IPHelperAPI()
        self._csv_logger = AppCsvLogger("network_terminal")

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

        # 1. Попытка нативного сбора через IP Helper API (GetExtendedTcpTable / GetExtendedUdpTable)
        native_success = False
        try:
            tcp_sockets = self._net_api.get_tcp_connections()
            for s in tcp_sockets:
                if s.state == "LISTEN":
                    listening_ports.append({
                        "port": s.local_port,
                        "ip": s.local_address,
                        "pid": s.pid,
                    })
                    if s.local_port > 10000 and s.pid > 4:
                        try:
                            proc = psutil.Process(s.pid)
                            proc_name = proc.name().lower()
                            if proc_name not in ["svchost.exe", "explorer.exe", "system", "services.exe", "lsass.exe"]:
                                suspicious_conns.append({
                                    "type": "listening",
                                    "port": s.local_port,
                                    "process": proc.name(),
                                    "pid": s.pid,
                                })
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                elif s.state == "ESTABLISHED":
                    established_conns.append({
                        "local": f"{s.local_address}:{s.local_port}",
                        "remote": f"{s.remote_address}:{s.remote_port}",
                        "pid": s.pid,
                    })
            native_success = len(tcp_sockets) > 0
        except Exception as ex:
            logger.debug(f"Нативный сбор IP Helper завершился с ошибкой: {ex}")

        # 2. Fallback на psutil при необходимости
        if not native_success:
            try:
                conns = psutil.net_connections(kind='inet')
                for c in conns:
                    if c.status == psutil.CONN_LISTEN and c.laddr:
                        listening_ports.append({
                            "port": c.laddr.port,
                            "ip": c.laddr.ip,
                            "pid": c.pid,
                        })
                        if c.laddr.port > 10000 and c.pid:
                            try:
                                proc = psutil.Process(c.pid)
                                if proc.name().lower() not in ["svchost.exe", "explorer.exe", "system"]:
                                    suspicious_conns.append({
                                        "type": "listening",
                                        "port": c.laddr.port,
                                        "process": proc.name(),
                                        "pid": c.pid,
                                    })
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                pass
                    elif c.status == psutil.CONN_ESTABLISHED and c.raddr:
                        established_conns.append({
                            "local": f"{c.laddr.ip}:{c.laddr.port}",
                            "remote": f"{c.raddr.ip}:{c.raddr.port}",
                            "pid": c.pid,
                        })
            except Exception as e:
                logger.debug(f"Ошибка при сборе сетевых подключений через psutil: {e}")

        # Получение статуса Firewall
        firewall_status = self._get_firewall_status()

        # Проверка на отключенный firewall
        if firewall_status.get("firewall_enabled") is False:
            findings.append(
                AuditFinding(
                    domain="network",
                    category="firewall_disabled",
                    title="Брандмауэр Windows отключен",
                    description="Отключение встроенного брандмауэра повышает риск несанкционированного доступа.",
                    severity=RiskLevel.CRITICAL,
                    evidence=firewall_status,
                )
            )

        metrics: Dict[str, Any] = {
            "listening_ports_count": len(listening_ports),
            "established_connections_count": len(established_conns),
            "suspicious_connections_count": len(suspicious_conns),
            "sample_listening_ports": listening_ports[:10],
            "suspicious_connections": suspicious_conns,
            "firewall_status": firewall_status,
            "engine": "Native IP Helper (iphlpapi.dll)" if native_success else "psutil fallback",
        }

        # Log network metrics to CSV via sensors
        self._log_network_metrics_csv(metrics)

        duration_ms = (time.perf_counter() - start_t) * 1000
        result = DomainAuditResult(
            domain_name="network",
            title_ru="Сетевая телеметрия и порты",
            status="critical" if findings else "ok",
            findings=findings,
            metrics=metrics,
            scan_duration_ms=round(duration_ms, 2),
        )
        self._last_result = result
        return result

    def _log_network_metrics_csv(self, metrics: Dict[str, Any]) -> None:
        """Log network metrics to CSV using Windows native tools.

        Args:
            metrics: Network metrics dictionary.
        """
        try:
            # Log listening ports count
            self._csv_logger.log_poll(
                poll_type="network_status",
                metric_name="listening_ports_count",
                value=metrics.get("listening_ports_count", 0),
                unit="ports",
                status="OK",
                details={"engine": metrics.get("engine", "unknown")},
                filename="network_terminal_status_polls.csv",
            )

            # Log established connections count
            self._csv_logger.log_poll(
                poll_type="network_status",
                metric_name="established_connections_count",
                value=metrics.get("established_connections_count", 0),
                unit="connections",
                status="OK",
                details={"engine": metrics.get("engine", "unknown")},
                filename="network_terminal_status_polls.csv",
            )

            # Log suspicious connections count
            self._csv_logger.log_poll(
                poll_type="network_status",
                metric_name="suspicious_connections_count",
                value=metrics.get("suspicious_connections_count", 0),
                unit="connections",
                status="OK",
                details={"engine": metrics.get("engine", "unknown")},
                filename="network_terminal_status_polls.csv",
            )

            # Log firewall status
            fw_status = metrics.get("firewall_status", {})
            self._csv_logger.log_poll(
                poll_type="network_status",
                metric_name="firewall_enabled",
                value=1 if fw_status.get("firewall_enabled") else 0,
                unit="bool",
                status="OK" if fw_status.get("firewall_enabled") else "WARNING",
                details={"profiles_enabled": fw_status.get("profiles_enabled", 0)},
                filename="network_terminal_status_polls.csv",
            )

        except Exception as ex:
            logger.debug(f"Failed to log network metrics to CSV: {ex}")


    def _get_firewall_status(self) -> Dict[str, Any]:
        """Получение статуса встроенного брандмауэра Windows через COM / PowerShell."""
        # 1. Попытка чтения через COM API "HNetCfg.FwPolicy2"
        try:
            import win32com.client  # type: ignore
            fw_policy = win32com.client.Dispatch("HNetCfg.FwPolicy2")
            # NET_FW_PROFILE2_DOMAIN = 1, PRIVATE = 2, PUBLIC = 4
            domain_on = fw_policy.FirewallEnabled(1)
            private_on = fw_policy.FirewallEnabled(2)
            public_on = fw_policy.FirewallEnabled(4)
            is_enabled = any([domain_on, private_on, public_on])
            return {
                "firewall_enabled": is_enabled,
                "profiles_enabled": sum([int(domain_on), int(private_on), int(public_on)]),
                "total_profiles": 3,
                "engine": "COM HNetCfg.FwPolicy2",
            }
        except Exception:
            pass

        # 2. Fallback на PowerShell
        cmd = [
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-NetFirewallProfile -All | Select-Object Name, Enabled | ConvertTo-Json -Compress",
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout.strip())
                profiles = data if isinstance(data, list) else [data]
                enabled_count = sum(1 for p in profiles if p.get("Enabled") is True)
                return {
                    "firewall_enabled": enabled_count > 0,
                    "profiles_enabled": enabled_count,
                    "total_profiles": len(profiles),
                    "engine": "PowerShell NetSecurity",
                }
        except Exception as e:
            logger.debug(f"Ошибка при проверке брандмауэра: {e}")

        return {"firewall_enabled": True, "engine": "Default assumption"}
