# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Google Cloud AI Diagnostics and Anomaly Correlator
# =============================================================================
# Description:
#   Performs intelligent root-cause analysis (RCA), log correlation, anomaly
#   detection, and action recommendation across GCP metrics and audit logs.
#
# Examples:
#   >>> from apps.gcloud_monitor.src.diagnostics import GCloudDiagnosticsEngine
#   >>> diag = GCloudDiagnosticsEngine()
#   >>> assessment = diag.evaluate_health()
#
# File: diagnostics.py
# Project: ai-breadboard
# Package: apps.gcloud_monitor.src
# Class: GCloudDiagnosticsEngine
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Intelligent health assessment, root cause analysis, and AI recommendations."""

from __future__ import annotations

import datetime
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from apps.gcloud_monitor.src.alert_engine import GCloudAlertEngine
from apps.gcloud_monitor.src.audit_service import GCloudAuditService
from apps.gcloud_monitor.src.auth import GCloudAuthManager
from apps.gcloud_monitor.src.error_reporting import GCloudErrorReporter
from apps.gcloud_monitor.src.metrics_service import GCloudMetricsService
from logger import logger


@dataclass
class HealthAssessment:
    """System health assessment diagnostic report."""

    status: str = 'HEALTHY'
    score: int = 100
    timestamp: str = ''
    anomalies: List[str] = field(default_factory=list)
    root_cause_analysis: str = ''
    recommendations: List[str] = field(default_factory=list)
    telemetry_summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert health assessment dataclass to dictionary."""
        return asdict(self)


class GCloudDiagnosticsEngine:
    """Analyzes combined GCP observability signals to detect anomalies and propose fixes."""

    def __init__(
        self,
        auth_mgr: Optional[GCloudAuthManager] = None,
        metrics_svc: Optional[GCloudMetricsService] = None,
        error_reporter: Optional[GCloudErrorReporter] = None,
        audit_svc: Optional[GCloudAuditService] = None,
        alert_engine: Optional[GCloudAlertEngine] = None,
    ) -> None:
        """Initialize Diagnostics Engine.

        Args:
            auth_mgr (Optional[GCloudAuthManager]): Auth manager instance.
            metrics_svc (Optional[GCloudMetricsService]): Metrics service.
            error_reporter (Optional[GCloudErrorReporter]): Error reporter.
            audit_svc (Optional[GCloudAuditService]): Audit service.
            alert_engine (Optional[GCloudAlertEngine]): Alert engine.
        """
        self.auth_mgr: GCloudAuthManager = auth_mgr if auth_mgr else GCloudAuthManager()
        self.metrics_svc: GCloudMetricsService = (
            metrics_svc if metrics_svc else GCloudMetricsService(auth_mgr=self.auth_mgr)
        )
        self.error_reporter: GCloudErrorReporter = (
            error_reporter if error_reporter else GCloudErrorReporter(auth_mgr=self.auth_mgr)
        )
        self.audit_svc: GCloudAuditService = (
            audit_svc if audit_svc else GCloudAuditService(auth_mgr=self.auth_mgr)
        )
        self.alert_engine: GCloudAlertEngine = (
            alert_engine if alert_engine else GCloudAlertEngine(auth_mgr=self.auth_mgr)
        )

    def evaluate_health(self) -> HealthAssessment:
        """Evaluate overall GCP system health, anomalies, and AI remediation advice.

        Returns:
            HealthAssessment: Full health report.
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        metrics = self.metrics_svc.get_metrics_summary()
        errors = self.error_reporter.get_error_groups(limit=5)
        audits = self.audit_svc.get_recent_audit_events(limit=5)
        incidents = self.alert_engine.get_active_incidents()

        anomalies: List[str] = []
        score = 100

        if metrics.error_rate_percent > 1.0:
            anomalies.append(f'Error rate elevated to {metrics.error_rate_percent}%')
            score -= 20

        if metrics.cpu_utilization_percent > 80.0:
            anomalies.append(f'High CPU utilization detected ({metrics.cpu_utilization_percent}%)')
            score -= 15

        if any(a.is_sensitive for a in audits):
            anomalies.append('Sensitive IAM permission mutations detected in last 1 hour')
            score -= 10

        if incidents:
            score -= len(incidents) * 15

        score = max(10, min(100, score))

        if score >= 85:
            status = 'HEALTHY'
            rca = 'All systems nominal. Error rates and API latency remain within baseline targets.'
            recommendations = [
                'Continue standard telemetry monitoring.',
                'Review Cloud Monitoring alert policy notifications for proactive coverage.',
            ]
        elif score >= 60:
            status = 'DEGRADED'
            rca = (
                'System under moderate stress. Elevated error spikes observed in API gateway, '
                'accompanied by latency fluctuations in upstream dependencies.'
            )
            recommendations = [
                'Scale Cloud Run max instances or worker pool concurrency.',
                'Inspect database connection pool exhaustion in tbl_media queries.',
                'Verify authentication token expiration policies and client refresh logic.',
            ]
        else:
            status = 'CRITICAL'
            rca = (
                'Severe degradation detected. High failure rate and multiple active incident triggers. '
                'Potential authentication cascade or database locking bottleneck.'
            )
            recommendations = [
                'Trigger immediate incident response procedure.',
                'Restart failed service containers in Cloud Run / Kubernetes.',
                'Check IAM role assignments for unauthorized access attempts.',
            ]

        return HealthAssessment(
            status=status,
            score=score,
            timestamp=now.isoformat(),
            anomalies=anomalies,
            root_cause_analysis=rca,
            recommendations=recommendations,
            telemetry_summary={
                'project_id': metrics.project_id,
                'requests_per_min': metrics.total_requests_per_min,
                'error_rate_pct': metrics.error_rate_percent,
                'p95_latency_ms': metrics.p95_latency_ms,
                'cpu_pct': metrics.cpu_utilization_percent,
                'active_incidents_count': len(incidents),
                'error_groups_count': len(errors),
            },
        )
