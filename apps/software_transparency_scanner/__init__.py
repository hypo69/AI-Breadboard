# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI Software Transparency Scanner Application Init
# =============================================================================
# Description:
#   Экспорт основных компонентов приложения AI Software Transparency Scanner.
#
# Examples:
#   >>> from apps.software_transparency_scanner import init_router, SoftwareInventory
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.software_transparency_scanner
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Приложение AI Software Transparency Scanner."""

from apps.software_transparency_scanner.core.models import (
    ConfigFile,
    EvidenceStatus,
    FullScanReport,
    GeminiAppResearch,
    NetworkEndpoint,
    ResearchRequest,
    ScanSummary,
    SoftwareItem,
    StorageCategory,
    StorageDirectory,
)
from apps.software_transparency_scanner.core.inventory import SoftwareInventory
from apps.software_transparency_scanner.core.storage_analyzer import StorageAnalyzer
from apps.software_transparency_scanner.core.config_inspector import ConfigInspector
from apps.software_transparency_scanner.core.network_tracker import NetworkTracker
from apps.software_transparency_scanner.core.gemini_researcher import GeminiResearcher
from apps.software_transparency_scanner.router import init_router

__all__ = [
    "init_router",
    "ConfigFile",
    "EvidenceStatus",
    "FullScanReport",
    "GeminiAppResearch",
    "NetworkEndpoint",
    "ResearchRequest",
    "ScanSummary",
    "SoftwareItem",
    "StorageCategory",
    "StorageDirectory",
    "SoftwareInventory",
    "StorageAnalyzer",
    "ConfigInspector",
    "NetworkTracker",
    "GeminiResearcher",
]
