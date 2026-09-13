# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit Tests for Website Intelligence Monitor (TDD Standard)
# =============================================================================
# Description:
#   Comprehensive unit tests for Website Intelligence Monitor:
#   authentication discovery, GA4 data reports, Search Console statistics,
#   technical telemetry probes, metrics normalization, period comparisons (WoW),
#   anomaly rule engine, AI root-cause diagnostics, and FastAPI REST endpoints.
#
# Examples:
#   $ pytest apps/website_monitor/tests/ -v --cov=apps.website_monitor
#
# File: test_website_monitor.py
# Project: ai-breadboard
# Package: apps.website_monitor.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Unit test suite for apps.website_monitor."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.website_monitor.router import init_router, router
from apps.website_monitor.src.anomaly_detector import AnomalyDetector, SiteAlert
from apps.website_monitor.src.auth import AuthStatus, WebsiteMonitorAuthManager
from apps.website_monitor.src.diagnostics import SiteHealthAssessment, WebsiteDiagnosticsEngine
from apps.website_monitor.src.ga4_service import (
    ChannelReport,
    GA4PeriodSummary,
    GA4Service,
    PageReport,
    RealtimeReport,
)
from apps.website_monitor.src.gsc_service import GSCService, SearchConsoleSummary, SearchQuery
from apps.website_monitor.src.normalizer import MetricDelta, MetricsNormalizer, UnifiedSiteReport
from apps.website_monitor.src.technical_service import EndpointHealth, SecurityEvent, TechnicalService, TechnicalSummary


@pytest.fixture
def auth_mgr() -> WebsiteMonitorAuthManager:
    """Fixture providing WebsiteMonitorAuthManager with test overrides."""
    return WebsiteMonitorAuthManager(
        property_id_override="properties/test987654",
        site_url_override="https://testsite.example.com",
    )


@pytest.fixture
def test_client() -> TestClient:
    """Fixture providing FastAPI test client with website monitor router."""
    app = FastAPI(title="Test Website Monitor")
    app.include_router(init_router())
    return TestClient(app)


def test_auth_manager(auth_mgr: WebsiteMonitorAuthManager) -> None:
    """Test auth status resolution and mock fallback."""
    creds, prop, site = auth_mgr.get_credentials()
    status = auth_mgr.get_status()

    assert prop == "properties/test987654"
    assert site == "https://testsite.example.com"
    assert status.property_id == "properties/test987654"
    assert status.site_url == "https://testsite.example.com"
    assert isinstance(status.is_mock, bool)


def test_ga4_service(auth_mgr: WebsiteMonitorAuthManager) -> None:
    """Test GA4 service realtime, summary, channels, and top pages."""
    svc = GA4Service(auth_mgr=auth_mgr)

    rt = svc.get_realtime_data()
    assert isinstance(rt, RealtimeReport)
    assert rt.active_users >= 1
    assert len(rt.top_pages) > 0
    assert len(rt.top_countries) > 0

    cur_summary = svc.get_period_summary(days_ago_start=7, days_ago_end=0, label="This Week")
    assert isinstance(cur_summary, GA4PeriodSummary)
    assert cur_summary.active_users == 12421
    assert cur_summary.conversions == 821

    prev_summary = svc.get_period_summary(days_ago_start=14, days_ago_end=7, label="Previous Week")
    assert isinstance(prev_summary, GA4PeriodSummary)
    assert prev_summary.active_users == 14893

    pages = svc.get_top_pages(limit=5)
    assert len(pages) == 5
    assert any(p.page_path == "/products" for p in pages)

    channels = svc.get_channel_breakdown()
    assert len(channels) >= 4
    assert any(ch.channel_group == "Organic Search" for ch in channels)


def test_gsc_service(auth_mgr: WebsiteMonitorAuthManager) -> None:
    """Test Google Search Console service query aggregation."""
    svc = GSCService(auth_mgr=auth_mgr)
    summary = svc.get_search_analytics(days=7)

    assert isinstance(summary, SearchConsoleSummary)
    assert summary.total_clicks > 0
    assert summary.total_impressions > 0
    assert summary.avg_ctr > 0.0
    assert len(summary.top_queries) > 0


def test_technical_service(auth_mgr: WebsiteMonitorAuthManager) -> None:
    """Test technical service endpoint probes and server summary."""
    svc = TechnicalService(auth_mgr=auth_mgr)
    summary = svc.get_technical_summary()

    assert isinstance(summary, TechnicalSummary)
    assert summary.availability_percent > 99.0
    assert summary.avg_response_time_ms > 0
    assert summary.status_200_count > 0
    assert len(summary.endpoint_probes) > 0
    assert len(summary.recent_security_events) > 0


def test_normalizer_and_anomaly_detector(auth_mgr: WebsiteMonitorAuthManager) -> None:
    """Test cross-layer report normalization and anomaly alert generation."""
    ga4_svc = GA4Service(auth_mgr=auth_mgr)
    gsc_svc = GSCService(auth_mgr=auth_mgr)
    tech_svc = TechnicalService(auth_mgr=auth_mgr)
    norm = MetricsNormalizer(ga4_svc=ga4_svc, gsc_svc=gsc_svc, tech_svc=tech_svc)

    report = norm.build_unified_report()
    assert isinstance(report, UnifiedSiteReport)
    assert "users" in report.deltas
    assert "sessions" in report.deltas
    assert "conversions" in report.deltas
    assert report.deltas["users"].change_percent < 0

    detector = AnomalyDetector()
    alerts = detector.detect_anomalies(report)
    assert len(alerts) > 0
    assert any(a.category == "TRAFFIC" for a in alerts)
    assert any(a.category == "CONVERSION" for a in alerts)


def test_diagnostics_engine(auth_mgr: WebsiteMonitorAuthManager) -> None:
    """Test AI diagnostics health evaluation and summary output."""
    ga4_svc = GA4Service(auth_mgr=auth_mgr)
    gsc_svc = GSCService(auth_mgr=auth_mgr)
    tech_svc = TechnicalService(auth_mgr=auth_mgr)
    norm = MetricsNormalizer(ga4_svc=ga4_svc, gsc_svc=gsc_svc, tech_svc=tech_svc)
    detector = AnomalyDetector()
    engine = WebsiteDiagnosticsEngine(normalizer=norm, anomaly_detector=detector)

    assessment = engine.evaluate_site_health()
    assert isinstance(assessment, SiteHealthAssessment)
    assert 0 <= assessment.health_score <= 100
    assert assessment.overall_status in ["EXCELLENT", "HEALTHY", "NEEDS_ATTENTION", "CRITICAL"]
    assert len(assessment.executive_summary) > 20
    assert len(assessment.action_items) >= 2


def test_fastapi_endpoints(test_client: TestClient) -> None:
    """Test all FastAPI REST endpoints for Website Intelligence Monitor."""
    # 1. Status
    res = test_client.get("/api/v1/website-monitor/status")
    assert res.status_code == 200
    assert "property_id" in res.json()

    # 2. Realtime
    res = test_client.get("/api/v1/website-monitor/realtime")
    assert res.status_code == 200
    assert "active_users" in res.json()

    # 3. Summary
    res = test_client.get("/api/v1/website-monitor/summary")
    assert res.status_code == 200
    data = res.json()
    assert "deltas" in data
    assert "current_period" in data

    # 4. Pages
    res = test_client.get("/api/v1/website-monitor/pages?limit=5")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # 5. Traffic Sources
    res = test_client.get("/api/v1/website-monitor/traffic-sources")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # 6. Search Console
    res = test_client.get("/api/v1/website-monitor/search-console?days=7")
    assert res.status_code == 200
    assert "total_clicks" in res.json()

    # 7. Technical
    res = test_client.get("/api/v1/website-monitor/technical")
    assert res.status_code == 200
    assert "availability_percent" in res.json()

    # 8. Alerts
    res = test_client.get("/api/v1/website-monitor/alerts")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # 9. Diagnostic
    res = test_client.get("/api/v1/website-monitor/diagnostic")
    assert res.status_code == 200
    assert "health_score" in res.json()
    assert "executive_summary" in res.json()
