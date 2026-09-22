# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: TShark Telemetry Collector
# =============================================================================
# Description:
#   Collects network packet metrics and integrates with AI-Breadboard telemetry system.
#
# File: collector.py
# Project: ai-breadboard
# Package: apps.tshark
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""TShark telemetry collector for system metrics integration."""

from __future__ import annotations

from typing import List, Optional, Any

from logger import logger
from apps.windows.telemetry.models import HardwareSensor
from .sensors import get_tshark_sensors


class TSharkTelemetryCollector:
    """Collector for TShark network packet telemetry metrics."""

    def __init__(self) -> None:
        """Initialize TShark telemetry collector."""
        self._last_packets: List[Any] = []
        self._wrapper_available: bool = False
        self._interface: str = ""
        self._is_capturing: bool = False

    def set_capture_state(self, wrapper_available: bool = False, interface: str = "",
                         is_capturing: bool = False) -> None:
        """Set current capture session state.

        Args:
            wrapper_available: Whether TShark binary is available.
            interface: Current capture interface.
            is_capturing: Whether capture is active.
        """
        self._wrapper_available = wrapper_available
        self._interface = interface
        self._is_capturing = is_capturing

    def set_packets(self, packets: List[Any]) -> None:
        """Set captured packets for sensor metrics.

        Args:
            packets: List of captured PacketSummary objects.
        """
        self._last_packets = packets

    def get_sensors(self) -> List[HardwareSensor]:
        """Get TShark packet sensors for telemetry integration.

        Returns:
            List[HardwareSensor]: TShark packet telemetry sensors.
        """
        return get_tshark_sensors(
            packets=self._last_packets,
            wrapper_available=self._wrapper_available,
            interface=self._interface,
            is_capturing=self._is_capturing,
        )

    def get_snapshot(self) -> dict[str, Any]:
        """Get current TShark telemetry snapshot.

        Returns:
            dict[str, any]: TShark telemetry snapshot.
        """
        sensors = self.get_sensors()
        
        # Extract key metrics from sensors
        snapshot = {
            "tshark_available": self._wrapper_available,
            "capture_interface": self._interface,
            "capture_active": self._is_capturing,
            "sensors_count": len(sensors),
        }
        
        # Add sensor values
        for sensor in sensors:
            if sensor.category == "network_packet":
                if sensor.sensor_id == "pkt_total":
                    snapshot["total_packets"] = int(sensor.value)
                elif sensor.sensor_id == "pkt_bytes_total":
                    snapshot["total_bytes"] = int(sensor.value)
                elif sensor.sensor_id == "pkt_rate":
                    snapshot["packet_rate"] = float(sensor.value)
        
        return snapshot


def get_tshark_telemetry() -> List[HardwareSensor]:
    """Convenience function to get TShark telemetry sensors.

    Returns:
        List[HardwareSensor]: TShark telemetry sensors.
    """
    collector = TSharkTelemetryCollector()
    return collector.get_sensors()
