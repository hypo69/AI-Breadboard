# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry - Incident Detector
# =============================================================================
# Description:
#   Модуль непрерывного анализа аномалий и автоматического выявления сбоев системы.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.incident_detector import IncidentDetector
#
# File: incident_detector.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-03 23:15:00
# =============================================================================

"""Модуль `IncidentDetector`.

Содержит полную реализацию детектора аномалий, перенесённую из `telemetry_research`.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# logger import handling
try:
    from logger import logger
except ImportError:
    from logger import logger

from apps.windows.telemetry.models import TelemetryIncident
from apps.windows.telemetry.ring_buffer import TelemetryRingBuffer


class IncidentDetector:
    """Детектор аномалий в потоках метрик и событий с фиксацией инцидентов."""

    def __init__(
        self,
        cpu_threshold: float = 90.0,
        disk_write_burst_mb: float = 100.0,
        net_burst_mb: float = 50.0,
        ring_buffer: Optional[TelemetryRingBuffer] = None,
    ) -> None:
        """Инициализирует детектор пороговыми значениями и ссылкой на кольцевой буфер.

        Args:
            cpu_threshold: Порог срабатывания по CPU % (по умолчанию 90.0).
            disk_write_burst_mb: Порог дисковой записи в МБ/с (по умолчанию 100.0).
            net_burst_mb: Порог сетевого трафика в МБ/с (по умолчанию 50.0).
            ring_buffer: Ссылка на экземпляр кольцевого буфера памяти.
        """
        self.cpu_threshold = cpu_threshold
        self.disk_write_burst_mb = disk_write_burst_mb
        self.net_burst_mb = net_burst_mb
        self.ring_buffer = ring_buffer or TelemetryRingBuffer()
        self._last_incident_epoch: float = 0.0
        self._cooldown_seconds: float = 60.0  # Не спамить одинаковыми инцидентами чаще раза в минуту

    def check_anomaly(
        self,
        system_snapshot: Dict[str, Any],
        processes: Optional[List[Dict[str, Any]]] = None,
        recent_events: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[TelemetryIncident]:
        """Анализирует срез метрик и возвращает TelemetryIncident при обнаружении аномалии.

        Args:
            system_snapshot: Текущий снимок системы (SystemSnapshot dict).
            processes: Список процессов текущего среза.
            recent_events: Последние дискретные события (W64, ETW, Defender).

        Returns:
            Optional[TelemetryIncident]: Объект инцидента или None при штатной работе.
        """
        now = time.time()
        cpu_pct = float(system_snapshot.get("cpu_total_percent") or system_snapshot.get("cpu_percent") or 0.0)
        disk_w_mbs = float(system_snapshot.get("disk_write_bytes_sec") or 0.0) / (1024.0 * 1024.0)
        net_tx_mbs = float(system_snapshot.get("network_sent_bytes_sec") or 0.0) / (1024.0 * 1024.0)
        net_rx_mbs = float(system_snapshot.get("network_recv_bytes_sec") or 0.0) / (1024.0 * 1024.0)

        trigger_type: Optional[str] = None
        severity = "warning"
        title = ""
        description = ""
        suspects: List[Dict[str, Any]] = []

        # 1. Проверка CPU Spike
        if cpu_pct >= self.cpu_threshold:
            trigger_type = "cpu_spike"
            severity = "critical" if cpu_pct >= 95.0 else "warning"
            title = f"Критическая нагрузка на процессор: {cpu_pct:.1f}%"
            description = f"Общая загрузка CPU превысила порог {self.cpu_threshold}%, достигнув {cpu_pct:.1f}%."

        # 2. Проверка Disk Write Burst
        elif disk_w_mbs >= self.disk_write_burst_mb:
            trigger_type = "disk_burst"
            severity = "warning"
            title = f"Аномальная скорость записи на диск: {disk_w_mbs:.1f} МБ/с"
            description = f"Скорость дисковой записи превысила порог {self.disk_write_burst_mb} МБ/с."

        # 3. Проверка Network Burst
        elif (net_tx_mbs + net_rx_mbs) >= self.net_burst_mb:
            trigger_type = "network_burst"
            severity = "warning"
            title = f"Всплеск сетевой активности: {(net_tx_mbs + net_rx_mbs):.1f} МБ/с"
            description = f"Суммарный сетевой трафик достиг {(net_tx_mbs + net_rx_mbs):.1f} МБ/с (TX: {net_tx_mbs:.1f}, RX: {net_rx_mbs:.1f})."

        # 4. Проверка подозрительных процессов (AppData, Temp, Public)
        if processes:
            for p in processes:
                exe_path = str(p.get("path") or p.get("exe") or "").lower()
                p_cpu = float(p.get("cpu_percent") or 0.0)
                is_suspicious_location = any(
                    loc in exe_path for loc in ("\\temp\\", "\\appdata\\local\\temp", "\\users\\public\\")
                )
                if is_suspicious_location and (p_cpu > 15.0 or trigger_type is not None):
                    suspects.append({
                        "pid": p.get("pid"),
                        "name": p.get("name"),
                        "path": exe_path,
                        "cpu_percent": p_cpu,
                        "memory_mb": p.get("memory_mb"),
                        "reason": "Запуск из временного каталога с повышенной активностью",
                    })
                    if trigger_type is None and p_cpu > 30.0:
                        trigger_type = "suspicious_process"
                        severity = "critical"
                        title = f"Подозрительный процесс из Temp: {p.get('name')} (PID {p.get('pid')})"
                        description = f"Процесс {p.get('name')} выполняется из {exe_path} и потребляет {p_cpu:.1f}% CPU."

                elif p_cpu >= 50.0:
                    suspects.append({
                        "pid": p.get("pid"),
                        "name": p.get("name"),
                        "path": exe_path,
                        "cpu_percent": p_cpu,
                        "memory_mb": p.get("memory_mb"),
                        "reason": f"Высокое индивидуальное потребление CPU: {p_cpu:.1f}%",
                    })

        # 5. Проверка событий безопасности (Defender / ETW)
        matched_events: List[Dict[str, Any]] = []
        if recent_events:
            for ev in recent_events:
                ev_type = str(ev.get("event_type") or "").lower()
                ev_str = str(ev).lower()
                if "defender" in ev_type or "threat" in ev_str or "malware" in ev_str:
                    matched_events.append(ev)
                    if trigger_type is None:
                        trigger_type = "defender_alert"
                        severity = "critical"
                        title = "Срабатывание Windows Defender / Защиты от угроз"
                        description = f"Зафиксировано событие безопасности: {ev.get('name') or ev_type}"

        if not trigger_type:
            return None

        # Проверка кулдауна, чтобы не генерировать дубликаты ежесекундно
        if (now - self._last_incident_epoch) < self._cooldown_seconds:
            return None

        self._last_incident_epoch = now
        inc_id = f"INC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"

        # Захватываем срез из кольцевого буфера (например, 5 минут до события)
        raw_window = self.ring_buffer.get_window(center_timestamp=now, before_seconds=300.0, after_seconds=0.0)

        incident = TelemetryIncident(
            incident_id=inc_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            trigger_type=trigger_type,
            severity=severity,
            title=title,
            description=description,
            trigger_metrics={
                "cpu_percent": cpu_pct,
                "disk_write_mbs": disk_w_mbs,
                "network_tx_mbs": net_tx_mbs,
                "network_rx_mbs": net_rx_mbs,
            },
            suspect_processes=suspects,
            related_events=matched_events or (recent_events[:10] if recent_events else []),
            metrics_summary={
                "buffer_samples_captured": len(raw_window),
                "peak_cpu": cpu_pct,
                "peak_disk_write_mbs": disk_w_mbs,
            },
            raw_window=raw_window,
        )

        logger.warning(f"Зафиксирован инцидент телеметрии [{incident.incident_id}]: {incident.title}")
        return incident

    @staticmethod
    def format_incident_markdown_for_llm(incident: TelemetryIncident) -> str:
        """Форматирует инцидент в компактный структурированный Markdown для AI / LLM анализа.

        Args:
            incident: Объект TelemetryIncident.

        Returns:
            str: Готовый markdown блок для контекста языковой модели.
        """
        lines = [
            f"### 🚨 ДИАГНОСТИЧЕСКИЙ ИНЦИДЕНТ: [{incident.incident_id}]",
            f"- **Тип триггера:** `{incident.trigger_type}` | **Критичность:** `{incident.severity.upper()}`",
            f"- **Время:** {incident.timestamp}",
            f"- **Сводка:** {incident.title}",
            f"- **Описание:** {incident.description}",
            "",
            "#### 📊 Метрики в момент инцидента:",
            f"- CPU: `{incident.trigger_metrics.get('cpu_percent', 0.0)}%`",
            f"- Диск (Запись): `{incident.trigger_metrics.get('disk_write_mbs', 0.0)} МБ/с`",
            f"- Сеть (TX / RX): `{incident.trigger_metrics.get('network_tx_mbs', 0.0)} МБ/с` / `{incident.trigger_metrics.get('network_rx_mbs', 0.0)} МБ/с`",
            f"- Сохранено секундных замеров в буфере: `{incident.metrics_summary.get('buffer_samples_captured', 0)}`",
            "",
        ]

        if incident.suspect_processes:
            lines.append("#### 🔍 Подозрительные процессы:")
            lines.append("| PID | Имя | Путь | CPU % | Причина |")
            lines.append("|---|---|---|---|---|")
            for sp in incident.suspect_processes:
                lines.append(
                    f"| {sp.get('pid', '-')} | `{sp.get('name', '-')}` | `{sp.get('path', '-')}` | {sp.get('cpu_percent', 0.0)}% | {sp.get('reason', '-')} |"
                )
            lines.append("")

        if incident.related_events:
            lines.append("#### 📋 Сопутствующие события системы (Events):")
            for ev in incident.related_events[:5]:
                ev_name = ev.get("name") or ev.get("event_type") or "event"
                ev_time = ev.get("timestamp", "")
                lines.append(f"- `{ev_time}`: **{ev_name}** ({ev.get('path') or ev.get('details') or ''})")
            lines.append("")

        lines.append("Инструкция: Оцените потенциальную угрозу (вирус/майнер/зависание/утечка) и предложите конкретные меры противодействия.")
        return "\n".join(lines)
