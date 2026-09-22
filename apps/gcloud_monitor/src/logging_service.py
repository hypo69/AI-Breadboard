# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Google Cloud Logging Service and Parser
# =============================================================================
# Description:
#   Interfaces with GCP Cloud Logging API to execute advanced filter queries,
#   fetch historical logs, tail real-time entries, and parse structured logs.
#
# Examples:
#   >>> from apps.gcloud_monitor.src.logging_service import GCloudLoggingService
#   >>> service = GCloudLoggingService()
#   >>> logs = service.query_logs(filter_expr='severity >= ERROR', max_entries=50)
#
# File: logging_service.py
# Project: ai-breadboard
# Package: apps.gcloud_monitor.src
# Class: GCloudLoggingService
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Cloud Logging queries, filter evaluations, and structured payload extraction."""

from __future__ import annotations

import datetime
import json
import random
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from apps.gcloud_monitor.src.auth import GCloudAuthManager
from logger import logger

try:
    from google.cloud import logging_v2
    GCLOUD_LOGGING_AVAILABLE = True
except ImportError:
    logging_v2 = None  # type: ignore
    GCLOUD_LOGGING_AVAILABLE = False


@dataclass
class HttpRequestPayload:
    """HTTP request telemetry embedded in a log entry."""

    request_method: str = ''
    request_url: str = ''
    status: int = 0
    response_size: int = 0
    latency_seconds: float = 0.0
    user_agent: str = ''
    remote_ip: str = ''


@dataclass
class LogEntry:
    """Normalized representation of a GCP Cloud Logging entry."""

    insert_id: str = ''
    timestamp: str = ''
    severity: str = 'INFO'
    resource_type: str = 'global'
    resource_labels: Dict[str, str] = field(default_factory=dict)
    log_name: str = ''
    text_payload: str = ''
    json_payload: Dict[str, Any] = field(default_factory=dict)
    http_request: Optional[HttpRequestPayload] = None
    trace: str = ''
    span_id: str = ''
    labels: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert log entry dataclass to JSON serializable dictionary."""
        return asdict(self)


class GCloudLoggingService:
    """Fetches, filters, and processes Google Cloud Logging entries."""

    def __init__(self, auth_mgr: Optional[GCloudAuthManager] = None) -> None:
        """Initialize Cloud Logging service.

        Args:
            auth_mgr (Optional[GCloudAuthManager]): Authentication manager instance.
        """
        self.auth_mgr: GCloudAuthManager = auth_mgr if auth_mgr else GCloudAuthManager()
        self._client: Any = False

    def _get_client(self) -> Any:
        """Instantiate or retrieve Google Cloud Logging client."""
        if self._client:
            return self._client
        if not GCLOUD_LOGGING_AVAILABLE:
            return False
        creds, proj_id = self.auth_mgr.get_credentials()
        if not creds:
            return False
        try:
            self._client = logging_v2.Client(credentials=creds, project=proj_id)
            return self._client
        except Exception as exc:
            logger.error(f'Failed initializing Cloud Logging client: {exc}')
            return False

    def query_logs(
        self,
        filter_expr: str = '',
        max_entries: int = 50,
        order_by: str = 'timestamp desc',
    ) -> List[LogEntry]:
        """Execute a Cloud Logging query with filter expression.

        Args:
            filter_expr (str): GCP Logging filter expression.
            max_entries (int): Max number of entries to retrieve.
            order_by (str): Sorting order.

        Returns:
            List[LogEntry]: List of parsed log entries.
        """
        client = self._get_client()
        if not client:
            return self._generate_mock_logs(filter_expr=filter_expr, limit=max_entries)

        try:
            _, project_id = self.auth_mgr.get_credentials()
            entries = client.list_entries(
                filter_=filter_expr or None,
                page_size=max_entries,
                order_by=logging_v2.DESCENDING if 'desc' in order_by else logging_v2.ASCENDING,
            )
            result: List[LogEntry] = []
            for raw in entries:
                if len(result) >= max_entries:
                    break
                http_req = None
                if raw.http_request:
                    http_req = HttpRequestPayload(
                        request_method=raw.http_request.get('requestMethod', ''),
                        request_url=raw.http_request.get('requestUrl', ''),
                        status=int(raw.http_request.get('status', 0)),
                        response_size=int(raw.http_request.get('responseSize', 0)),
                        user_agent=raw.http_request.get('userAgent', ''),
                        remote_ip=raw.http_request.get('remoteIp', ''),
                    )

                text_pay = raw.payload if isinstance(raw.payload, str) else ''
                json_pay = raw.payload if isinstance(raw.payload, dict) else {}

                result.append(
                    LogEntry(
                        insert_id=raw.insert_id or '',
                        timestamp=raw.timestamp.isoformat() if raw.timestamp else '',
                        severity=raw.severity or 'INFO',
                        resource_type=raw.resource.type if raw.resource else 'global',
                        resource_labels=raw.resource.labels if raw.resource else {},
                        log_name=raw.log_name or '',
                        text_payload=text_pay,
                        json_payload=json_pay,
                        http_request=http_req,
                        trace=raw.trace or '',
                        span_id=raw.span_id or '',
                        labels=raw.labels or {},
                    )
                )
            return result
        except Exception as exc:
            logger.error(f'Error querying GCP logs: {exc}. Falling back to simulated logs.')
            return self._generate_mock_logs(filter_expr=filter_expr, limit=max_entries)

    def _generate_mock_logs(self, filter_expr: str = '', limit: int = 50) -> List[LogEntry]:
        """Generate realistic simulated GCP log entries for development & offline inspection."""
        severities = ['INFO', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'DEBUG']
        services = [
            ('cloud_run_revision', 'service/api-gateway', 'run.googleapis.com'),
            ('gce_instance', 'compute/worker-node-1', 'compute.googleapis.com'),
            ('cloud_function', 'function/auth-webhook', 'cloudfunctions.googleapis.com'),
            ('k8s_container', 'k8s/rag-ingestor', 'container.googleapis.com'),
        ]
        sample_messages = [
            ('INFO', 'HTTP GET /api/v1/health 200 OK - 14ms'),
            ('INFO', 'User authentication token issued successfully: user_id=usr_9281a'),
            ('WARNING', 'Database connection pool usage reached 82% capacity'),
            ('ERROR', 'AuthenticationError: Invalid bearer token signature or expired claim'),
            ('ERROR', 'DatabaseTimeout: Query execution exceeded timeout threshold (5000ms) on tbl_media'),
            ('CRITICAL', 'OutOfMemoryError: Container instance memory limit exceeded (1024MB allocated)'),
            ('INFO', "PubSub topic 'event-bus-telemetry' published message msg_882947"),
        ]

        now = datetime.datetime.now(datetime.timezone.utc)
        results: List[LogEntry] = []
        for i in range(min(limit, 30)):
            ts = (now - datetime.timedelta(seconds=i * 12)).isoformat()
            sev, msg = random.choice(sample_messages)
            res_type, res_name, log_prefix = random.choice(services)

            if 'severity >= ERROR' in filter_expr and sev not in ['ERROR', 'CRITICAL']:
                continue

            entry = LogEntry(
                insert_id=f'ins_{i:06d}_{random.randint(1000, 9999)}',
                timestamp=ts,
                severity=sev,
                resource_type=res_type,
                resource_labels={'service_name': res_name, 'location': 'europe-west1'},
                log_name=f'projects/mock-breadboard/logs/{log_prefix}',
                text_payload=msg,
                json_payload={'event': 'telemetry_event', 'code': 500 if sev == 'ERROR' else 200},
                http_request=HttpRequestPayload(
                    request_method='POST' if sev in ['ERROR', 'CRITICAL'] else 'GET',
                    request_url='https://api.breadboard.app/v1/dispatch',
                    status=500 if sev in ['ERROR', 'CRITICAL'] else 200,
                    latency_seconds=round(random.uniform(0.01, 1.8), 3),
                    remote_ip='192.168.1.104',
                ),
                trace=f'projects/mock-breadboard/traces/tr_{random.randint(100000, 999999)}',
                span_id=f'sp_{random.randint(1000, 9999)}',
                labels={'environment': 'production', 'version': 'v1.4.2'},
            )
            results.append(entry)
        return results
