# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Network analyzer module initialization and exports
# =============================================================================
# Description:
#   Package entry point exposing TShark wrapper, models, analyzer, and AI detector
#   for deep packet inspection and network security monitoring.
#
# Examples:
#   >>> from src.network import TSharkWrapper, TrafficAnalyzer
#
# File: __init__.py
# Project: ai-breadboard
# Package: src.network
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Network traffic and TShark capture module."""

from .models import (
    NetworkInterface,
    CaptureFilter,
    PacketSummary,
    TrafficStats,
    AnomalyReport,
)
from .tshark_wrapper import TSharkWrapper
from .analyzer import TrafficAnalyzer
from .ai_detector import AIDetector

__all__ = [
    "NetworkInterface",
    "CaptureFilter",
    "PacketSummary",
    "TrafficStats",
    "AnomalyReport",
    "TSharkWrapper",
    "TrafficAnalyzer",
    "AIDetector",
]
