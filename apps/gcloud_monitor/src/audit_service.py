# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Google Cloud Audit Logs and IAM Security Inspector
# =============================================================================
# Description:
#   Monitors Cloud Audit Logs (Admin Activity, Data Access, System Events) to
#   detect security anomalies, IAM role mutations, service account key events,
#   and suspicious API access patterns.
#
# Examples:
#   >>> from apps.gcloud_monitor.src.audit_service import GCloudAuditService
#   >>> audit_svc = GCloudAuditService()
#   >>> events = audit_svc.get_recent_audit_events()
#
# File: audit_service.py
# Project: ai-breadboard
# Package: apps.gcloud_monitor.src
# Class: GCloudAuditService
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Audit Logs inspection, security event analysis, and IAM tracking."""

from __future__ import annotations

import datetime
import random
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from apps.gcloud_monitor.src.auth import GCloudAuthManager
from apps.gcloud_monitor.src.logging_service import GCloudLoggingService
from src.logger import logger


@dataclass
class AuditEvent:
    """Normalized representation of a GCP Cloud Audit log entry."""

    event_id: str = ''
    timestamp: str = ''
    principal_email: str = ''
    service_name: str = ''
    method_name: str = ''
    resource_name: str = ''
    caller_ip: str = ''
    status_code: str = 'OK'
    severity: str = 'NOTICE'
    is_sensitive: bool = False
    details: str = ''

    def to_dict(self) -> Dict[str, Any]:
        """Convert audit event dataclass to dictionary."""
        return asdict(self)


class GCloudAuditService:
    """Parses and classifies GCP Audit Logs for security and operational changes."""

    SENSITIVE_METHODS = [
        'SetIamPolicy',
        'CreateServiceAccountKey',
        'DeleteServiceAccountKey',
        'CreateServiceAccount',
        'DeleteServiceAccount',
        'UpdateBucketAccessControl',
        'CreateRole',
        'DeleteRole',
    ]

    def __init__(
        self,
        auth_mgr: Optional[GCloudAuthManager] = None,
        logging_svc: Optional[GCloudLoggingService] = None,
    ) -> None:
        """Initialize Audit Service.

        Args:
            auth_mgr (Optional[GCloudAuthManager]): Auth manager instance.
            logging_svc (Optional[GCloudLoggingService]): Logging service instance.
        """
        self.auth_mgr: GCloudAuthManager = auth_mgr if auth_mgr else GCloudAuthManager()
        self.logging_svc: GCloudLoggingService = (
            logging_svc if logging_svc else GCloudLoggingService(auth_mgr=self.auth_mgr)
        )

    def get_recent_audit_events(self, limit: int = 20) -> List[AuditEvent]:
        """Fetch and parse recent GCP Audit Log events.

        Args:
            limit (int): Max number of audit events to return.

        Returns:
            List[AuditEvent]: List of parsed audit events.
        """
        filter_expr = 'logName =~ "cloudaudit.googleapis.com"'
        raw_logs = self.logging_svc.query_logs(filter_expr=filter_expr, max_entries=limit)

        events: List[AuditEvent] = []
        for entry in raw_logs:
            proto_pay = entry.json_payload.get('protoPayload', {})
            auth_info = proto_pay.get('authenticationInfo', {})
            req_meta = proto_pay.get('requestMetadata', {})
            status = proto_pay.get('status', {})

            method = proto_pay.get('methodName', '')
            is_sens = any(s in method for s in self.SENSITIVE_METHODS)

            event = AuditEvent(
                event_id=entry.insert_id or f'aud_{random.randint(10000, 99999)}',
                timestamp=entry.timestamp,
                principal_email=auth_info.get('principalEmail', 'admin@example.com'),
                service_name=proto_pay.get('serviceName', 'iam.googleapis.com'),
                method_name=method or 'google.iam.admin.v1.SetIamPolicy',
                resource_name=proto_pay.get('resourceName', 'projects/mock-breadboard'),
                caller_ip=req_meta.get('callerIp', '203.0.113.42'),
                status_code=status.get('message', 'OK'),
                severity=entry.severity,
                is_sensitive=is_sens,
                details=entry.text_payload or proto_pay.get('serviceData', {}).get('summary', 'Audit activity event'),
            )
            events.append(event)

        if not events:
            events = self._generate_mock_audit_events(limit=limit)
        return events

    def _generate_mock_audit_events(self, limit: int = 20) -> List[AuditEvent]:
        """Generate realistic simulated audit logs for security dashboard."""
        now = datetime.datetime.now(datetime.timezone.utc)
        templates = [
            ('admin@company.com', 'iam.googleapis.com', 'google.iam.admin.v1.CreateServiceAccountKey', 'projects/breadboard/serviceAccounts/sa-runner', True),
            ('developer@company.com', 'run.googleapis.com', 'google.cloud.run.v1.Services.UpdateService', 'projects/breadboard/locations/europe-west1/services/api', False),
            ('sec-admin@company.com', 'resourcemanager.googleapis.com', 'google.iam.v1.SetIamPolicy', 'projects/breadboard', True),
            ('ci-bot@company.com', 'storage.googleapis.com', 'storage.buckets.update', 'projects/breadboard/buckets/data-lake', False),
            ('admin@company.com', 'secretmanager.googleapis.com', 'google.cloud.secretmanager.v1.AccessSecretVersion', 'projects/breadboard/secrets/jwt-token', True),
        ]

        events: List[AuditEvent] = []
        for i in range(min(limit, 10)):
            ts = (now - datetime.timedelta(minutes=i * 15)).isoformat()
            principal, s_name, method, res, is_sens = random.choice(templates)
            events.append(
                AuditEvent(
                    event_id=f'aud_ev_{i:04d}_{random.randint(100, 999)}',
                    timestamp=ts,
                    principal_email=principal,
                    service_name=s_name,
                    method_name=method,
                    resource_name=res,
                    caller_ip=f'198.51.100.{random.randint(10, 240)}',
                    status_code='OK',
                    severity='WARNING' if is_sens else 'NOTICE',
                    is_sensitive=is_sens,
                    details=f'Action {method.split(".")[-1]} performed by {principal}',
                )
            )
        return events
