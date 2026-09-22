# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Anomaly Detection and Business Alert Engine
# =============================================================================
# Description:
#   Evaluates threshold rules and statistical shifts across traffic channels,
#   conversion dropouts, 404/5xx error spikes, and server response slowdowns.
#
# Examples:
#   >>> from apps.website_monitor.src.anomaly_detector import AnomalyDetector
#   >>> detector = AnomalyDetector()
#   >>> alerts = detector.detect_anomalies(unified_report)
#
# File: anomaly_detector.py
# Project: ai-breadboard
# Package: apps.website_monitor.src
# Class: AnomalyDetector
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"Rule-based and statistical anomaly detection engine for website intelligence."

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from apps.website_monitor.src.normalizer import UnifiedSiteReport
from logger import logger


@dataclass
class SiteAlert:
    "Structured business or technical alert notification."
    alert_id: str
    severity: str  # 'CRITICAL', 'WARNING', 'INFO'
    category: str  # 'TRAFFIC', 'CONVERSION', 'TECHNICAL', 'SEARCH'
    title: str
    description: str
    impact_metric: str
    change_value: str
    recommended_action: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AnomalyDetector:
    "Evaluates cross-layer data to spot actionable anomalies and incidents."

    def __init__(self, thresholds: Optional[Dict[str, float]] = None) -> None:
        self.thresholds = thresholds or {
            'traffic_drop_percent': 15.0,
            'conversion_drop_percent': 10.0,
            'error_404_spike_count': 50,
            'error_5xx_threshold': 2,
            'latency_p95_ms': 500.0,
        }

    def detect_anomalies(self, report: UnifiedSiteReport) -> List[SiteAlert]:
        "Analyze report deltas and return detected anomalies and alerts."
        alerts: List[SiteAlert] = []

        # 1. Traffic Drift Anomaly Check
        user_delta = report.deltas.get('users')
        if user_delta and user_delta.change_percent <= -self.thresholds.get('traffic_drop_percent', 15.0):
            alerts.append(
                SiteAlert(
                    alert_id='ALT-TRAFFIC-DROP',
                    severity='WARNING',
                    category='TRAFFIC',
                    title='Significant Traffic Drop Detected',
                    description=f'Weekly active users dropped by {abs(user_delta.change_percent):.1f}% compared to previous period.',
                    impact_metric='Active Users',
                    change_value=f'{user_delta.change_percent:+.1f}%',
                    recommended_action='Check Google Search Console indexing status and top marketing campaign links.',
                )
            )

        # 2. Conversion Drop Check
        conv_delta = report.deltas.get('conversions')
        if conv_delta and conv_delta.change_percent <= -self.thresholds.get('conversion_drop_percent', 10.0):
            alerts.append(
                SiteAlert(
                    alert_id='ALT-CONVERSION-DROP',
                    severity='CRITICAL',
                    category='CONVERSION',
                    title='Conversion Dropout on Key Funnel',
                    description=f'Total conversions decreased by {abs(conv_delta.change_percent):.1f}%, indicating checkout or lead form friction.',
                    impact_metric='Conversions',
                    change_value=f'{conv_delta.change_percent:+.1f}%',
                    recommended_action='Inspect /checkout funnel steps and payment gateway logs for processing errors.',
                )
            )

        # 3. Technical & Server 404 / 5xx Errors
        if report.technical.status_404_count > self.thresholds.get('error_404_spike_count', 50):
            alerts.append(
                SiteAlert(
                    alert_id='ALT-404-SPIKE',
                    severity='WARNING',
                    category='TECHNICAL',
                    title='Elevated 404 Not Found Errors',
                    description=f'{report.technical.status_404_count} broken links or missing resources detected recently.',
                    impact_metric='404 Errors',
                    change_value=f'{report.technical.status_404_count} occurrences',
                    recommended_action='Review recent site deployments or URL rewrite rules to fix broken routes.',
                )
            )

        if report.technical.status_5xx_count >= self.thresholds.get('error_5xx_threshold', 2):
            alerts.append(
                SiteAlert(
                    alert_id='ALT-5XX-ERRORS',
                    severity='CRITICAL',
                    category='TECHNICAL',
                    title='Backend 5xx Server Errors Detected',
                    description=f'{report.technical.status_5xx_count} internal server errors encountered during requests.',
                    impact_metric='5xx Errors',
                    change_value=f'{report.technical.status_5xx_count} errors',
                    recommended_action='Check application exception logs and database connection pool health.',
                )
            )

        return alerts
