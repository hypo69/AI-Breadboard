# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Defender Core Package
# =============================================================================
# Description:
#   Инициализация ядра приложения Windows Defender Security Center.
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows_defender.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Пакет основных сервисов и анализаторов Microsoft Defender."""

from apps.windows_defender.core.ai_diagnostician import AIDiagnostician
from apps.windows_defender.core.asr_manager import ASRManager
from apps.windows_defender.core.cfa_manager import ControlledFolderAccessManager
from apps.windows_defender.core.defender_service import DefenderService
from apps.windows_defender.core.event_correlator import EventCorrelator
from apps.windows_defender.core.exclusions_auditor import ExclusionsAuditor
from apps.windows_defender.core.models import (
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
from apps.windows_defender.core.process_tree_watcher import ProcessTreeWatcher
from apps.windows_defender.core.threat_manager import ThreatManager

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
