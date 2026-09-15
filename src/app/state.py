# -*- coding: utf-8 -*-
"""Application state container stored in FastAPI's app.state.

Access from request handlers:
    chat_model = request.app.state.chat_model
    ws_hub     = request.app.state.ws_hub
    metrics    = request.app.state.metrics

Both single-user (localhost) and multi-user (server) deployments use
the same state — user isolation is handled at the business logic layer
via user_id, not via separate service instances.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class AppState:
    """All shared application services, populated during lifespan startup."""

    # Core AI models (UnifiedChatModel instances)
    chat_model: Optional[Any] = None
    narrator_model: Optional[Any] = None

    # WebSocket hub for real-time communication
    ws_hub: Optional[Any] = None

    # Prometheus-compatible metrics collector
    metrics: Optional[Any] = None

    # Plugin registry for hot-reload support
    plugin_registry: Optional[Any] = None

    # Loaded plugins dictionary
    plugins: Optional[Any] = None

    # Server start timestamp for uptime calculation
    started_at: float = field(default_factory=time.time)

    @property
    def uptime_seconds(self) -> float:
        """Seconds elapsed since application startup."""
        return time.time() - self.started_at
