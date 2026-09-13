# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Website Intelligence Monitor Application Package
# =============================================================================
# Description:
#   Package exports for the Website Intelligence Monitor application desk.
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.website_monitor
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Website Intelligence Monitor Application."""

from apps.website_monitor.router import init_router, router
from apps.website_monitor.src import (
    AnomalyDetector,
    AuthStatus,
    ChannelReport,
    EndpointHealth,
    GA4PeriodSummary,
    GA4Service,
    GSCService,
    MetricDelta,
    MetricsNormalizer,
    PageReport,
    RealtimeReport,
    SearchConsoleSummary,
    SearchQuery,
    SecurityEvent,
    SiteAlert,
    SiteHealthAssessment,
    TechnicalService,
    TechnicalSummary,
    WebsiteDiagnosticsEngine,
    WebsiteMonitorAuthManager,
)

__all__ = [
    "router",
    "init_router",
    "WebsiteMonitorAuthManager",
    "AuthStatus",
    "GA4Service",
    "RealtimeReport",
    "GA4PeriodSummary",
    "PageReport",
    "ChannelReport",
    "GSCService",
    "SearchConsoleSummary",
    "SearchQuery",
    "TechnicalService",
    "TechnicalSummary",
    "EndpointHealth",
    "SecurityEvent",
    "MetricsNormalizer",
    "UnifiedSiteReport",
    "MetricDelta",
    "AnomalyDetector",
    "SiteAlert",
    "WebsiteDiagnosticsEngine",
    "SiteHealthAssessment",
]
