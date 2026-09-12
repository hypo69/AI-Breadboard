# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI System Diagnostics and Bottleneck Analyzer
# =============================================================================
# Description:
#   Evaluates system telemetry snapshots against heuristic anomaly rules
#   and invokes AI LLM reasoning models to diagnose performance degradation,
#   thermal throttling, and resource bottlenecks.
#
# Examples:
#   >>> from src.system.ai_diagnostics import SystemAIDiagnostician
#   >>> diagnostician = SystemAIDiagnostician()
#   >>> report = await diagnostician.diagnose(snapshot)
#   >>> print(report.health_score, report.summary)
#
# File: ai_diagnostics.py
# Project: ai-breadboard
# Package: src.system
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""AI-powered telemetry diagnostics and performance analyzer."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, List, Optional

from src.logger import logger
from src.system.models import AnomalyItem, SystemDiagnosticReport, SystemSnapshot


class SystemAIDiagnostician:
    """Intelligent diagnostics engine for host system telemetry."""

    def __init__(self, chat_model: Optional[Any] = None) -> None:
        """Initialize AI diagnostician with optional chat model backend.

        Args:
            chat_model: Optional UnifiedChatModel instance for LLM inference.
        """
        self.chat_model = chat_model

    def evaluate_heuristics(self, snapshot: SystemSnapshot) -> tuple[int, List[AnomalyItem], List[str]]:
        """Run fast rule-based heuristic checks over telemetry snapshot.

        Args:
            snapshot: Point-in-time system snapshot.

        Returns:
            tuple[int, List[AnomalyItem], List[str]]: Health score, anomalies, recommendations.
        """
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

    async def diagnose(self, snapshot: SystemSnapshot) -> SystemDiagnosticReport:
        """Run complete heuristic and AI LLM diagnostic analysis.

        Args:
            snapshot: Current telemetry snapshot.

        Returns:
            SystemDiagnosticReport: Structured diagnostic report.
        """
        score, anomalies, recommendations = self.evaluate_heuristics(snapshot)
        summary_text = (
            f"System health is rated at {score}/100 with {len(anomalies)} detected telemetry anomalies."
        )

        model_name = "Heuristic Analyzer"
        if self.chat_model is not None:
            try:
                prompt = (
                    "You are an expert Windows Hardware and System Performance Copilot. "
                    "Analyze the following JSON snapshot of CPU, RAM, GPU, Disks, and Top Processes:\n\n"
                    f"CPU: {snapshot.cpu.model} ({snapshot.cpu.total_percent}% load)\n"
                    f"RAM: {snapshot.memory.used_gb}/{snapshot.memory.total_gb} GB ({snapshot.memory.percent}%)\n"
                    f"Top Processes: {[p.model_dump() for p in snapshot.top_processes[:5]]}\n"
                    f"Sensors: {[s.model_dump() for s in snapshot.sensors[:5]]}\n\n"
                    "Provide a 2-3 sentence executive assessment and 2 key action recommendations."
                )

                response = await self.chat_model.ask(prompt)
                if response and isinstance(response, str) and response.strip():
                    summary_text = response.strip()
                    model_name = getattr(self.chat_model, "active_provider", "Unified AI")
            except Exception as ex:
                logger.debug(f"LLM diagnosis skipped, using heuristic fallback: {ex}")

        return SystemDiagnosticReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            health_score=score,
            summary=summary_text,
            anomalies=anomalies,
            recommendations=recommendations,
            ai_model_used=model_name,
        )
