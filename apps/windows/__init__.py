# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI Windows Diagnostic & Administration Center Package
# =============================================================================
# Description:
#   Комплексный набор инструментов диагностики, аудита, оптимизации,
#   безопасности и SafeOps управления для Windows.
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""AI Windows Diagnostic & Administration Center."""

__version__ = "2.0.0"
__author__ = "hypo69"

# Ленивая загрузка экспортов (PEP 562) для предотвращения циклических зависимостей
# и экономии оперативной памяти (не подгружает тяжелый AI-стек и FastAPI при импорте телеметрии).
_LAZY_EXPORTS = {
    "WindowsAIDiagnostician": ("apps.windows.ai.diagnostician", "WindowsAIDiagnostician"),
    "WindowsAIRootCauseAnalyzer": ("apps.windows.ai.root_cause_analyzer", "WindowsAIRootCauseAnalyzer"),
    "AIW64Collector": ("apps.windows.ai_w64_collector", "AIW64Collector"),
    "get_w64_collector": ("apps.windows.ai_w64_collector", "get_w64_collector"),
    "start_w64_collector": ("apps.windows.ai_w64_collector", "start_w64_collector"),
    "stop_w64_collector": ("apps.windows.ai_w64_collector", "stop_w64_collector"),
    "AIW64ETWCollector": ("apps.windows.ai_w64_etw_collector", "AIW64ETWCollector"),
    "WinAPI": ("apps.windows.core.winapi", "WinAPI"),
    "SystemState": ("apps.windows.core.data_model", "SystemState"),
    "ProcessIntelligence": ("apps.windows.process_intelligence", "ProcessIntelligence"),
    "SoftwareAuditEngine": ("apps.windows.core.software_audit", "SoftwareAuditEngine"),
    "InstalledAppInfo": ("apps.windows.core.data_model", "InstalledAppInfo"),
    "AppCategory": ("apps.windows.core.data_model", "AppCategory"),
    "AppExecutionInfo": ("apps.windows.core.data_model", "AppExecutionInfo"),
    "SoftwareAuditReport": ("apps.windows.core.data_model", "SoftwareAuditReport"),
    "RootCauseEngine": ("apps.windows.core.root_cause_engine", "RootCauseEngine"),
    "SafeExecutor": ("apps.windows.core.safe_executor", "SafeExecutor"),
    "RiskLevel": ("apps.windows.core.models", "RiskLevel"),
    "ActionType": ("apps.windows.core.models", "ActionType"),
    "RemediationAction": ("apps.windows.core.models", "RemediationAction"),
    "AuditFinding": ("apps.windows.core.models", "AuditFinding"),
    "DomainAuditResult": ("apps.windows.core.models", "DomainAuditResult"),
    "HealthScoreSummary": ("apps.windows.core.models", "HealthScoreSummary"),
    "FullAuditReport": ("apps.windows.core.models", "FullAuditReport"),
    "InvestigationReport": ("apps.windows.core.models", "InvestigationReport"),
    "init_router": ("apps.windows.router", "init_router"),
    "router": ("apps.windows.router", "router"),
}


def __getattr__(name: str):
    """Ленивая динамическая загрузка модулей и символов пакета."""
    if name in _LAZY_EXPORTS:
        module_path, attr_name = _LAZY_EXPORTS[name]
        module = __import__(module_path, fromlist=[attr_name])
        attr = getattr(module, attr_name)
        globals()[name] = attr
        return attr
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    "WinAPI",
    "SystemState",
    "ProcessIntelligence",
    "SoftwareAuditEngine",
    "InstalledAppInfo",
    "AppCategory",
    "AppExecutionInfo",
    "SoftwareAuditReport",
    "RootCauseEngine",
    "SafeExecutor",
    "WindowsAIDiagnostician",
    "WindowsAIRootCauseAnalyzer",
    "AIW64Collector",
    "AIW64ETWCollector",
    "get_w64_collector",
    "start_w64_collector",
    "stop_w64_collector",
    "RiskLevel",
    "ActionType",
    "RemediationAction",
    "AuditFinding",
    "DomainAuditResult",
    "HealthScoreSummary",
    "FullAuditReport",
    "InvestigationReport",
    "init_router",
    "router",
]
