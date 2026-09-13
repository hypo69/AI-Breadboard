# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Website Intelligence Monitor Package Initialization
# =============================================================================
# Description:
#   Package exports for the Website Intelligence Monitor app.
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.website_monitor.src
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"Website Intelligence Monitor engine package."

from apps.website_monitor.src.auth import AuthStatus, WebsiteMonitorAuthManager
from apps.website_monitor.src.ga4_service import GA4Service, RealtimeReport, GA4PeriodSummary, PageReport, ChannelReport
from apps.website_monitor.src.gsc_service import GSCService, SearchConsoleSummary, SearchQuery
from apps.website_monitor.src.technical_service import TechnicalService, TechnicalSummary, EndpointHealth, SecurityEvent
from apps.website_monitor.src.normalizer import MetricsNormalizer, UnifiedSiteReport, MetricDelta
from apps.website_monitor.src.anomaly_detector import AnomalyDetector, SiteAlert
from apps.website_monitor.src.diagnostics import WebsiteDiagnosticsEngine, SiteHealthAssessment

__all__ = [
    'AuthStatus',
    'WebsiteMonitorAuthManager',
    'GA4Service',
    'RealtimeReport',
    'GA4PeriodSummary',
    'PageReport',
    'ChannelReport',
    'GSCService',
    'SearchConsoleSummary',
    'SearchQuery',
    'TechnicalService',
    'TechnicalSummary',
    'EndpointHealth',
    'SecurityEvent',
    'MetricsNormalizer',
    'UnifiedSiteReport',
    'MetricDelta',
    'AnomalyDetector',
    'SiteAlert',
    'WebsiteDiagnosticsEngine',
    'SiteHealthAssessment',
]
