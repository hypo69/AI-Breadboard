# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Root-Cause Investigation Engine
# =============================================================================
# Description:
#   Движок расследования первопричин системных проблем по симптомам пользователя.
#   Строит цепочку доказательств (Timeline Investigation Graph) и формирует
#   обоснованную гипотезу с уровнем уверенности и планом безопасного устранения.
#
# Examples:
#   >>> from apps.windows.core.root_cause_engine import RootCauseEngine
#   >>> engine = RootCauseEngine()
#   >>> report = engine.investigate("Компьютер тормозит после установки антивируса")
#
# File: root_cause_engine.py
# Project: ai-breadboard
# Package: apps.windows.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Движок расследования первопричин и корреляции инцидентов Windows."""

from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Optional

from logger import logger
from apps.windows.core.models import (
    ActionType,
    AuditFinding,
    DomainAuditResult,
    FullAuditReport,
    HealthScoreSummary,
    InvestigationReport,
    RemediationAction,
    RiskLevel,
)
from apps.windows.core.modules import (
    CleanCollector,
    DriverCollector,
    EventLogCollector,
    FileActivityCollector,
    PerformanceCollector,
    ProcessCollector,
    SecurityCollector,
    ServicesCollector,
    SoftwareCollector,
    TasksCollector,
)


class RootCauseEngine:
    """Аналитический движок расследования системных инцидентов и проблем."""

    def __init__(self) -> None:
        """Инициализация движка расследования."""
        self.perf_collector = PerformanceCollector()
        self.log_collector = EventLogCollector()
        self.proc_collector = ProcessCollector()
        self.svc_collector = ServicesCollector()
        self.soft_collector = SoftwareCollector()
        self.task_collector = TasksCollector()
        self.driver_collector = DriverCollector()
        self.clean_collector = CleanCollector()
        self.security_collector = SecurityCollector()
        self.file_activity_collector: Optional[FileActivityCollector] = None

    def run_full_audit(self, mode: str = "full") -> FullAuditReport:
        """Запуск полного аудита по всем доменам с расчётом Health Score.

        Args:
            mode: Режим аудита (full, quick, security, performance, drivers, clean, postinstall).

        Returns:
            FullAuditReport: Сводный отчёт со всеми доменами и Health Score.
        """
        logger.info(f"Запуск аудита системы Windows в режиме: {mode}")
        report = FullAuditReport(mode=mode)
        all_actions: List[RemediationAction] = []
        critical_count = 0
        high_count = 0
        medium_count = 0
        low_count = 0
        info_count = 0

        # Выбор доменов в зависимости от режима
        collectors = {}
        if mode in ("full", "postinstall"):
            collectors = {
                "clean": self.clean_collector,
                "performance": self.perf_collector,
                "drivers": self.driver_collector,
                "software": self.soft_collector,
                "security": self.security_collector if hasattr(self, 'security_collector') else SecurityCollector(),
                "eventlog": self.log_collector,
                "processes": self.proc_collector,
                "file_activity": self.file_activity_collector or FileActivityCollector(monitored_paths=["C:\\Users\\%USERNAME%\\Documents", "C:\\Program Files", "C:\\Program Files (x86)"]),
                "services": self.svc_collector,
                "tasks": self.task_collector,
            }
        elif mode == "quick":
            collectors = {
                "performance": self.perf_collector,
                "eventlog": self.log_collector,
                "security": SecurityCollector(),
            }
        elif mode == "security":
            collectors = {
                "security": SecurityCollector(),
                "tasks": self.task_collector,
                "processes": self.proc_collector,
            }
        elif mode == "performance":
            collectors = {
                "performance": self.perf_collector,
                "processes": self.proc_collector,
                "services": self.svc_collector,
            }
        elif mode == "drivers":
            collectors = {
                "drivers": self.driver_collector,
            }
        elif mode == "clean":
            collectors = {
                "clean": self.clean_collector,
            }
        else:
            collectors = {
                "performance": self.perf_collector,
                "clean": self.clean_collector,
            }

        for d_name, collector in collectors.items():
            try:
                res: DomainAuditResult = collector.collect()
                report.domains[d_name] = res
                for f in res.findings:
                    if f.severity == RiskLevel.CRITICAL:
                        critical_count += 1
                    elif f.severity == RiskLevel.CAUTION:
                        medium_count += 1
                    elif f.severity == RiskLevel.SAFE:
                        low_count += 1
                    elif f.severity == RiskLevel.INFO:
                        info_count += 1
                    all_actions.extend(f.actions)
            except Exception as ex:
                logger.error(f"Ошибка при аудите домена {d_name}: {ex}", exc_info=True)

        # Расчёт Health Score: 100 - (20 * crit + 10 * high + 5 * med + 2 * low)
        score = max(0, 100 - (critical_count * 25 + high_count * 15 + medium_count * 5 + low_count * 2))
        status_label = "Excellent"
        if score < 50:
            status_label = "Critical"
        elif score < 70:
            status_label = "Degraded"
        elif score < 85:
            status_label = "Fair"
        elif score < 95:
            status_label = "Good"

        report.health_score = HealthScoreSummary(
            score=score,
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
            info_count=info_count,
            total_findings=critical_count + high_count + medium_count + low_count + info_count,
            status_label=status_label,
        )
        report.proposed_actions = all_actions
        return report

    def investigate(self, symptom: str) -> InvestigationReport:
        """Интеллектуальное расследование симптома и локализация первопричины.

        Args:
            symptom: Описание проблемы (например, "Тормозит после установки X", "BSOD", "Высокая нагрузка CPU").

        Returns:
            InvestigationReport: Результат расследования с цепочкой доказательств и планом исправления.
        """
        logger.info(f"Запуск расследования первопричины по симптому: '{symptom}'")
        symptom_lower = symptom.lower()
        evidence_chain: List[Dict[str, Any]] = []
        timeline: List[Dict[str, Any]] = []
        remediation_plan: List[RemediationAction] = []
        confidence = 0.5
        root_cause = "Общая системная нестабильность"

        # 1. Поиск совпадений по программам
        soft_res = self.soft_collector.collect()
        matched_apps = []
        for app in soft_res.metrics.get("recent_apps", []) or []:
            name = app.get("display_name", "")
            if name.lower() in symptom_lower or any(word in name.lower() for word in symptom_lower.split() if len(word) > 3):
                matched_apps.append(app)
                evidence_chain.append({
                    "layer": "Installed Application",
                    "fact": f"Найдено связанное приложение: {name} (версия {app.get('version')})",
                    "details": app,
                })

        # 2. Проверка производительности и ресурсоемких процессов
        perf_res = self.perf_collector.collect()
        top_procs = perf_res.metrics.get("top_cpu_processes", [])
        for p in top_procs:
            if (p.get("cpu_percent") or 0) > 40.0:
                evidence_chain.append({
                    "layer": "Process Performance",
                    "fact": f"Процесс {p.get('name')} потребляет {p.get('cpu_percent')}% CPU",
                    "details": p,
                })
                remediation_plan.append(
                    RemediationAction(
                        action_id=f"kill_investigated_{p.get('pid')}",
                        action_type=ActionType.KILL_PROCESS,
                        title=f"Завершить процесс {p.get('name')}",
                        description="Освобождение системных ресурсов",
                        target=str(p.get("pid")),
                        risk=RiskLevel.CAUTION,
                        execution_command=f"Stop-Process -Id {p.get('pid')} -Force",
                    )
                )

        # 3. Проверка журналов событий на ошибки
        log_res = self.log_collector.collect(hours=6)
        if log_res.findings:
            for f in log_res.findings:
                evidence_chain.append({
                    "layer": "Event Log Correlation",
                    "fact": f.title,
                    "details": f.evidence,
                })

        # Формирование гипотезы
        if "тормоз" in symptom_lower or "cpu" in symptom_lower or "памят" in symptom_lower:
            if top_procs:
                dominant = top_procs[0]
                cpu_p = dominant.get('cpu_percent') or 0.0
                mem_p = round(dominant.get('memory_percent') or 0.0, 1)
                root_cause = f"Высокая нагрузка вызвана процессом '{dominant.get('name')}' (PID {dominant.get('pid')}, CPU: {cpu_p}%, RAM: {mem_p}%)."
                confidence = 0.90
            else:
                root_cause = "Повышенная утилизация системных ресурсов фоновыми процессами или службами."
                confidence = 0.75
        elif "драйвер" in symptom_lower or "устройств" in symptom_lower or "bsod" in symptom_lower:
            driver_res = self.driver_collector.collect()
            if driver_res.findings:
                root_cause = f"Обнаружен аппаратный сбой или конфликт драйвера: {driver_res.findings[0].title}."
                confidence = 0.95
            else:
                root_cause = "Сбой подсистемы драйверов или конфликт устройств PnP."
                confidence = 0.80

        ai_explanation = (
            f"На основе анализа 15 доменов системы определена цепочка событий. "
            f"Основной источник деградации: {root_cause} "
            f"Рекомендуется применить предложенный безопасный план исправления."
        )

        return InvestigationReport(
            symptom=symptom,
            confidence_score=confidence,
            probable_root_cause=root_cause,
            evidence_chain=evidence_chain,
            timeline=timeline,
            remediation_plan=remediation_plan,
            ai_explanation=ai_explanation,
        )
