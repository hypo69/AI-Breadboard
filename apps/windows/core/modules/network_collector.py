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

        try:
            conns = psutil.net_connections(kind='inet')
            for c in conns:
                if c.status == psutil.CONN_LISTEN and c.laddr:
                    listening_ports.append({
                        "port": c.laddr.port,
                        "ip": c.laddr.ip,
                        "pid": c.pid,
                    })
                elif c.status == psutil.CONN_ESTABLISHED and c.raddr:
                    established_conns.append({
                        "local": f"{c.laddr.ip}:{c.laddr.port}",
                        "remote": f"{c.raddr.ip}:{c.raddr.port}",
                        "pid": c.pid,
                    })
        except Exception as e:
            logger.debug(f"Ошибка при сборе сетевых подключений: {e}")

        metrics: Dict[str, Any] = {
            "listening_ports_count": len(listening_ports),
            "established_connections_count": len(established_conns),
            "sample_listening_ports": listening_ports[:10],
        }

        duration_ms = (time.perf_counter() - start_t) * 1000
        return DomainAuditResult(
            domain_name="network",
            title_ru="Сетевая телеметрия и порты",
            status="ok",
            findings=findings,
            metrics=metrics,
            scan_duration_ms=round(duration_ms, 2),
        )
