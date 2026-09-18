# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Defender AI Diagnostician & Security Posture Engine
# =============================================================================
# Description:
#   Интеллектуальный корреляционный движок анализа защищенности системы.
#   Сопоставляет статус Defender, правила ASR, Controlled Folder Access,
#   опасные исключения, цепочки процессов и системные события безопасности,
#   рассчитывает Security Posture Score (0-100) и формирует практические рекомендации.
#
# File: ai_diagnostician.py
# Project: ai-breadboard
# Package: apps.windows_defender.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модуль комплексного AI-анализа защищенности и корреляции угроз."""

from __future__ import annotations

from typing import List, Optional

from src.logger import logger
from apps.windows_defender.core.asr_manager import ASRManager
from apps.windows_defender.core.cfa_manager import ControlledFolderAccessManager
from apps.windows_defender.core.defender_service import DefenderService
from apps.windows_defender.core.event_correlator import EventCorrelator
from apps.windows_defender.core.exclusions_auditor import ExclusionsAuditor
from apps.windows_defender.core.models import (
    DefenderDiagnosticReport,
    ProtectionState,
)
from apps.windows_defender.core.process_tree_watcher import ProcessTreeWatcher
from apps.windows_defender.core.threat_manager import ThreatManager


class AIDiagnostician:
    """Аналитический движок корреляции и оценки защищенности."""

    def __init__(
        self,
        defender_service: Optional[DefenderService] = None,
        asr_manager: Optional[ASRManager] = None,
        cfa_manager: Optional[ControlledFolderAccessManager] = None,
        exclusions_auditor: Optional[ExclusionsAuditor] = None,
        threat_manager: Optional[ThreatManager] = None,
        event_correlator: Optional[EventCorrelator] = None,
        process_watcher: Optional[ProcessTreeWatcher] = None,
    ) -> None:
        """Инициализация AI Diagnostician со всеми зависимостями."""
        self._service = defender_service or DefenderService()
        self._asr = asr_manager or ASRManager(self._service)
        self._cfa = cfa_manager or ControlledFolderAccessManager(self._service)
        self._exclusions = exclusions_auditor or ExclusionsAuditor(self._service)
        self._threats = threat_manager or ThreatManager(self._service)
        self._events = event_correlator or EventCorrelator()
        self._processes = process_watcher or ProcessTreeWatcher()

    def generate_diagnostic_report(self) -> DefenderDiagnosticReport:
        """Генерация комплексного отчета защищенности системы.

        Returns:
            DefenderDiagnosticReport: Детальный отчет с оценкой и рекомендациями.
        """
        status = self._service.get_defender_status()
        asr_rules = self._asr.get_asr_rules()
        cfa_info = self._cfa.get_cfa_status()
        exclusions_report = self._exclusions.audit_exclusions()
        threats = self._threats.get_threats_history(limit=20)
        suspicious_chains = self._processes.scan_suspicious_chains()

        score = 100
        critical_findings: List[str] = []
        warnings: List[str] = []
        recommendations: List[str] = []

        # 1. Анализ базовой защиты Defender
        if not status.antivirus_enabled or not status.real_time_protection_enabled:
            score -= 35
            critical_findings.append("Защита в реальном времени (Real-Time Protection) отключена!")
            recommendations.append("Немедленно включите защиту в реальном времени Defender.")
        
        if not status.cloud_protection_enabled:
            score -= 15
            warnings.append("Облачная защита (Cloud-delivered protection / MAPS) отключена.")
            recommendations.append("Активируйте облачную защиту для оперативного блокирования новейших угроз.")

        if not status.behavior_monitor_enabled:
            score -= 15
            warnings.append("Поведенческий мониторинг (Behavior Monitoring) отключен.")
            recommendations.append("Включите поведенческий анализ для защиты от неизвестных вредоносных цепочек.")

        if not status.tamper_protection_enabled:
            score -= 10
            warnings.append("Защита от несанкционированного изменения (Tamper Protection) отключена.")
            recommendations.append("Включите Tamper Protection, чтобы вредоносное ПО не могло отключить антивирус.")

        if not status.pua_protection_enabled:
            score -= 5
            warnings.append("Защита от потенциально нежелательных программ (PUA) отключена.")
            recommendations.append("Включите PUA Protection в режим блокировки.")

        # 2. Анализ Controlled Folder Access (Ransomware)
        if not cfa_info.enabled:
            score -= 5
            warnings.append("Контролируемый доступ к папкам (Controlled Folder Access) не активен.")
            recommendations.append("Рассмотрите включение Controlled Folder Access для защиты ключевых документов от вымогателей.")

        # 3. Анализ исключений
        if exclusions_report.suspicious_count > 0:
            penalty = min(25, exclusions_report.suspicious_count * 10)
            score -= penalty
            critical_findings.append(f"Обнаружено {exclusions_report.suspicious_count} опасных исключений антивируса (широкие маски дисков/системные папки/интерпретаторы).")
            recommendations.append("Проведите ревизию и удалите широкие исключения из списка Defender.")

        # 4. Анализ ASR правил
        enabled_asr = sum(1 for r in asr_rules if r.state in (ProtectionState.ENABLED, ProtectionState.AUDIT))
        if enabled_asr == 0:
            score -= 10
            warnings.append("Ни одно правило Attack Surface Reduction (ASR) не настроено.")
            recommendations.append("Настройте правила ASR (блокировка дочерних процессов Office, дампа LSASS и запуска обфусцированных скриптов).")

        # 5. Анализ подозрительных процессов
        if suspicious_chains:
            score -= min(25, len(suspicious_chains) * 15)
            critical_findings.append(f"Зафиксировано {len(suspicious_chains)} подозрительных цепочек процессов / признаков бесфайловых атак.")
            recommendations.append("Исследуйте дерево активных процессов и завершите скомпрометированные процессы.")

        # Нормализация оценки
        score = max(0, min(100, score))

        # Итоговая сводка
        if score >= 90:
            summary = "Высокий уровень защищенности. Все ключевые эшелоны обороны Defender активны."
        elif score >= 70:
            summary = "Удовлетворительный уровень защиты. Имеются непримененные политики ASR или незначительные предупреждения."
        elif score >= 40:
            summary = "Повышенный риск! Отключены важные компоненты защиты или присутствуют опасные исключения."
        else:
            summary = "КРИТИЧЕСКИЙ РИСК! Базовая защита деактивирована или обнаружены активные аномалии процессов."

        active_count = sum(1 for t in threats if t.status.lower() == "active")
        quarantined_count = sum(1 for t in threats if "quarantine" in t.status.lower())

        return DefenderDiagnosticReport(
            security_score=score,
            status_summary=summary,
            critical_findings=critical_findings,
            warnings=warnings,
            recommendations=recommendations,
            status=status,
            exclusions_audit=exclusions_report,
            active_threats_count=active_count,
            quarantined_threats_count=quarantined_count,
            suspicious_process_chains=suspicious_chains,
        )
