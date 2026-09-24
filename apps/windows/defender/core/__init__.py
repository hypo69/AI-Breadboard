# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Defender Core Package
# =============================================================================
# Description:
#   Инициализация ядра приложения Windows Defender Security Center.
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.defender.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Пакет основных сервисов и анализаторов Microsoft Defender."""

from apps.windows.defender.core.ai_diagnostician import AIDiagnostician
from apps.windows.defender.core.asr_manager import ASRManager
from apps.windows.defender.core.cfa_manager import ControlledFolderAccessManager
from apps.windows.defender.core.defender_service import DefenderService
from apps.windows.defender.core.event_correlator import EventCorrelator
from apps.windows.defender.core.exclusions_auditor import ExclusionsAuditor
from apps.windows.defender.core.models import (
    ASRRuleInfo,
    ControlledFolderAccessInfo,
    DefenderDiagnosticReport,
    DefenderEventRecord,
    DefenderStatus,
    ExclusionItem,
    ExclusionsAuditReport,
    ScanRequest,
    ScanResponse,
    ScanType,
    ServiceStatus,
    SuspiciousProcessChain,
    ThreatRecord,
)
from apps.windows.defender.core.process_tree_watcher import ProcessTreeWatcher
from apps.windows.defender.core.threat_manager import ThreatManager

__all__ = [
    "DefenderService",
    "ASRManager",
    "ControlledFolderAccessManager",
    "ExclusionsAuditor",
    "ThreatManager",
    "EventCorrelator",
    "ProcessTreeWatcher",
    "AIDiagnostician",
    "DefenderStatus",
    "ServiceStatus",
    "ASRRuleInfo",
    "ControlledFolderAccessInfo",
    "ExclusionItem",
    "ExclusionsAuditReport",
    "ThreatRecord",
    "DefenderEventRecord",
    "SuspiciousProcessChain",
    "ScanRequest",
    "ScanResponse",
    "ScanType",
    "DefenderDiagnosticReport",
]
