# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry_Research - Diagnostic Engine
# =============================================================================
# Description:
#   Универсальный диагностический движок и системный анализатор телеметрии Windows.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry_research.diagnostic_engine import DiagnosticEngine
#
#     service = DiagnosticEngine()
#
# File: diagnostic_engine.py
# Project: ai-breadboard
# Package: apps.windows.telemetry_research
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 12:00:00
# =============================================================================

from __future__ import annotations
"""Универсальный диагностический движок и системный анализатор телеметрии Windows."""

import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

try:
    from logger import logger
except ImportError:
    from logger import logger

from apps.windows.telemetry.models import AnomalyItem, SystemDiagnosticReport, SystemSnapshot, TelemetryIncident
from apps.windows.telemetry_research.grouped_telemetry import (
    GroupDiagnosticResult,
    GroupedTelemetryBuilder,
    SynthesisDiagnosticResult,
    TelemetryGroupInfo,
)
from apps.windows.telemetry_research.incident_detector import IncidentDetector


class DiagnosticEngine(ABC):
    """Абстрактный базовый класс для диагностических движков телеметрии."""

    def __init__(self, chat_model: Optional[Any] = None) -> None:
        self.chat_model = chat_model

    @abstractmethod
    def evaluate_heuristics(self, data: Any) -> Tuple[int, List[AnomalyItem], List[str]]:
        """Выполнение детерминированных эвристических проверок."""
        pass

    def build_prompt(self, data: Any, score: int, anomalies: List[AnomalyItem], summary_text: str) -> str:
        """Построение контекстного промпта для языковой модели."""
        return (
            "Проанализируйте обнаруженные системные аномалии и метрики хоста:\n\n"
            f"Аномалии: {[a.model_dump() for a in anomalies]}\n"
            f"Текущий статус: {summary_text}\n\n"
            "ТРЕБОВАНИЯ К ОТВЕТУ:\n"
            "1. Немедленно предоставьте краткую диагностическую оценку (2-3 предложения) и 2-3 ключевые меры по устранению узких мест.\n"
            "2. Выведите готовый аналитический ответ сразу на русском языке без шаблонных вводных фраз."
        )

    async def diagnose(self, data: Any) -> SystemDiagnosticReport:
        """Запуск эвристического анализа с последующим опциональным LLM-синтезом."""
        stages: List[Dict[str, Any]] = [
            {
                "stage": "init",
                "title": "Сбор телеметрии",
                "message": "🔌 Получение актуального среза телеметрии и сенсоров хоста...",
                "details": "WMI, LibreHardwareMonitor, системные процессы и ресурсы хранилища",
            }
        ]
        system_instruction = (
            "Вы — ведущий инженер по системной диагностике и анализу производительности хоста. "
            "Ваша задача: на основе переданных сенсоров и телеметрии немедленно предоставить краткую экспертную оценку и практические рекомендации по оптимизации ресурсов. "
            "Сразу выведите готовый аналитический ответ на русском языке."
        )
        model_name = "Heuristic Analyzer"
        generated_prompt: Optional[str] = None
        raw_response: Optional[str] = None
        error_msg: Optional[str] = None

        # 1. Эвристический анализ
        try:
            score, anomalies, recommendations = self.evaluate_heuristics(data)
            summary_text = (
                f"Интегральный индекс здоровья: {score}/100. "
                f"Обнаружено аномалий: {len(anomalies)}. "
                + (f"Критические узкие места: {', '.join([a.title for a in anomalies if a.severity == 'critical'])}." if anomalies else "Система в стабильном состоянии.")
            )
        except Exception as ex:
            logger.error(f"Ошибка эвристического анализа: {ex}")
            score = 50
            anomalies = [AnomalyItem(subsystem="Diagnostics", severity="warning", title="Evaluation Error", description=str(ex))]
            recommendations = ["Проверьте доступность сенсоров и службы сбора телеметрии."]
            summary_text = f"Ошибка оценки: {ex}"

        # 2. Нейросетевой анализ при наличии активной модели
        executor: Optional[Any] = self.chat_model
        if executor is not None:
            if hasattr(executor, "active_provider"):
                model_name = getattr(executor, "active_provider", "Unified AI")
            elif hasattr(executor, "model_id"):
                model_name = f"Gemini CLI ({getattr(executor, 'model_id', 'gemini-3.1-flash-lite')})"
            else:
                model_name = "AI Model"

            prompt = self.build_prompt(data, score, anomalies, summary_text)
            generated_prompt = prompt
            stages.append({
                "stage": "prompt",
                "title": "Формирование контекста сенсоров",
                "message": "📝 Передача состояния всех сенсоров и параметров в AI-модель...",
                "details": "Телеметрия, датчики, накопители, процессы и память",
                "generated_prompt": prompt,
                "system_instruction": system_instruction,
            })

            try:
                if hasattr(executor, "ask"):
                    response = await executor.ask(prompt, system_instruction=system_instruction)
                elif hasattr(executor, "chat"):
                    response = await executor.chat(prompt)
                elif callable(executor):
                    response = await executor(prompt)
                else:
                    response = str(executor)

                raw_response = str(response).strip()
                if raw_response:
                    summary_text = raw_response
            except Exception as ai_err:
                logger.warning(f"Ошибка вызова языковой модели: {ai_err}")
                error_msg = str(ai_err)

        return SystemDiagnosticReport(
            health_score=score,
            summary=summary_text,
            anomalies=anomalies,
            recommendations=recommendations,
            ai_model_used=model_name,
            system_instruction=system_instruction,
            generated_prompt=generated_prompt,
            raw_response=raw_response,
            error=error_msg,
            stages=stages,
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

        # ЦП
        cpu = snapshot.cpu
        if cpu and cpu.total_percent is not None:
            if cpu.total_percent >= 90.0:
                score -= 25
                anomalies.append(AnomalyItem(subsystem="CPU", severity="critical", title="Critical CPU Saturation", description=f"Overall CPU usage is at {cpu.total_percent}%, causing system lag."))
                recommendations.append("Inspect top CPU processes and consider terminating unresponsive tasks.")
            elif cpu.total_percent >= 75.0:
                score -= 10
                anomalies.append(AnomalyItem(subsystem="CPU", severity="warning", title="Elevated CPU Load", description=f"CPU load is elevated ({cpu.total_percent}%)."))

        # Оперативная память
        mem = snapshot.memory
        if mem and mem.percent is not None:
            if mem.percent >= 92.0:
                score -= 30
                anomalies.append(AnomalyItem(subsystem="RAM", severity="critical", title="RAM Exhaustion Danger", description=f"System RAM is {mem.percent}% full ({mem.used_gb}/{mem.total_gb} GB)."))
                recommendations.append("Close memory-heavy applications or increase virtual memory paging size.")
            elif mem.percent >= 80.0:
                score -= 10
                anomalies.append(AnomalyItem(subsystem="RAM", severity="warning", title="High Memory Pressure", description=f"RAM utilization is at {mem.percent}%."))

        # Дисковые разделы
        for disk in snapshot.disks or []:
            d_pct = getattr(disk, "percent", getattr(disk, "load_percent", 0.0))
            if d_pct >= 95.0:
                score -= 15
                anomalies.append(AnomalyItem(subsystem="Disk", severity="critical", title=f"Drive {disk.device} Almost Full", description=f"Volume {disk.mountpoint} is {d_pct}% full with only {disk.free_gb} GB remaining."))
                recommendations.append(f"Free up disk space on drive {disk.device} to prevent write failures.")
            elif d_pct >= 85.0:
                score -= 5
                anomalies.append(AnomalyItem(subsystem="Disk", severity="warning", title=f"Low Space on {disk.device}", description=f"Volume {disk.mountpoint} is at {d_pct}% capacity."))

        # Физические накопители и SMART
        for p_disk in snapshot.physical_disks or []:
            if p_disk.health_status and p_disk.health_status.lower() in ["warning", "unhealthy", "error", "bad"]:
                score -= 25
                anomalies.append(AnomalyItem(subsystem="Storage", severity="critical", title=f"SMART Warning on {p_disk.model}", description=f"Physical drive {getattr(p_disk, 'device_id', '')} ({p_disk.model}) reports health status: {p_disk.health_status}."))
                recommendations.append(f"Perform disk backup and replace failing drive {p_disk.model}.")
            if p_disk.temperature_celsius and p_disk.temperature_celsius >= 60.0:
                score -= 10
                anomalies.append(AnomalyItem(subsystem="Storage", severity="warning", title=f"Overheating Storage: {p_disk.model}", description=f"Drive temperature {p_disk.temperature_celsius}°C exceeds recommended operating limits."))

        # Температурные сенсоры LHM
        for sensor in snapshot.sensors or []:
            if getattr(sensor, "category", "") == "temperature" or getattr(sensor, "sensor_category", "") == "Temperatures":
                val = getattr(sensor, "value", 0.0)
                s_name = getattr(sensor, "name", getattr(sensor, "sensor_name", "Sensor"))
                if val >= 85.0:
                    score -= 20
                    anomalies.append(AnomalyItem(subsystem="Thermals", severity="critical", title=f"High Temperature on {s_name}", description=f"Sensor {s_name} reading {val}°C exceeds safe operating threshold."))
                    recommendations.append("Check chassis airflow, fan speeds, and clean heatsink dust filters.")
                elif val >= 75.0:
                    score -= 5
                    anomalies.append(AnomalyItem(subsystem="Thermals", severity="warning", title=f"Elevated Temperature on {s_name}", description=f"Sensor {s_name} reading {val}°C is elevated."))

        # Топ-процессы
        ignored_processes = {"system idle process", "system", "idle"}
        for proc in (snapshot.top_processes or [])[:10]:
            p_name_lower = (proc.name or "").strip().lower()
            if proc.pid in [0, 4] or p_name_lower in ignored_processes:
                continue
            if proc.cpu_percent and proc.cpu_percent >= 60.0:
                anomalies.append(AnomalyItem(subsystem="Process", severity="warning", title=f"High CPU Consumer: {proc.name} (PID {proc.pid})", description=f"Process {proc.name} is consuming {proc.cpu_percent:.1f}% CPU single-handedly."))
            if proc.memory_mb and proc.memory_mb >= 6144.0:
                anomalies.append(AnomalyItem(subsystem="Process", severity="warning", title=f"High Memory Consumer: {proc.name} (PID {proc.pid})", description=f"Process {proc.name} is using {proc.memory_mb:.0f} MB RAM."))

        # Стабильность ОС и обновления
        if snapshot.alerts and getattr(snapshot.alerts, "reboot_pending", False):
            anomalies.append(AnomalyItem(subsystem="Updates", severity="warning", title="System Reboot Pending", description="Windows Updates or system components require a restart."))
            recommendations.append("Schedule a restart to finalize pending Windows system updates.")

        score = max(0, min(100, score))
        if not recommendations:
            recommendations.append("System telemetry is within healthy operating parameters.")
        return (score, anomalies, recommendations)

    def build_prompt(self, snapshot: Any, score: int, anomalies: List[AnomalyItem], summary_text: str) -> str:
        """Построение обогащенного диагностического контекста в формате JSON для языковой модели."""
        if not isinstance(snapshot, SystemSnapshot):
            return super().build_prompt(snapshot, score, anomalies, summary_text)

        builder = GroupedTelemetryBuilder()
        groups = builder.build_all_groups(snapshot)
        groups_payload = {g.group_id: g.payload for g in groups}

        return (
            "Вы — ведущий инженер по анализу системной телеметрии и надежности Windows.\n"
            "Ниже приведен структурированный срез телеметрии хоста по 4 ключевым доменам:\n\n"
            f"```json\n{json.dumps(groups_payload, ensure_ascii=False, indent=2)}\n```\n\n"
            f"Обнаруженные детерминированные аномалии: {[a.model_dump() for a in anomalies]}\n"
            f"Расчетный индекс здоровья (Heuristic Score): {score}/100\n\n"
            "ИНСТРУКЦИИ:\n"
            "1. Немедленно выдайте краткое аналитическое резюме состояния хоста (2-3 предложения).\n"
            "2. Перечислите 2-4 конкретных практических шага по оптимизации и устранению найденных узких мест.\n"
            "3. Отвечайте строго на русском языке."
        )

    def _build_minimal_group_prompt(
        self,
        group_id: str,
        title: str,
        status: str,
        anomalies: List[str],
        key_metrics: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Формирует ультра-компактный JSON-промпт, содержащий исключительно параметры, требующие внимания/уточнения."""
        data: Dict[str, Any] = {
            "group": group_id,
            "status": status,
        }
        if anomalies:
            data["anomalies"] = anomalies
        if key_metrics:
            data["metrics"] = key_metrics

        # Точечное добавление только проблемного контекста
        if group_id == "compute_thermals":
            cpu = payload.get("cpu", {})
            if cpu.get("load_percent", 0.0) >= 70.0 or (cpu.get("package_temperature_celsius") or 0.0) >= 75.0:
                data["cpu_load_pct"] = cpu.get("load_percent")
                if cpu.get("package_temperature_celsius"):
                    data["temp_c"] = cpu.get("package_temperature_celsius")
        elif group_id == "memory_processes":
            ram = payload.get("ram", {})
            if ram.get("used_percent", 0.0) >= 75.0:
                data["ram_used_pct"] = ram.get("used_percent")
            top_p = payload.get("top_active_processes", [])
            if top_p and (top_p[0].get("cpu_percent", 0.0) >= 50.0 or top_p[0].get("memory_percent", 0.0) >= 30.0):
                data["top_proc"] = f"{top_p[0].get('name')} (CPU {top_p[0].get('cpu_percent')}%, RAM {top_p[0].get('memory_mb')}MB)"
        elif group_id == "storage_smart":
            parts = [p for p in payload.get("storage_partitions", []) if p.get("used_percent", 0.0) >= 85.0]
            if parts:
                data["critical_volumes"] = [{p.get("device", "vol"): f"{p.get('used_percent')}% full"} for p in parts]
        elif group_id == "system_network":
            if payload.get("system_updates", {}).get("reboot_pending"):
                data["reboot_pending"] = True

        return data

    async def diagnose_group(
        self,
        group_id: str = "",
        payload: Optional[Dict[str, Any]] = None,
        title: str = "",
        group_info: Optional[TelemetryGroupInfo] = None,
    ) -> GroupDiagnosticResult:
        """Диагностика одной изолированной группы телеметрии с помощью эвристики и LLM."""
        gid = group_id or (group_info.group_id if group_info else "general")
        gtitle = title or (group_info.title if group_info else gid)
        gpayload = payload if payload is not None else (group_info.payload if group_info else {})

        status = "ok"
        key_metrics: Dict[str, Any] = {}
        anomalies: List[str] = []
        recommendations: List[str] = []

        if gid == "compute_thermals":
            cpu = gpayload.get("cpu", {})
            cpu_load = cpu.get("load_percent", 0.0)
            pkg_temp = cpu.get("package_temperature_celsius") or 0.0
            key_metrics["cpu_load"] = f"{cpu_load}%"
            key_metrics["package_temp"] = f"{pkg_temp}°C" if pkg_temp else "N/A"
            if cpu_load >= 85.0 or pkg_temp >= 85.0:
                status = "critical"
                anomalies.append(f"Критическая нагрузка/нагрев CPU: {cpu_load}%, {pkg_temp}°C")
                recommendations.append("Проверьте систему охлаждения и фоновые процессы.")
            elif cpu_load >= 70.0 or pkg_temp >= 75.0:
                status = "warning"
                anomalies.append(f"Повышенная нагрузка CPU: {cpu_load}%")
        elif gid == "memory_processes":
            ram = gpayload.get("ram", {})
            ram_used = ram.get("used_percent", 0.0)
            key_metrics["ram_used_percent"] = f"{ram_used}%"
            if ram_used >= 90.0:
                status = "critical"
                anomalies.append(f"Память исчерпана: {ram_used}%")
                recommendations.append("Закройте неиспользуемые программы.")
            elif ram_used >= 75.0:
                status = "warning"
                anomalies.append(f"Высокое потребление памяти: {ram_used}%")
        elif gid == "storage_smart":
            parts = gpayload.get("storage_partitions", [])
            max_d = max([p.get("used_percent", 0.0) for p in parts] or [0.0])
            key_metrics["max_disk_used"] = f"{max_d}%"
            if max_d >= 95.0:
                status = "critical"
                anomalies.append(f"Том заполнен на {max_d}%")
                recommendations.append("Очистите дисковое пространство.")
            elif max_d >= 85.0:
                status = "warning"
                anomalies.append(f"Низкий объем свободного места на диске ({max_d}%)")
        elif gid == "system_network":
            reboot = gpayload.get("system_updates", {}).get("reboot_pending", False)
            key_metrics["reboot_pending"] = reboot
            if reboot:
                status = "warning"
                anomalies.append("Ожидается перезагрузка для завершения обновлений ОС.")
                recommendations.append("Запланируйте перезагрузку компьютера.")

        summary = f"Подсистема '{gtitle}' находится в статусе: {status.upper()}."
        model_name = "Heuristic Analyzer"
        raw_response = None
        system_instruction = "Вы — системный диагност. Дайте краткую экспертную оценку (1-2 предложения) и 1 рекомендацию строго на русском языке."
        prompt_dict = self._build_minimal_group_prompt(gid, gtitle, status, anomalies, key_metrics, gpayload)
        generated_prompt = json.dumps(prompt_dict, ensure_ascii=False, indent=2)

        executor = self.chat_model
        if executor is not None:
            if hasattr(executor, "active_provider"):
                model_name = getattr(executor, "active_provider", "Unified AI")
            elif hasattr(executor, "model_id"):
                model_name = f"Gemini CLI ({getattr(executor, 'model_id', 'gemini-3.1-flash-lite')})"
            else:
                model_name = "AI Model"

            try:
                if hasattr(executor, "ask"):
                    res = await executor.ask(generated_prompt, system_instruction=system_instruction)
                elif hasattr(executor, "chat"):
                    res = await executor.chat(generated_prompt, system_instruction=system_instruction)
                elif callable(executor):
                    res = await executor(generated_prompt)
                else:
                    res = str(executor)
                raw_response = str(res).strip()
                summary = raw_response
            except Exception as ex:
                logger.warning(f"Ошибка LLM анализа группы {gid}: {ex}")

        return GroupDiagnosticResult(
            group_id=gid,
            title=gtitle,
            icon="bi-cpu",
            status=status,
            summary=summary,
            anomalies=anomalies,
            recommendations=recommendations,
            key_metrics=key_metrics,
            raw_response=raw_response,
            generated_prompt=generated_prompt,
            system_instruction=system_instruction,
            ai_model_used=model_name,
        )

    async def synthesize_final_report(self, groups: List[GroupDiagnosticResult]) -> SynthesisDiagnosticResult:
        """Синтез общего вердикта по результатам всех групп."""
        has_critical = any(g.status == "critical" for g in groups)
        has_warning = any(g.status == "warning" for g in groups)
        health_score = 60 if has_critical else (78 if has_warning else 100)
        status_label = "Критическое" if has_critical else ("Внимание" if has_warning else "Отличное")

        actions = []
        for g in groups:
            actions.extend(g.recommendations)

        summary = f"Общий вердикт: синтез завершен по {len(groups)} доменам. Индекс здоровья: {health_score}/100 ({status_label})."
        model_name = "Heuristic Analyzer"
        raw_response = None
        system_instruction = "Вы — ведущий инженер. Сформулируйте общий вердикт (1-2 предложения) и 2-3 приоритетных действия строго на русском языке."
        
        # Ультра-компактный JSON промпт синтеза: передаются только статусы и выявленные аномалии
        synth_payload = {
            "health_score": health_score,
            "status": status_label,
            "domains": [
                {
                    "group": g.group_id,
                    "status": g.status,
                    "anomalies": g.anomalies,
                    "metrics": g.key_metrics,
                }
                for g in groups
            ],
        }
        generated_prompt = json.dumps(synth_payload, ensure_ascii=False, indent=2)

        executor = self.chat_model
        if executor is not None:
            if hasattr(executor, "active_provider"):
                model_name = getattr(executor, "active_provider", "Unified AI")
            try:
                if hasattr(executor, "ask"):
                    res = await executor.ask(generated_prompt, system_instruction=system_instruction)
                    raw_response = str(res).strip()
                    summary = raw_response
            except Exception as ex:
                logger.warning(f"Ошибка LLM синтеза вердикта: {ex}")

        return SynthesisDiagnosticResult(
            health_score=health_score,
            status_label=status_label,
            executive_summary=summary,
            critical_actions=actions[:4] if actions else ["Система функционирует штатно."],
            raw_response=raw_response,
            generated_prompt=generated_prompt,
            system_instruction=system_instruction,
            ai_model_used=model_name,
            groups_evaluated=len(groups),
        )

    async def synthesize_all_groups(self, groups: List[GroupDiagnosticResult]) -> SynthesisDiagnosticResult:
        """Алиас для synthesize_final_report."""
        return await self.synthesize_final_report(groups)

    async def diagnose_incident(self, incident: TelemetryIncident) -> SystemDiagnosticReport:
        """Формирует экспертный диагностический отчет по инциденту аномалии с привлечением LLM.

        Args:
            incident: Зафиксированный объект TelemetryIncident.

        Returns:
            SystemDiagnosticReport: Диагностический отчет с рекомендациями.
        """
        score = 40 if incident.severity == 'critical' else 65
        anomalies = [
            AnomalyItem(
                subsystem=f'Incident [{incident.trigger_type}]',
                severity=incident.severity,
                title=incident.title,
                description=incident.description,
            )
        ]
        recommendations = [
            f"Проверьте процессы, вызвавшие триггер ({', '.join([p.get('name', '') for p in incident.suspect_processes]) or 'системная активность'}).",
            "Изучите сопутствующие системные события и сетевые соединения в окне инцидента.",
        ]

        summary_text = f"Инцидент {incident.incident_id} [{incident.severity.upper()}]: {incident.title}. {incident.description}"
        model_name = "Incident Heuristic Analyzer"
        prompt = IncidentDetector.format_incident_markdown_for_llm(incident)
        raw_response = None
        error_msg = None

        executor = self.chat_model
        if executor is not None:
            if hasattr(executor, "active_provider"):
                model_name = getattr(executor, "active_provider", "Unified AI")
            elif hasattr(executor, "model_id"):
                model_name = f"Gemini CLI ({getattr(executor, 'model_id', 'gemini-3.1-flash-lite')})"
            else:
                model_name = "AI Model"

            try:
                if hasattr(executor, "ask"):
                    res = await executor.ask(prompt)
                elif hasattr(executor, "chat"):
                    res = await executor.chat(prompt)
                elif callable(executor):
                    res = await executor(prompt)
                else:
                    res = str(executor)
                raw_response = str(res).strip()
                if raw_response:
                    summary_text = raw_response
            except Exception as ex:
                logger.warning(f"Ошибка вызова LLM для инцидента {incident.incident_id}: {ex}")
                error_msg = str(ex)

        return SystemDiagnosticReport(
            health_score=score,
            summary=summary_text,
            anomalies=anomalies,
            recommendations=recommendations,
            ai_model_used=model_name,
            generated_prompt=prompt,
            raw_response=raw_response,
            error=error_msg,
        )
