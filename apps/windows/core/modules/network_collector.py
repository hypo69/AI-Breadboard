# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Network & Connection Intelligence Collector
# =============================================================================
# Description:
#   Сбор активных TCP/UDP соединений, открытых портов (Listening Ports),
#   сетевых адаптеров и сопоставление сетевой активности с процессами (PID).
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
from apps.windows.core.models import AuditFinding, DomainAuditResult, RiskLevel


class NetworkCollector:
    """Коллектор фактов о сетевых адаптерах и подключениях."""

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

        try:
            conns = psutil.net_connections(kind='inet')
            for c in conns:
                if c.status == psutil.CONN_LISTEN and c.laddr:
                    listening_ports.append({
                        "port": c.laddr.port,
                        "ip": c.laddr.ip,
                        "pid": c.pid,
                    })
                    # Проверка необычных портов для прослушивания
                    if c.laddr.port > 10000 and c.pid:
                        try:
                            proc = psutil.Process(c.pid)
                            if proc.name() not in ["svchost.exe", "explorer.exe", "system"]:
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
            logger.debug(f"Ошибка при сборе сетевых подключений: {e}")

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
        }

        duration_ms = (time.perf_counter() - start_t) * 1000
        return DomainAuditResult(
            domain_name="network",
            title_ru="Сетевая телеметрия и порты",
            status="critical" if findings else "ok",
            findings=findings,
            metrics=metrics,
            scan_duration_ms=round(duration_ms, 2),
        )

    def _get_firewall_status(self) -> Dict[str, Any]:
        """Получение статуса встроенного брандмауэра Windows."""
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
                }
        except Exception as e:
            logger.debug(f"Ошибка при проверке брандмауэра: {e}")
        return {"firewall_enabled": True}
