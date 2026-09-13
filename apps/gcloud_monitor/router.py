# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Google Cloud Monitor FastAPI Router
# =============================================================================
# Description:
#   FastAPI REST endpoints for querying Google Cloud Logging, Monitoring
#   Metrics, Audit events, Error Reporting, and AI Health diagnostics.
#
# Examples:
#   >>> from fastapi import FastAPI
#   >>> from apps.gcloud_monitor.router import router
#   >>> app = FastAPI()
#   >>> app.include_router(router)
#
# File: router.py
# Project: ai-breadboard
# Package: apps.gcloud_monitor
# Class: N/A
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI endpoints for Google Cloud Observability & Monitoring."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from apps.gcloud_monitor.src.alert_engine import GCloudAlertEngine
from apps.gcloud_monitor.src.audit_service import GCloudAuditService
from apps.gcloud_monitor.src.auth import GCloudAuthManager
from apps.gcloud_monitor.src.diagnostics import GCloudDiagnosticsEngine
from apps.gcloud_monitor.src.error_reporting import GCloudErrorReporter
from apps.gcloud_monitor.src.logging_service import GCloudLoggingService
from apps.gcloud_monitor.src.metrics_service import GCloudMetricsService
from src.logger import logger

router = APIRouter(prefix='/api/gcloud', tags=['Google Cloud Monitor'])

# Initialize singleton services
auth_manager = GCloudAuthManager()
logging_service = GCloudLoggingService(auth_mgr=auth_manager)
metrics_service = GCloudMetricsService(auth_mgr=auth_manager)
audit_service = GCloudAuditService(auth_mgr=auth_manager, logging_svc=logging_service)
error_reporter = GCloudErrorReporter(auth_mgr=auth_manager, logging_svc=logging_service)
alert_engine = GCloudAlertEngine(
    auth_mgr=auth_manager, metrics_svc=metrics_service, logging_svc=logging_service
)
diagnostics_engine = GCloudDiagnosticsEngine(
    auth_mgr=auth_manager,
    metrics_svc=metrics_service,
    error_reporter=error_reporter,
    audit_svc=audit_service,
    alert_engine=alert_engine,
)


class LogQueryRequest(BaseModel):
    """Request schema for searching Cloud Logging."""

    filter_expr: str = Field(default='', description='Cloud Logging filter expression')
    limit: int = Field(default=50, ge=1, le=500, description='Max logs to fetch')
    order_by: str = Field(default='timestamp desc', description='Log sort ordering')


@router.get('/status')
async def get_gcloud_status() -> Dict[str, Any]:
    """Get current GCP authentication and connectivity status."""
    status = auth_manager.get_status()
    return {
        'authenticated': status.authenticated,
        'auth_type': status.auth_type,
        'project_id': status.project_id,
        'client_email': status.client_email,
        'is_mock': status.is_mock,
        'details': status.details,
    }


@router.get('/logs')
async def get_logs(
    filter: str = Query(default='', description='GCP filter expression'),
    limit: int = Query(default=30, ge=1, le=500, description='Max entries to return'),
) -> List[Dict[str, Any]]:
    """Retrieve parsed logs matching query filter."""
    logs = logging_service.query_logs(filter_expr=filter, max_entries=limit)
    return [entry.to_dict() for entry in logs]


@router.post('/logs/query')
async def post_query_logs(req: LogQueryRequest) -> List[Dict[str, Any]]:
    """Execute structured log query."""
    logs = logging_service.query_logs(
        filter_expr=req.filter_expr, max_entries=req.limit, order_by=req.order_by
    )
    return [entry.to_dict() for entry in logs]


@router.get('/metrics')
async def get_metrics() -> Dict[str, Any]:
    """Get real-time Cloud Monitoring metrics dashboard."""
    summary = metrics_service.get_metrics_summary()
    return summary.to_dict()


@router.get('/audit')
async def get_audit_logs(
    limit: int = Query(default=20, ge=1, le=100, description='Max audit events')
) -> List[Dict[str, Any]]:
    """Get parsed Cloud Audit Logs for IAM and administrative actions."""
    events = audit_service.get_recent_audit_events(limit=limit)
    return [ev.to_dict() for ev in events]


@router.get('/errors')
async def get_errors(
    limit: int = Query(default=10, ge=1, le=50, description='Max error groups')
) -> List[Dict[str, Any]]:
    """Get aggregated Error Reporting clusters and stack traces."""
    groups = error_reporter.get_error_groups(limit=limit)
    return [grp.to_dict() for grp in groups]


@router.get('/incidents')
async def get_incidents() -> List[Dict[str, Any]]:
    """Get active alert incidents and threshold breaches."""
    incidents = alert_engine.get_active_incidents()
    return [inc.to_dict() for inc in incidents]


@router.get('/diagnostic')
async def get_diagnostic() -> Dict[str, Any]:
    """Run comprehensive AI diagnostics and health assessment."""
    assessment = diagnostics_engine.evaluate_health()
    return assessment.to_dict()
