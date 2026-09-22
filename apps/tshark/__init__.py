# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Network analyzer module initialization and exports
# =============================================================================
# Description:
#   Package entry point exposing TShark wrapper, models, analyzer, AI detector
#   and packet sensors for deep packet inspection and network security monitoring.
#
# Examples:
#   >>> from apps.tshark import TSharkWrapper, TrafficAnalyzer, get_tshark_sensors
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.tshark
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
from .sensors import TSharkPacketSensor, get_tshark_sensors
from .collector import TSharkTelemetryCollector, get_tshark_telemetry

__all__ = [
    "NetworkInterface",
    "CaptureFilter",
    "PacketSummary",
    "TrafficStats",
    "AnomalyReport",
    "TSharkWrapper",
    "TrafficAnalyzer",
    "AIDetector",
    "TSharkPacketSensor",
    "get_tshark_sensors",
    "TSharkTelemetryCollector",
    "get_tshark_telemetry",
]
