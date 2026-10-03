# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry - Compactor
# =============================================================================
# Description:
#   Модуль логарифмического и многоуровневого сжатия (rollup) временных рядов.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.compactor import TelemetryCompactor, compute_percentile
#
# File: compactor.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-03 23:25:00
# =============================================================================

"""Модуль `TelemetryCompactor` и вспомогательная функция `compute_percentile`.

Перенесены из `telemetry_research` без обертки.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple

from apps.windows.telemetry.models import ProcessMetricRollup, SystemMetricRollup


def compute_percentile(values: Sequence[float], p: float = 95.0) -> float:
    """Вычисляет перцентиль выборки методом линейной интерполяции.

    Args:
        values: Последовательность числовых значений.
        p: Желаемый перцентиль (0..100), по умолчанию 95.0.

    Returns:
        float: Значение перцентиля (0.0 при пустой выборке).
    """
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    if n == 1:
        return float(sorted_vals[0])
    p_clamped = max(0.0, min(100.0, p))
    rank = (p_clamped / 100.0) * (n - 1)
    lower = int(math.floor(rank))
    upper = int(math.ceil(rank))
    weight = rank - lower
    return float(sorted_vals[lower] + weight * (sorted_vals[upper] - sorted_vals[lower]))


class TelemetryCompactor:
    """Компаратор и агрегатор временных рядов телеметрии."""

    @staticmethod
    def get_tier_for_age(age_seconds: float) -> str:
        """Определяет гранулярность (tier) в зависимости от возраста данных.

        Args:
            age_seconds: Возраст данных в секундах.

        Returns:
            str: Уровень агрегации ('1s', '2s', '5s', '10s', '30s', '1m', '5m', '15m', '1h', '6h').
        """
        if age_seconds <= 60.0:
            return "1s"
        elif age_seconds <= 300.0:
            return "2s"
        elif age_seconds <= 900.0:
            return "5s"
        elif age_seconds <= 1800.0:
            return "10s"
        elif age_seconds <= 3600.0:
            return "30s"
        elif age_seconds <= 10800.0:
            return "1m"
        elif age_seconds <= 43200.0:
            return "5m"
        elif age_seconds <= 86400.0:
            return "15m"
        elif age_seconds <= 604800.0:
            return "1h"
        else:
            return "6h"

    @staticmethod
    def compact_system_metrics(
        samples: List[Dict[str, Any]],
        period_start: str,
        period_end: str,
        tier: str = "1m",
    ) -> SystemMetricRollup:
        """Агрегирует список сырых замеров хоста в один SystemMetricRollup.

        Args:
            samples: Список словарей замеров (SystemSnapshot или сжатых метрик).
            period_start: ISO timestamp начала периода.
            period_end: ISO timestamp окончания периода.
            tier: Уровень гранулярности бакета.

        Returns:
            SystemMetricRollup: Сжатый бакет с расчётом avg, min, max, p95 и total.
        """
        count = len(samples)
        if count == 0:
            return SystemMetricRollup(
                period_start=period_start,
                period_end=period_end,
                duration_seconds=0.0,
                sample_count=0,
                tier=tier,
            )
        # Длительность периода
        duration_sec = 60.0
        try:
            t0 = datetime.fromisoformat(period_start)
            t1 = datetime.fromisoformat(period_end)
            duration_sec = max(1.0, (t1 - t0).total_seconds())
        except Exception:
            duration_sec = float(count)
        cpu_vals: List[float] = []
        ram_used_vals: List[float] = []
        ram_pct_vals: List[float] = []
        disk_read_rates: List[float] = []
        disk_write_rates: List[float] = []
        net_rx_rates: List[float] = []
        net_tx_rates: List[float] = []
        for s in samples:
            cpu_val = float(s.get("cpu_total_percent") or s.get("cpu_percent") or 0.0)
            cpu_vals.append(cpu_val)
            ram_used = float(s.get("memory_used_gb") or 0.0)
            ram_pct = float(s.get("memory_percent") or 0.0)
            ram_used_vals.append(ram_used)
            ram_pct_vals.append(ram_pct)
            disk_r = float(s.get("disk_read_bytes_sec") or 0.0) / (1024.0 * 1024.0)
            disk_w = float(s.get("disk_write_bytes_sec") or 0.0) / (1024.0 * 1024.0)
            disk_read_rates.append(disk_r)
            disk_write_rates.append(disk_w)
            net_rx = float(s.get("network_recv_bytes_sec") or 0.0) / (1024.0 * 1024.0)
            net_tx = float(s.get("network_sent_bytes_sec") or 0.0) / (1024.0 * 1024.0)
            net_rx_rates.append(net_rx)
            net_tx_rates.append(net_tx)
        sample_dt = duration_sec / max(1, count)
        cpu_avg = sum(cpu_vals) / count
        cpu_min = min(cpu_vals)
        cpu_max = max(cpu_vals)
        cpu_p95 = compute_percentile(cpu_vals, 95.0)
        ram_avg = sum(ram_used_vals) / count
        ram_min = min(ram_used_vals)
        ram_max = max(ram_used_vals)
        ram_pct_avg = sum(ram_pct_vals) / count
        ram_pct_max = max(ram_pct_vals)
        disk_r_avg = sum(disk_read_rates) / count
        disk_r_max = max(disk_read_rates)
        disk_r_total = sum(disk_read_rates) * sample_dt
        disk_w_avg = sum(disk_write_rates) / count
        disk_w_max = max(disk_write_rates)
        disk_w_total = sum(disk_write_rates) * sample_dt
        net_rx_avg = sum(net_rx_rates) / count
        net_rx_max = max(net_rx_rates)
        net_rx_total = sum(net_rx_rates) * sample_dt
        net_tx_avg = sum(net_tx_rates) / count
        net_tx_max = max(net_tx_rates)
        net_tx_total = sum(net_tx_rates) * sample_dt
        return SystemMetricRollup(
            period_start=period_start,
            period_end=period_end,
            duration_seconds=round(duration_sec, 2),
            sample_count=count,
            tier=tier,
            cpu_avg=round(cpu_avg, 2),
            cpu_min=round(cpu_min, 2),
            cpu_max=round(cpu_max, 2),
            cpu_p95=round(cpu_p95, 2),
            ram_avg_gb=round(ram_avg, 3),
            ram_min_gb=round(ram_min, 3),
            ram_max_gb=round(ram_max, 3),
            ram_percent_avg=round(ram_pct_avg, 2),
            ram_percent_max=round(ram_pct_max, 2),
            disk_read_avg_mbs=round(disk_r_avg, 3),
            disk_read_max_mbs=round(disk_r_max, 3),
            disk_read_total_mb=round(disk_r_total, 3),
            disk_write_avg_mbs=round(disk_w_avg, 3),
            disk_write_max_mbs=round(disk_w_max, 3),
            disk_write_total_mb=round(disk_w_total, 3),
            network_rx_avg_mbs=round(net_rx_avg, 3),
            network_rx_max_mbs=round(net_rx_max, 3),
            network_rx_total_mb=round(net_rx_total, 3),
            network_tx_avg_mbs=round(net_tx_avg, 3),
            network_tx_max_mbs=round(net_tx_max, 3),
            network_tx_total_mb=round(net_tx_total, 3),
        )

    @staticmethod
    def compact_process_metrics(
        process_samples: List[Dict[str, Any]],
        period_start: str,
        period_end: str,
    ) -> List[ProcessMetricRollup]:
        """Группирует и агрегирует замеры процессов по имени/PID.

        Args:
            process_samples: Список замеров процессов.
            period_start: Начало периода.
            period_end: Конец периода.

        Returns:
            List[ProcessMetricRollup]: Агрегированные показатели каждого процесса.
        """
        duration_sec = 60.0
        try:
            t0 = datetime.fromisoformat(period_start)
            t1 = datetime.fromisoformat(period_end)
            duration_sec = max(1.0, (t1 - t0).total_seconds())
        except Exception:
            duration_sec = 60.0
        # Группировка по (name, pid)
        grouped: Dict[Tuple[str, Optional[int]], List[Dict[str, Any]]] = {}
        for p in process_samples:
            key = (str(p.get("name", "unknown")), p.get("pid"))
            grouped.setdefault(key, []).append(p)
        results: List[ProcessMetricRollup] = []
        for (name, pid), p_list in grouped.items():
            count = len(p_list)
            cpu_vals = [float(item.get("cpu_percent") or 0.0) for item in p_list]
            ram_vals = [float(item.get("memory_mb") or 0.0) for item in p_list]
            read_bytes_sec = [float(item.get("read_bytes_sec") or 0.0) for item in p_list]
            write_bytes_sec = [float(item.get("write_bytes_sec") or 0.0) for item in p_list]
            rx_bytes_sec = [float(item.get("rx_bytes_sec") or 0.0) for item in p_list]
            tx_bytes_sec = [float(item.get("tx_bytes_sec") or 0.0) for item in p_list]
            sample_dt = duration_sec / max(1, count)
            path = p_list[0].get("path") or p_list[0].get("exe")
            cpu_avg = sum(cpu_vals) / count
            cpu_max = max(cpu_vals)
            cpu_p95 = compute_percentile(cpu_vals, 95.0)
            ram_avg = sum(ram_vals) / count
            ram_max = max(ram_vals)
            disk_r_tot = (sum(read_bytes_sec) * sample_dt) / (1024.0 * 1024.0)
            disk_w_tot = (sum(write_bytes_sec) * sample_dt) / (1024.0 * 1024.0)
            net_rx_tot = (sum(rx_bytes_sec) * sample_dt) / (1024.0 * 1024.0)
            net_tx_tot = (sum(tx_bytes_sec) * sample_dt) / (1024.0 * 1024.0)
            results.append(
                ProcessMetricRollup(
                    name=name,
                    pid=pid,
                    period_start=period_start,
                    period_end=period_end,
                    duration_seconds=round(duration_sec, 2),
                    sample_count=count,
                    path=path,
                    cpu_avg=round(cpu_avg, 2),
                    cpu_max=round(cpu_max, 2),
                    cpu_p95=round(cpu_p95, 2),
                    ram_avg_mb=round(ram_avg, 2),
                    ram_max_mb=round(ram_max, 2),
                    disk_read_total_mb=round(disk_r_tot, 3),
                    disk_write_total_mb=round(disk_w_tot, 3),
                    network_rx_total_mb=round(net_rx_tot, 3),
                    network_tx_total_mb=round(net_tx_tot, 3),
                )
            )
        return results
