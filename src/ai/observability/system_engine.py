# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: System Telemetry Diagnostic Engine
# =============================================================================
# Description:
#   Implements specific heuristic rules for SystemSnapshot telemetry.
#
# File: system_engine.py
# Project: ai-breadboard
# Package: src.ai.observability
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""System telemetry specific diagnostic engine."""

from __future__ import annotations
from typing import List, Tuple
from apps.windows.telemetry.models import AnomalyItem, SystemSnapshot
from src.ai.observability.engine import DiagnosticEngine

class SystemDiagnosticEngine(DiagnosticEngine):
    """Diagnoses system telemetry anomalies."""

    def evaluate_heuristics(self, snapshot: SystemSnapshot) -> Tuple[int, List[AnomalyItem], List[str]]:
        """Run rule-based heuristic checks over telemetry snapshot."""
        score = 100
        anomalies: List[AnomalyItem] = []
        recommendations: List[str] = []

        # 1. CPU Load Analysis
        if snapshot.cpu.total_percent >= 90.0:
            score -= 25
            anomalies.append(
                AnomalyItem(
                    subsystem="CPU",
                    severity="critical",
                    title="Critical CPU Saturation",
                    description=f"Overall CPU usage is at {snapshot.cpu.total_percent}%, causing system lag.",
                )
            )
            recommendations.append("Inspect top CPU processes and consider terminating unresponsive tasks.")
        elif snapshot.cpu.total_percent >= 75.0:
            score -= 10
            anomalies.append(
                AnomalyItem(
                    subsystem="CPU",
                    severity="warning",
                    title="Elevated CPU Load",
                    description=f"CPU load is elevated ({snapshot.cpu.total_percent}%).",
                )
            )

        # 2. Memory Analysis
        if snapshot.memory.percent >= 92.0:
            score -= 30
            anomalies.append(
                AnomalyItem(
                    subsystem="RAM",
                    severity="critical",
                    title="RAM Exhaustion Danger",
                    description=f"System RAM is {snapshot.memory.percent}% full ({snapshot.memory.used_gb}/{snapshot.memory.total_gb} GB).",
                )
            )
            recommendations.append("Close memory-heavy applications or increase virtual memory paging size.")
        elif snapshot.memory.percent >= 80.0:
            score -= 10
            anomalies.append(
                AnomalyItem(
                    subsystem="RAM",
                    severity="warning",
                    title="High Memory Pressure",
                    description=f"RAM utilization is at {snapshot.memory.percent}%.",
                )
            )

        # 3. Storage Space Analysis
        for disk in snapshot.disks:
            if disk.percent >= 95.0:
                score -= 15
                anomalies.append(
                    AnomalyItem(
                        subsystem="Disk",
                        severity="critical",
                        title=f"Drive {disk.device} Almost Full",
                        description=f"Volume {disk.mountpoint} is {disk.percent}% full with only {disk.free_gb} GB remaining.",
                    )
                )
                recommendations.append(f"Free up disk space on drive {disk.device} to prevent write failures.")
            elif disk.percent >= 85.0:
                score -= 5
                anomalies.append(
                    AnomalyItem(
                        subsystem="Disk",
                        severity="warning",
                        title=f"Low Space on {disk.device}",
                        description=f"Volume {disk.mountpoint} is at {disk.percent}% capacity.",
                    )
                )

        # 4. Thermal Sensors Analysis
        for sensor in snapshot.sensors:
            if sensor.category == "temperature" and sensor.value >= 85.0:
                score -= 20
                anomalies.append(
                    AnomalyItem(
                        subsystem="Thermals",
                        severity="critical",
                        title=f"High Temperature on {sensor.name}",
                        description=f"Sensor {sensor.name} reading {sensor.value}°C exceeds safe operating threshold.",
                    )
                )
                recommendations.append("Check chassis airflow, fan speeds, and clean heatsink dust filters.")

        # 5. Runaway Process Check
        for proc in snapshot.top_processes[:5]:
            if proc.cpu_percent >= 60.0:
                anomalies.append(
                    AnomalyItem(
                        subsystem="Process",
                        severity="warning",
                        title=f"High CPU Consumer: {proc.name} (PID {proc.pid})",
                        description=f"Process {proc.name} is consuming {proc.cpu_percent}% CPU single-handedly.",
                    )
                )

        score = max(0, min(100, score))
        if not recommendations:
            recommendations.append("System telemetry is within healthy operating parameters.")

        
        return score, anomalies, recommendations
