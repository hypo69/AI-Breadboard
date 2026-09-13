# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Analytics Normalization & Period Comparison Engine
# =============================================================================
# Description:
#   Aggregates business metrics (GA4), search engine metrics (GSC), and technical
#   telemetry into a single normalized data structure with period delta comparisons.
#
# Examples:
#   >>> from apps.website_monitor.src.normalizer import MetricsNormalizer
#   >>> norm = MetricsNormalizer()
#   >>> report = norm.build_unified_report()
#
# File: normalizer.py
# Project: ai-breadboard
# Package: apps.website_monitor.src
# Class: MetricsNormalizer
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"Data normalization and period comparison calculation engine."

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from apps.website_monitor.src.ga4_service import GA4PeriodSummary, GA4Service
from apps.website_monitor.src.gsc_service import GSCService, SearchConsoleSummary
from apps.website_monitor.src.technical_service import TechnicalService, TechnicalSummary


@dataclass
class MetricDelta:
    "Metric value with current, previous, and percentage change."
    name: str
    current: float
    previous: float
    change_percent: float
    trend: str  # 'up', 'down', 'flat'

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class UnifiedSiteReport:
    "Unified 3-layer normalized report for site owner."
    timestamp: str
    current_period: GA4PeriodSummary
    previous_period: GA4PeriodSummary
    deltas: Dict[str, MetricDelta]
    technical: TechnicalSummary
    search_console: SearchConsoleSummary
    channels: List[Dict[str, Any]]
    top_pages: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'current_period': self.current_period.to_dict(),
            'previous_period': self.previous_period.to_dict(),
            'deltas': {k: v.to_dict() for k, v in self.deltas.items()},
            'technical': self.technical.to_dict(),
            'search_console': self.search_console.to_dict(),
            'channels': self.channels,
            'top_pages': self.top_pages,
        }


class MetricsNormalizer:
    "Cross-layer normalization engine combining GA4, GSC, and Server metrics."

    def __init__(
        self,
        ga4_svc: Optional[GA4Service] = None,
        gsc_svc: Optional[GSCService] = None,
        tech_svc: Optional[TechnicalService] = None,
    ) -> None:
        self.ga4 = ga4_svc or GA4Service()
        self.gsc = gsc_svc or GSCService()
        self.tech = tech_svc or TechnicalService()

    def _calc_delta(self, name: str, cur: float, prev: float) -> MetricDelta:
        if prev == 0:
            pct = 0.0
        else:
            pct = round(((cur - prev) / prev) * 100, 2)
        trend = 'up' if pct > 0.5 else ('down' if pct < -0.5 else 'flat')
        return MetricDelta(name=name, current=cur, previous=prev, change_percent=pct, trend=trend)

    def build_unified_report(self) -> UnifiedSiteReport:
        "Construct a fully normalized site report comparing this week vs previous week."
        cur = self.ga4.get_period_summary(days_ago_start=7, days_ago_end=0, label='This Week')
        prev = self.ga4.get_period_summary(days_ago_start=14, days_ago_end=7, label='Previous Week')
        tech = self.tech.get_technical_summary()
        gsc = self.gsc.get_search_analytics(days=7)
        channels = [ch.to_dict() for ch in self.ga4.get_channel_breakdown()]
        pages = [p.to_dict() for p in self.ga4.get_top_pages(limit=10)]

        deltas = {
            'users': self._calc_delta('Active Users', cur.active_users, prev.active_users),
            'sessions': self._calc_delta('Sessions', cur.sessions, prev.sessions),
            'page_views': self._calc_delta('Page Views', cur.page_views, prev.page_views),
            'conversions': self._calc_delta('Conversions', cur.conversions, prev.conversions),
            'engagement_rate': self._calc_delta('Engagement Rate (%)', cur.engagement_rate, prev.engagement_rate),
        }

        return UnifiedSiteReport(
            timestamp=datetime.utcnow().isoformat(),
            current_period=cur,
            previous_period=prev,
            deltas=deltas,
            technical=tech,
            search_console=gsc,
            channels=channels,
            top_pages=pages,
        )
