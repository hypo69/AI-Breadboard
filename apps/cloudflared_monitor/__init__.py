# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Cloudflared Monitor Application Package
# =============================================================================
# Description:
#   Root package initialization for the Cloudflared Tunnel Monitor application.
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.cloudflared_monitor
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Cloudflared Tunnel Monitor standalone application."""

from .router import get_state, init_router, router
from .src.state import (
    CloudflaredAnomaly,
    CloudflaredDiagnosticReport,
    CloudflaredLogEntry,
    CloudflaredProcessInfo,
    CloudflaredState,
    EndpointHealth,
)

__all__ = [
    "CloudflaredAnomaly",
    "CloudflaredDiagnosticReport",
    "CloudflaredLogEntry",
    "CloudflaredProcessInfo",
    "CloudflaredState",
    "EndpointHealth",
    "get_state",
    "init_router",
    "router",
]
