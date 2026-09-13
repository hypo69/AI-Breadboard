# -*- coding: utf-8 -*-
"""Prometheus-compatible metrics collector.

Records HTTP request latency + counts, WebSocket connection counts,
and exports Prometheus text exposition format at GET /health/metrics.

Usage:
    metrics = create_metrics()
    metrics.record_request("/api/chat", 142.3, 200)
    # In a route:
    return PlainTextResponse(metrics.prometheus_output())
"""
from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock
from typing import Dict, List, Optional


class MetricsCollector:
    """Thread-safe in-memory metrics with Prometheus text output."""

    def __init__(self, started_at: Optional[float] = None) -> None:
        self._lock = Lock()
        self._started_at = started_at or time.time()
        # {route: {status_code: count}}
        self._request_counts: Dict[str, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
        # {route: [latency_ms, ...]}  — capped at 1000 samples
        self._latencies: Dict[str, List[float]] = defaultdict(list)
        self._ws_connections: int = 0

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def record_request(self, route: str, latency_ms: float, status_code: int = 200) -> None:
        with self._lock:
            self._request_counts[route][status_code] += 1
            self._latencies[route].append(latency_ms)
            if len(self._latencies[route]) > 1000:
                self._latencies[route] = self._latencies[route][-1000:]

    def increment_ws(self) -> None:
        with self._lock:
            self._ws_connections += 1

    def decrement_ws(self) -> None:
        with self._lock:
            self._ws_connections = max(0, self._ws_connections - 1)

    def set_ws(self, count: int) -> None:
        with self._lock:
            self._ws_connections = max(0, count)

    # ------------------------------------------------------------------
    # Summary (for /health/detailed)
    # ------------------------------------------------------------------

    @property
    def uptime_seconds(self) -> float:
        return time.time() - self._started_at

    def get_summary(self) -> dict:
        with self._lock:
            total = sum(sum(v.values()) for v in self._request_counts.values())
            return {
                "total_requests": total,
                "ws_connections": self._ws_connections,
                "uptime_seconds": round(self.uptime_seconds, 1),
            }

    # ------------------------------------------------------------------
    # Prometheus output
    # ------------------------------------------------------------------

    def _pct(self, values: List[float], p: float) -> float:
        if not values:
            return 0.0
        s = sorted(values)
        return s[min(int(len(s) * p / 100), len(s) - 1)]

    def prometheus_output(self) -> str:
        lines: List[str] = []
        with self._lock:
            lines += [
                "# HELP ai_breadboard_uptime_seconds Application uptime in seconds",
                "# TYPE ai_breadboard_uptime_seconds gauge",
                f"ai_breadboard_uptime_seconds {self.uptime_seconds:.1f}",
                "# HELP ai_breadboard_ws_connections_active Active WebSocket connections",
                "# TYPE ai_breadboard_ws_connections_active gauge",
                f"ai_breadboard_ws_connections_active {self._ws_connections}",
                "# HELP ai_breadboard_http_requests_total HTTP requests by route and status",
                "# TYPE ai_breadboard_http_requests_total counter",
            ]
            for route, status_map in self._request_counts.items():
                r = route.replace('"', '\\"')
                for status, count in status_map.items():
                    lines.append(f'ai_breadboard_http_requests_total{{route="{r}",status="{status}"}} {count}')

            lines += [
                "# HELP ai_breadboard_request_latency_ms Latency percentiles in ms",
                "# TYPE ai_breadboard_request_latency_ms summary",
            ]
            for route, lats in self._latencies.items():
                r = route.replace('"', '\\"')
                for q, pct in ((0.5, 50), (0.95, 95), (0.99, 99)):
                    lines.append(f'ai_breadboard_request_latency_ms{{route="{r}",quantile="{q}"}} {self._pct(lats, pct):.2f}')

        return "\n".join(lines) + "\n"


def create_metrics(started_at: Optional[float] = None) -> MetricsCollector:
    """Factory — use this to create a MetricsCollector tied to an app instance."""
    return MetricsCollector(started_at=started_at)
