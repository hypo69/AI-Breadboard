# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Defender Core -   Init  
# =============================================================================
# Description:
#   Пакет основных сервисов и анализаторов Microsoft Defender.
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.defender.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 04:11:30
# =============================================================================

"""Пакет основных сервисов и анализаторов Microsoft Defender."""

from apps.windows.sdk.modules.defender.core.ai_diagnostician import AIDiagnostician
from apps.windows.sdk.modules.defender.core.asr_manager import ASRManager
from apps.windows.sdk.modules.defender.core.cfa_manager import ControlledFolderAccessManager
from apps.windows.sdk.modules.defender.core.defender_service import DefenderService
from apps.windows.sdk.modules.defender.core.event_correlator import EventCorrelator
from apps.windows.sdk.modules.defender.core.exclusions_auditor import ExclusionsAuditor
from apps.windows.sdk.modules.defender.core.models import (
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
from apps.windows.sdk.modules.defender.core.process_tree_watcher import ProcessTreeWatcher
from apps.windows.sdk.modules.defender.core.threat_manager import ThreatManager

__all__ = [
    'DefenderService',
    'ASRManager',
    'ControlledFolderAccessManager',
    'ExclusionsAuditor',
    'ThreatManager',
    'EventCorrelator',
    'ProcessTreeWatcher',
    'AIDiagnostician',
    'DefenderStatus',
    'ServiceStatus',
    'ASRRuleInfo',
    'ControlledFolderAccessInfo',
    'ExclusionItem',
    'ExclusionsAuditReport',
    'ThreatRecord',
    'DefenderEventRecord',
    'SuspiciousProcessChain',
    'ScanRequest',
    'ScanResponse',
    'ScanType',
    'DefenderDiagnosticReport',
]