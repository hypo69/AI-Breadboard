# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Website Intelligence Monitor FastAPI Router
# =============================================================================
# Description:
#   FastAPI REST endpoints for Website Intelligence Monitor:
#   real-time visitors, GA4 traffic channels, top pages, Search Console metrics,
#   technical telemetry, active anomaly alerts, and AI diagnostics.
#
# Examples:
#   >>> from fastapi import FastAPI
#   >>> from apps.website_monitor.router import init_router
#   >>> app = FastAPI()
#   >>> app.include_router(init_router())
#
# File: router.py
# Project: ai-breadboard
# Package: apps.website_monitor
# Class: N/A
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI REST endpoints for Website Intelligence Monitor."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from apps.website_monitor.src.anomaly_detector import AnomalyDetector
from apps.website_monitor.src.auth import WebsiteMonitorAuthManager
from apps.website_monitor.src.diagnostics import WebsiteDiagnosticsEngine
from apps.website_monitor.src.ga4_service import GA4Service
from apps.website_monitor.src.gsc_service import GSCService
from apps.website_monitor.src.normalizer import MetricsNormalizer
from apps.website_monitor.src.technical_service import TechnicalService
from src.logger import logger
from apps.common.csv_logger import AppCsvLogger

router = APIRouter(prefix="/api/v1/website-monitor", tags=["Website Intelligence Monitor"])
_csv_logger = AppCsvLogger("website_monitor")

# Singleton services

auth_manager = WebsiteMonitorAuthManager()
ga4_service = GA4Service(auth_mgr=auth_manager)
gsc_service = GSCService(auth_mgr=auth_manager)
technical_service = TechnicalService(auth_mgr=auth_manager)
normalizer = MetricsNormalizer(ga4_svc=ga4_service, gsc_svc=gsc_service, tech_svc=technical_service)
anomaly_detector = AnomalyDetector()
diagnostics_engine = WebsiteDiagnosticsEngine(normalizer=normalizer, anomaly_detector=anomaly_detector)


def init_router() -> APIRouter:
    """Return configured APIRouter instance for registration."""
    return router


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """Get current connection and authentication status."""
    status = auth_manager.get_status()
    res = {
        "authenticated": status.authenticated,
        "auth_type": status.auth_type,
        "property_id": status.property_id,
        "site_url": status.site_url,
        "client_email": status.client_email,
        "is_mock": status.is_mock,
        "details": status.details,
    }
    _csv_logger.log_poll(
        poll_type="auth_status",
        metric_name="authenticated",
        value=status.authenticated,
        unit="bool",
        status="AUTHENTICATED" if status.authenticated else "UNAUTHENTICATED",
        details={"site_url": status.site_url, "property_id": status.property_id},
        filename="website_monitor_polls.csv",
    )
    return res


@router.get("/realtime")
async def get_realtime() -> Dict[str, Any]:
    """Get current active visitors, locations, and pages in realtime (last 30m)."""
    data = ga4_service.get_realtime_data().to_dict()
    _csv_logger.log_poll(
        poll_type="realtime_visitors",
        metric_name="active_users_last_30m",
        value=data.get("active_users", 0),
        unit="users",
        status="OK",
        details={"top_pages": data.get("top_pages", [])[:3]},
        filename="website_monitor_polls.csv",
    )
    return data


@router.get("/summary")
async def get_unified_summary() -> Dict[str, Any]:
    """Get complete 3-layer normalized report with period deltas."""
    return normalizer.build_unified_report().to_dict()


@router.get("/pages")
async def get_top_pages(
    limit: int = Query(default=10, ge=1, le=50, description="Max pages to return")
) -> List[Dict[str, Any]]:
    """Get top performing pages by views and conversions."""
    pages = ga4_service.get_top_pages(limit=limit)
    return [p.to_dict() for p in pages]


@router.get("/traffic-sources")
async def get_traffic_sources() -> List[Dict[str, Any]]:
    """Get traffic acquisition channels and conversion rates."""
    channels = ga4_service.get_channel_breakdown()
    return [ch.to_dict() for ch in channels]


@router.get("/search-console")
async def get_search_console(
    days: int = Query(default=7, ge=1, le=90, description="Date range in days")
) -> Dict[str, Any]:
    """Get Google Search Console queries, clicks, impressions, and CTR."""
    return gsc_service.get_search_analytics(days=days).to_dict()


@router.get("/technical")
async def get_technical_telemetry() -> Dict[str, Any]:
    """Get server availability, response times, 404/5xx errors, and security events."""
    return technical_service.get_technical_summary().to_dict()


@router.get("/alerts")
async def get_active_alerts() -> List[Dict[str, Any]]:
    """Get active anomaly alerts across traffic, conversion, and technical layers."""
    report = normalizer.build_unified_report()
    alerts = anomaly_detector.detect_anomalies(report)
    if alerts:
        _csv_logger.log_event(
            event_type="anomalies_detected",
            status="ALERT",
            details={"count": len(alerts), "titles": [a.title for a in alerts]},
            filename="website_monitor_anomalies.csv",
        )
    return [a.to_dict() for a in alerts]


@router.get("/diagnostic")
async def get_ai_diagnostic() -> Dict[str, Any]:
    """Get AI root-cause diagnosis, health score, and recommended actions."""
    assessment = diagnostics_engine.evaluate_site_health()
    _csv_logger.log_poll(
        poll_type="site_health_diagnostic",
        metric_name="health_score",
        value=getattr(assessment, "health_score", 100),
        unit="score",
        status=getattr(assessment, "status", "OK"),
        details={"summary": getattr(assessment, "summary", "")},
        filename="website_monitor_polls.csv",
    )
    return assessment.to_dict()

