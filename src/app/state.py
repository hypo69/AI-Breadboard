# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard APP - State Module
# =============================================================================
# Description:
#   Application state container stored in FastAPI's app.state.
#
# Usage Examples:
#   Python API:
#     from src.app.state import AppState
#
#     service = AppState()
#     result = service.uptime_seconds()
#     print(result)
#
# File: state.py
# Project: ai-breadboard
# Package: src.app
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

from __future__ import annotations
"""Application state container stored in FastAPI's app.state.

Access from request handlers:
    chat_model = request.app.state.chat_model
    ws_hub     = request.app.state.ws_hub
    metrics    = request.app.state.metrics

Both single-user (localhost) and multi-user (server) deployments use
the same state — user isolation is handled at the business logic layer
via user_id, not via separate service instances."""

import time
from dataclasses import dataclass, field
from typing import Any, Optional

@dataclass
class AppState:
    """All shared application services, populated during lifespan startup."""
    chat_model: Optional[Any] = None
    narrator_model: Optional[Any] = None
    ws_hub: Optional[Any] = None
    metrics: Optional[Any] = None
    plugin_registry: Optional[Any] = None
    plugins: Optional[Any] = None
    started_at: float = field(default_factory=time.time)

    @property
    def uptime_seconds(self) -> float:
        """Seconds elapsed since application startup."""
        return time.time() - self.started_at