# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit Tests for Google Cloud Monitor (TDD Standard)
# =============================================================================
# Description:
#   Exhaustive test suite covering authentication resolution, Cloud Logging
#   filter queries, Cloud Monitoring time-series aggregations, Cloud Audit IAM
#   security analysis, Error Reporting clustering, Alert policies, AI diagnostics,
#   and all FastAPI REST endpoints.
#
# Examples:
#   $ pytest apps/gcloud_monitor/tests/ -v --cov=apps.gcloud_monitor
#
# File: test_gcloud_monitor.py
# Project: ai-breadboard
# Package: apps.gcloud_monitor.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Exhaustive unit test suite for apps.gcloud_monitor."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.gcloud_monitor.router import router
from apps.gcloud_monitor.src.alert_engine import GCloudAlertEngine, Incident
from apps.gcloud_monitor.src.audit_service import AuditEvent, GCloudAuditService
from apps.gcloud_monitor.src.auth import AuthStatus, GCloudAuthManager
from apps.gcloud_monitor.src.diagnostics import GCloudDiagnosticsEngine, HealthAssessment
from apps.gcloud_monitor.src.error_reporting import ErrorGroup, GCloudErrorReporter
from apps.gcloud_monitor.src.logging_service import GCloudLoggingService, HttpRequestPayload, LogEntry
from apps.gcloud_monitor.src.metrics_service import GCloudMetricsService, MetricsDashboardSummary


@pytest.fixture
def auth_mgr() -> GCloudAuthManager:
    """Fixture providing GCloudAuthManager with explicit test project ID.

    Returns:
        GCloudAuthManager: Configured auth manager for testing.
    """
    # Arrange: initialize auth manager with dedicated test project identifier
    test_project: str = 'test-gcp-breadboard'
    return GCloudAuthManager(project_id_override=test_project)


@pytest.fixture
def test_client() -> TestClient:
    """Fixture providing FastAPI test client with gcloud router included.

    Returns:
        TestClient: Synchronous test client for HTTP requests.
    """
    # Arrange: create FastAPI application instance and mount router
    app: FastAPI = FastAPI(title='Test GCloud App')
    app.include_router(router)
    return TestClient(app)


def test_auth_manager_initialization_happy_path(auth_mgr: GCloudAuthManager) -> None:
    """Verify auth manager initialization, credential discovery, and project ID.

    Check: get_credentials returns a tuple and get_status returns valid AuthStatus.
    """
    # Act: resolve credentials and status
    creds, proj_id = auth_mgr.get_credentials()
    status: AuthStatus = auth_mgr.get_status()

    # Assert: verify project ID and status object properties
    assert proj_id == 'test-gcp-breadboard', f'Expected test-gcp-breadboard, got: {proj_id}'
    assert status.project_id == 'test-gcp-breadboard', 'Status project_id mismatch'
    assert status.auth_type in ['service_account', 'oauth2', 'adc', 'mock'], f'Unexpected auth_type: {status.auth_type}'
    assert isinstance(status.authenticated, bool), 'Authenticated flag must be boolean'


def test_logging_service_query_and_filter(auth_mgr: GCloudAuthManager) -> None:
    """Verify Cloud Logging service executes queries and returns normalized LogEntry items.

    Check: entries contain insert_id, timestamp, severity, and payload representations.
    """
    # Arrange: instantiate logging service
    svc: GCloudLoggingService = GCloudLoggingService(auth_mgr=auth_mgr)
    test_limit: int = 10
    filter_expr: str = 'severity >= ERROR'

    # Act: execute query
    logs: list[LogEntry] = svc.query_logs(filter_expr=filter_expr, max_entries=test_limit)

    # Assert: check returned log list structure
    assert len(logs) > 0, 'Logging service returned empty log list'
    assert len(logs) <= test_limit, f'Logs count exceeded requested limit of {test_limit}'
    first_entry: LogEntry = logs[0]
    assert first_entry.insert_id != '', 'Log entry insert_id must not be empty'
    assert first_entry.severity in ['INFO', 'WARNING', 'ERROR', 'CRITICAL', 'DEBUG'], f'Invalid severity: {first_entry.severity}'
    assert isinstance(first_entry.to_dict(), dict), 'LogEntry.to_dict() must return a dictionary'


def test_metrics_service_summary_computation(auth_mgr: GCloudAuthManager) -> None:
    """Verify Cloud Monitoring service compiles dashboard summary and time series metrics.

    Check: metrics summary contains valid throughput, latency, CPU, and time-series points.
    """
    # Arrange: instantiate metrics service
    svc: GCloudMetricsService = GCloudMetricsService(auth_mgr=auth_mgr)

    # Act: get dashboard summary
    summary: MetricsDashboardSummary = svc.get_metrics_summary()

    # Assert: verify numeric ranges and dataclass properties
    assert summary.project_id == 'test-gcp-breadboard', f'Project mismatch in summary: {summary.project_id}'
    assert summary.total_requests_per_min >= 0.0, 'Requests per minute must be non-negative'
    assert summary.cpu_utilization_percent >= 0.0, 'CPU utilization must be non-negative'
    assert summary.p95_latency_ms >= 0.0, 'P95 latency must be non-negative'
    assert len(summary.metrics) > 0, 'Metrics time-series collection must not be empty'
    assert isinstance(summary.to_dict(), dict), 'MetricsDashboardSummary.to_dict() must return a dictionary'


def test_audit_service_security_events(auth_mgr: GCloudAuthManager) -> None:
    """Verify Cloud Audit service extracts and flags sensitive administrative operations.

    Check: audit events contain caller principal, service name, method name, and sensitivity flag.
    """
    # Arrange: instantiate audit service
    svc: GCloudAuditService = GCloudAuditService(auth_mgr=auth_mgr)
    test_limit: int = 5

    # Act: retrieve audit events
    events: list[AuditEvent] = svc.get_recent_audit_events(limit=test_limit)

    # Assert: check audit events format
    assert len(events) > 0, 'Audit service returned no audit events'
    assert len(events) <= test_limit, f'Events count exceeded limit of {test_limit}'
    first_event: AuditEvent = events[0]
    assert first_event.principal_email != '', 'AuditEvent principal_email must not be empty'
    assert first_event.service_name != '', 'AuditEvent service_name must not be empty'
    assert first_event.method_name != '', 'AuditEvent method_name must not be empty'
    assert isinstance(first_event.is_sensitive, bool), 'AuditEvent is_sensitive must be boolean'


def test_error_reporting_clustering(auth_mgr: GCloudAuthManager) -> None:
    """Verify Error Reporting groups exception logs into clustered ErrorGroup objects.

    Check: groups contain error_type, occurrences_count, affected_users, and stack traces.
    """
    # Arrange: instantiate error reporter
    reporter: GCloudErrorReporter = GCloudErrorReporter(auth_mgr=auth_mgr)
    test_limit: int = 5

    # Act: extract error clusters
    groups: list[ErrorGroup] = reporter.get_error_groups(limit=test_limit)

    # Assert: check clustered error groups
    assert len(groups) > 0, 'Error reporter returned no error groups'
    first_group: ErrorGroup = groups[0]
    assert first_group.group_id != '', 'ErrorGroup group_id must not be empty'
    assert first_group.error_type != '', 'ErrorGroup error_type must not be empty'
    assert first_group.occurrences_count >= 1, 'ErrorGroup occurrences_count must be at least 1'
    assert first_group.sample_stack_trace != '', 'ErrorGroup sample_stack_trace must not be empty'


def test_alert_engine_incident_evaluation(auth_mgr: GCloudAuthManager) -> None:
    """Verify Alert Engine evaluates thresholds and produces structured Incident objects.

    Check: active incidents list is structured with policy_name, severity, and state.
    """
    # Arrange: instantiate alert engine
    engine: GCloudAlertEngine = GCloudAlertEngine(auth_mgr=auth_mgr)

    # Act: get active incidents
    incidents: list[Incident] = engine.get_active_incidents()

    # Assert: verify incidents list
    assert isinstance(incidents, list), 'Active incidents must be returned as a list'
    for inc in incidents:
        assert inc.incident_id != '', 'Incident incident_id must not be empty'
        assert inc.policy_name != '', 'Incident policy_name must not be empty'
        assert inc.state in ['OPEN', 'RESOLVED', 'ACKNOWLEDGED'], f'Invalid incident state: {inc.state}'


def test_diagnostics_ai_health_scoring(auth_mgr: GCloudAuthManager) -> None:
    """Verify AI Diagnostics engine calculates overall health score, RCA, and recommendations.

    Check: score is between 0 and 100, status is one of HEALTHY/DEGRADED/CRITICAL.
    """
    # Arrange: instantiate diagnostics engine
    engine: GCloudDiagnosticsEngine = GCloudDiagnosticsEngine(auth_mgr=auth_mgr)

    # Act: evaluate overall system health
    report: HealthAssessment = engine.evaluate_health()

    # Assert: check health assessment structure
    assert report.status in ['HEALTHY', 'DEGRADED', 'CRITICAL'], f'Unexpected status: {report.status}'
    assert 0 <= report.score <= 100, f'Health score out of bounds [0, 100]: {report.score}'
    assert len(report.root_cause_analysis) > 0, 'Root cause analysis string must not be empty'
    assert isinstance(report.recommendations, list), 'Recommendations must be a list'
    assert len(report.recommendations) > 0, 'Recommendations list must not be empty'


def test_fastapi_rest_endpoints(test_client: TestClient) -> None:
    """Verify all FastAPI REST endpoints under /api/gcloud/* respond with HTTP 200 OK.

    Check: /status, /logs, /logs/query, /metrics, /audit, /errors, /incidents, /diagnostic.
    """
    # 1. GET /api/gcloud/status
    res_status = test_client.get('/api/gcloud/status')
    assert res_status.status_code == 200, f'Status endpoint failed: {res_status.text}'
    assert 'project_id' in res_status.json(), 'Response JSON missing project_id'

    # 2. GET /api/gcloud/logs
    res_logs = test_client.get('/api/gcloud/logs?limit=5')
    assert res_logs.status_code == 200, f'Logs endpoint failed: {res_logs.text}'
    assert isinstance(res_logs.json(), list), 'Logs endpoint must return list'

    # 3. POST /api/gcloud/logs/query
    res_post_logs = test_client.post(
        '/api/gcloud/logs/query',
        json={'filter_expr': 'severity >= INFO', 'limit': 5, 'order_by': 'timestamp desc'}
    )
    assert res_post_logs.status_code == 200, f'Logs query endpoint failed: {res_post_logs.text}'
    assert isinstance(res_post_logs.json(), list), 'Logs query endpoint must return list'

    # 4. GET /api/gcloud/metrics
    res_metrics = test_client.get('/api/gcloud/metrics')
    assert res_metrics.status_code == 200, f'Metrics endpoint failed: {res_metrics.text}'
    assert 'total_requests_per_min' in res_metrics.json(), 'Response JSON missing total_requests_per_min'

    # 5. GET /api/gcloud/audit
    res_audit = test_client.get('/api/gcloud/audit?limit=5')
    assert res_audit.status_code == 200, f'Audit endpoint failed: {res_audit.text}'
    assert isinstance(res_audit.json(), list), 'Audit endpoint must return list'

    # 6. GET /api/gcloud/errors
    res_errors = test_client.get('/api/gcloud/errors?limit=5')
    assert res_errors.status_code == 200, f'Errors endpoint failed: {res_errors.text}'
    assert isinstance(res_errors.json(), list), 'Errors endpoint must return list'

    # 7. GET /api/gcloud/incidents
    res_inc = test_client.get('/api/gcloud/incidents')
    assert res_inc.status_code == 200, f'Incidents endpoint failed: {res_inc.text}'
    assert isinstance(res_inc.json(), list), 'Incidents endpoint must return list'

    # 8. GET /api/gcloud/diagnostic
    res_diag = test_client.get('/api/gcloud/diagnostic')
    assert res_diag.status_code == 200, f'Diagnostic endpoint failed: {res_diag.text}'
    assert 'root_cause_analysis' in res_diag.json(), 'Response JSON missing root_cause_analysis'
    assert 'score' in res_diag.json(), 'Response JSON missing score'
