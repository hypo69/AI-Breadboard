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

import json
from typing import Any, Dict, List, Optional, Tuple
from apps.windows.telemetry.models import AnomalyItem, SystemSnapshot
from src.ai.observability.engine import DiagnosticEngine
from src.ai.observability.grouped_telemetry import (
    GroupedTelemetryBuilder,
    GroupDiagnosticResult,
    SynthesisDiagnosticResult,
    TelemetryGroupInfo,
)

class SystemDiagnosticEngine(DiagnosticEngine):
    """Диагностический движок для комплексного анализа телеметрии хоста и сенсоров."""

    def evaluate_heuristics(self, snapshot: SystemSnapshot) -> Tuple[int, List[AnomalyItem], List[str]]:
        """Выполнение детерминированного эвристического анализа сенсоров и телеметрии хоста.

        Args:
            snapshot: Актуальный срез телеметрии системы (SystemSnapshot).

        Returns:
            Tuple[int, List[AnomalyItem], List[str]]: Кортеж (индекс_здоровья, список_аномалий, рекомендации).
        """
        score = 100
        anomalies: List[AnomalyItem] = []
        recommendations: List[str] = []

        # 1. Анализ нагрузки на центральный процессор (CPU)
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

        # 2. Анализ оперативной памяти (RAM) и файла подкачки (Swap)
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

        # 3. Анализ дискового пространства и разделов
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

        # 4. Анализ здоровья физических дисков (SMART)
        for p_disk in snapshot.physical_disks:
            if p_disk.health_status and p_disk.health_status.lower() in ["warning", "unhealthy", "error", "bad"]:
                score -= 25
                anomalies.append(
                    AnomalyItem(
                        subsystem="Storage",
                        severity="critical",
                        title=f"SMART Warning on {p_disk.model}",
                        description=f"Physical drive {p_disk.device_id} ({p_disk.model}) reports health status: {p_disk.health_status}.",
                    )
                )
                recommendations.append(f"Perform disk backup and replace failing drive {p_disk.model}.")
            if p_disk.temperature_celsius and p_disk.temperature_celsius >= 60.0:
                score -= 10
                anomalies.append(
                    AnomalyItem(
                        subsystem="Storage",
                        severity="warning",
                        title=f"Overheating Storage: {p_disk.model}",
                        description=f"Drive temperature {p_disk.temperature_celsius}°C exceeds recommended operating limits.",
                    )
                )

        # 5. Анализ аппаратных сенсоров (температуры, кулеры, напряжение)
        for sensor in snapshot.sensors:
            if sensor.category == "temperature":
                if sensor.value >= 85.0:
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
                elif sensor.value >= 75.0:
                    score -= 5
                    anomalies.append(
                        AnomalyItem(
                            subsystem="Thermals",
                            severity="warning",
                            title=f"Elevated Temperature on {sensor.name}",
                            description=f"Sensor {sensor.name} reading {sensor.value}°C is elevated.",
                        )
                    )

        # 6. Анализ ресурсоемких процессов с фильтрацией системных псевдопроцессов
        ignored_processes = {"system idle process", "system", "idle"}
        for proc in snapshot.top_processes[:10]:
            p_name_lower = (proc.name or "").strip().lower()
            if proc.pid in [0, 4] or p_name_lower in ignored_processes:
                continue

            if proc.cpu_percent >= 60.0:
                anomalies.append(
                    AnomalyItem(
                        subsystem="Process",
                        severity="warning",
                        title=f"High CPU Consumer: {proc.name} (PID {proc.pid})",
                        description=f"Process {proc.name} is consuming {proc.cpu_percent:.1f}% CPU single-handedly.",
                    )
                )
            if proc.memory_mb >= 6144.0 or proc.memory_percent >= 40.0:
                anomalies.append(
                    AnomalyItem(
                        subsystem="Process",
                        severity="warning",
                        title=f"High Memory Consumer: {proc.name} (PID {proc.pid})",
                        description=f"Process {proc.name} is using {proc.memory_mb:.0f} MB RAM ({proc.memory_percent:.1f}%).",
                    )
                )

        # 7. Проверка системных предупреждений и необходимости перезагрузки
        if snapshot.alerts and getattr(snapshot.alerts, "reboot_pending", False):
            anomalies.append(
                AnomalyItem(
                    subsystem="Updates",
                    severity="warning",
                    title="System Reboot Pending",
                    description="Windows Updates or system components require a restart.",
                )
            )
            recommendations.append("Schedule a restart to finalize pending Windows system updates.")

        score = max(0, min(100, score))
        if not recommendations:
            recommendations.append("System telemetry is within healthy operating parameters.")

        return score, anomalies, recommendations

    def build_prompt(self, snapshot: Any, score: int, anomalies: List[AnomalyItem], summary_text: str) -> str:
        """Построение обогащенного диагностического контекста в формате JSON для языковой модели.

        Включает полную сводку по дискам, оперативной памяти, процессору, сенсорам,
        точкам восстановления, обновлениям и выявленным аномалиям.
        """
        if not isinstance(snapshot, SystemSnapshot):
            return super().build_prompt(snapshot, score, anomalies, summary_text)

        # Сбор статуса точек восстановления системы (быстрая проверка)
        backup_info: Dict[str, Any] = {
            "system_protection": "Enabled",
            "restore_points_count": 0,
            "latest_restore_point": "None",
        }
        try:
            from apps.windows.core.system_restore import WindowsSystemRestoreManager
            restore_mgr = WindowsSystemRestoreManager(timeout_seconds=3)
            prot = restore_mgr.check_protection_status()
            backup_info["system_protection"] = "Enabled" if prot.get("system_protection_enabled") else "Disabled"
            points = restore_mgr.list_restore_points()
            backup_info["restore_points_count"] = len(points)
            if points:
                backup_info["latest_restore_point"] = points[0].get("creation_time") or points[0].get("description", "")
        except Exception:
            pass

        # Топ активных процессов (фильтруя системные псевдопроцессы и idle)
        active_processes = [
            {
                "pid": p.pid,
                "name": p.name,
                "cpu_percent": round(p.cpu_percent, 1),
                "memory_mb": round(p.memory_mb, 1),
            }
            for p in snapshot.top_processes
            if p.pid not in [0, 4] and (p.name or "").lower() not in ["system idle process", "system", "idle"]
        ][:8]

        # Формирование словаря телеметрии хоста
        telemetry_payload: Dict[str, Any] = {
            "host_system": {
                "hostname": snapshot.hostname,
                "os": f"{snapshot.os_name} {snapshot.os_build}".strip(),
                "uptime_hours": round(snapshot.uptime_seconds / 3600, 1),
            },
            "cpu": {
                "model": snapshot.cpu.model,
                "load_percent": round(snapshot.cpu.total_percent, 1),
                "physical_cores": snapshot.cpu.physical_cores,
                "logical_cores": snapshot.cpu.logical_cores,
                "frequency_mhz": snapshot.cpu.frequency_mhz,
            },
            "memory": {
                "total_gb": snapshot.memory.total_gb,
                "used_gb": snapshot.memory.used_gb,
                "available_gb": snapshot.memory.available_gb,
                "used_percent": snapshot.memory.percent,
                "swap_percent": snapshot.memory.swap_percent,
            },
            "storage_partitions": [
                {
                    "device": d.device,
                    "mountpoint": d.mountpoint,
                    "total_gb": d.total_gb,
                    "free_gb": d.free_gb,
                    "used_percent": d.percent,
                }
                for d in snapshot.disks
            ],
            "physical_drives_smart": [
                {
                    "model": p.model,
                    "media_type": p.media_type,
                    "size_gb": p.size_gb,
                    "smart_health": p.health_status,
                    "temperature_celsius": p.temperature_celsius,
                }
                for p in snapshot.physical_disks
            ],
            "sensors": {
                "temperatures_celsius": {
                    s.name: s.value for s in snapshot.sensors if s.category == "temperature" or "temp" in s.sensor_id.lower()
                },
                "fans_speed": {
                    s.name: f"{s.value} {s.unit}" for s in snapshot.sensors if s.category == "fan" or "fan" in s.sensor_id.lower()
                },
                "voltages": {
                    s.name: f"{s.value} {s.unit}" for s in snapshot.sensors if s.category == "voltage" or "voltage" in s.sensor_id.lower()
                },
                "powers_watt": {
                    s.name: f"{s.value} {s.unit}" for s in snapshot.sensors if s.category == "power" or "power" in s.sensor_id.lower()
                },
                "all_sensor_readings": [
                    {
                        "name": s.name,
                        "category": s.category,
                        "value": s.value,
                        "unit": s.unit,
                    }
                    for s in snapshot.sensors
                ],
            },
            "backup_and_restore": backup_info,
            "system_updates": {
                "reboot_pending": bool(snapshot.alerts and snapshot.alerts.reboot_pending),
                "status": snapshot.updates.status if snapshot.updates else "Up to date",
            },
            "top_active_processes": active_processes,
        }

        if anomalies:
            telemetry_payload["detected_anomalies"] = [
                {
                    "subsystem": a.subsystem,
                    "severity": a.severity,
                    "title": a.title,
                    "description": a.description,
                }
                for a in anomalies
            ]

        json_context = json.dumps(telemetry_payload, indent=2, ensure_ascii=False)

        prompt = (
            "Вы — ведущий инженер по системной диагностике и анализу производительности хоста.\n"
            "Проанализируйте следующие входные данные телеметрии, аппаратных сенсоров и процессов системы в формате JSON:\n\n"
            f"```json\n{json_context}\n```\n\n"
            "ТРЕБОВАНИЯ К ОТВЕТУ:\n"
            "1. Проанализируйте значения всех сенсоров (температуры, вентиляторы, утилизацию дисковых разделов, память, CPU и топ процессов).\n"
            "2. Выявите узкие места, перегрузки и аномалии оборудования или программных служб.\n"
            "3. Сформируйте краткую экспертную оценку состояния (2-3 предложения) и 2-3 ключевые меры по устранению узких мест и оптимизации ресурсов.\n"
            "4. ВАЖНО: Запрещено выводить шаблонные подтверждения вроде 'Контекст принят', 'Жду инструкций' или 'Готов к работе'. Сразу выводите готовый анализ на русском языке."
        )
        return prompt

    def get_diagnostic_groups(self, snapshot: SystemSnapshot) -> List[TelemetryGroupInfo]:
        """Формирует список подготовленных функциональных групп телеметрии из системного снимка."""
        builder = GroupedTelemetryBuilder()
        return builder.build_all_groups(snapshot)

    async def diagnose_group(
        self,
        group_id: str,
        payload: Dict[str, Any],
        title: str = "",
    ) -> GroupDiagnosticResult:
        """Выполняет целевой AI-анализ одной конкретной группы телеметрии.

        Args:
            group_id: Идентификатор группы (compute_thermals, memory_processes, storage_smart, system_network).
            payload: Словарь с данными телеметрии группы.
            title: Заголовок группы.

        Returns:
            GroupDiagnosticResult: Структурированный результат анализа группы.
        """
        titles_map = {
            "compute_thermals": "CPU, GPU и Охлаждение",
            "memory_processes": "Память и Процессы",
            "storage_smart": "Диски и Хранилище",
            "system_network": "Сеть и Стабильность ОС",
        }
        icons_map = {
            "compute_thermals": "bi-fire",
            "memory_processes": "bi-memory",
            "storage_smart": "bi-hdd",
            "system_network": "bi-shield-check",
        }

        group_title = title or titles_map.get(group_id, "Группа телеметрии")
        icon = icons_map.get(group_id, "bi-cpu")

        # Извлечение ключевых метрик для быстрой отрисовки в карточке UI
        key_metrics: Dict[str, Any] = {}
        if group_id == "compute_thermals":
            cpu_info = payload.get("cpu", {})
            key_metrics["cpu_load"] = f"{cpu_info.get('load_percent', 0)}%"
            key_metrics["cpu_model"] = cpu_info.get("model", "CPU")
            temps = payload.get("sensors", {}).get("temperatures_celsius", {})
            key_metrics["max_temp"] = f"{max(temps.values())}°C" if temps else "Норма"
        elif group_id == "memory_processes":
            ram = payload.get("ram", {})
            key_metrics["ram_used"] = f"{ram.get('used_gb', 0)} / {ram.get('total_gb', 0)} GB ({ram.get('used_percent', 0)}%)"
            procs = payload.get("top_active_processes", [])
            key_metrics["top_process"] = f"{procs[0]['name']} ({procs[0]['cpu_percent']}%)" if procs else "Нет"
        elif group_id == "storage_smart":
            parts = payload.get("storage_partitions", [])
            max_used = max([p.get("used_percent", 0) for p in parts]) if parts else 0
            key_metrics["max_volume_fill"] = f"{max_used}%"
            key_metrics["volumes_count"] = len(parts)
        elif group_id == "system_network":
            updates = payload.get("system_updates", {})
            key_metrics["reboot_pending"] = "Да" if updates.get("reboot_pending") else "Нет"
            key_metrics["update_status"] = updates.get("status", "Up to date")

        json_str = json.dumps(payload, indent=2, ensure_ascii=False)
        prompt = (
            f"Вы — ведущий инженер по системной диагностике. Проанализируйте данные домена '{group_title}':\n\n"
            f"```json\n{json_str}\n```\n\n"
            "ТРЕБОВАНИЯ К ОТВЕТУ:\n"
            "1. Сформулируйте краткий вердикт состояния данного домена (1-2 предложения).\n"
            "2. Выделите ключевые аномалии или риски (если есть).\n"
            "3. Дайте 1-2 конкретные рекомендации по оптимизации.\n"
            "4. ВАЖНО: Запрещено отвечать фразами вроде 'Контекст принят' или 'Жду инструкций'. Сразу выводите готовый ответ на русском языке."
        )

        system_instruction = (
            f"Вы — эксперт по анализу системного домена '{group_title}'. "
            "Немедленно предоставьте краткий, информативный технический вердикт и рекомендации на русском языке."
        )

        model_name = "Heuristic Analyzer"
        summary_text = f"Телеметрия домена '{group_title}' в пределах нормы."
        raw_response: Optional[str] = None
        status = "ok"

        executor: Optional[Any] = self.chat_model
        if executor is not None:
            if hasattr(executor, "active_provider"):
                model_name = getattr(executor, "active_provider", "Unified AI")
            elif hasattr(executor, "model_id"):
                model_name = f"Gemini CLI ({getattr(executor, 'model_id', 'gemini-3.1-flash-lite')})"
            else:
                model_name = "AI Model"

            try:
                if hasattr(executor, "ask"):
                    if hasattr(executor, "_get_active_model"):
                        res = await executor.ask(
                            prompt,
                            model_name="gemini_cli:gemini-3.1-flash-lite",
                            system_instruction=system_instruction,
                        )
                    else:
                        res = await executor.ask(prompt, system_instruction=system_instruction)
                elif hasattr(executor, "chat"):
                    res = await executor.chat(prompt, system_instruction=system_instruction)
                else:
                    res = None

                if res and isinstance(res, str) and res.strip():
                    cleaned = res.strip()
                    if not (cleaned.startswith("Error:") or cleaned.startswith("Model error:")):
                        summary_text = cleaned
                        raw_response = cleaned
            except Exception as e:
                summary_text = f"Сводка {group_title}: параметры получены (ошибка LLM: {e})"

        # Эвристическая оценка статуса карточки (ok / warning / critical)
        if group_id == "compute_thermals":
            cpu_pct = payload.get("cpu", {}).get("load_percent", 0)
            temps = payload.get("sensors", {}).get("temperatures_celsius", {})
            max_t = max(temps.values()) if temps else 0
            if cpu_pct >= 90 or max_t >= 85:
                status = "critical"
            elif cpu_pct >= 75 or max_t >= 75:
                status = "warning"
        elif group_id == "memory_processes":
            ram_pct = payload.get("ram", {}).get("used_percent", 0)
            top_cpu = max([p.get("cpu_percent", 0) for p in payload.get("top_active_processes", [])] or [0])
            if ram_pct >= 90 or top_cpu >= 85:
                status = "critical"
            elif ram_pct >= 75 or top_cpu >= 50:
                status = "warning"
        elif group_id == "storage_smart":
            parts = payload.get("storage_partitions", [])
            max_fill = max([p.get("used_percent", 0) for p in parts]) if parts else 0
            if max_fill >= 95:
                status = "critical"
            elif max_fill >= 85:
                status = "warning"
        elif group_id == "system_network":
            updates = payload.get("system_updates", {})
            if updates.get("reboot_pending"):
                status = "warning"

        return GroupDiagnosticResult(
            group_id=group_id,
            title=group_title,
            icon=icon,
            status=status,
            summary=summary_text,
            key_metrics=key_metrics,
            raw_response=raw_response,
            ai_model_used=model_name,
        )

    async def synthesize_final_report(
        self,
        groups: List[GroupDiagnosticResult],
    ) -> SynthesisDiagnosticResult:
        """Формирует итоговый вердикт и приоритетный план действий на основе результатов всех групп."""
        groups_summary = "\n\n".join([
            f"### {g.title} (Статус: {g.status}):\n{g.summary}"
            for g in groups
        ])

        prompt = (
            "Вы — ведущий системный архитектор. На основе результатов по 4 доменам сформируйте итоговый вердикт:\n\n"
            f"{groups_summary}\n\n"
            "ТРЕБОВАНИЯ К ОТВЕТУ:\n"
            "1. Сформулируйте общее экспертное заключение по стабильности хоста (2-3 предложения).\n"
            "2. Укажите до 3 ключевых мер в порядке приоритета.\n"
            "3. Оцените общий Health Score хоста числом от 0 до 100.\n"
            "4. ВАЖНО: Запрещено выводить шаблонные подтверждения. Сразу пишите итоговый вердикт на русском языке."
        )

        critical_count = sum(1 for g in groups if g.status == "critical")
        warning_count = sum(1 for g in groups if g.status == "warning")
        calc_score = max(20, 100 - (critical_count * 20) - (warning_count * 10))

        status_label = "Отличное" if calc_score >= 85 else ("Внимание" if calc_score >= 60 else "Критическое")
        executive_summary = f"Аудит всех {len(groups)} подсистем завершен. Индекс здоровья системы: {calc_score}/100."
        actions: List[str] = []
        model_name = "Heuristic Analyzer"

        executor: Optional[Any] = self.chat_model
        if executor is not None:
            if hasattr(executor, "active_provider"):
                model_name = getattr(executor, "active_provider", "Unified AI")
            elif hasattr(executor, "model_id"):
                model_name = f"Gemini CLI ({getattr(executor, 'model_id', 'gemini-3.1-flash-lite')})"
            else:
                model_name = "AI Model"

            try:
                if hasattr(executor, "ask"):
                    res = await executor.ask(prompt, system_instruction="Вы — системный эксперт. Сформируйте краткий итоговый вердикт.")
                    if res and isinstance(res, str) and res.strip():
                        executive_summary = res.strip()
            except Exception:
                pass

        if critical_count > 0:
            actions.append("Устранить критические узкие места в хранилище и процессах.")
        if warning_count > 0:
            actions.append("Провести плановую оптимизацию подсистем с повышенной нагрузкой.")
        if not actions:
            actions.append("Система работает в штатном режиме, оптимизация не требуется.")

        return SynthesisDiagnosticResult(
            health_score=calc_score,
            status_label=status_label,
            executive_summary=executive_summary,
            critical_actions=actions,
            ai_model_used=model_name,
            groups_evaluated=len(groups),
        )


